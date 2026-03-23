from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from datetime import datetime, timedelta
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
import secrets
import re

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/dashboard/user')
    
    # Import inside route to avoid circular imports
    from forms import LoginForm
    from models.user import User
    from models.user import PreRegisteredStudent
    from app import bcrypt
    
    form = LoginForm()
    if form.validate_on_submit():
        data = form.email.data
        # allow login by email or student number
        user = User.query.filter((User.email == data) | (User.student_number == data)).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            if not user.is_active:
                flash('Your account is suspended.', 'danger')
                return redirect('/login')
            login_user(user, remember=form.remember.data)
            user.last_login = datetime.utcnow()
            from app import db
            db.session.commit()
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            # direct to appropriate dashboard based on role
            if user.role == 'admin':
                return redirect('/admin/')
            elif user.role == 'leader':
                return redirect('/dashboard/leader')
            else:
                return redirect('/dashboard/user')
        else:
            flash('Login failed. Check email/student number and password.', 'danger')
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect('/dashboard/user')
    
    # Import all required modules at the top
    from forms import RegistrationForm
    from models.user import User
    from models.user import PreRegisteredStudent
    from app import bcrypt, db
    
    form = RegistrationForm()
    if form.validate_on_submit():
        student_number = form.student_number.data.strip()
        
        # Validate student number against pre-registered students
        pre_student = PreRegisteredStudent.query.filter_by(student_number=student_number).first()
        
        if not pre_student:
            flash('Your student number is not registered in the system. Please contact the admin to register you first.', 'danger')
            return render_template('auth/register.html', form=form)
        
        if pre_student.is_registered:
            flash('This student number has already been registered. Please login with your credentials.', 'danger')
            return render_template('auth/register.html', form=form)
        
        # Check if user already exists with this student number
        existing_user = User.query.filter_by(student_number=student_number).first()
        if existing_user:
            flash('An account with this student number already exists. Please login.', 'danger')
            return render_template('auth/register.html', form=form)
        
        # Check if email already exists
        existing_email = User.query.filter_by(email=form.email.data).first()
        if existing_email:
            flash('An account with this email already exists. Please use a different email or login.', 'danger')
            return render_template('auth/register.html', form=form)
        
        hashed = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            student_number=student_number,
            email=form.email.data,
            password_hash=hashed
        )
        db.session.add(user)
        
        # Mark pre-registered student as registered
        pre_student.is_registered = True
        pre_student.email = form.email.data
        
        db.session.commit()
        flash('Account created successfully! Please log in.', 'success')
        return redirect('/login')
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect('/')

def validate_password_strength(password):
    """Validate password strength and return any errors"""
    errors = []
    if len(password) < 8:
        errors.append('Password must be at least 8 characters long')
    if not re.search(r'[A-Z]', password):
        errors.append('Password must contain at least one uppercase letter')
    if not re.search(r'[a-z]', password):
        errors.append('Password must contain at least one lowercase letter')
    if not re.search(r'[0-9]', password):
        errors.append('Password must contain at least one number')
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append('Password must contain at least one special character (!@#$%^&*)')
    return errors

def send_reset_email(user):
    """Generate reset token and send email"""
    # Generate secure token
    reset_token = secrets.token_urlsafe(32)
    user.reset_token = reset_token
    user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
    db.session.commit()
    
    # Create email
    reset_url = url_for('auth.reset_password', token=reset_token, _external=True)
    
    msg = Message('Password Reset Request',
                  sender=('DUT Club Management', 'noreply@dutclubs.com'),
                  recipients=[user.email])
    
    msg.html = render_template('auth/email/reset_password.html',
                              user=user,
                              reset_url=reset_url)
    msg.body = render_template('auth/email/reset_password.txt',
                              user=user,
                              reset_url=reset_url)
    
    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Handle forgot password request - shows onscreen password reset after email validation"""
    if current_user.is_authenticated:
        return redirect('/dashboard/user')
    
    # If token is provided, handle password reset directly
    token = request.args.get('token')
    if token:
        return reset_password(token)
    
    if request.method == 'POST':
        # Check if this is a password reset submission (has token) or email submission
        reset_token = request.form.get('token')
        password = request.form.get('password')
        
        if reset_token and password:
            # Password reset submission - process directly
            return process_onscreen_password_reset(reset_token)
        
        # Email submission - validate and show password reset form
        email = request.form.get('email', '').strip()
        
        if not email:
            flash('Please enter your email address.', 'danger')
            return render_template('auth/forgot-password.html')
        
        # Check if email exists in database
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate reset token for onscreen password reset
            reset_token = secrets.token_urlsafe(32)
            user.reset_token = reset_token
            user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()
            
            # Show password reset form directly (onscreen)
            flash('Email verified! Please enter your new password.', 'success')
            return render_template('auth/forgot-password.html', 
                                  token=reset_token, 
                                  email=email,
                                  show_reset_form=True)
        else:
            # For security, still show success message but redirect to login
            flash('If an account exists with this email, you will receive password reset instructions.', 'info')
            return redirect('/login')
    
    return render_template('auth/forgot-password.html')


def process_onscreen_password_reset(token):
    """Process password reset submitted from onscreen form"""
    # Verify token
    user = User.query.filter_by(reset_token=token).first()
    
    if not user or not user.reset_token_expiry or user.reset_token_expiry < datetime.utcnow():
        flash('The password reset link is invalid or has expired. Please try again.', 'danger')
        return redirect('/forgot-password')
    
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    # Validate passwords match
    if password != confirm_password:
        flash('Passwords do not match.', 'danger')
        return render_template('auth/forgot-password.html', 
                              token=token, 
                              email=user.email,
                              show_reset_form=True)
    
    # Validate password strength
    errors = validate_password_strength(password)
    if errors:
        for error in errors:
            flash(error, 'danger')
        return render_template('auth/forgot-password.html', 
                              token=token, 
                              email=user.email,
                              show_reset_form=True)
    
    # Update password
    user.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    user.reset_token = None
    user.reset_token_expiry = None
    db.session.commit()
    
    flash('Your password has been reset successfully! Please log in with your new password.', 'success')
    return redirect('/login')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Handle password reset with token"""
    if current_user.is_authenticated:
        return redirect('/dashboard/user')
    
    # Verify token
    user = User.query.filter_by(reset_token=token).first()
    
    if not user or not user.reset_token_expiry or user.reset_token_expiry < datetime.utcnow():
        flash('The password reset link is invalid or has expired.', 'danger')
        return redirect('/login')
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validate passwords match
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/reset-password.html', token=token)
        
        # Validate password strength
        errors = validate_password_strength(password)
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('auth/reset-password.html', token=token)
        
        # Update password
        user.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()
        
        # Send confirmation email
        msg = Message('Password Reset Successful',
                      sender=('DUT Club Management', 'noreply@dutclubs.com'),
                      recipients=[user.email])
        msg.html = render_template('auth/email/password_changed.html', user=user)
        msg.body = f"Hello {user.first_name},\n\nYour password has been successfully reset. If you did not make this change, please contact support immediately.\n\nBest regards,\nDUT Club Management Team"
        
        try:
            mail.send(msg)
        except:
            pass  # Don't fail if confirmation email fails
        
        flash('Your password has been reset successfully! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset-password.html', token=token)
