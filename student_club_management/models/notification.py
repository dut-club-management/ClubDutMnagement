from app import db
from datetime import datetime

class Notification(db.Model):
    """In-app notifications for users"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(140), nullable=False)
    message = db.Column(db.Text, nullable=False)
    # notification_type: info, event, announcement, reminder, warning, 
    #                   club_membership, event_registration, approval, request, chat
    notification_type = db.Column(db.String(32), nullable=False, default='info')
    link = db.Column(db.String(255), nullable=True)  # Optional link to related content
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='notifications')
    
    def __repr__(self):
        return f"<Notification {self.id} for User {self.user_id}>"
    
    @staticmethod
    def create_notification(user_id, title, message, notification_type='info', link=None):
        """Helper method to create a notification"""
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            link=link
        )
        db.session.add(notification)
        return notification
    
    @staticmethod
    def send_to_user(user_id, title, message, notification_type='info', link=None):
        """Create and commit a notification for a user"""
        notification = Notification.create_notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            link=link
        )
        db.session.commit()
        return notification
    
    @staticmethod
    def send_to_multiple_users(user_ids, title, message, notification_type='info', link=None):
        """Create notifications for multiple users"""
        notifications = []
        for user_id in user_ids:
            notification = Notification.create_notification(
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                link=link
            )
            notifications.append(notification)
        db.session.commit()
        return notifications
    
    @staticmethod
    def send_event_reminder(event, user_ids):
        """Send event reminder to multiple users"""
        title = f"📅 Event Reminder: {event.event_name}"
        message = f"Don't forget! {event.event_name} is happening on {event.event_date.strftime('%B %d, %Y at %I:%M %p')} at {event.location}"
        return Notification.send_to_multiple_users(
            user_ids=user_ids,
            title=title,
            message=message,
            notification_type='reminder',
            link=f'/events/{event.id}'
        )
    
    @staticmethod
    def send_announcement_notification(announcement, user_ids):
        """Send announcement notification to club members"""
        title = f"📢 New Announcement: {announcement.title}"
        message = announcement.content[:200] + "..." if len(announcement.content) > 200 else announcement.content
        return Notification.send_to_multiple_users(
            user_ids=user_ids,
            title=title,
            message=message,
            notification_type='announcement',
            link=f'/announcements/{announcement.id}'
        )
    
    # ==================== Club Notifications ====================
    
    @staticmethod
    def notify_student_joined_club(student, club):
        """Notify student when they join a club"""
        title = f"✅ Joined Club: {club.club_name}"
        message = f"You have successfully joined {club.club_name}. Welcome aboard!"
        return Notification.send_to_user(
            user_id=student.id,
            title=title,
            message=message,
            notification_type='club_membership',
            link=f'/clubs/{club.id}'
        )
    
    @staticmethod
    def notify_student_left_club(student, club):
        """Notify student when they leave a club"""
        title = f"❌ Left Club: {club.club_name}"
        message = f"You have left {club.club_name}."
        return Notification.send_to_user(
            user_id=student.id,
            title=title,
            message=message,
            notification_type='club_membership',
            link=f'/clubs/{club.id}'
        )
    
    @staticmethod
    def notify_leader_student_joined(club, student):
        """Notify club leader when a student joins their club"""
        title = f"👤 New Member: {student.first_name} {student.last_name}"
        message = f"{student.first_name} {student.last_name} has joined your club {club.club_name}."
        return Notification.send_to_user(
            user_id=club.created_by,
            title=title,
            message=message,
            notification_type='club_membership',
            link=f'/clubs/{club.id}/manage'
        )
    
    @staticmethod
    def notify_leader_student_left(club, student):
        """Notify club leader when a student leaves their club"""
        title = f"👋 Member Left: {student.first_name} {student.last_name}"
        message = f"{student.first_name} {student.last_name} has left your club {club.club_name}."
        return Notification.send_to_user(
            user_id=club.created_by,
            title=title,
            message=message,
            notification_type='club_membership',
            link=f'/clubs/{club.id}/manage'
        )
    
    @staticmethod
    def notify_leader_club_approved(club):
        """Notify leader when their club is approved"""
        title = f"🎉 Club Approved: {club.club_name}"
        message = f"Your club '{club.club_name}' has been approved and is now active!"
        return Notification.send_to_user(
            user_id=club.created_by,
            title=title,
            message=message,
            notification_type='approval',
            link=f'/clubs/{club.id}'
        )
    
    @staticmethod
    def notify_leader_club_rejected(club, reason=None):
        """Notify leader when their club is rejected"""
        title = f"❌ Club Rejected: {club.club_name}"
        reason_msg = f" Reason: {reason}" if reason else ""
        message = f"Your club '{club.club_name}' has been rejected.{reason_msg}"
        return Notification.send_to_user(
            user_id=club.created_by,
            title=title,
            message=message,
            notification_type='warning',
            link=f'/clubs/{club.id}'
        )
    
    # ==================== Event Notifications ====================
    
    @staticmethod
    def notify_student_joined_event(student, event):
        """Notify student when they join an event"""
        title = f"✅ Registered for Event: {event.event_name}"
        message = f"You have successfully registered for {event.event_name} on {event.event_date.strftime('%B %d, %Y at %I:%M %p')}."
        return Notification.send_to_user(
            user_id=student.id,
            title=title,
            message=message,
            notification_type='event_registration',
            link=f'/events/{event.id}'
        )
    
    @staticmethod
    def notify_leader_event_joined(event, student):
        """Notify event leader when a student joins their event"""
        title = f"🎫 New Attendee: {student.first_name} {student.last_name}"
        message = f"{student.first_name} {student.last_name} has registered for your event '{event.event_name}'."
        return Notification.send_to_user(
            user_id=event.created_by,
            title=title,
            message=message,
            notification_type='event_registration',
            link=f'/events/{event.id}/attendance'
        )
    
    @staticmethod
    def notify_leader_event_approved(event):
        """Notify leader when their event is approved"""
        title = f"🎉 Event Approved: {event.event_name}"
        message = f"Your event '{event.event_name}' has been approved and is now visible to students!"
        return Notification.send_to_user(
            user_id=event.created_by,
            title=title,
            message=message,
            notification_type='approval',
            link=f'/events/{event.id}'
        )
    
    @staticmethod
    def notify_leader_event_rejected(event, reason=None):
        """Notify leader when their event is rejected"""
        title = f"❌ Event Rejected: {event.event_name}"
        reason_msg = f" Reason: {reason}" if reason else ""
        message = f"Your event '{event.event_name}' has been rejected.{reason_msg}"
        return Notification.send_to_user(
            user_id=event.created_by,
            title=title,
            message=message,
            notification_type='warning',
            link=f'/events/{event.id}'
        )
    
    @staticmethod
    def notify_event_reminder_24h(event, user_ids):
        """Send reminder notification 24 hours before event"""
        title = f"⏰ Tomorrow: {event.event_name}"
        message = f"Don't forget! {event.event_name} is happening tomorrow at {event.event_date.strftime('%I:%M %p')} at {event.location}."
        return Notification.send_to_multiple_users(
            user_ids=user_ids,
            title=title,
            message=message,
            notification_type='reminder',
            link=f'/events/{event.id}'
        )
    
    @staticmethod
    def notify_event_reminder_1h(event, user_ids):
        """Send reminder notification 1 hour before event"""
        title = f"🚨 Starting Soon: {event.event_name}"
        message = f"{event.event_name} starts in 1 hour at {event.location}. Don't be late!"
        return Notification.send_to_multiple_users(
            user_ids=user_ids,
            title=title,
            message=message,
            notification_type='reminder',
            link=f'/events/{event.id}'
        )
    
    @staticmethod
    def notify_club_meeting_reminder(club, user_ids, meeting_time):
        """Send reminder notification 24 hours before club meeting"""
        day_name = meeting_time.strftime('%A')
        time_str = meeting_time.strftime('%I:%M %p')
        title = f"📅 Club Meeting Tomorrow: {club.club_name}"
        message = f"Don't forget! {club.club_name} has a meeting tomorrow ({day_name}) at {time_str}."
        return Notification.send_to_multiple_users(
            user_ids=user_ids,
            title=title,
            message=message,
            notification_type='reminder',
            link=f'/clubs/{club.id}'
        )
    
    @staticmethod
    def notify_club_meeting_reminder_1h(club, user_ids, meeting_time):
        """Send reminder notification 1 hour before club meeting"""
        time_str = meeting_time.strftime('%I:%M %p')
        title = f"🚨 Meeting Starting Soon: {club.club_name}"
        message = f"{club.club_name} meeting starts in 1 hour at {time_str}. See you there!"
        return Notification.send_to_multiple_users(
            user_ids=user_ids,
            title=title,
            message=message,
            notification_type='reminder',
            link=f'/clubs/{club.id}'
        )
    
    # ==================== Request Notifications ====================
    
    @staticmethod
    def notify_leader_student_request(club, student, request_type, message):
        """Notify leader about a student's request (leave club, move club, etc.)"""
        title = f"📋 Request from {student.first_name} {student.last_name}"
        request_msg = f"Request: {request_type}\n{message}"
        return Notification.send_to_user(
            user_id=club.created_by,
            title=title,
            message=request_msg,
            notification_type='request',
            link=f'/clubs/{club.id}/manage'
        )
    
    @staticmethod
    def notify_student_request_processed(student, club, request_type, approved):
        """Notify student about their request being approved/denied"""
        status = "approved" if approved else "denied"
        title = f"📋 Your {request_type} Request {status.title()}"
        message = f"Your request to {request_type} for {club.club_name} has been {status}."
        return Notification.send_to_user(
            user_id=student.id,
            title=title,
            message=message,
            notification_type='approval' if approved else 'warning',
            link=f'/clubs/{club.id}'
        )
    
    @staticmethod
    def notify_student_moved_to_club(student, old_club, new_club):
        """Notify student when they are moved to a new club"""
        title = f"🔄 Club Transfer: {new_club.club_name}"
        message = f"You have been moved from {old_club.club_name} to {new_club.club_name}."
        return Notification.send_to_user(
            user_id=student.id,
            title=title,
            message=message,
            notification_type='club_membership',
            link=f'/clubs/{new_club.id}'
        )
    
    @staticmethod
    def notify_admin_club_deletion_request(club):
        """Notify admin when a leader requests to delete their club"""
        from models.user import User
        # Get all admin users
        admins = User.query.filter_by(role='admin').all()
        
        title = f"🗑️ Club Deletion Request: {club.club_name}"
        message = f"Leader has requested to delete club '{club.club_name}'. Admin approval is required."
        
        for admin in admins:
            Notification.send_to_user(
                user_id=admin.id,
                title=title,
                message=message,
                notification_type='request',
                link=f'/admin/clubs'
            )
    
    @staticmethod
    def create_event_reminder(user_id, event, reminder_type, message):
        """Create event reminder notification"""
        return Notification.send_to_user(
            user_id=user_id,
            title=f"⏰ Event Reminder: {event.event_name}",
            message=message,
            notification_type='reminder',
            link=f'/events/{event.id}'
        )
    
    @staticmethod
    def create_club_reminder(user_id, club, reminder_type, message):
        """Create club reminder notification"""
        return Notification.send_to_user(
            user_id=user_id,
            title=f"🏛️ Club Reminder: {club.club_name}",
            message=message,
            notification_type='reminder',
            link=f'/clubs/{club.id}'
        )


class AnnouncementNotification(db.Model):
    """Track which users have received announcement notifications"""
    id = db.Column(db.Integer, primary_key=True)
    announcement_id = db.Column(db.Integer, db.ForeignKey('announcement.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    email_sent = db.Column(db.Boolean, default=False)
    notification_sent = db.Column(db.Boolean, default=False)
    is_read = db.Column(db.Boolean, default=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('announcement_id', 'user_id', name='unique_announcement_notification'),)
    
    def __repr__(self):
        return f"<AnnouncementNotification announcement={self.announcement_id} user={self.user_id}>"

