from app import create_app, db
from models.user import User
from models.club import Club
from models.event import Event
from models.membership import Membership
from models.notification import Notification
from models.analytics import Analytics
import os

def comprehensive_health_check():
    """Check all aspects of the application"""
    app = create_app()
    
    with app.app_context():
        issues = []
        
        print("🔍 COMPREHENSIVE HEALTH CHECK")
        print("=" * 50)
        
        # 1. Database connectivity
        try:
            from sqlalchemy import text
            db.session.execute(text("SELECT 1"))
            print("✅ Database connection: OK")
        except Exception as e:
            issues.append(f"❌ Database connection failed: {e}")
            print(f"❌ Database connection: {e}")
        
        # 2. Model integrity
        try:
            user_count = User.query.count()
            club_count = Club.query.count()
            event_count = Event.query.count()
            membership_count = Membership.query.count()
            notification_count = Notification.query.count()
            analytics_count = Analytics.query.count()
            
            print(f"✅ Model counts: Users={user_count}, Clubs={club_count}, Events={event_count}")
            print(f"✅ Model counts: Memberships={membership_count}, Notifications={notification_count}, Analytics={analytics_count}")
            
            if user_count == 0:
                issues.append("❌ No users found in database")
            if club_count == 0:
                issues.append("❌ No clubs found in database")
                
        except Exception as e:
            issues.append(f"❌ Model integrity check failed: {e}")
            print(f"❌ Model integrity check: {e}")
        
        # 3. Analytics system
        try:
            analytics_data = Analytics.query.limit(10).all()
            print(f"✅ Analytics system: {len(analytics_data)} records found")
            
            # Check for required analytics fields
            required_fields = ['metric_type', 'metric_date', 'metric_value']
            for record in analytics_data[:3]:
                missing_fields = []
                for field in required_fields:
                    if not hasattr(record, field):
                        missing_fields.append(field)
                if missing_fields:
                    issues.append(f"❌ Analytics record missing fields: {missing_fields}")
                    
        except Exception as e:
            issues.append(f"❌ Analytics system check failed: {e}")
            print(f"❌ Analytics system check: {e}")
        
        # 4. File system checks
        try:
            # Check essential files exist
            essential_files = [
                'app.py',
                'requirements.txt',
                'launch_app.py',
                'models/__init__.py',
                'templates/dashboard/admin.html',
                'templates/analytics/dashboard.html'
            ]
            
            for file in essential_files:
                if os.path.exists(file):
                    print(f"✅ File exists: {file}")
                else:
                    issues.append(f"❌ Missing file: {file}")
                    
        except Exception as e:
            issues.append(f"❌ File system check failed: {e}")
        
        # 5. Import checks
        try:
            from services.analytics_service import AnalyticsService
            from services.analytics_service import ReminderService
            from routes.analytics import analytics_bp
            print("✅ All imports successful")
            
        except ImportError as e:
            issues.append(f"❌ Import error: {e}")
            print(f"❌ Import error: {e}")
        
        print("=" * 50)
        print(f"📊 HEALTH CHECK SUMMARY")
        print(f"Total issues found: {len(issues)}")
        
        if issues:
            print("\n🚨 ISSUES FOUND:")
            for i, issue in enumerate(issues, 1):
                print(f"{i}. {issue}")
        else:
            print("\n🎉 ALL SYSTEMS HEALTHY!")
        
        return len(issues) == 0

if __name__ == "__main__":
    is_healthy = comprehensive_health_check()
    exit(0 if is_healthy else 1)
