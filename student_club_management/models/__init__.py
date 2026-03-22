from app import db

# import model classes so they are registered
from models.user import User, PreRegisteredStudent
from models.club import Club
from models.event import Event
from models.membership import Membership
from models.announcement import Announcement, AnnouncementReaction, AnnouncementComment
from models.resource import Resource
from models.booking import Booking
from models.achievement import Achievement
from models.association import event_attendees, announcement_read_receipts, UserAchievement
from models.attendance import EventAttendance
from models.notification import Notification, AnnouncementNotification
from models.chat import ChatConversation, ChatMessage, ChatRequest
from models.analytics import Analytics, EventReminder, ClubReminder
