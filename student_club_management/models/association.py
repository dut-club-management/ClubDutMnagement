from app import db
from datetime import datetime

# many-to-many tables without extra fields

event_attendees = db.Table(
    'event_attendees',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('event_id', db.Integer, db.ForeignKey('event.id'), primary_key=True)
)

announcement_read_receipts = db.Table(
    'announcement_read_receipts',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('announcement_id', db.Integer, db.ForeignKey('announcement.id'), primary_key=True)
)

# association object for achievements with earned_date
class UserAchievement(db.Model):
    __tablename__ = 'user_achievement'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievement.id'), primary_key=True)
    earned_date = db.Column(db.DateTime, default=datetime.utcnow)

    # backrefs defined in models

    def __repr__(self):
        return f"<UserAchievement user={self.user_id} ach={self.achievement_id}>"