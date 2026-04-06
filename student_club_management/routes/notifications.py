from flask import Blueprint, render_template, jsonify, request, redirect, flash, current_app
from flask_login import login_required, current_user
from models.notification import Notification
from app import db
from datetime import datetime

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')

@notifications_bp.route('/')
@login_required
def index():
    """Show all notifications for current user"""
    notifications = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.created_at.desc()).all()
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return render_template('notifications/index.html', 
                         notifications=notifications,
                         unread_count=unread_count)

# API: Get unread count - Returns total number of unread notifications for real-time badge
@notifications_bp.route('/api/unread-count')
@login_required
def unread_count():
    """Get count of unread notifications"""
    try:
        count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        return jsonify({'count': count})
    except Exception as e:
        print(f"❌ Notifications API error: {e}")
        return jsonify({'count': 0})

# API: Get latest - Returns recent notifications for dropdown/preview
@notifications_bp.route('/api/latest')
@login_required
def latest():
    """Get latest notifications for dropdown"""
    notifications = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.created_at.desc()).limit(5).all()
    return jsonify([{
        'id': n.id,
        'title': n.title,
        'message': n.message,
        'type': n.notification_type,
        'is_read': n.is_read,
        'link': n.link,
        'created_at': n.created_at.strftime('%b %d, %Y %I:%M %p')
    } for n in notifications])

# API: Mark read - Marks a specific notification as read
@notifications_bp.route('/api/mark-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_read(notification_id):
    """Mark a notification as read"""
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    notification.is_read = True
    db.session.commit()
    return jsonify({'success': True})

# API: Mark all read - Marks all user notifications as read
@notifications_bp.route('/api/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    """Mark all notifications as read"""
    from app import db
    Notification.query.filter_by(user_id=current_user.id, is_read=False)\
        .update({'is_read': True})
    db.session.commit()
    return jsonify({'success': True})

# API: Delete notification - Deletes a specific notification
@notifications_bp.route('/api/delete/<int:notification_id>', methods=['POST'])
@login_required
def delete(notification_id):
    """Delete a notification"""
    from app import db
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(notification)
    db.session.commit()
    return jsonify({'success': True})

@notifications_bp.route('/delete/<int:notification_id>')
@login_required
def delete_redirect(notification_id):
    """Delete notification and redirect"""
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != current_user.id:
        flash('Unauthorized', 'danger')
        return redirect('/notifications')
    
    db.session.delete(notification)
    db.session.commit()
    flash('Notification deleted', 'success')
    return redirect('/notifications')


def send_event_notification(event, user_ids, notification_type='event'):
    """Helper function to send event notifications"""
    title = f"📅 New Event: {event.event_name}"
    message = f"A new event '{event.event_name}' has been created. Date: {event.event_date.strftime('%B %d, %Y at %I:%M %p')}"
    
    notifications = []
    for user_id in user_ids:
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            link=f'/events/{event.id}'
        )
        notifications.append(notification)
    
    if notifications:
        db.session.add_all(notifications)
        db.session.commit()
    
    return notifications


def send_reminder_notifications():
    """Send reminders for upcoming events (can be called by scheduler)"""
    from datetime import datetime, timedelta
    from models.event import Event
    from models.attendance import EventAttendance
    
    # Find events happening in the next 24 hours
    now = datetime.utcnow()
    tomorrow = now + timedelta(hours=24)
    
    upcoming_events = Event.query.filter(
        Event.status == 'approved',
        Event.event_date > now,
        Event.event_date <= tomorrow
    ).all()
    
    for event in upcoming_events:
        # Get attendees who haven't received a reminder
        attendances = EventAttendance.query.filter_by(event_id=event.id, is_attended=False).all()
        user_ids = [a.user_id for a in attendances]
        
        if user_ids:
            Notification.notify_event_reminder_24h(event, user_ids)
    
    return len(upcoming_events)


def send_meeting_reminders():
    """Send reminders for upcoming club meetings"""
    from datetime import datetime, timedelta
    from models.club import Club
    from models.membership import Membership
    import re
    
    # Find clubs with meeting schedules
    clubs = Club.query.filter(
        Club.status == 'active',
        Club.meeting_schedule.isnot(None),
        Club.meeting_schedule != ''
    ).all()
    
    now = datetime.utcnow()
    reminders_sent = 0
    
    for club in clubs:
        # Parse meeting schedule to find next meeting time
        # Format: "Monday 14:00" or "Wed 15:30"
        if club.meeting_schedule:
            meeting_info = parse_meeting_schedule(club.meeting_schedule, now)
            if meeting_info:
                next_meeting = meeting_info['next_meeting']
                # If meeting is within 24 hours
                if now < next_meeting <= now + timedelta(hours=24):
                    # Get all club members
                    memberships = Membership.query.filter_by(club_id=club.id).all()
                    user_ids = [m.user_id for m in memberships]
                    
                    if user_ids:
                        Notification.notify_club_meeting_reminder(club, user_ids, next_meeting)
                        reminders_sent += 1
    
    return reminders_sent


def parse_meeting_schedule(schedule_str, reference_date):
    """Parse meeting schedule string and return next meeting datetime"""
    from datetime import datetime, timedelta
    
    # Day name to number mapping
    days = {
        'monday': 0, 'mon': 0,
        'tuesday': 1, 'tue': 1,
        'wednesday': 2, 'wed': 2,
        'thursday': 3, 'thu': 3,
        'friday': 4, 'fri': 4,
        'saturday': 5, 'sat': 5,
        'sunday': 6, 'sun': 6
    }
    
    # Try to parse "DayName Time" format
    schedule_str = schedule_str.strip().lower()
    
    for day_name, day_num in days.items():
        if day_name in schedule_str:
            # Extract time
            time_match = re.search(r'(\d{1,2}):(\d{2})', schedule_str)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2))
                
                # Find next occurrence of this day
                current_day = reference_date.weekday()
                days_ahead = day_num - current_day
                if days_ahead <= 0:
                    days_ahead += 7
                
                next_meeting = reference_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                next_meeting += timedelta(days=days_ahead)
                
                return {
                    'day_name': day_name,
                    'time': f"{hour:02d}:{minute:02d}",
                    'next_meeting': next_meeting
                }
    
    return None


def send_1hour_event_reminders():
    """Send reminders for events happening in 1 hour"""
    from datetime import datetime, timedelta
    from models.event import Event
    from models.attendance import EventAttendance
    
    now = datetime.utcnow()
    one_hour = now + timedelta(hours=1)
    
    # Find events starting in the next hour
    upcoming_events = Event.query.filter(
        Event.status == 'approved',
        Event.event_date > now,
        Event.event_date <= one_hour
    ).all()
    
    for event in upcoming_events:
        attendances = EventAttendance.query.filter_by(event_id=event.id, is_attended=False).all()
        user_ids = [a.user_id for a in attendances]
        
        if user_ids:
            Notification.notify_event_reminder_1h(event, user_ids)
    
    return len(upcoming_events)


def send_1hour_meeting_reminders():
    """Send reminders for club meetings happening in 1 hour"""
    from datetime import datetime, timedelta
    from models.club import Club
    from models.membership import Membership
    
    clubs = Club.query.filter(
        Club.status == 'active',
        Club.meeting_schedule.isnot(None),
        Club.meeting_schedule != ''
    ).all()
    
    now = datetime.utcnow()
    reminders_sent = 0
    
    for club in clubs:
        if club.meeting_schedule:
            meeting_info = parse_meeting_schedule(club.meeting_schedule, now)
            if meeting_info:
                next_meeting = meeting_info['next_meeting']
                # If meeting is within 1 hour
                if now < next_meeting <= now + timedelta(hours=1):
                    memberships = Membership.query.filter_by(club_id=club.id).all()
                    user_ids = [m.user_id for m in memberships]
                    
                    if user_ids:
                        Notification.notify_club_meeting_reminder_1h(club, user_ids, next_meeting)
                        reminders_sent += 1
    
    return reminders_sent


# API endpoint to trigger reminder notifications (can be called by cron job)
@notifications_bp.route('/api/send-reminders', methods=['POST'])
@login_required
def api_send_reminders():
    """API endpoint to send event reminders (for scheduled tasks)"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    events_count = send_reminder_notifications()
    meetings_count = send_meeting_reminders()
    
    return jsonify({
        'success': True, 
        'events_processed': events_count,
        'meetings_processed': meetings_count,
        'message': f'Sent reminders for {events_count} events and {meetings_count} meetings'
    })

@notifications_bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Mark all notifications as read"""
    try:
        # Update all unread notifications
        unread_notifications = Notification.query.filter_by(
            user_id=current_user.id, 
            is_read=False
        ).all()
        
        for notification in unread_notifications:
            notification.is_read = True
            notification.read_at = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'All notifications marked as read',
            'count': 0
        })
    except Exception as e:
        print(f"❌ Mark all read error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@notifications_bp.route('/api/recent')
@login_required
def recent_notifications():
    """Get recent notifications for dashboard"""
    try:
        notifications = Notification.query.filter_by(user_id=current_user.id)\
            .order_by(Notification.created_at.desc())\
            .limit(10).all()
        
        notifications_data = []
        for notification in notifications:
            notifications_data.append({
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'type': notification.type,
                'is_read': notification.is_read,
                'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'action_url': notification.action_url
            })
        
        return jsonify(notifications_data)
    except Exception as e:
        print(f"❌ Recent notifications error: {e}")
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/api/recent')
@login_required
def recent_notifications():
    """Get recent notifications for dashboard"""
    try:
        notifications = Notification.query.filter_by(user_id=current_user.id)\
            .order_by(Notification.created_at.desc())\
            .limit(10).all()
        
        notifications_data = []
        for notification in notifications:
            notifications_data.append({
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'type': notification.type,
                'is_read': notification.is_read,
                'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'action_url': notification.action_url
            })
        
        return jsonify(notifications_data)
    except Exception as e:
        print(f"❌ Recent notifications error: {e}")
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/mark-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Mark a specific notification as read"""
    try:
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=current_user.id
        ).first()
        
        if not notification:
            return jsonify({'success': False, 'error': 'Notification not found'}), 404
        
        notification.is_read = True
        notification.read_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Notification marked as read'
        })
    except Exception as e:
        print(f"❌ Mark notification read error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@notifications_bp.route('/delete/<int:notification_id>', methods=['DELETE'])
@login_required
def delete_notification(notification_id):
    """Delete a notification"""
    try:
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=current_user.id
        ).first()
        
        if not notification:
            return jsonify({'success': False, 'error': 'Notification not found'}), 404
        
        db.session.delete(notification)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Notification deleted'
        })
    except Exception as e:
        print(f"❌ Delete notification error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

