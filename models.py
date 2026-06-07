from flask_sqlalchemy import SQLAlchemy
from app import app

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    phone= db.Column(db.String(10), unique=True, nullable=False)
    passhash = db.Column(db.String(256), nullable=False)
    fullname = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    is_blacklisted = db.Column(db.Boolean, nullable=False, default=False)
    
    bookings = db.relationship('Booking', backref='user', lazy=True)
    assigned_treks = db.relationship('Trek', backref='assigned_staff', lazy=True)
    
class Trek(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)
    duration = db.Column(db.Integer, nullable=False) 
    available_slots = db.Column(db.Integer, nullable=False)
    assigned_staff_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Open')
    
    bookings = db.relationship('Booking', backref='trek', lazy=True)    
    
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    trek_id = db.Column(db.Integer, db.ForeignKey('trek.id'), nullable=False)
    booking_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Booked')    
    
with app.app_context():
    db.create_all()
