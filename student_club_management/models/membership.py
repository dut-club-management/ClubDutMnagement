from app import db
from datetime import datetime

class Membership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)
    role = db.Column(db.String(64), nullable=False, default='member')
    joined_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(32), nullable=False, default='active')
    contributions = db.Column(db.Integer, default=0)
    last_active = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<Membership user={self.user_id} club={self.club_id} role={self.role}>"
