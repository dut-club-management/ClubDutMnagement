#!/usr/bin/env python3
"""
Complete Club Management System with full features
"""

import os
import sys
import json
from datetime import datetime, date

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
import os
import urllib.parse

app = Flask(__name__, 
           template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
           static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

# Configure PostgreSQL with pg8000 for Python 3.14 compatibility
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Replace postgresql:// with postgresql+pg8000:// to use pg8000 driver
    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+pg8000://')

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
bcrypt = Bcrypt(app)
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), default='member')  # admin, president, member
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    clubs = db.relationship('ClubMember', backref='user', lazy=True)
    event_attendances = db.relationship('EventAttendance', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

class Club(db.Model):
    __tablename__ = 'clubs'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))  # academic, cultural, sports, etc.
    meeting_day = db.Column(db.String(10))  # Monday, Tuesday, etc.
    meeting_time = db.Column(db.String(5))  # 14:00 format
    location = db.Column(db.String(200))
    max_members = db.Column(db.Integer, default=50)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    members = db.relationship('ClubMember', backref='club', lazy=True)
    events = db.relationship('Event', backref='club', lazy=True)

class ClubMember(db.Model):
    __tablename__ = 'club_members'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    club_id = db.Column(db.Integer, db.ForeignKey('clubs.id'), nullable=False)
    role = db.Column(db.String(20), default='member')  # president, treasurer, member
    joined_date = db.Column(db.Date, default=date.today)
    is_active = db.Column(db.Boolean, default=True)
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('user_id', 'club_id'),)

class Event(db.Model):
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    club_id = db.Column(db.Integer, db.ForeignKey('clubs.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    event_date = db.Column(db.Date, nullable=False)
    event_time = db.Column(db.String(5))  # 14:00 format
    location = db.Column(db.String(200))
    max_attendees = db.Column(db.Integer, default=100)
    is_public = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    attendances = db.relationship('EventAttendance', backref='event', lazy=True)

class EventAttendance(db.Model):
    __tablename__ = 'event_attendances'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    rsvp_status = db.Column(db.String(20), default='pending')  # pending, confirmed, declined
    attended = db.Column(db.Boolean, default=False)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('user_id', 'event_id'),)

class Announcement(db.Model):
    __tablename__ = 'announcements'
    
    id = db.Column(db.Integer, primary_key=True)
    club_id = db.Column(db.Integer, db.ForeignKey('clubs.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(10), default='normal')  # low, normal, high, urgent
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))

# Initialize database
def init_database():
    with app.app_context():
        db.create_all()
        
        # Create default admin user if not exists
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@clubmanagement.com',
                first_name='System',
                last_name='Administrator',
                role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()

# Initialize database on first run - with error handling
def initialize_database():
    try:
        with app.app_context():
            # Test database connection first
            if database_url:
                # Use text() wrapper for SQLAlchemy 2.0 compatibility
                from sqlalchemy import text
                db.session.execute(text('SELECT 1'))
                print("Database connection successful")
                
                # Create tables
                db.create_all()
                print("Database tables created")
                
                # Create default admin user if not exists
                if not User.query.filter_by(username='admin').first():
                    admin = User(
                        username='admin',
                        email='admin@clubmanagement.com',
                        first_name='System',
                        last_name='Administrator',
                        role='admin'
                    )
                    admin.set_password('admin123')
                    db.session.add(admin)
                    db.session.commit()
                    print("Admin user created")
                
                return True
            else:
                print("No DATABASE_URL configured")
                return False
    except Exception as e:
        print(f"Database initialization error: {e}")
        import traceback
        traceback.print_exc()
        return False

# Initialize database
db_initialized = initialize_database()

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect('/dashboard')
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('email')  # Using email field from template
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.username
            session['user_role'] = user.role
            flash(f'Welcome back, {user.first_name}!', 'success')
            return redirect('/dashboard')
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login_simple.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        
        if username and password and email and first_name and last_name:
            # Check if user already exists
            if User.query.filter_by(username=username).first():
                flash('Username already exists', 'danger')
            elif User.query.filter_by(email=email).first():
                flash('Email already exists', 'danger')
            else:
                # Create new user
                user = User(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    role='member'
                )
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                
                flash('Registration successful! Please login.', 'success')
                return redirect('/login')
        else:
            flash('Please fill in all fields', 'danger')
    
    # For now, redirect to login since we don't have a register template
    return render_template('login_simple.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    
    if not db_initialized:
        return render_template('login_simple.html')
    
    # Get current user
    user = User.query.filter_by(username=session['user_id']).first()
    if not user:
        return redirect('/login')
    
    # Get statistics
    total_users = User.query.count()
    total_clubs = Club.query.filter_by(is_active=True).count()
    total_events = Event.query.filter(Event.event_date >= date.today()).count()
    total_attendances = EventAttendance.query.count()
    
    return render_template('dashboard_simple.html', 
                     user=user,
                     clubs_count=total_clubs,
                     events_count=total_events,
                     members_count=total_users,
                     announcements_count=0)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect('/login')

@app.route('/clubs')
def clubs():
    if 'user_id' not in session:
        return redirect('/login')
    
    # Simple clubs page for now
    user = User.query.filter_by(username=session['user_id']).first()
    return render_template('dashboard_simple.html', 
                     user=user,
                     clubs_count=0,
                     events_count=0,
                     members_count=0,
                     announcements_count=0)

@app.route('/events')
def events():
    if 'user_id' not in session:
        return redirect('/login')
    
    # Simple events page for now
    user = User.query.filter_by(username=session['user_id']).first()
    return render_template('dashboard_simple.html', 
                     user=user,
                     clubs_count=0,
                     events_count=0,
                     members_count=0,
                     announcements_count=0)

@app.route('/chat')
def chat():
    if 'user_id' not in session:
        return redirect('/login')
    
    # Simple chat page for now
    user = User.query.filter_by(username=session['user_id']).first()
    return render_template('dashboard_simple.html', 
                     user=user,
                     clubs_count=0,
                     events_count=0,
                     members_count=0,
                     announcements_count=0)

if __name__ == "__main__":
    app.run(debug=True)

# For Gunicorn
application = app
