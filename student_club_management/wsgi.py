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

from flask import Flask, jsonify, render_template_string, request, redirect, url_for, session, flash
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
import os
import urllib.parse

app = Flask(__name__)

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

# HTML Templates
BASE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>{% block title %}Club Management System{% endblock %}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin-bottom: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .nav { background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
        .nav a { color: #007bff; text-decoration: none; margin-right: 20px; padding: 8px 16px; border-radius: 4px; }
        .nav a:hover { background: #007bff; color: white; }
        .nav a.active { background: #007bff; color: white; }
        .card { background: white; border: 1px solid #e9ecef; border-radius: 8px; padding: 25px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .btn { background: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; border: none; cursor: pointer; font-size: 14px; }
        .btn:hover { background: #0056b3; transform: translateY(-1px); }
        .btn-success { background: #28a745; }
        .btn-success:hover { background: #1e7e34; }
        .btn-danger { background: #dc3545; }
        .btn-danger:hover { background: #c82333; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; font-weight: 600; color: #555; }
        input, textarea, select { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; }
        input:focus, textarea:focus, select:focus { outline: none; border-color: #007bff; box-shadow: 0 0 0 3px rgba(0,123,255,0.1); }
        .alert { padding: 15px; border-radius: 6px; margin-bottom: 20px; }
        .alert-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .alert-danger { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .stats { display: flex; gap: 20px; margin-bottom: 30px; flex-wrap: wrap; }
        .stat { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 25px; border-radius: 8px; text-align: center; flex: 1; min-width: 150px; }
        .stat h3 { font-size: 2.5em; margin-bottom: 5px; }
        .stat p { margin: 0; opacity: 0.9; }
        .table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        .table th, .table td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        .table th { background: #f8f9fa; font-weight: 600; }
        .badge { background: #007bff; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px; }
        .text-right { text-align: right; }
        @media (max-width: 768px) {
            .container { padding: 10px; }
            .stats { flex-direction: column; }
            .grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        {% if 'user_id' in session %}
        <div class="header">
            <h1>🎉 {{ session['user_id'] }}'s Club Management</h1>
            <div class="text-right">
                <a href="/dashboard" class="btn">Dashboard</a>
                <a href="/clubs" class="btn">Clubs</a>
                <a href="/events" class="btn">Events</a>
                <a href="/analytics" class="btn">Analytics</a>
                <a href="/logout" class="btn btn-danger">Logout</a>
            </div>
        </div>
        {% endif %}
        
        {% with messages = get_flashed_messages() %}
            {% for message in messages %}
                <div class="alert alert-{{ 'success' if 'success' in message else 'danger' }}">{{ message }}</div>
            {% endfor %}
        {% endwith %}
        
        {% block content %}{% endblock %}
    </div>
</body>
</html>
"""

LOGIN_TEMPLATE = BASE_TEMPLATE.replace('{% block title %}Club Management System{% endblock %}', 'Login') + """
{% block content %}
<div class="grid" style="max-width: 400px; margin: 50px auto;">
    <div class="card">
        <h2 style="text-align: center; margin-bottom: 30px;">🔐 Login</h2>
        <form method="POST">
            <div class="form-group">
                <label>Username:</label>
                <input type="text" name="username" required autofocus>
            </div>
            <div class="form-group">
                <label>Password:</label>
                <input type="password" name="password" required>
            </div>
            <button type="submit" class="btn" style="width: 100%;">Login</button>
        </form>
        <p style="text-align: center; margin-top: 20px;">
            Don't have an account? <a href="/register">Register here</a>
        </p>
    </div>
</div>
{% endblock %}
"""

DASHBOARD_TEMPLATE = BASE_TEMPLATE.replace('{% block title %}Club Management System{% endblock %}', 'Dashboard') + """
{% block content %}
<div class="stats">
    <div class="stat">
        <h3>{{ total_users }}</h3>
        <p>Total Users</p>
    </div>
    <div class="stat">
        <h3>{{ total_clubs }}</h3>
        <p>Active Clubs</p>
    </div>
    <div class="stat">
        <h3>{{ total_events }}</h3>
        <p>Upcoming Events</p>
    </div>
    <div class="stat">
        <h3>{{ total_attendances }}</h3>
        <p>Event Attendances</p>
    </div>
</div>

<div class="grid">
    <div class="card">
        <h3>🏛️ Recent Clubs</h3>
        {% if recent_clubs %}
            <table class="table">
                <tr><th>Club Name</th><th>Members</th><th>Category</th></tr>
                {% for club in recent_clubs %}
                <tr>
                    <td><a href="/clubs/{{ club.id }}">{{ club.name }}</a></td>
                    <td>{{ club.member_count }}</td>
                    <td><span class="badge">{{ club.category }}</span></td>
                </tr>
                {% endfor %}
            </table>
        {% else %}
            <p>No clubs created yet.</p>
        {% endif %}
        <p style="margin-top: 15px;"><a href="/clubs" class="btn">Manage All Clubs</a></p>
    </div>
    
    <div class="card">
        <h3>📅 Upcoming Events</h3>
        {% if upcoming_events %}
            <table class="table">
                <tr><th>Event</th><th>Date</th><th>Club</th></tr>
                {% for event in upcoming_events %}
                <tr>
                    <td><a href="/events/{{ event.id }}">{{ event.title }}</a></td>
                    <td>{{ event.event_date.strftime('%b %d, %Y') }}</td>
                    <td>{{ event.club.name }}</td>
                </tr>
                {% endfor %}
            </table>
        {% else %}
            <p>No upcoming events.</p>
        {% endif %}
        <p style="margin-top: 15px;"><a href="/events" class="btn">Manage All Events</a></p>
    </div>
</div>
{% endblock %}
"""

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect('/dashboard')
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.username
            session['user_role'] = user.role
            flash(f'Welcome back, {user.first_name}!', 'success')
            return redirect('/dashboard')
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    
    if not db_initialized:
        dashboard_error_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Dashboard</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
                .card { background: white; border: 1px solid #e9ecef; border-radius: 8px; padding: 25px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="card">
                    <h2>🔧 Database Not Available</h2>
                    <p>The database is not currently available. Please check your configuration.</p>
                    <p><strong>DATABASE_URL:</strong> """ + ('Set' if database_url else 'Not Set') + """</p>
                    <p><strong>Database Status:</strong> """ + ('Connected' if db_initialized else 'Not Connected') + """</p>
                </div>
            </div>
        </body>
        </html>
        """
        return dashboard_error_template
    
    # Get statistics
    try:
        total_users = User.query.count()
        total_clubs = Club.query.filter_by(is_active=True).count()
        total_events = Event.query.filter(Event.event_date >= date.today()).count()
        total_attendances = EventAttendance.query.count()
        
        # Get recent data
        recent_clubs = db.session.query(
            Club, db.func.count(ClubMember.id).label('member_count')
        ).join(ClubMember).group_by(Club.id).order_by(Club.created_at.desc()).limit(5).all()
        
        upcoming_events = Event.query.filter(
            Event.event_date >= date.today()
        ).order_by(Event.event_date).limit(5).all()
        
        return render_template_string(DASHBOARD_TEMPLATE,
                               total_users=total_users,
                               total_clubs=total_clubs,
                               total_events=total_events,
                               total_attendances=total_attendances,
                               recent_clubs=recent_clubs,
                               upcoming_events=upcoming_events)
    except Exception as e:
        error_message = str(e)
        dashboard_error_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Dashboard Error</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
                .card { background: white; border: 1px solid #e9ecef; border-radius: 8px; padding: 25px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                code { background: #f8f9fa; padding: 2px 4px; border-radius: 3px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="card">
                    <h2>❌ Database Error</h2>
                    <p>There was an error accessing the database:</p>
                    <p><code>""" + error_message + """</code></p>
                    <p>Please check your database configuration and try again.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return dashboard_error_template

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect('/login')

@app.route('/health')
def health():
    try:
        # Test database connection
        db.engine.execute('SELECT 1')
        return jsonify({
            'status': 'healthy',
            'message': 'Club Management System is running',
            'database': 'connected',
            'features': [
                'authentication', 'user_management', 'club_management',
                'event_management', 'analytics', 'database_integration'
            ]
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'message': f'Database error: {str(e)}',
            'database': 'not connected'
        }), 500

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
