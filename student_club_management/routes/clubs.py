from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models.club import Club
from models.membership import Membership
from models.notification import Notification
from app import db

clubs_bp = Blueprint('clubs', __name__, url_prefix='/clubs')

@clubs_bp.route('/')
def list_clubs():
    try:
        # Show all active clubs
        clubs = Club.query.filter_by(status='active').all()
        return render_template('clubs/list.html', clubs=clubs)
    except Exception as e:
        print(f"❌ Clubs list error: {e}")
        # Return empty clubs list if query fails
        return render_template('clubs/list.html', clubs=[])

# join club endpoint
def ensure_member(user_id, club_id):
    return Membership.query.filter_by(user_id=user_id, club_id=club_id).first()

@clubs_bp.route('/<int:club_id>/join', methods=['POST'])
@login_required
def join_club(club_id):
    club = Club.query.get_or_404(club_id)
    # only active clubs can be joined
    if club.status != 'active':
        flash('Cannot join this club.', 'warning')
        return redirect(f'/clubs/{club_id}')
    existing = ensure_member(current_user.id, club_id)
    if existing:
        flash('You are already a member of this club.', 'info')
        return redirect(f'/clubs/{club_id}')
    # check max members limit
    if club.max_members and len(club.members) >= club.max_members:
        flash(f'Club is full ({club.max_members} members max).', 'warning')
        return redirect(f'/clubs/{club_id}')
    # create membership
    membership = Membership(user_id=current_user.id, club_id=club_id)
    from flask import current_app
    current_app.extensions['sqlalchemy'].db.session.add(membership)
    current_app.extensions['sqlalchemy'].db.session.commit()
    
    # Send notification to student
    try:
        Notification.notify_student_joined_club(current_user, club)
    except:
        pass  # Don't fail if notification fails
    
    # Send notification to club leader
    try:
        if club.created_by != current_user.id:
            Notification.notify_leader_student_joined(club, current_user)
    except:
        pass
    
    flash(f'You have joined {club.club_name}!', 'success')
    return redirect(f'/clubs/{club_id}')

@clubs_bp.route('/<int:club_id>')
def detail(club_id):
    club = Club.query.get_or_404(club_id)
    return render_template('clubs/detail.html', club=club, members=club.members)

@clubs_bp.route('/create', methods=['GET','POST'])
@login_required
def create():
    try:
        print("🔍 Club create: Starting club creation...")
        
        from forms import ClubForm
        print("🔍 Club create: Form imported")
        
        form = ClubForm()
        print("🔍 Club create: Form created")
        
        if form.validate_on_submit():
            print("🔍 Club create: Form validated, creating club...")
            print(f"🔍 Club create: Club name: {form.club_name.data}")
            print(f"🔍 Club create: Category: {form.category.data}")
            print(f"🔍 Club create: Max members: {form.max_members.data}")
            
            new_club = Club(
                club_name=form.club_name.data,
                description=form.description.data,
                category=form.category.data,
                max_members=form.max_members.data,
                meeting_schedule=form.meeting_schedule.data,
                created_by=current_user.id,
                status='pending'
            )
            
            print("🔍 Club create: Club object created")
            
            from flask import current_app
            current_app.extensions['sqlalchemy'].db.session.add(new_club)
            print("🔍 Club create: Club added to session")
            
            current_app.extensions['sqlalchemy'].db.session.commit()
            print("🔍 Club create: Club committed to database")
            
            flash('Club created successfully! It is now pending approval.', 'success')
            print("🔍 Club create: Success message flashed")
            
            return redirect(f'/clubs/{new_club.id}')
        else:
            print("🔍 Club create: Form not validated, showing form")
            if form.errors:
                print(f"🔍 Club create: Form errors: {form.errors}")
            
        print("🔍 Club create: Rendering create template")
        return render_template('clubs/create.html', form=form)
        
    except Exception as e:
        print(f"❌ Club creation error: {e}")
        print(f"❌ Error type: {type(e)}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
        flash('Error creating club. Please try again.', 'danger')
        return redirect('/clubs')

@clubs_bp.route('/<int:club_id>/edit', methods=['GET','POST'])
@login_required
def edit(club_id):
    club = Club.query.get_or_404(club_id)
    
    # Only club creator can edit
    if club.created_by != current_user.id:
        return 'Unauthorized', 403
    
    from forms import ClubEditForm
    form = ClubEditForm(obj=club)
    if form.validate_on_submit():
        club.club_name = form.club_name.data
        club.description = form.description.data
        club.category = form.category.data
        club.max_members = form.max_members.data
        club.meeting_schedule = form.meeting_schedule.data
        from flask import current_app
        current_app.extensions['sqlalchemy'].db.session.commit()
        flash('Club updated successfully.', 'success')
        return redirect(f'/clubs/{club.id}')
    return render_template('clubs/edit.html', club=club, form=form)

@clubs_bp.route('/<int:club_id>/manage')
@login_required
def manage(club_id):
    club = Club.query.get_or_404(club_id)
    
    # Only club creator can manage
    if club.created_by != current_user.id:
        return 'Unauthorized', 403
    
    return render_template('clubs/manage.html', club=club)
@clubs_bp.route('/<int:club_id>/delete', methods=['POST'])
@login_required
def delete_club(club_id):
    from flask import current_app
    from models.notification import Notification
    
    club = Club.query.get_or_404(club_id)
    
    # Only club creator can request deletion
    if club.created_by != current_user.id:
        return 'Unauthorized', 403
    
    # Leaders can only request deletion - admin must approve
    club.status = 'pending_deletion'
    current_app.extensions['sqlalchemy'].db.session.commit()
    
    # Notify admin about deletion request
    try:
        Notification.notify_admin_club_deletion_request(club)
    except:
        pass
    
    flash('Club deletion requested. Admin approval required before the club is deleted.', 'info')
    return redirect('/dashboard/leader')

@clubs_bp.route('/<int:club_id>/kick/<int:user_id>', methods=['POST'])
@login_required
def kick_member(club_id, user_id):
    from models.membership import Membership
    club = Club.query.get_or_404(club_id)
    
    # Only club creator can kick members
    if club.created_by != current_user.id:
        return 'Unauthorized', 403
    
    member = Membership.query.filter_by(user_id=user_id, club_id=club_id).first_or_404()
    from flask import current_app
    current_app.extensions['sqlalchemy'].db.session.delete(member)
    current_app.extensions['sqlalchemy'].db.session.commit()
    flash('Member removed from club.', 'success')
    return redirect(f'/clubs/{club_id}/manage')

# View all user memberships
@clubs_bp.route('/manage')
@login_required
def manage_memberships():
    from models.membership import Membership
    memberships = Membership.query.filter_by(user_id=current_user.id).all()
    return render_template('clubs/memberships.html', memberships=memberships)

# Leave club
@clubs_bp.route('/<int:club_id>/leave', methods=['POST'])
@login_required
def leave_club(club_id):
    from models.membership import Membership
    from models.notification import Notification
    from models.user import User
    
    club = Club.query.get_or_404(club_id)
    membership = Membership.query.filter_by(user_id=current_user.id, club_id=club_id).first()
    
    if not membership:
        flash('You are not a member of this club.', 'warning')
        return redirect(f'/clubs/{club_id}')
    
    # Don't allow leader to leave their own club
    if club.created_by == current_user.id:
        flash('Club leader cannot leave their own club. Transfer leadership first.', 'warning')
        return redirect(f'/clubs/{club_id}')
    
    user = User.query.get(current_user.id)
    current_app.extensions['sqlalchemy'].db.session.delete(membership)
    current_app.extensions['sqlalchemy'].db.session.commit()
    
    # Notify student
    try:
        Notification.notify_student_left_club(user, club)
    except:
        pass
    
    # Notify leader
    try:
        Notification.notify_leader_student_left(club, user)
    except:
        pass
    
    flash(f'You have left {club.club_name}.', 'success')
    return redirect('/clubs')

# Request to leave club
@clubs_bp.route('/<int:club_id>/request-leave', methods=['POST'])
@login_required
def request_leave_club(club_id):
    from models.membership import Membership
    from models.notification import Notification
    from models.user import User
    
    club = Club.query.get_or_404(club_id)
    membership = Membership.query.filter_by(user_id=current_user.id, club_id=club_id).first()
    
    if not membership:
        flash('You are not a member of this club.', 'warning')
        return redirect(f'/clubs/{club_id}')
    
    request_message = request.form.get('message', 'I want to leave this club.')
    user = User.query.get(current_user.id)
    
    # Notify leader about the request
    try:
        Notification.notify_leader_student_request(club, user, 'leave club', request_message)
    except:
        pass
    
    flash('Your request to leave the club has been sent to the club leader.', 'info')
    return redirect(f'/clubs/{club_id}')

# Request to move to another club
@clubs_bp.route('/request-move', methods=['POST'])
@login_required
def request_move_club():
    from models.membership import Membership
    from models.notification import Notification
    from models.user import User
    
    from_club_id = request.form.get('from_club_id')
    to_club_id = request.form.get('to_club_id')
    message = request.form.get('message', 'I would like to move to another club.')
    
    if not from_club_id or not to_club_id:
        flash('Please select both clubs.', 'warning')
        return redirect('/clubs')
    
    if from_club_id == to_club_id:
        flash('Please select different clubs.', 'warning')
        return redirect('/clubs')
    
    from_club = Club.query.get(from_club_id)
    to_club = Club.query.get(to_club_id)
    
    if not from_club or not to_club:
        flash('Invalid clubs selected.', 'warning')
        return redirect('/clubs')
    
    # Check membership in from_club
    membership = Membership.query.filter_by(user_id=current_user.id, club_id=from_club_id).first()
    if not membership:
        flash('You are not a member of the selected source club.', 'warning')
        return redirect('/clubs')
    
    # Check if already member of target club
    existing = Membership.query.filter_by(user_id=current_user.id, club_id=to_club_id).first()
    if existing:
        flash('You are already a member of the target club.', 'warning')
        return redirect('/clubs')
    
    # Send request to leader of source club
    try:
        Notification.notify_leader_student_request(from_club, current_user, f'move to {to_club.club_name}', message)
    except:
        pass
    
    flash(f'Your request to move to {to_club.club_name} has been sent to the leader.', 'info')
    return redirect('/clubs')

# Leader: Remove member from club
@clubs_bp.route('/<int:club_id>/remove-member/<int:user_id>', methods=['POST'])
@login_required
def remove_member(club_id, user_id):
    from models.membership import Membership
    from models.notification import Notification
    from models.user import User
    
    club = Club.query.get_or_404(club_id)
    
    # Only club creator can remove members
    if club.created_by != current_user.id:
        flash('You do not have permission to remove members.', 'danger')
        return redirect(f'/clubs/{club_id}/manage')
    
    membership = Membership.query.filter_by(user_id=user_id, club_id=club_id).first()
    if not membership:
        flash('Member not found in this club.', 'warning')
        return redirect(f'/clubs/{club_id}/manage')
    
    # Don't allow removing yourself
    if user_id == current_user.id:
        flash('You cannot remove yourself as the leader.', 'warning')
        return redirect(f'/clubs/{club_id}/manage')
    
    user = User.query.get(user_id)
    current_app.extensions['sqlalchemy'].db.session.delete(membership)
    current_app.extensions['sqlalchemy'].db.session.commit()
    
    # Notify student
    try:
        Notification.notify_student_left_club(user, club)
    except:
        pass
    
    flash(f'{user.first_name} {user.last_name} has been removed from the club.', 'success')
    return redirect(f'/clubs/{club_id}/manage')

# Leader: Move student to another club
@clubs_bp.route('/<int:club_id>/move-member/<int:user_id>', methods=['POST'])
@login_required
def move_member(club_id, user_id):
    from models.membership import Membership
    from models.notification import Notification
    from models.user import User
    
    club = Club.query.get_or_404(club_id)
    target_club_id = request.form.get('target_club_id')
    
    # Only club creator can move members
    if club.created_by != current_user.id:
        flash('You do not have permission to move members.', 'danger')
        return redirect(f'/clubs/{club_id}/manage')
    
    if not target_club_id:
        flash('Please select a target club.', 'warning')
        return redirect(f'/clubs/{club_id}/manage')
    
    target_club = Club.query.get(target_club_id)
    if not target_club:
        flash('Target club not found.', 'warning')
        return redirect(f'/clubs/{club_id}/manage')
    
    if target_club.status != 'active':
        flash('Cannot move student to an inactive club.', 'warning')
        return redirect(f'/clubs/{club_id}/manage')
    
    # Check if already member of target club
    existing = Membership.query.filter_by(user_id=user_id, club_id=target_club_id).first()
    if existing:
        flash('Student is already a member of the target club.', 'warning')
        return redirect(f'/clubs/{club_id}/manage')
    
    # Check target club capacity
    if target_club.max_members and len(target_club.members) >= target_club.max_members:
        flash(f'Target club is full ({target_club.max_members} members max).', 'warning')
        return redirect(f'/clubs/{club_id}/manage')
    
    user = User.query.get(user_id)
    membership = Membership.query.filter_by(user_id=user_id, club_id=club_id).first()
    
    if membership:
        current_app.extensions['sqlalchemy'].db.session.delete(membership)
    
    # Create new membership in target club
    new_membership = Membership(user_id=user_id, club_id=target_club_id)
    current_app.extensions['sqlalchemy'].db.session.add(new_membership)
    current_app.extensions['sqlalchemy'].db.session.commit()
    
    # Notify student about the move
    try:
        Notification.notify_student_moved_to_club(user, club, target_club)
    except:
        pass
    
    flash(f'{user.first_name} {user.last_name} has been moved to {target_club.club_name}.', 'success')
    return redirect(f'/clubs/{club_id}/manage')

# Leader: Approve leave request (manual removal)
@clubs_bp.route('/<int:club_id>/approve-leave/<int:user_id>', methods=['POST'])
@login_required
def approve_leave(club_id, user_id):
    from models.membership import Membership
    from models.notification import Notification
    from models.user import User
    
    club = Club.query.get_or_404(club_id)
    
    # Only club creator can approve leave
    if club.created_by != current_user.id:
        flash('You do not have permission.', 'danger')
        return redirect(f'/clubs/{club_id}/manage')
    
    membership = Membership.query.filter_by(user_id=user_id, club_id=club_id).first()
    if not membership:
        flash('Member not found.', 'warning')
        return redirect(f'/clubs/{club_id}/manage')
    
    user = User.query.get(user_id)
    current_app.extensions['sqlalchemy'].db.session.delete(membership)
    current_app.extensions['sqlalchemy'].db.session.commit()
    
    # Notify student
    try:
        Notification.notify_student_request_processed(user, club, 'leave', True)
    except:
        pass
    
    flash(f'{user.first_name} {user.last_name}\'s leave request has been approved.', 'success')
    return redirect(f'/clubs/{club_id}/manage')

# Leader: Deny leave request
@clubs_bp.route('/<int:club_id>/deny-leave/<int:user_id>', methods=['POST'])
@login_required
def deny_leave(club_id, user_id):
    from models.membership import Membership
    from models.notification import Notification
    from models.user import User
    
    club = Club.query.get_or_404(club_id)
    
    # Only club creator can deny leave
    if club.created_by != current_user.id:
        flash('You do not have permission.', 'danger')
        return redirect(f'/clubs/{club_id}/manage')
    
    user = User.query.get(user_id)
    
    # Notify student
    try:
        Notification.notify_student_request_processed(user, club, 'leave', False)
    except:
        pass
    
    flash(f'{user.first_name} {user.last_name}\'s leave request has been denied.', 'info')
    return redirect(f'/clubs/{club_id}/manage')
