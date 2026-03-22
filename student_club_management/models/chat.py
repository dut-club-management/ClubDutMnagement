from app import db
from datetime import datetime

class ChatConversation(db.Model):
    """Chat conversation between users (student and leader)"""
    id = db.Column(db.Integer, primary_key=True)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=True)  # Optional club context
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=True)  # Optional event context
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    participant_one = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    participant_two = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(255), nullable=True)  # Subject of the conversation
    status = db.Column(db.String(32), nullable=False, default='open')  # open, closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by])
    user_one = db.relationship('User', foreign_keys=[participant_one])
    user_two = db.relationship('User', foreign_keys=[participant_two])
    club = db.relationship('Club', backref='conversations')
    event = db.relationship('Event', backref='conversations')
    messages = db.relationship('ChatMessage', backref='conversation', lazy=True, 
                               order_by='ChatMessage.created_at.desc()')
    
    def __repr__(self):
        return f"<ChatConversation {self.id} between {self.participant_one} and {self.participant_two}>"
    
    def get_other_participant(self, user_id):
        """Get the other participant in the conversation"""
        if self.participant_one == user_id:
            return self.user_two
        return self.user_one
    
    def get_unread_count(self, user_id):
        """Get count of unread messages for a user"""
        return ChatMessage.query.filter_by(
            conversation_id=self.id, 
            recipient_id=user_id,
            is_read=False
        ).count()


class ChatMessage(db.Model):
    """Individual messages in a chat conversation"""
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('chat_conversation.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id])
    recipient = db.relationship('User', foreign_keys=[recipient_id])
    
    def __repr__(self):
        return f"<ChatMessage {self.id} from {self.sender_id}>"


class ChatRequest(db.Model):
    """Requests from students (leave club, move club, etc.) that need leader approval"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)
    request_type = db.Column(db.String(64), nullable=False)  # leave, move
    target_club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=True)  # For move requests
    message = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(32), nullable=False, default='pending')  # pending, approved, denied
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id])
    club = db.relationship('Club', foreign_keys=[club_id])
    target_club = db.relationship('Club', foreign_keys=[target_club_id])
    reviewer = db.relationship('User', foreign_keys=[reviewed_by])
    
    def __repr__(self):
        return f"<ChatRequest {self.id} from User {self.user_id} type={self.request_type}>"

