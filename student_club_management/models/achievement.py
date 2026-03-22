from app import db
from datetime import datetime

class Achievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    badge_image = db.Column(db.String(255), nullable=False)
    criteria_type = db.Column(db.String(64), nullable=True)
    criteria_value = db.Column(db.Integer, nullable=True)
    points = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    users_earned = db.relationship('UserAchievement', backref='achievement', lazy=True)

    def __repr__(self):
        return f"<Achievement {self.name}>"