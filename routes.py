from flask import render_template,request,url_for,redirect,flash
from app import app, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Trek, Booking
from flask_login import login_user, logout_user, login_required, current_user
from functools import wraps
from datetime import datetime

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
    treks = Trek.query.count()
    bookings = Booking.query.count()
    return render_template('admin/admin.html', users=users, pending_staff=pending_staff, staff=staff, treks=treks, bookings=bookings)

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
        
        if not assigned_staff_id:
            if status in ['Open', 'Approved']:
                flash('You cannot add a trek with status as Open or Approved without assigning staff!', 'warning')
                return redirect(url_for('add_trek'))
            else:
                status = 'Pending'
        if not name or not location or not difficulty or not price or not duration or not available_slots or not start_date or not end_date or not status:
            flash('Fill the required fields to Continue!', 'danger')
            return redirect(url_for('add_trek'))
        db.session.add(Trek(name=name, location=location, difficulty=difficulty, price=price, description=description, duration=duration, available_slots=available_slots, assigned_staff_id=assigned_staff_id, start_date=start_date, end_date=end_date, status=status))
        db.session.commit()
        flash('Trek added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    staff = User.query.filter_by(role='staff' , is_blacklisted=False , staff_status='approved').all()
    return render_template('admin/add_trek.html',staff=staff)
        
        

@app.route('/staff')
@login_required
@staff_required
def staff_dashboard():
    return render_template('staff/staff.html')

@app.route('/user')
@login_required
@user_required
def user_dashboard():
    return render_template('user.html')