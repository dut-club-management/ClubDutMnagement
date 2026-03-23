from flask import Blueprint, render_template, redirect, flash, request, current_app
from flask_login import login_required, current_user
from models.user import User
from models.membership import Membership
from models.event import Event
from models.club import Club
from models.user import PreRegisteredStudent
from app import db
import bcrypt

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/user')
@login_required
def user_dashboard():
    try:
        user_clubs = Membership.query.filter_by(user_id=current_user.id).count()
        # Show approved events from clubs user is member of
        upcoming_events = Event.query.filter(Event.status == 'approved').all()
        user_memberships = Membership.query.filter_by(user_id=current_user.id).all()
        
        return render_template('dashboard/user.html', 
                             user=current_user,
                             clubs_count=user_clubs,
                             upcoming_events=upcoming_events,
                             memberships=user_memberships)
    except Exception as e:
        print(f"❌ User dashboard error: {e}")
        # Return basic dashboard with default values if queries fail
        return render_template('dashboard/user.html', 
                             user=current_user,
                             clubs_count=0,
                             upcoming_events=[],
                             memberships=[])

@dashboard_bp.route('/leader')
@login_required
def leader_dashboard():
    try:
        # Get clubs created by current user
        my_clubs = Club.query.filter_by(created_by=current_user.id).all()
        
        # Count total members across all user's clubs
        total_members = 0
        for club in my_clubs:
            total_members += len(club.members)
        
        return render_template('dashboard/leader.html', 
                             created_clubs=my_clubs,
                             total_members=total_members)
    except Exception as e:
        print(f"❌ Leader dashboard error: {e}")
        # Return basic dashboard with default values if queries fail
        return render_template('dashboard/leader.html', 
                             created_clubs=[],
                             total_members=0)

@dashboard_bp.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return 'Unauthorized', 403
    # Redirect to the new admin panel
    return redirect('/admin/')
    
    try:
        total_users = User.query.count()
        total_clubs = Club.query.count()
        total_events = Event.query.count()
        total_memberships = Membership.query.count()
        pending_clubs = Club.query.filter_by(status='pending').count()
        pending_club_list = Club.query.filter_by(status='pending').all()
        
        # Get active events count
        active_events = Event.query.filter_by(status='approved').count()
        
        # Get recent users
        recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
        
        # Get recent clubs
        recent_clubs = Club.query.order_by(Club.created_at.desc()).limit(5).all()
        
        # Get active members count
        active_members = Membership.query.filter_by(status='active').count()
        
        return render_template('dashboard/admin.html',
                             total_users=total_users,
                             total_clubs=total_clubs,
                             pending_clubs=pending_clubs,
                             pending_club_list=pending_club_list,
                             active_events=active_events,
                             recent_users=recent_users,
                             recent_clubs=recent_clubs,
                             active_members=active_members)
    except Exception as e:
        print(f"❌ Admin dashboard error: {e}")
        # Return basic dashboard with default values if queries fail
        return render_template('dashboard/admin.html',
                             total_users=0,
                             total_clubs=0,
                             pending_clubs=0,
                             pending_club_list=[],
                             active_events=0,
                             recent_users=[],
                             recent_clubs=[],
                             active_members=0)

@dashboard_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    # Get pre-registered student info if available
    pre_student = PreRegisteredStudent.query.filter_by(student_number=current_user.student_number).first()
    
    if request.method == 'POST':
        # Update profile
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()
        bio = request.form.get('bio', '').strip()
        interests = request.form.get('interests', '').strip()
        
        if not first_name or not last_name or not email:
            flash('First name, last name, and email are required.', 'danger')
            return redirect('/dashboard/profile')
        
        # Check if email is taken by another user
        existing_email = User.query.filter(User.email == email, User.id != current_user.id).first()
        if existing_email:
            flash('This email is already in use by another account.', 'danger')
            return redirect('/dashboard/profile')
        
        current_user.first_name = first_name
        current_user.last_name = last_name
        current_user.email = email
        current_user.bio = bio if bio else None
        current_user.interests = interests if interests else None
        
        # Update pre-registered student info if exists
        if pre_student:
            pre_student.first_name = first_name
            pre_student.last_name = last_name
            pre_student.email = email
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect('/dashboard/profile')
    
    return render_template('dashboard/profile.html', 
                         user=current_user,
                         pre_student=pre_student)

@dashboard_bp.route('/profile/update-password', methods=['POST'])
@login_required
def update_password():
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    if not current_password or not new_password or not confirm_password:
        flash('All password fields are required.', 'danger')
        return redirect('/dashboard/profile')
    
    if not bcrypt.check_password_hash(current_user.password_hash, current_password):
        flash('Current password is incorrect.', 'danger')
        return redirect('/dashboard/profile')
    
    if new_password != confirm_password:
        flash('New passwords do not match.', 'danger')
        return redirect('/dashboard/profile')
    
    if len(new_password) < 6:
        flash('Password must be at least 6 characters.', 'danger')
        return redirect('/dashboard/profile')
    
    current_user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
    db.session.commit()
    flash('Password updated successfully!', 'success')
    return redirect('/dashboard/profile')
