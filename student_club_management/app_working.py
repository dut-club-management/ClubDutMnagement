from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_mail import Mail
from flask_migrate import Migrate
from datetime import datetime
import os

# Initialize extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
mail = Mail()
migrate = Migrate()

def create_app(config_name='development'):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Configuration
    if config_name == 'development':
        app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clubmanagement.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['MAIL_SERVER'] = 'smtp.gmail.com'
        app.config['MAIL_PORT'] = 587
        app.config['MAIL_USE_TLS'] = True
        app.config['MAIL_USERNAME'] = 'your-email@gmail.com'
        app.config['MAIL_PASSWORD'] = 'your-app-password'
    
    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    
    # Login manager configuration
    login_manager.login_view = 'login'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from models.user import User
        return User.query.get(int(user_id))
    
    # Routes
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect('/dashboard')
        return '''
        <h1>🎓 DUT Club Management System</h1>
        <p>Welcome to the Student Club Management System!</p>
        <ul>
            <li><a href="/login">Login</a></li>
            <li><a href="/dashboard">Dashboard</a></li>
            <li><a href="/clubs">Clubs</a></li>
        </ul>
        <h3>🚀 App is working! Ready for full development.</h3>
        '''
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect('/dashboard')
            
        if request.method == 'POST':
            email_or_student_number = request.form.get('email')
            password = request.form.get('password')
            
            from models.user import User
            user = User.query.filter(
                (User.email == email_or_student_number) | 
                (User.student_number == email_or_student_number)
            ).first()
            
            if user and bcrypt.check_password_hash(user.password_hash, password):
                if user.is_active:
                    login_user(user)
                    flash('Login successful!', 'success')
                    return redirect('/dashboard')
                else:
                    flash('Your account is suspended.', 'danger')
            else:
                flash('Invalid email/student number or password.', 'danger')
        
        return render_template('login_simple.html')
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect('/')
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        from models.club import Club
        from models.event import Event
        from models.announcement import Announcement
        from models.membership import Membership
        
        # Get statistics
        clubs_count = Club.query.filter_by(status='active').count()
        events_count = Event.query.filter(Event.event_date >= datetime.now()).count()
        members_count = User.query.filter_by(is_active=True).count()
        announcements_count = Announcement.query.count()
        
        return render_template('dashboard_simple.html', 
                             user=current_user,
                             clubs_count=clubs_count,
                             events_count=events_count,
                             members_count=members_count,
                             announcements_count=announcements_count)
    
    @app.route('/clubs')
    @login_required
    def clubs():
        from models.club import Club
        clubs = Club.query.filter_by(status='active').all()
        
        clubs_html = '''
        <h1>🏫 Student Clubs</h1>
        <p>Browse and join student clubs at DUT.</p>
        '''
        
        for club in clubs:
            clubs_html += f'''
            <div style="border: 1px solid #ddd; padding: 1rem; margin: 1rem 0; border-radius: 8px;">
                <h3>{club.club_name}</h3>
                <p><strong>Category:</strong> {club.category}</p>
                <p>{club.description}</p>
                <p><strong>Meeting Schedule:</strong> {club.meeting_schedule}</p>
                <p><strong>Members:</strong> {len(club.members) if club.members else 0}</p>
                <a href="/clubs/{club.id}" style="background: #667eea; color: white; padding: 0.5rem 1rem; text-decoration: none; border-radius: 4px;">View Details</a>
            </div>
            '''
        
        clubs_html += '''
        <br>
        <a href="/dashboard">← Back to Dashboard</a>
        '''
        
        return clubs_html
    
    @app.route('/events')
    @login_required
    def events():
        from models.event import Event
        from datetime import datetime
        
        events = Event.query.filter(Event.event_date >= datetime.now()).order_by(Event.event_date).all()
        
        events_html = '''
        <h1>📅 Upcoming Events</h1>
        <p>Check out upcoming events from various clubs.</p>
        '''
        
        for event in events:
            events_html += f'''
            <div style="border: 1px solid #ddd; padding: 1rem; margin: 1rem 0; border-radius: 8px;">
                <h3>{event.event_name}</h3>
                <p>{event.description}</p>
                <p><strong>Date:</strong> {event.event_date.strftime('%Y-%m-%d %H:%M')}</p>
                <p><strong>Location:</strong> {event.location}</p>
                <a href="/events/{event.id}" style="background: #667eea; color: white; padding: 0.5rem 1rem; text-decoration: none; border-radius: 4px;">View Details</a>
            </div>
            '''
        
        events_html += '''
        <br>
        <a href="/dashboard">← Back to Dashboard</a>
        '''
        
        return events_html
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return '<h1>404 - Page Not Found</h1>', 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return '<h1>500 - Internal Server Error</h1>', 500
    
    return app
