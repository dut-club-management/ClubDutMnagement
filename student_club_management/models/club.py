from app import db
from datetime import datetime

class Club(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    club_name = db.Column(db.String(140), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(64), nullable=False)
    logo_url = db.Column(db.String(255), nullable=False, default='default-club.png')
    cover_image = db.Column(db.String(255), nullable=True)
    meeting_schedule = db.Column(db.String(255), nullable=True)
    social_links = db.Column(db.Text, nullable=True)  # JSON format
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    max_members = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(32), nullable=False, default='pending')
    rejection_reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # relationships
    members = db.relationship('Membership', backref='club', lazy=True)
    events = db.relationship('Event', backref='club', lazy=True)
    announcements = db.relationship('Announcement', backref='club', lazy=True)
    bookings = db.relationship('Booking', backref='club', lazy=True)
    creator = db.relationship('User', backref='created_clubs', foreign_keys=[created_by])

    def __repr__(self):
        return f"<Club {self.club_name}>"
