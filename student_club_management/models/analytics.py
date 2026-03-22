from app import db
from datetime import datetime, timedelta

class Analytics(db.Model):
    """Store analytics data for dashboard metrics"""
    __tablename__ = 'analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    metric_type = db.Column(db.String(50), nullable=False)  # 'membership_growth', 'event_attendance', 'participation'
    metric_date = db.Column(db.Date, nullable=False)
    metric_value = db.Column(db.Integer, nullable=False)
    extra_data = db.Column(db.JSON)  # Additional data like breakdown by category (renamed from metadata)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('metric_type', 'metric_date', name='unique_analytics_metric'),)
    
    def __repr__(self):
        return f"<Analytics {self.metric_type}: {self.metric_value} on {self.metric_date}>"

class EventReminder(db.Model):
    """Track event reminders sent to users"""
    __tablename__ = 'event_reminders'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reminder_type = db.Column(db.String(20), nullable=False)  # '1_day', '1_hour', '1_week'
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    event = db.relationship('Event', backref='reminders')
    user = db.relationship('User', backref='event_reminders')
    
    __table_args__ = (db.UniqueConstraint('event_id', 'user_id', 'reminder_type', name='unique_event_reminder'),)
    
    def __repr__(self):
        return f"<EventReminder {self.reminder_type} for Event {self.event_id} to User {self.user_id}>"

class ClubReminder(db.Model):
    """Track club deadline reminders sent to users"""
    __tablename__ = 'club_reminders'
    
    id = db.Column(db.Integer, primary_key=True)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reminder_type = db.Column(db.String(20), nullable=False)  # 'membership_deadline', 'meeting_reminder'
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    club = db.relationship('Club', backref='reminders')
    user = db.relationship('User', backref='club_reminders')
    
    __table_args__ = (db.UniqueConstraint('club_id', 'user_id', 'reminder_type', name='unique_club_reminder'),)
    
    def __repr__(self):
        return f"<ClubReminder {self.reminder_type} for Club {self.club_id} to User {self.user_id}>"
