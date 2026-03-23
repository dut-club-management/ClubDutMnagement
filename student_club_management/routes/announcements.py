from flask import Blueprint, render_template, request, redirect, flash, jsonify
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from app import db
from models.announcement import Announcement, AnnouncementReaction, AnnouncementComment
from models.club import Club
from models.membership import Membership
from models.notification import Notification, AnnouncementNotification
from datetime import datetime
import json
import os
from werkzeug.utils import secure_filename
from flask import current_app
from sqlalchemy import select, func

announcements_bp = Blueprint('announcements', __name__, url_prefix='/announcements')

@announcements_bp.route('/')
@login_required
def index():
    """Show all announcements for current user based on their club memberships"""
    if current_user.role == 'admin':
        announcements = Announcement.query.order_by(Announcement.pinned.desc(), Announcement.created_at.desc()).all()
    elif current_user.role == 'leader':
        # Show all announcements from all active clubs for any leader
        active_clubs = Club.query.filter(Club.status == 'active').all()
        club_ids = [c.id for c in active_clubs]
        announcements = Announcement.query.filter(Announcement.club_id.in_(club_ids)).order_by(
            Announcement.pinned.desc(), Announcement.created_at.desc()
        ).all()
    else:
        memberships = Membership.query.filter_by(user_id=current_user.id, status='active').all()
        club_ids = [m.club_id for m in memberships]
        announcements = Announcement.query.filter(Announcement.club_id.in_(club_ids)).order_by(
            Announcement.pinned.desc(), Announcement.created_at.desc()
        ).all()
    
    return render_template('announcements/index.html', announcements=announcements)

@announcements_bp.route('/api/unread-count')
@login_required
def unread_count():
    """Get count of unread announcements for real-time badge updates"""
    try:
        if current_user.role == 'admin':
            club_ids = [c.id for c in Club.query.all()]
        elif current_user.role == 'leader':
            # Show all active clubs for any leader
            active_clubs = Club.query.filter(Club.status == 'active').all()
            club_ids = [c.id for c in active_clubs]
        else:
            memberships = Membership.query.filter_by(user_id=current_user.id, status='active').all()
            club_ids = [m.club_id for m in memberships]
        
        if not club_ids:
            return jsonify({'count': 0})
        
        read_receipts = db.session.query(AnnouncementNotification.announcement_id).filter(
            AnnouncementNotification.user_id == current_user.id
        ).subquery()
        
        unread_count = db.session.query(func.count(Announcement.id)).filter(
            Announcement.club_id.in_(club_ids),
            ~Announcement.id.in_(select(read_receipts))
        ).scalar() or 0
        
        return jsonify({'count': unread_count})
    except Exception as e:
        print(f"❌ Announcements API error: {e}")
        return jsonify({'count': 0})

@announcements_bp.route('/club/<int:club_id>')
@login_required
def club_announcements(club_id):
    """Show announcements for a specific club"""
    club = Club.query.get_or_404(club_id)
    
    if current_user.role == 'student':
        membership = Membership.query.filter_by(user_id=current_user.id, club_id=club_id, status='active').first()
        if not membership and club.created_by != current_user.id:
            flash("You do not have access to this club's announcements", 'warning')
            return redirect('/announcements')
    
    announcements = Announcement.query.filter_by(club_id=club_id).order_by(
        Announcement.pinned.desc(), Announcement.created_at.desc()
    ).all()
    
    return render_template('announcements/club.html', club=club, announcements=announcements)

@announcements_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new announcement"""
    try:
        if current_user.role not in ['leader', 'admin']:
            flash('Only leaders and admins can create announcements', 'warning')
            return redirect('/announcements')
        
        class AnnouncementForm(FlaskForm):
            pass
        
        form = AnnouncementForm()
        
        if request.method == 'POST':
            send_to = request.form.get('send_to', 'club_members')
            club_id = request.form.get('club_id')
            title = request.form.get('title')
            content = request.form.get('content')
            priority = request.form.get('priority', 'normal')
            pinned = request.form.get('pinned') == 'on'
            
            print(f"🔍 Form data: send_to={send_to}, club_id={club_id}, title={title}")
            
            if send_to == 'club_members':
                if not club_id:
                    flash('Please select a club', 'danger')
                    return redirect('/announcements/create')
            elif send_to == 'students_only':
                if not club_id:
                    club = Club.query.filter(Club.status == 'active').first()
                    if club:
                        club_id = str(club.id)
                    else:
                        flash('No active clubs available', 'danger')
                        return redirect('/announcements/create')
            else:
                if not club_id:
                    club = Club.query.filter(Club.status == 'active').first()
                    if club:
                        club_id = str(club.id)
                    else:
                        flash('No active clubs available', 'danger')
                        return redirect('/announcements/create')
            
            if not title or not content:
                flash('Title and content are required', 'danger')
                return redirect('/announcements/create')
            
            # Validate club exists
            club = Club.query.get(club_id)
            if not club:
                flash('Club not found', 'danger')
                return redirect('/announcements/create')
            
            print(f"🔍 Using club: {club.club_name} (ID: {club.id})")
            
            resource_links = request.form.get('resource_links', '')
            resource_links_json = None
            if resource_links:
                try:
                    links = [l.strip() for l in resource_links.split('\n') if l.strip()]
                    resource_links_json = json.dumps(links)
                    print(f"🔍 Resource links: {links}")
                except Exception as e:
                    print(f"⚠️ Error parsing resource links: {e}")
                    resource_links_json = None
            
            attachment_url = None
            attachment_name = None
            if 'attachment' in request.files:
                file = request.files['attachment']
                if file.filename:
                    filename = secure_filename(file.filename)
                    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'announcements')
                    os.makedirs(upload_folder, exist_ok=True)
                    filepath = os.path.join(upload_folder, f"{datetime.now().timestamp()}_{filename}")
                    file.save(filepath)
                    attachment_url = f"static/uploads/announcements/{os.path.basename(filepath)}"
                    attachment_name = file.filename
                    print(f"🔍 Attachment saved: {attachment_url}")
            
            announcement = Announcement(
                club_id=int(club_id),
                created_by=current_user.id,
                title=title,
                content=content,
                priority=priority,
                pinned=pinned,
                attachment_url=attachment_url,
                attachment_name=attachment_name,
                resource_links=resource_links_json
            )
            
            print(f"🔍 Creating announcement: {announcement.title}")
            db.session.add(announcement)
            db.session.commit()
            print(f"✅ Announcement created successfully with ID: {announcement.id}")
            
            try:
                if send_to == 'all_users' and current_user.role == 'admin':
                    from models.user import User
                    all_users = User.query.filter(User.id != current_user.id).all()
                    user_ids = [u.id for u in all_users]
                    if user_ids:
                        Notification.send_announcement_notification(announcement, user_ids)
                elif send_to == 'students_only' and current_user.role in ['admin', 'leader']:
                    from models.user import User
                    students = User.query.filter(User.role == 'student', User.id != current_user.id).all()
                    user_ids = [u.id for u in students]
                    if user_ids:
                        Notification.send_announcement_notification(announcement, user_ids)
                else:
                    members = Membership.query.filter_by(club_id=club_id, status='active').all()
                    user_ids = [m.user_id for m in members if m.user_id != current_user.id]
                    if user_ids:
                        Notification.send_announcement_notification(announcement, user_ids)
            except Exception as e:
                print(f"⚠️ Error sending notifications: {e}")
            
            flash('Announcement created successfully!', 'success')
            return redirect(f'/announcements/{announcement.id}')
        
        # Show all clubs for admin (including pending ones), active clubs for others
        if current_user.role == 'admin':
            clubs = Club.query.all()
        else:
            clubs = Club.query.filter(Club.status == 'active').all()
        
        return render_template('announcements/create.html', form=form, clubs=clubs)
        
    except Exception as e:
        print(f"❌ Announcement creation error: {e}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
        flash('Error creating announcement. Please try again.', 'danger')
        return redirect('/announcements/create')

@announcements_bp.route('/<int:announcement_id>')
@login_required
def detail(announcement_id):
    """View announcement details"""
    try:
        print(f"🔍 Viewing announcement {announcement_id}")
        
        announcement = Announcement.query.get_or_404(announcement_id)
        club = Club.query.get(announcement.club_id)
        
        print(f"🔍 Found announcement: {announcement.title}")
        print(f"🔍 Club: {club.club_name if club else 'None'}")
        
        if current_user.role == 'student':
            membership = Membership.query.filter_by(
                user_id=current_user.id, 
                club_id=announcement.club_id, 
                status='active'
            ).first()
            if not membership and club.created_by != current_user.id:
                flash("You do not have access to this announcement", 'warning')
                return redirect('/announcements')
        
        comments = AnnouncementComment.query.filter_by(announcement_id=announcement_id).order_by(
            AnnouncementComment.created_at.asc()
        ).all()
        
        user_reaction = announcement.get_user_reaction(current_user.id)
        reactions_count = announcement.get_reactions_count()
        
        # Parse resource links from JSON
        resource_links = []
        if announcement.resource_links:
            try:
                import json
                resource_links = json.loads(announcement.resource_links)
                print(f"🔍 Parsed {len(resource_links)} resource links")
            except Exception as e:
                print(f"⚠️ Error parsing resource links: {e}")
                resource_links = []
        
        print(f"✅ Rendering announcement detail template")
        return render_template('announcements/detail.html', 
                             announcement=announcement,
                             club=club,
                             comments=comments,
                             user_reaction=user_reaction,
                             reactions_count=reactions_count,
                             resource_links=resource_links)
        
    except Exception as e:
        print(f"❌ Announcement detail error: {e}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
        flash('Error loading announcement. Please try again.', 'danger')
        return redirect('/announcements')

@announcements_bp.route('/<int:announcement_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(announcement_id):
    """Edit an announcement"""
    announcement = Announcement.query.get_or_404(announcement_id)
    club = Club.query.get(announcement.club_id)
    
    if current_user.role == 'student':
        flash('You do not have permission to edit announcements', 'danger')
        return redirect('/announcements')
    
    if current_user.role == 'leader' and announcement.created_by != current_user.id:
        flash('You can only edit your own announcements', 'danger')
        return redirect('/announcements')
    
    if request.method == 'POST':
        announcement.title = request.form.get('title')
        announcement.content = request.form.get('content')
        announcement.priority = request.form.get('priority', 'normal')
        announcement.pinned = request.form.get('pinned') == 'on'
        
        resource_links = request.form.get('resource_links', '')
        if resource_links:
            try:
                links = [l.strip() for l in resource_links.split('\n') if l.strip()]
                announcement.resource_links = json.dumps(links)
            except:
                pass
        
        if 'attachment' in request.files:
            file = request.files['attachment']
            if file.filename:
                filename = secure_filename(file.filename)
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'announcements')
                os.makedirs(upload_folder, exist_ok=True)
                filepath = os.path.join(upload_folder, f"{datetime.now().timestamp()}_{filename}")
                file.save(filepath)
                announcement.attachment_url = f"static/uploads/announcements/{os.path.basename(filepath)}"
                announcement.attachment_name = file.filename
        
        db.session.commit()
        flash('Announcement updated successfully!', 'success')
        return redirect(f'/announcements/{announcement.id}')
    
    resource_links_list = []
    if announcement.resource_links:
        try:
            resource_links_list = json.loads(announcement.resource_links)
        except:
            pass
    
    return render_template('announcements/edit.html', 
                         announcement=announcement,
                         resource_links=resource_links_list)

@announcements_bp.route('/<int:announcement_id>/delete', methods=['POST'])
@login_required
def delete(announcement_id):
    """Delete an announcement"""
    try:
        print(f"🔍 Announcement delete: Starting deletion of announcement {announcement_id}")
        
        announcement = Announcement.query.get_or_404(announcement_id)
        club = Club.query.get(announcement.club_id)
        
        print(f"🔍 Announcement delete: Found announcement: {announcement.title}")
        print(f"🔍 Announcement delete: User role: {current_user.role}")
        
        if current_user.role == 'admin':
            print("🔍 Announcement delete: Admin user - allowing deletion")
        elif current_user.role == 'leader':
            if announcement.created_by != current_user.id:
                print(f"🔍 Announcement delete: Leader trying to delete other's announcement (created_by: {announcement.created_by}, current_user: {current_user.id})")
                flash('You can only delete your own announcements', 'danger')
                return redirect('/announcements')
            else:
                print("🔍 Announcement delete: Leader deleting own announcement - allowed")
        elif current_user.role == 'student':
            print("🔍 Announcement delete: Student user - denying deletion")
            flash('You do not have permission to delete announcements', 'danger')
            return redirect('/announcements')
        
        print("🔍 Announcement delete: Deleting announcement from database...")
        db.session.delete(announcement)
        db.session.commit()
        print("🔍 Announcement delete: Successfully deleted and committed")
        
        flash('Announcement deleted successfully!', 'success')
        return redirect('/announcements')
        
    except Exception as e:
        print(f"❌ Announcement delete error: {e}")
        print(f"❌ Error type: {type(e)}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
        flash('Error deleting announcement. Please try again.', 'danger')
        return redirect('/announcements')

# API: React to announcement
@announcements_bp.route('/api/<int:announcement_id>/react', methods=['POST'])
@login_required
def react(announcement_id):
    """Add or remove reaction to announcement"""
    data = request.get_json()
    reaction_type = data.get('reaction_type')
    
    announcement = Announcement.query.get_or_404(announcement_id)
    
    existing = AnnouncementReaction.query.filter_by(
        announcement_id=announcement_id,
        user_id=current_user.id
    ).first()
    
    if existing:
        if existing.reaction_type == reaction_type:
            db.session.delete(existing)
            db.session.commit()
            return jsonify({'success': True, 'action': 'removed'})
        else:
            existing.reaction_type = reaction_type
            db.session.commit()
            return jsonify({'success': True, 'action': 'updated'})
    else:
        reaction = AnnouncementReaction(
            announcement_id=announcement_id,
            user_id=current_user.id,
            reaction_type=reaction_type
        )
        db.session.add(reaction)
        db.session.commit()
        return jsonify({'success': True, 'action': 'added'})

# API: Get reactions
@announcements_bp.route('/api/<int:announcement_id>/reactions')
@login_required
def get_reactions(announcement_id):
    """Get all reactions for an announcement"""
    announcement = Announcement.query.get_or_404(announcement_id)
    counts = announcement.get_reactions_count()
    user_reaction = announcement.get_user_reaction(current_user.id)
    
    return jsonify({
        'counts': counts,
        'user_reaction': user_reaction,
        'total': sum(counts.values())
    })

# API: Add comment
@announcements_bp.route('/api/<int:announcement_id>/comment', methods=['POST'])
@login_required
def add_comment(announcement_id):
    """Add a comment to an announcement"""
    data = request.get_json()
    content = data.get('content', '').strip()
    
    if not content:
        return jsonify({'error': 'Comment cannot be empty'}), 400
    
    announcement = Announcement.query.get_or_404(announcement_id)
    
    comment = AnnouncementComment(
        announcement_id=announcement_id,
        user_id=current_user.id,
        content=content
    )
    db.session.add(comment)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'comment': {
            'id': comment.id,
            'content': comment.content,
            'user_name': f"{current_user.first_name} {current_user.last_name}",
            'created_at': comment.created_at.strftime('%b %d, %Y %I:%M %p')
        }
    })

# API: Mark announcement as read
@announcements_bp.route('/api/<int:announcement_id>/mark-read', methods=['POST'])
@login_required
def mark_read(announcement_id):
    """Mark announcement as read for current user"""
    notification = AnnouncementNotification.query.filter_by(
        announcement_id=announcement_id, 
        user_id=current_user.id
    ).first()
    if notification:
        notification.notification_sent = True
    else:
        notification = AnnouncementNotification(
            announcement_id=announcement_id,
            user_id=current_user.id
        )
        db.session.add(notification)
    db.session.commit()
    return jsonify({'success': True})

# API: Mark all announcements as read
@announcements_bp.route('/api/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    """Mark all announcements as read for current user"""
    if current_user.role == 'admin':
        club_ids = [c.id for c in Club.query.all()]
    elif current_user.role == 'leader':
        # Show all active clubs for any leader (consistent with other functions)
        active_clubs = Club.query.filter(Club.status == 'active').all()
        club_ids = [c.id for c in active_clubs]
    else:
        memberships = Membership.query.filter_by(user_id=current_user.id, status='active').all()
        club_ids = [m.club_id for m in memberships]
    
    if club_ids:
        announcements = Announcement.query.filter(Announcement.club_id.in_(club_ids)).all()
        announcement_ids = [a.id for a in announcements]
        notifications = AnnouncementNotification.query.filter(
            AnnouncementNotification.user_id == current_user.id,
            AnnouncementNotification.announcement_id.in_(announcement_ids)
        ).all()
        for notification in notifications:
            notification.is_read = True
        db.session.commit()
    
    return jsonify({'success': True})

# API: Delete comment
@announcements_bp.route('/api/comment/<int:comment_id>', methods=['DELETE'])
@login_required
def delete_comment(comment_id):
    """Delete a comment"""
    comment = AnnouncementComment.query.get_or_404(comment_id)
    
    if comment.user_id != current_user.id:
        club = Club.query.get(comment.announcement.club_id)
        if current_user.role == 'leader' and club.created_by != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        if current_user.role != 'admin' and current_user.role != 'leader':
            return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(comment)
    db.session.commit()
    
    return jsonify({'success': True})

