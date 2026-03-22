from flask import Blueprint, render_template, redirect, flash, request, current_app
from flask_login import login_required, current_user
from models.user import User, PreRegisteredStudent
from models.club import Club
from models.event import Event
from models.membership import Membership

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# helper decorator to ensure admin role

def admin_required(func):
    @login_required
    def wrapper(*args, **kwargs):
        if current_user.role != 'admin':
            return 'Unauthorized', 403
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

@admin_bp.route('/')
@admin_required
def admin_index():
    # redirect into dashboard admin view which already collects statistics
    return redirect('/dashboard/admin')

@admin_bp.route('/users')
@admin_required
def manage_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/clubs')
@admin_required
def manage_clubs():
    clubs = Club.query.order_by(Club.created_at.desc()).all()
    return render_template('admin/clubs.html', clubs=clubs)

@admin_bp.route('/events')
@admin_required
def manage_events():
    events = Event.query.order_by(Event.event_date.desc()).all()
    return render_template('admin/events.html', events=events)

@admin_bp.route('/settings')
@admin_required
def settings():
    # Get system statistics for settings page
    users_count = User.query.count()
    clubs_count = Club.query.count()
    events_count = Event.query.count()
    active_members = Membership.query.filter_by(status='active').count()
    
    return render_template('admin/settings.html',
                         users_count=users_count,
                         clubs_count=clubs_count,
                         events_count=events_count,
                         active_members=active_members)

@admin_bp.route('/clubs/approve/<int:club_id>', methods=['POST'])
@admin_required
def approve_club(club_id):
    from app import db
    from models.notification import Notification
    club = Club.query.get_or_404(club_id)
    club.status = 'active'
    db.session.commit()
    
    # Notify leader that club is approved
    try:
        Notification.notify_leader_club_approved(club)
    except:
        pass
    
    flash('Club approved successfully.', 'success')
    return redirect('/dashboard/admin')

@admin_bp.route('/clubs/reject/<int:club_id>', methods=['POST'])
@admin_required
def reject_club(club_id):
    from app import db
    from models.notification import Notification
    reason = request.form.get('reason', '')
    club = Club.query.get_or_404(club_id)
    club.status = 'rejected'
    club.rejection_reason = reason
    db.session.commit()
    
    # Notify leader that club is rejected
    try:
        Notification.notify_leader_club_rejected(club, reason)
    except:
        pass
    
    flash('Club rejected.', 'warning')
    return redirect('/dashboard/admin')

@admin_bp.route('/clubs/approve-delete/<int:club_id>', methods=['POST'])
@admin_required
def approve_delete_club(club_id):
    from models.notification import Notification
    from models.membership import Membership
    from models.announcement import Announcement
    from models.event import Event
    from models.booking import Booking
    
    club = Club.query.get_or_404(club_id)
    
    # Delete related records first
    Membership.query.filter_by(club_id=club_id).delete()
    Announcement.query.filter_by(club_id=club_id).delete()
    Event.query.filter_by(club_id=club_id).delete()
    Booking.query.filter_by(club_id=club_id).delete()
    
    # Notify leader
    try:
        Notification.send_to_user(
            user_id=club.created_by,
            title=f"Club Deleted: {club.club_name}",
            message=f"Your club '{club.club_name}' has been deleted by the admin.",
            notification_type='warning'
        )
    except:
        pass
    
    # Delete the club
    db.session.delete(club)
    db.session.commit()
    
    flash(f'Club "{club.club_name}" has been permanently deleted.', 'success')
    return redirect('/admin/clubs')

@admin_bp.route('/clubs/deny-delete/<int:club_id>', methods=['POST'])
@admin_required
def deny_delete_club(club_id):
    from models.notification import Notification
    
    club = Club.query.get_or_404(club_id)
    club.status = 'active'
    db.session.commit()
    
    # Notify leader
    try:
        Notification.send_to_user(
            user_id=club.created_by,
            title=f"Club Deletion Denied: {club.club_name}",
            message=f"Your request to delete '{club.club_name}' has been denied by the admin.",
            notification_type='info'
        )
    except:
        pass
    
    flash(f'Club deletion request denied. {club.club_name} is now active.', 'info')
    return redirect('/admin/clubs')

@admin_bp.route('/events/approve/<int:event_id>', methods=['POST'])
@admin_required
def approve_event(event_id):
    from app import db
    from models.notification import Notification
    event = Event.query.get_or_404(event_id)
    event.status = 'approved'
    db.session.commit()
    
    # Notify leader that event is approved
    try:
        Notification.notify_leader_event_approved(event)
    except:
        pass
    
    flash(f'Event "{event.event_name}" approved and is now visible to students!', 'success')
    return redirect('/admin/events')

@admin_bp.route('/events/reject/<int:event_id>', methods=['POST'])
@admin_required
def reject_event(event_id):
    from app import db
    from models.notification import Notification
    reason = request.form.get('reason', '')
    event = Event.query.get_or_404(event_id)
    event.status = 'rejected'
    db.session.commit()
    
    # Notify leader that event is rejected
    try:
        Notification.notify_leader_event_rejected(event, reason)
    except:
        pass
    
    flash(f'Event "{event.event_name}" rejected.', 'warning')
    return redirect('/admin/events')

# User Management Routes
@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    from models.notification import Notification
    from models.chat import ChatMessage, ChatConversation, ChatRequest
    from models.announcement import AnnouncementComment, AnnouncementReaction
    from models.attendance import EventAttendance
    
    user = User.query.get_or_404(user_id)
    # Don't allow deleting yourself
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect('/admin/users')
    
    # Delete all related records first to avoid foreign key constraint errors
    
    # Delete notifications where user is the recipient
    Notification.query.filter_by(user_id=user.id).delete()
    
    # Delete chat messages sent by this user
    ChatMessage.query.filter_by(sender_id=user.id).delete()
    
    # Delete chat conversations where this user is a participant
    ChatConversation.query.filter_by(participant_one=user.id).delete()
    ChatConversation.query.filter_by(participant_two=user.id).delete()
    
    # Delete chat requests where user is the requester
    ChatRequest.query.filter_by(user_id=user.id).delete()
    
    # Delete announcement comments by this user
    AnnouncementComment.query.filter_by(user_id=user.id).delete()
    
    # Delete announcement reactions by this user
    AnnouncementReaction.query.filter_by(user_id=user.id).delete()
    
    # Delete event attendance records
    EventAttendance.query.filter_by(user_id=user.id).delete()
    
    # Delete memberships
    Membership.query.filter_by(user_id=user.id).delete()
    
    # Now delete the user
    db.session.delete(user)
    db.session.commit()
    flash(f'User "{user.first_name} {user.last_name}" has been deleted.', 'success')
    return redirect('/admin/users')

@admin_bp.route('/users/toggle-role/<int:user_id>', methods=['POST'])
@admin_required
def toggle_user_role(user_id):
    user = User.query.get_or_404(user_id)
    # Don't allow modifying yourself
    if user.id == current_user.id:
        flash('You cannot change your own role.', 'danger')
        return redirect('/admin/users')
    
    # Toggle between student and admin
    user.role = 'admin' if user.role == 'student' else 'student'
    db.session.commit()
    flash(f'User role updated to {user.role}.', 'success')
    return redirect('/admin/users')

@admin_bp.route('/users/set-role/<int:user_id>', methods=['POST'])
@admin_required
def set_user_role(user_id):
    from app import db
    user = User.query.get_or_404(user_id)
    # Don't allow modifying yourself
    if user.id == current_user.id:
        flash('You cannot change your own role.', 'danger')
        return redirect('/admin/users')
    
    new_role = request.form.get('role', 'student')
    # Only allow valid roles: student, leader, admin
    valid_roles = ['student', 'leader', 'admin']
    if new_role not in valid_roles:
        flash('Invalid role selected.', 'danger')
        return redirect('/admin/users')
    
    old_role = user.role
    user.role = new_role
    db.session.commit()
    flash(f'User role changed from {old_role} to {new_role}.', 'success')
    return redirect('/admin/users')

# Pre-Registered Students Management Routes
@admin_bp.route('/students')
@admin_required
def manage_students():
    students = PreRegisteredStudent.query.order_by(PreRegisteredStudent.created_at.desc()).all()
    registered_count = PreRegisteredStudent.query.filter_by(is_registered=True).count()
    pending_count = PreRegisteredStudent.query.filter_by(is_registered=False).count()
    return render_template('admin/students.html', 
                         students=students,
                         registered_count=registered_count,
                         pending_count=pending_count)

@admin_bp.route('/students/add', methods=['POST'])
@admin_required
def add_student():
    from app import db
    student_number = request.form.get('student_number', '').strip()
    id_number = request.form.get('id_number', '').strip()
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    email = request.form.get('email', '').strip()
    
    # Validation - required fields
    if not student_number or not id_number or not first_name or not last_name:
        flash('Please fill in all required fields (Student Number, ID Number, First Name, Last Name).', 'danger')
        return redirect('/admin/students')
    
    # Validation - student number must be 8-9 digits
    if not student_number.isdigit() or len(student_number) < 8 or len(student_number) > 9:
        flash('Student number must be 8 or 9 digits.', 'danger')
        return redirect('/admin/students')
    
    # Validation - ID number must be 13 digits and only numbers
    if not id_number.isdigit() or len(id_number) != 13:
        flash('ID number must be exactly 13 digits.', 'danger')
        return redirect('/admin/students')
    
    # Check if student_number already exists in pre-registered students
    existing = PreRegisteredStudent.query.filter_by(student_number=student_number).first()
    if existing:
        flash(f'Student with number {student_number} already exists.', 'danger')
        return redirect('/admin/students')
    
    # Check if student_number already registered as a user
    existing_user = User.query.filter_by(student_number=student_number).first()
    if existing_user:
        flash(f'Student number {student_number} is already registered as a user.', 'danger')
        return redirect('/admin/students')
    
    # Create new pre-registered student
    new_student = PreRegisteredStudent(
        student_number=student_number,
        id_number=id_number,
        first_name=first_name,
        last_name=last_name,
        email=email if email else None
    )
    db.session.add(new_student)
    db.session.commit()
    flash(f'Student {first_name} {last_name} ({student_number}) has been added successfully.', 'success')
    return redirect('/admin/students')

@admin_bp.route('/students/delete/<int:student_id>', methods=['POST'])
@admin_required
def delete_student(student_id):
    from app import db
    student = PreRegisteredStudent.query.get_or_404(student_id)
    student_num = student.student_number
    db.session.delete(student)
    db.session.commit()
    flash(f'Student {student_num} has been removed from the pre-registered list.', 'success')
    return redirect('/admin/students')

@admin_bp.route('/students/toggle-status/<int:student_id>', methods=['POST'])
@admin_required
def toggle_student_status(student_id):
    from app import db
    student = PreRegisteredStudent.query.get_or_404(student_id)
    student.is_registered = not student.is_registered
    db.session.commit()
    status = 'registered' if student.is_registered else 'pending'
    flash(f'Student {student.student_number} status updated to {status}.', 'success')
    return redirect('/admin/students')
