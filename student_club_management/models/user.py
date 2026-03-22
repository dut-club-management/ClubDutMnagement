from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime

# association tables imported in __init__ to avoid circular imports

class PreRegisteredStudent(db.Model):
    """Pre-registered students that admin adds before student can register"""
    id = db.Column(db.Integer, primary_key=True)
    student_number = db.Column(db.String(64), unique=True, nullable=False)
    id_number = db.Column(db.String(64), nullable=False)  # National ID or other ID
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), nullable=True)  # Optional email
    is_registered = db.Column(db.Boolean, default=False)  # True after student registers
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<PreRegisteredStudent {self.student_number}>"


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_number = db.Column(db.String(64), unique=True, nullable=False)
    # Encrypted sensitive fields (for data at rest security)
    encrypted_student_number = db.Column(db.String(256), nullable=True)
    encrypted_id_number = db.Column(db.String(256), nullable=True)
    encrypted_email = db.Column(db.String(256), nullable=True)
    # Regular fields (email used for login, student_number for display)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    profile_image = db.Column(db.String(255), nullable=False, default='default-avatar.png')
    bio = db.Column(db.Text, nullable=True)
    interests = db.Column(db.Text, nullable=True)  # store as JSON or comma-separated
    role = db.Column(db.String(32), nullable=False, default='student')
    is_active = db.Column(db.Boolean, default=True)
    email_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(128), nullable=True)
    reset_token = db.Column(db.String(128), nullable=True, unique=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # relationships
    memberships = db.relationship('Membership', backref='user', lazy=True)
    events_created = db.relationship('Event', backref='creator', lazy=True, foreign_keys='Event.created_by')
    resources_booked = db.relationship('Booking', backref='booker', lazy=True, foreign_keys='Booking.booked_by')

    # many-to-many intermediates
    attending_events = db.relationship('Event', secondary='event_attendees', backref='attendees', lazy='dynamic')
    achievements = db.relationship('UserAchievement', backref='user', lazy=True)

    def __repr__(self):
        return f"<User {self.student_number}>"
    
    def encrypt_sensitive_data(self):
        """Encrypt sensitive fields for data at rest security"""
        from utils.encryption import encrypt
        if self.student_number:
            self.encrypted_student_number = encrypt(self.student_number)
        if self.email:
            self.encrypted_email = encrypt(self.email)
    
    def decrypt_sensitive_data(self):
        """Decrypt sensitive fields for display"""
        from utils.encryption import decrypt
        if self.encrypted_student_number:
            self.student_number = decrypt(self.encrypted_student_number)
        if self.encrypted_email:
            self.email = decrypt(self.encrypted_email)
