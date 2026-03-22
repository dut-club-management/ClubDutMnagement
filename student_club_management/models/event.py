from app import db
from datetime import datetime

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_name = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=True)
    location = db.Column(db.String(255), nullable=False)
    max_attendees = db.Column(db.Integer, nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(32), nullable=False, default='pending')  # pending, approved, ongoing, completed
    
    # Event type and club requirements
    requires_club = db.Column(db.Boolean, default=False)  # True = club members join as team, False = individual join
    min_club_members = db.Column(db.Integer, nullable=True)  # minimum members per club if requires_club=True
    max_club_members = db.Column(db.Integer, nullable=True)  # maximum members per club if requires_club=True
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=True)  # club that created this event
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Note: relationships are defined in Club and User models (backref)
    # - club: accessed via Event.club (from Club.events relationship)
    # - creator: accessed via Event.creator (from User.events_created backref)

    def __repr__(self):
        return f"<Event {self.event_name} at {self.event_date}>"
