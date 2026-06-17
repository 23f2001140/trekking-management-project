from flask import render_template,request,url_for,redirect,flash
from app import app, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Trek, Booking
from flask_login import login_user, logout_user, login_required, current_user
from functools import wraps
from datetime import datetime
import os

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to continue.', 'danger')
            return redirect(url_for('login'))
        if current_user.role != 'admin':
            flash('Access denied!', 'danger')
            return redirect(url_for('index'))
        return function(*args, **kwargs)
    return wrapper

def staff_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to continue.', 'danger')
            return redirect(url_for('login'))
        if current_user.role != 'staff':
            flash('Access denied!', 'danger')
            return redirect(url_for('index'))
        return function(*args, **kwargs)
    return wrapper

def user_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to continue.', 'danger')
            return redirect(url_for('login'))
        if current_user.role != 'user':
            flash('Access denied!', 'danger')
            return redirect(url_for('index'))
        return function(*args, **kwargs)
    return wrapper

def not_blacklisted(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if current_user.is_blacklisted:
            flash('Your account has been blacklisted. Please contact support at support@trekcentral.com.', 'danger')
            logout_user()
            return redirect(url_for('login'))
        return function(*args, **kwargs)
    return wrapper

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif current_user.role == 'staff':
            return redirect(url_for('staff_dashboard'))
        elif current_user.role == 'user':
            return redirect(url_for('user_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.passhash, password):
            if user.is_blacklisted:
                flash('Your account has been blacklisted. Please contact support at support@trekcentral.com.', 'danger')
                return redirect(url_for('login'))
            if user.role == 'staff' and user.staff_status == 'pending':
                flash('Your staff account is pending approval. Please wait for admin approval.', 'danger')
                return redirect(url_for('login'))
            
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        
        else:
            flash('Invalid username or password!', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        phone = request.form['phone']
        password = request.form['password']
        cpassword = request.form['cpassword']
        fullname = request.form['fullname']
        role = request.form['role']
        if not username or not phone or not password or not cpassword or not fullname:
            flash('All fields are required!', 'danger')
            return redirect(url_for('register'))
        if(password != cpassword):
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('register'))
        if(User.query.filter_by(username=username).first()):
            flash('Username already exists!', 'danger')
            return redirect(url_for('register'))
        if(User.query.filter_by(phone=phone).first()):
            flash('Phone number already exists!', 'danger')
            return redirect(url_for('register'))
        if role not in ['user', 'staff']:
            flash('Invalid role selected!', 'danger')
            return redirect(url_for('register'))
        if role == 'staff':
            db.session.add(User(username=username, phone=phone, passhash=generate_password_hash(password), fullname=fullname, role='staff'))
            db.session.commit()
            flash('Your registration for staff is successful! Please wait for admin approval.', 'success')
            return redirect(url_for('login'))
        if role == 'user':
            db.session.add(User(username=username, phone=phone, passhash=generate_password_hash(password), fullname=fullname))
            db.session.commit()
            flash('Registration successful!', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

#Admin routes
@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    users = User.query.filter_by(role='user').count()
    pending_staff = User.query.filter_by(role='staff', staff_status='pending').all()
    staff = User.query.filter_by(role='staff', staff_status='approved').count()
    treks = Trek.query.all()
    bookings = Booking.query.count()
    chart_labels=[]
    chart_count=[]
    for trek in treks:
        chart_labels.append(trek.name)
        bookings_count=len([booking for booking in trek.bookings if booking.status == 'Booked'])
        chart_count.append(bookings_count)
    
    return render_template('admin/admin.html', users=users, pending_staff=pending_staff, staff=staff, treks=treks, bookings=bookings, chart_labels=chart_labels, chart_count=chart_count)

@app.route('/admin/approve_staff/<int:staff_id>')
@login_required
@admin_required
def approve_staff(staff_id):
    staffm=User.query.get(staff_id)
    if not staffm:
        flash('Staff member not found!', 'danger')
        return redirect(url_for('admin_dashboard'))
    if staffm.role != 'staff':
        flash('User is not a staff member!', 'danger')
        return redirect(url_for('admin_dashboard'))
    if staffm.staff_status != 'pending':
        flash('Staff member is not pending approval!', 'danger')
        return redirect(url_for('admin_dashboard'))
    staffm.staff_status = 'approved'
    db.session.commit()
    flash('Staff member approved successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject_staff/<int:staff_id>')
@login_required
@admin_required
def reject_staff(staff_id):
    staffm=User.query.get(staff_id)
    if not staffm:
        flash('Staff member not found!', 'danger')
        return redirect(url_for('admin_dashboard'))
    if staffm.role != 'staff':
        flash('User is not a staff member!', 'danger')
        return redirect(url_for('admin_dashboard'))
    if staffm.staff_status != 'pending':
        flash('Staff member is not pending approval!', 'danger')
        return redirect(url_for('admin_dashboard'))
    db.session.delete(staffm)
    db.session.commit()
    flash('Staff member rejected and deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/profile', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_profile():
    if request.method == 'POST':
        uname = request.form['username']
        fullname = request.form['fullname']
        phone = request.form['phone']
        password = request.form['password']
        cpassword = request.form['cpassword']
        confirm_password = request.form['confirm_password']
        
        if(User.query.filter_by(username=uname).first() and uname != current_user.username):
            flash('Username already exists!', 'danger')
            return redirect(url_for('admin_profile'))
        
        if not fullname or not phone:
            flash('Full name and phone number are required!', 'danger')
            return redirect(url_for('admin_profile'))
        
        if not check_password_hash(current_user.passhash, cpassword):
            flash('Incorrect current password!', 'danger')
            return redirect(url_for('admin_profile'))
        
        if(uname != current_user.username):
            current_user.username = uname
        current_user.fullname = fullname
        current_user.phone = phone
        
        if password:
            if password != confirm_password:
                flash('New passwords do not match!', 'danger')
                return redirect(url_for('admin_profile'))
            current_user.passhash = generate_password_hash(password)
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('admin_profile'))
    
    return render_template('admin/admin_profile.html')

#For image upload
TREK_IMAGES_FOLDER = os.path.join( 'static','trek_images')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_trek_image(trek_id):
    for ext in ['jpg', 'jpeg', 'png']:
        path = os.path.join(TREK_IMAGES_FOLDER, f"{trek_id}.{ext}")

        if os.path.exists(path):
            return url_for('static', filename=f"trek_images/{trek_id}.{ext}")

    return None

@app.route('/admin/add_trek', methods=['GET', 'POST'])
@login_required
@admin_required
def add_trek():
    if request.method == 'POST':
        name = request.form['name']
        location = request.form['location']
        difficulty = request.form['difficulty']
        price = request.form['price']
        description = request.form['description'] or None
        available_slots = request.form['available_slots']
        assigned_staff_id = request.form['assigned_staff_id'] or None
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
        status = request.form['status']
        
        if(end_date <= start_date):
            flash('End date should be greater than start date!', 'danger')
            return redirect(url_for('add_trek'))
        
        duration = (end_date - start_date).days
        
        if available_slots.isnumeric() and int(available_slots) < 0:
            flash('Slots cannot be negative!', 'danger')
            return redirect(url_for('add_trek'))
        
        if not assigned_staff_id:
            if status in ['Open', 'Approved']:
                flash('You cannot add a trek with status as Open or Approved without assigning staff!', 'warning')
                return redirect(url_for('add_trek'))
            else:
                status = 'Pending'
        if not name or not location or not difficulty or not price or not duration or not available_slots or not start_date or not end_date or not status:
            flash('Fill the required fields to Continue!', 'danger')
            return redirect(url_for('add_trek'))
        
        trek=Trek(name=name, location=location, difficulty=difficulty, price=price, description=description, duration=duration, available_slots=available_slots, assigned_staff_id=assigned_staff_id, start_date=start_date, end_date=end_date, status=status)
        db.session.add(trek)
        db.session.commit()
        
        image= request.files.get('image')
        image_ext=None
        if image and allowed_file(image.filename):
            image_ext=image.filename.rsplit('.', 1)[1].lower()
            os.makedirs(TREK_IMAGES_FOLDER, exist_ok=True)
            image.save(os.path.join(TREK_IMAGES_FOLDER, f"{trek.id}.{image_ext}"))
        
        flash('Trek added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    staff = User.query.filter_by(role='staff' , is_blacklisted=False , staff_status='approved').all()
    return render_template('admin/add_trek.html',staff=staff)

@app.route('/admin/treks_details' , methods=['GET', 'POST'])
@login_required
@admin_required
def trek_details():
    treks_q=Trek.query
    difficulty=request.args.get('difficulty')
    search=request.args.get('sch')
    if difficulty and search:
        if search.isnumeric():
            treks_q=treks_q.filter(Trek.difficulty==difficulty , Trek.id==search)
        else:
             treks_q=treks_q.filter(Trek.difficulty==difficulty , Trek.location.ilike('%'+search+'%'))
    elif difficulty:
        treks_q=treks_q.filter_by(difficulty=difficulty)
    elif search:
        if search.isnumeric():
            treks_q=treks_q.filter(Trek.id==search)
        else:
            treks_q=treks_q.filter(Trek.location.ilike('%'+search+'%'))
    
    if not treks_q.first():
        flash('No Treks Found!', 'danger')
        return redirect(url_for('trek_details'))
        
    treks=treks_q.all()
    return render_template('admin/treks.html' , treks=treks, get_trek_image=get_trek_image)
        
@app.route('/admin/trek_update/<int:trek_id>' , methods=['GET', 'POST'])
@login_required
@admin_required
def trek_update(trek_id):
    if request.method == 'POST':
        trek=Trek.query.get(trek_id)
        if not trek:
            flash('Trek not found!', 'danger')
            return redirect(url_for('trek_details'))
        name = request.form.get('name')
        location = request.form.get('location')
        difficulty = request.form.get('difficulty')
        price = request.form.get('price')
        description = request.form.get('description')
        available_slots = request.form.get('available_slots')
        assigned_staff_id = request.form.get('assigned_staff_id')
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
        status = request.form.get('status')
        
        if(end_date <= start_date):
            flash('End date should be greater than start date!', 'danger')
            return redirect(url_for('trek_update', trek_id=trek_id))
        
        duration = (end_date - start_date).days
        if available_slots.isnumeric() and int(available_slots) < 0:
            flash('Slots cannot be negative!', 'danger')
            return redirect(url_for('add_trek'))
        
        if not assigned_staff_id:
            if status in ['Open', 'Approved', 'Closed', 'Completed']:
                flash('You cannot add a trek with status as Open, Approved, Closed or Completed without assigning staff!', 'warning')
                return redirect(url_for('trek_update', trek_id=trek_id))
            else:
                status = 'Pending'
        else:
            if status == 'Pending':
                flash('You cannot choose Trek status as Pending When staff is assigned!', 'warning')
                return redirect(url_for('trek_update', trek_id=trek_id))
        if not name or not location or not difficulty or not price or not duration or not available_slots or not start_date or not end_date or not status:
            flash('Fill the required fields to Continue!', 'danger')
            return redirect(url_for('trek_update', trek_id=trek_id))
        trek.name = name
        trek.location = location
        trek.difficulty = difficulty
        trek.price = price
        trek.description = description
        trek.duration = duration
        trek.available_slots = available_slots
        trek.assigned_staff_id = assigned_staff_id
        trek.start_date = start_date
        trek.end_date = end_date
        trek.status = status
        db.session.commit()
        flash('Trek updated successfully!', 'success')
        return redirect(url_for('trek_details'))
        
        
    trek=Trek.query.get(trek_id)
    staff = User.query.filter_by(role='staff' , is_blacklisted=False , staff_status='approved').all()
    if not trek:
        flash('Trek not found!', 'danger')
        return redirect(url_for('trek_details'))
    return render_template('admin/update_trek.html' , trek=trek , get_trek_image=get_trek_image, staff=staff)

@app.route('/admin/delete_trek/<int:trek_id>' , methods=['GET', 'POST'])
@login_required
@admin_required
def delete_trek(trek_id):
    if request.method == 'POST':
        trek=Trek.query.get(trek_id)
        if not trek:
            flash('Invalid trek id!', 'danger')
            return redirect(url_for('trek_details'))
        
        for ext in ALLOWED_EXTENSIONS:
            path = os.path.join(TREK_IMAGES_FOLDER, f"{trek.id}.{ext}")
            if os.path.exists(path):
                os.remove(path)
                break
        db.session.delete(trek)
        db.session.commit()
        flash('Trek deleted successfully!', 'success')
        return redirect(url_for('trek_details'))
    
    trek=Trek.query.get(trek_id)
    if not trek:
        flash('Invalid trek id!', 'danger')
        return redirect(url_for('trek_details'))
    
    
    return render_template('admin/trek_delete_confirmation.html' , trek_id=trek_id)

@app.route('/admin/users_details')
@login_required
@admin_required
def admin_users_details():
    users_q=User.query.filter_by(role='user')
    user=request.args.get('user')
    if user:
        if user.isnumeric():
            users_q=users_q.filter(User.id==user)
        else:
            users_q=users_q.filter(User.fullname.ilike('%'+user+'%'))
    
    if not users_q.first():
        flash('No Users Found!', 'danger')
        return redirect(url_for('admin_users_details'))
    users=users_q.all()
    return render_template('admin/users_details.html', users=users)

@app.route('/admin/blacklist_user/<int:user_id>')
@login_required
@admin_required
def admin_blacklist_user(user_id):
    user=User.query.get(user_id)
    if not user:
        flash('User not found!', 'danger')
        return redirect(url_for('admin_users_details'))
    if user.is_blacklisted:
        flash('User is already blacklisted!', 'danger')
        return redirect(url_for('admin_users_details'))
    user.is_blacklisted=True
    db.session.commit()
    flash('User blacklisted successfully!', 'success')
    return redirect(url_for('admin_users_details'))

@app.route('/admin/activate_user/<int:user_id>')
@login_required
@admin_required
def admin_activate_user(user_id):
    user=User.query.get(user_id)
    if not user:
        flash('User not found!', 'danger')
        return redirect(url_for('admin_users_details'))
    if not user.is_blacklisted:
        flash('User is already activated!', 'danger')
        return redirect(url_for('admin_users_details'))
    user.is_blacklisted=False
    db.session.commit()
    flash('User activated successfully!', 'success')
    return redirect(url_for('admin_users_details'))

@app.route('/admin/staff_details')
@login_required
@admin_required
def admin_staff_details():
    staff_q=User.query.filter_by(role='staff' , staff_status='approved')
    pending_staff = User.query.filter_by(role='staff', staff_status='pending').all()
    staf=request.args.get('staff')
    if staf:
        if staf.isnumeric():
            staff_q=staff_q.filter(User.id==staf)
        else:
            staff_q=staff_q.filter(User.fullname.ilike('%'+staf+'%'))
    
    if not staff_q.first():
        flash('No Staff Found!', 'danger')
        return redirect(url_for('admin_staff_details'))
    staff=staff_q.all()
    return render_template('admin/staff_details.html', staff=staff, pending_staff=pending_staff)

@app.route('/admin/blacklist_staff/<int:staff_id>')
@login_required
@admin_required
def admin_blacklist_staff(staff_id):
    staff=User.query.get(staff_id)
    if not staff:
        flash('Staff not found!', 'danger')
        return redirect(url_for('admin_staff_details'))
    if staff.is_blacklisted:
        flash('Staff is already blacklisted!', 'danger')
        return redirect(url_for('admin_staff_details'))
    staff.is_blacklisted=True
    db.session.commit()
    flash('Staff blacklisted successfully!', 'success')
    return redirect(url_for('admin_staff_details'))

@app.route('/admin/activate_staff/<int:staff_id>')
@login_required
@admin_required
def admin_activate_staff(staff_id):
    staff=User.query.get(staff_id)
    if not staff:
        flash('Staff not found!', 'danger')
        return redirect(url_for('admin_staff_details'))
    if not staff.is_blacklisted:
        flash('Staff is already activated!', 'danger')
        return redirect(url_for('admin_staff_details'))
    staff.is_blacklisted=False
    db.session.commit()
    flash('Staff activated successfully!', 'success')
    return redirect(url_for('admin_staff_details'))

@app.route('/admin/booking_details')
@login_required
@admin_required
def admin_booking_details():
    bookings=Booking.query.all()
    return render_template('admin/admin_bookings.html', bookings=bookings)


@app.route('/user')
@login_required
@user_required
@not_blacklisted
def user_dashboard():
    treks=Trek.query.filter_by(status='Open').all()
    upcoming_treks=Trek.query.filter_by(status='Approved').all()
    bookings=Booking.query.filter_by(user_id=current_user.id).all()
    bookings_status={ booking.trek_id: booking.status for booking in bookings }
    difficulty=request.args.get('difficulty')
    location=request.args.get('location')
    
    if difficulty and location:
        treks=Trek.query.filter(Trek.difficulty==difficulty , Trek.location.ilike('%'+location+'%') , Trek.status=='Open').all()
        upcoming_treks=Trek.query.filter(Trek.difficulty==difficulty , Trek.location.ilike('%'+location+'%') , Trek.status=='Approved').all()
    elif difficulty:
        treks=Trek.query.filter_by(difficulty=difficulty , status='Open').all()
        upcoming_treks=Trek.query.filter_by(difficulty=difficulty , status='Approved').all()
    elif location:
        treks=Trek.query.filter(Trek.location.ilike('%'+location+'%') , Trek.status=='Open').all()
        upcoming_treks=Trek.query.filter(Trek.location.ilike('%'+location+'%') , Trek.status=='Approved').all()

    return render_template('users/user.html', treks=treks, upcoming_treks=upcoming_treks, bookings_status=bookings_status, get_trek_image=get_trek_image)

@app.route('/user/trek_booking/<int:trek_id>')
@login_required
@user_required
@not_blacklisted
def user_trek_booking(trek_id):
    trek=Trek.query.get(trek_id)
    if not trek:
        flash('Trek not found!', 'danger')
        return redirect(url_for('user_dashboard'))
    if trek.status != 'Open':
        flash('You cannot book this trek!', 'danger')
        return redirect(url_for('user_dashboard'))
    if(Booking.query.filter_by(user_id=current_user.id, trek_id=trek_id, status='Booked').first()):
        flash('You have already booked this trek!', 'danger')
        return redirect(url_for('user_dashboard'))
    if(Booking.query.filter_by(user_id=current_user.id, trek_id=trek_id, status='Cancelled').first()):
        flash('You have cancelled this booking! Cannot book again!', 'danger')
        return redirect(url_for('user_dashboard'))
    if trek.available_slots < 1:
        flash('Slots Are Full!', 'danger')
        return redirect(url_for('user_dashboard'))
    trek.available_slots -= 1
    booking_date=datetime.now().date()
    booking=Booking(user_id=current_user.id, trek_id=trek_id, booking_date=booking_date)
    db.session.add(booking)
    db.session.commit()
    flash('Booking successful!', 'success')
    return redirect(url_for('user_dashboard'))

@app.route('/user/my_bookings')
@login_required
@user_required
@not_blacklisted
def my_bookings():
    bookings=Booking.query.filter_by(user_id=current_user.id).all()
    ongoing_bookings=[booking for booking in bookings if booking.status=='Booked' and booking.trek.status in ['Open', 'Closed', 'Started']]
    past_bookings=[booking for booking in bookings if booking.status=='Cancelled' or booking.trek.status == 'Completed']
    return render_template('users/my_bookings.html', ongoing_bookings=ongoing_bookings, past_bookings=past_bookings, get_trek_image=get_trek_image)

@app.route('/user/cancel_booking/<int:booking_id>' , methods=['GET', 'POST'])
@login_required
@user_required
@not_blacklisted
def cancel_booking(booking_id):
    if request.method == 'POST':
        booking=Booking.query.get(booking_id)
        if not booking:
            flash('Booking not found!', 'danger')
            return redirect(url_for('user_dashboard'))
        if booking.user_id != current_user.id:
            flash('You are not authorized to cancel this booking!', 'danger')
            return redirect(url_for('user_dashboard'))
        booking.trek.available_slots += 1
        booking.status='Cancelled'
        db.session.commit()
        flash('Booking cancelled successfully!', 'success')
        return redirect(url_for('user_dashboard'))
    booking=Booking.query.get(booking_id)
    if not booking:
        flash('Booking not found!', 'danger')
        return redirect(url_for('user_dashboard'))
    if booking.user_id != current_user.id:
        flash('You are not authorized to cancel this booking!', 'danger')
        return redirect(url_for('user_dashboard'))
    return render_template('users/cancel_booking_confirmation.html', booking=booking)
    

@app.route('/user/profile', methods=['GET', 'POST'])
@login_required
@user_required
@not_blacklisted
def user_profile():
    if request.method == 'POST':
        uname = request.form['username']
        fullname = request.form['fullname']
        phone = request.form['phone']
        password = request.form['password']
        cpassword = request.form['cpassword']
        confirm_password = request.form['confirm_password']
        
        if(User.query.filter_by(username=uname).first() and uname != current_user.username):
            flash('Username already exists!', 'danger')
            return redirect(url_for('user_profile'))
        
        if not fullname or not phone:
            flash('Full name and phone number are required!', 'danger')
            return redirect(url_for('user_profile'))
        
        if not check_password_hash(current_user.passhash, cpassword):
            flash('Incorrect current password!', 'danger')
            return redirect(url_for('user_profile'))
        
        if(uname != current_user.username):
            current_user.username = uname
        current_user.fullname = fullname
        current_user.phone = phone
        
        if password:
            if password != confirm_password:
                flash('New passwords do not match!', 'danger')
                return redirect(url_for('user_profile'))
            current_user.passhash = generate_password_hash(password)
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('user_profile'))
    
    return render_template('users/user_profile.html')


@app.route('/staff')
@login_required
@staff_required
@not_blacklisted
def staff_dashboard():
    assigned_treks=Trek.query.filter_by(assigned_staff_id=current_user.id).all()
    trek_participants={}
    for trek in assigned_treks:
        trek_participants[trek.id]=len([booking for booking in trek.bookings if booking.status == 'Booked'])
    total_p=0
    for trek in assigned_treks:
        if trek.status != 'Completed':
            total_p += len([booking for booking in trek.bookings if booking.status == 'Booked'])
        
    return render_template('staff/staff.html', assigned_treks=assigned_treks, trek_participants=trek_participants, total_p=total_p, get_trek_image=get_trek_image)

@app.route('/staff/manage_trek/<int:trek_id>', methods=['GET', 'POST'])
@login_required
@staff_required
@not_blacklisted
def manage_trek(trek_id):
    if request.method == 'POST':
        trek=Trek.query.get(trek_id)
        if not trek:
            flash('Trek not found!', 'danger')
            return redirect(url_for('staff_dashboard'))
        if trek.assigned_staff_id != current_user.id:
            flash('You are not authorized to manage this trek!', 'danger')
            return redirect(url_for('staff_dashboard'))
        status = request.form.get('status')
        available_slots = request.form.get('available_slots')
        if(status):
            if status in ['Open', 'Closed', 'Started', 'Completed']:
                trek.status = status
                db.session.commit()
                flash('Trek status updated successfully!', 'success')
                return redirect(url_for('manage_trek', trek_id=trek_id))
            else:
                flash('Invalid status!', 'danger')
                return redirect(url_for('manage_trek', trek_id=trek_id))
        if available_slots.isnumeric():
            if int(available_slots) < 0:
                flash('Slots cannot be negative!', 'danger')
                return redirect(url_for('manage_trek', trek_id=trek_id))
            else:
                trek.available_slots = int(available_slots)
                db.session.commit()
                flash('Slots updated successfully!', 'success')
                return redirect(url_for('manage_trek', trek_id=trek_id))
        else:
            flash('Please Enter Numeric Value for slots!', 'danger')
            return redirect(url_for('manage_trek', trek_id=trek_id))
    trek=Trek.query.get(trek_id)
    trek_users=[booking for booking in trek.bookings if booking.status == 'Booked']
    cancelled_users=[booking for booking in trek.bookings if booking.status == 'Cancelled']
    
    if not trek:
        flash('Trek not found!', 'danger')
        return redirect(url_for('staff_dashboard'))
    if trek.assigned_staff_id != current_user.id:
        flash('You are not authorized to manage this trek!', 'danger')
        return redirect(url_for('staff_dashboard'))
    return render_template('staff/manage_trek.html', trek=trek, trek_users=trek_users, cancelled_users=cancelled_users, get_trek_image=get_trek_image)

@app.route('/staff/profile', methods=['GET', 'POST'])
@login_required
@staff_required
@not_blacklisted
def staff_profile():
    if request.method == 'POST':
        uname = request.form['username']
        fullname = request.form['fullname']
        phone = request.form['phone']
        password = request.form['password']
        cpassword = request.form['cpassword']
        confirm_password = request.form['confirm_password']
        
        if(User.query.filter_by(username=uname).first() and uname != current_user.username):
            flash('Username already exists!', 'danger')
            return redirect(url_for('staff_profile'))
        
        if not fullname or not phone:
            flash('Full name and phone number are required!', 'danger')
            return redirect(url_for('staff_profile'))
        
        if not check_password_hash(current_user.passhash, cpassword):
            flash('Incorrect current password!', 'danger')
            return redirect(url_for('staff_profile'))
        
        if(uname != current_user.username):
            current_user.username = uname
        current_user.fullname = fullname
        current_user.phone = phone
        
        if password:
            if password != confirm_password:
                flash('New passwords do not match!', 'danger')
                return redirect(url_for('staff_profile'))
            current_user.passhash = generate_password_hash(password)
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('staff_profile'))
    
    return render_template('staff/staff_profile.html')