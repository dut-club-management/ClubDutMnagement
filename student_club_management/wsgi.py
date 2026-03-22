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

app = Flask(__name__, template_folder='templates')

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

if __name__ == "__main__":
    app.run(debug=True)

# For Gunicorn
application = app
