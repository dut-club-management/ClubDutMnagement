from app import db
from datetime import datetime

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=True)  # Make nullable for all_users announcements
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(140), nullable=False)
    content = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(16), nullable=False, default='normal')
    pinned = db.Column(db.Boolean, default=False)
    expiry_date = db.Column(db.DateTime, nullable=True)
    
    # Audience targeting
    send_to = db.Column(db.String(20), nullable=False, default='club_members')  # club_members, all_users, students_only
    
    # Attachments and links support
    attachment_url = db.Column(db.String(500), nullable=True)
    attachment_name = db.Column(db.String(255), nullable=True)
    resource_links = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships - use foreign_keys to avoid backref conflicts
    creator = db.relationship('User', foreign_keys=[created_by])
    reactions = db.relationship('AnnouncementReaction', backref='announcement', lazy=True,
                                cascade='all, delete-orphan')
    comments = db.relationship('AnnouncementComment', backref='announcement', lazy=True,
                              cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Announcement {self.title}>"
    
    def get_reactions_count(self):
        counts = {}
        for reaction in self.reactions:
            counts[reaction.reaction_type] = counts.get(reaction.reaction_type, 0) + 1
        return counts
    
    def get_user_reaction(self, user_id):
        for reaction in self.reactions:
            if reaction.user_id == user_id:
                return reaction.reaction_type
        return None


class AnnouncementReaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    announcement_id = db.Column(db.Integer, db.ForeignKey('announcement.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reaction_type = db.Column(db.String(32), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', foreign_keys=[user_id])
    
    __table_args__ = (db.UniqueConstraint('announcement_id', 'user_id', name='unique_announcement_reaction'),)
    
    def __repr__(self):
        return f"<AnnouncementReaction {self.reaction_type} by User {self.user_id}>"


class AnnouncementComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    announcement_id = db.Column(db.Integer, db.ForeignKey('announcement.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', foreign_keys=[user_id])
    
    def __repr__(self):
        return f"<AnnouncementComment by User {self.user_id}>"
