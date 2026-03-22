from app import create_app, db
from services.analytics_service import AnalyticsService

app = create_app()
with app.app_context():
    try:
        print("Testing participation trends step by step...")
        
        # Test event participation
        from models.event import Event
        from models.attendance import EventAttendance
        from datetime import date, timedelta
        
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        event_participation = db.session.query(
            EventAttendance.checked_in_at,
            EventAttendance.id
        ).filter(
            EventAttendance.is_attended == True,
            EventAttendance.checked_in_at >= start_date,
            EventAttendance.checked_in_at <= end_date
        ).group_by(EventAttendance.checked_in_at).all()
        
        print(f"Event participation records: {len(event_participation)}")
        for i, record in enumerate(event_participation):
            print(f"  {i}: date={record[0]}, count={record[1]}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
