from datetime import datetime, timedelta, date
from sqlalchemy import func
from models.analytics import Analytics, EventReminder, ClubReminder
from models.event import Event
from models.attendance import EventAttendance
from models.club import Club
from models.membership import Membership
from models.user import User
from models.notification import Notification
from app import db

class AnalyticsService:
    
    @staticmethod
    def calculate_membership_growth(days=30):
        """Calculate membership growth over specified period"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Get daily membership counts
        membership_data = db.session.query(
            func.date(Membership.joined_date).label('date'),
            func.count(Membership.id).label('count')
        ).filter(
            func.date(Membership.joined_date) >= start_date,
            func.date(Membership.joined_date) <= end_date
        ).group_by(func.date(Membership.joined_date)).all()
        
        # Convert Row objects to dictionaries with proper date handling
        membership_data_dict = []
        for record in membership_data:
            # Ensure record.date is a date object, not string
            record_date = record.date if hasattr(record, 'date') else record[0]
            membership_data_dict.append({
                'date': record_date,
                'count': record.count if hasattr(record, 'count') else record[1]
            })
        
        return AnalyticsService._store_analytics('membership_growth', membership_data_dict, days)
    
    @staticmethod
    def calculate_event_attendance(days=30):
        """Calculate event attendance trends"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Get daily attendance counts
        attendance_data = db.session.query(
            func.date(EventAttendance.checked_in_at).label('date'),
            func.count(EventAttendance.id).label('count')
        ).filter(
            EventAttendance.is_attended == True,
            func.date(EventAttendance.checked_in_at) >= start_date,
            func.date(EventAttendance.checked_in_at) <= end_date
        ).group_by(func.date(EventAttendance.checked_in_at)).all()
        
        # Convert Row objects to dictionaries with proper date handling
        attendance_data_dict = []
        for record in attendance_data:
            # Ensure record.date is a date object, not string
            record_date = record.date if hasattr(record, 'date') else record[0]
            attendance_data_dict.append({
                'date': record_date,
                'count': record.count if hasattr(record, 'count') else record[1]
            })
        
        return AnalyticsService._store_analytics('event_attendance', attendance_data_dict, days)
    
    @staticmethod
    def calculate_participation_trends(days=30):
        """Calculate overall participation trends"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Get participation data (events + club activities)
        event_participation = db.session.query(
            func.date(EventAttendance.checked_in_at).label('date'),
            func.count(EventAttendance.id).label('count')
        ).filter(
            EventAttendance.is_attended == True,
            func.date(EventAttendance.checked_in_at) >= start_date,
            func.date(EventAttendance.checked_in_at) <= end_date
        ).group_by(func.date(EventAttendance.checked_in_at))
        
        membership_activity = db.session.query(
            func.date(Membership.joined_date).label('date'),
            func.count(Membership.id).label('count')
        ).filter(
            func.date(Membership.joined_date) >= start_date,
            func.date(Membership.joined_date) <= end_date
        ).group_by(func.date(Membership.joined_date))
        
        # Combine data
        participation_data = {}
        
        # Add event participation
        for record in event_participation:
            date_str = str(record.date)
            participation_data[date_str] = participation_data.get(date_str, 0) + record.count
        
        # Add membership activity
        for record in membership_activity:
            date_str = str(record.date)
            participation_data[date_str] = participation_data.get(date_str, 0) + record.count
        
        # Convert back to list format
        combined_data = []
        for k, v in participation_data.items():
            combined_data.append({'date': datetime.strptime(k, '%Y-%m-%d').date(), 'count': v})
        
        return AnalyticsService._store_analytics('participation', combined_data, days)
    
    @staticmethod
    def _store_analytics(metric_type, data, days):
        """Store analytics data in database"""
        for record in data:
            # Handle both string and date objects
            record_date = record['date']
            if isinstance(record_date, str):
                record_date = datetime.strptime(record_date, '%Y-%m-%d').date()
            
            existing = Analytics.query.filter_by(
                metric_type=metric_type,
                metric_date=record_date
            ).first()
            
            if existing:
                existing.metric_value = record['count']
                existing.extra_data = record.get('extra_data', {})
            else:
                analytics = Analytics(
                    metric_type=metric_type,
                    metric_date=record_date,
                    metric_value=record['count'],
                    extra_data=record.get('extra_data', {})
                )
                db.session.add(analytics)
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error storing analytics: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        return data
    
    @staticmethod
    def get_analytics_data(metric_type, days=30):
        """Get analytics data for a specific metric"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        return Analytics.query.filter(
            Analytics.metric_type == metric_type,
            Analytics.metric_date >= start_date,
            Analytics.metric_date <= end_date
        ).order_by(Analytics.metric_date).all()
    
    @staticmethod
    def get_dashboard_summary():
        """Get summary data for admin dashboard"""
        today = date.today()
        thirty_days_ago = today - timedelta(days=30)
        
        # Basic counts
        total_users = User.query.count()
        total_clubs = Club.query.count()
        total_events = Event.query.count()
        total_memberships = Membership.query.count()
        
        # Recent activity (last 30 days)
        new_users = User.query.filter(User.created_at >= thirty_days_ago).count()
        new_clubs = Club.query.filter(Club.created_at >= thirty_days_ago).count()
        new_events = Event.query.filter(Event.created_at >= thirty_days_ago).count()
        new_memberships = Membership.query.filter(Membership.joined_date >= thirty_days_ago).count()
        
        # Attendance stats
        recent_attendance = EventAttendance.query.filter(
            EventAttendance.checked_in_at >= thirty_days_ago,
            EventAttendance.is_attended == True
        ).count()
        
        # Club status breakdown
        active_clubs = Club.query.filter_by(status='active').count()
        pending_clubs = Club.query.filter_by(status='pending').count()
        
        return {
            'total_counts': {
                'users': total_users,
                'clubs': total_clubs,
                'events': total_events,
                'memberships': total_memberships
            },
            'recent_activity': {
                'new_users': new_users,
                'new_clubs': new_clubs,
                'new_events': new_events,
                'new_memberships': new_memberships,
                'recent_attendance': recent_attendance
            },
            'club_status': {
                'active': active_clubs,
                'pending': pending_clubs
            }
        }

class ReminderService:
    
    @staticmethod
    def send_event_reminders():
        """Send automatic event reminders"""
        from datetime import datetime, timedelta
        from models.notification import Notification
        
        now = datetime.utcnow()
        
        # Get events happening in 1 day, 1 hour, and 1 week
        one_day_later = now + timedelta(days=1)
        one_hour_later = now + timedelta(hours=1)
        one_week_later = now + timedelta(days=7)
        
        # 1 day reminders
        events_1day = Event.query.filter(
            Event.event_date >= now,
            Event.event_date <= one_day_later,
            Event.status == 'approved'
        ).all()
        
        for event in events_1day:
            attendees = EventAttendance.query.filter_by(event_id=event.id).all()
            for attendance in attendees:
                # Check if reminder already sent
                existing = EventReminder.query.filter_by(
                    event_id=event.id,
                    user_id=attendance.user_id,
                    reminder_type='1_day'
                ).first()
                
                if not existing:
                    # Send notification
                    Notification.create_event_reminder(
                        attendance.user_id,
                        event,
                        '1_day',
                        f"Reminder: {event.event_name} is tomorrow!"
                    )
                    
                    # Track reminder
                    reminder = EventReminder(
                        event_id=event.id,
                        user_id=attendance.user_id,
                        reminder_type='1_day'
                    )
                    db.session.add(reminder)
        
        # 1 hour reminders
        events_1hour = Event.query.filter(
            Event.event_date >= now,
            Event.event_date <= one_hour_later,
            Event.status == 'approved'
        ).all()
        
        for event in events_1hour:
            attendees = EventAttendance.query.filter_by(event_id=event.id).all()
            for attendance in attendees:
                # Check if reminder already sent
                existing = EventReminder.query.filter_by(
                    event_id=event.id,
                    user_id=attendance.user_id,
                    reminder_type='1_hour'
                ).first()
                
                if not existing:
                    # Send notification
                    Notification.create_event_reminder(
                        attendance.user_id,
                        event,
                        '1_hour',
                        f"URGENT: {event.event_name} starts in 1 hour!"
                    )
                    
                    # Track reminder
                    reminder = EventReminder(
                        event_id=event.id,
                        user_id=attendance.user_id,
                        reminder_type='1_hour'
                    )
                    db.session.add(reminder)
        
        db.session.commit()
    
    @staticmethod
    def send_club_reminders():
        """Send club deadline reminders"""
        from datetime import datetime, timedelta
        from models.notification import Notification
        
        now = datetime.utcnow()
        
        # Get clubs with upcoming deadlines or meetings
        clubs = Club.query.filter_by(status='active').all()
        
        for club in clubs:
            # Check for meeting schedule and send reminders
            if club.meeting_schedule:
                # Check if reminder already sent
                existing = ClubReminder.query.filter_by(
                    club_id=club.id,
                    user_id=club.created_by,
                    reminder_type='meeting_reminder'
                ).first()
                
                if not existing:
                    # This is a simplified version - you could enhance with proper date parsing
                    Notification.create_club_reminder(
                        club.created_by,
                        club,
                        'meeting_reminder',
                        f"Reminder: {club.club_name} has a meeting scheduled"
                    )
                    
                    # Track reminder
                    reminder = ClubReminder(
                        club_id=club.id,
                        user_id=club.created_by,
                        reminder_type='meeting_reminder'
                    )
                    db.session.add(reminder)
        
        db.session.commit()
