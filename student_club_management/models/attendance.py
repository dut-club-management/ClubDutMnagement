from app import db
from datetime import datetime
import uuid

class EventAttendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    qr_code = db.Column(db.String(500), nullable=False, unique=True)  # QR code data
    qr_token = db.Column(db.String(36), nullable=False, unique=True)  # Unique token for QR encoding
    is_attended = db.Column(db.Boolean, default=False)
    checked_in_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    event = db.relationship('Event', backref=db.backref('attendances', lazy=True))
    user = db.relationship('User', backref=db.backref('attendance_records', lazy=True))
    
    def __repr__(self):
        return f"<EventAttendance {self.user_id} at Event {self.event_id}>"
    
    @classmethod
    def create_for_registration(cls, event_id, user_id):
        """Create an attendance record with QR code when student registers"""
        # Check if already exists
        existing = cls.query.filter_by(event_id=event_id, user_id=user_id).first()
        if existing:
            return existing
        
        # Create unique token
        token = str(uuid.uuid4())
        
        # QR code contains: event_id|user_id|token
        qr_data = f"{event_id}|{user_id}|{token}"
        
        new_record = cls(
            event_id=event_id,
            user_id=user_id,
            qr_code=qr_data,
            qr_token=token
        )
        db.session.add(new_record)
        db.session.commit()
        return new_record
    
    @classmethod
    def get_by_token(cls, token):
        """Retrieve attendance record by QR token"""
        return cls.query.filter_by(qr_token=token).first()
