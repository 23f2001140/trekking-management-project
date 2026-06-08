from flask import render_template,request,url_for,redirect,flash
from app import app, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Trek, Booking
from flask_login import login_user, logout_user, login_required, current_user
from functools import wraps

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to continue.', 'error')
            return redirect(url_for('login'))
        if current_user.role != 'admin':
            flash('Access denied!', 'error')
            return redirect(url_for('index'))
        return function(*args, **kwargs)
    return wrapper

def staff_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to continue.', 'error')
            return redirect(url_for('login'))
        if current_user.role != 'staff':
            flash('Access denied!', 'error')
            return redirect(url_for('index'))
        return function(*args, **kwargs)
    return wrapper

def user_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to continue.', 'error')
            return redirect(url_for('login'))
        if current_user.role != 'user':
            flash('Access denied!', 'error')
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
                flash('Your account has been blacklisted. Please contact support at support@trekcentral.com.', 'error')
                return redirect(url_for('login'))
            if user.role == 'staff' and user.staff_status == 'pending':
                flash('Your staff account is pending approval. Please wait for admin approval.', 'error')
                return redirect(url_for('login'))
            
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        
        else:
            flash('Invalid username or password!', 'error')
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
            flash('All fields are required!', 'error')
            return redirect(url_for('register'))
        if(password != cpassword):
            flash('Passwords do not match!', 'error')
            return redirect(url_for('register'))
        if(User.query.filter_by(username=username).first()):
            flash('Username already exists!', 'error')
            return redirect(url_for('register'))
        if(User.query.filter_by(phone=phone).first()):
            flash('Phone number already exists!', 'error')
            return redirect(url_for('register'))
        if role not in ['user', 'staff']:
            flash('Invalid role selected!', 'error')
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

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    users = User.query.filter_by(role='user').all()
    pending_staff = User.query.filter_by(role='staff', staff_status='pending').all()
    staff = User.query.filter_by(role='staff', staff_status='approved').all()
    return render_template('admin.html', users=users, pending_staff=pending_staff, staff=staff)

@app.route('/admin/approve_staff/<int:staff_id>')
@login_required
@admin_required
def approve_staff(staff_id):
    staffm=User.query.get(staff_id)
    if not staffm:
        flash('Staff member not found!', 'error')
        return redirect(url_for('admin_dashboard'))
    if staffm.role != 'staff':
        flash('User is not a staff member!', 'error')
        return redirect(url_for('admin_dashboard'))
    if staffm.staff_status != 'pending':
        flash('Staff member is not pending approval!', 'error')
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
        flash('Staff member not found!', 'error')
        return redirect(url_for('admin_dashboard'))
    if staffm.role != 'staff':
        flash('User is not a staff member!', 'error')
        return redirect(url_for('admin_dashboard'))
    if staffm.staff_status != 'pending':
        flash('Staff member is not pending approval!', 'error')
        return redirect(url_for('admin_dashboard'))
    db.session.delete(staffm)
    db.session.commit()
    flash('Staff member rejected and deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/staff')
@login_required
@staff_required
def staff_dashboard():
    return render_template('staff.html')

@app.route('/user')
@login_required
@user_required
def user_dashboard():
    return render_template('user.html')