from flask import render_template,request,url_for,redirect,flash
from app import app
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Trek, Booking



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.passhash, password):
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
        if(password != cpassword):
            flash('Passwords do not match!', 'error')
            return redirect(url_for('register'))
        if(User.query.filter_by(username=username).first()):
            flash('Username already exists!', 'error')
            return redirect(url_for('register'))
        if(User.query.filter_by(phone=phone).first()):
            flash('Phone number already exists!', 'error')
            return redirect(url_for('register'))
        db.session.add(User(username=username, phone=phone, passhash=generate_password_hash(password), fullname=fullname))
        db.session.commit()
        flash('Registration successful!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')