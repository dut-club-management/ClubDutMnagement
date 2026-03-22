"""
Scheduled tasks for automated reminders and analytics updates
Run this script periodically (e.g., daily via cron job)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from services.analytics_service import ReminderService, AnalyticsService
from datetime import datetime, date

def run_scheduled_tasks():
    """Run all scheduled tasks"""
    app = create_app()
    
    with app.app_context():
        print("🔄 Running scheduled tasks...")
        
        try:
            # Send event reminders
            print("📧 Sending event reminders...")
            ReminderService.send_event_reminders()
            print("✅ Event reminders sent successfully")
            
            # Send club reminders
            print("🏛️ Sending club reminders...")
            ReminderService.send_club_reminders()
            print("✅ Club reminders sent successfully")
            
            # Update analytics data
            print("📊 Updating analytics data...")
            AnalyticsService.calculate_membership_growth(30)
            AnalyticsService.calculate_event_attendance(30)
            AnalyticsService.calculate_participation_trends(30)
            print("✅ Analytics data updated successfully")
            
            print("🎉 All scheduled tasks completed successfully!")
            
        except Exception as e:
            print(f"❌ Error running scheduled tasks: {e}")
            db.session.rollback()
        finally:
            db.session.close()

if __name__ == "__main__":
    run_scheduled_tasks()
