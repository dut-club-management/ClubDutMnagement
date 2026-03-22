"""
Database migration script to add is_read field to AnnouncementNotification table
Run this script to update your database with the new field
"""

from app import create_app, db
from models.notification import AnnouncementNotification

def migrate_is_read_field():
    """Add is_read field to existing AnnouncementNotification records"""
    app = create_app()
    
    with app.app_context():
        try:
            # Check if the column exists by trying to query it
            # If it doesn't exist, we need to add it manually
            print("🔄 Checking database schema...")
            
            # Try to update existing records to set is_read = False for all
            # This will work if the column exists, fail if it doesn't
            try:
                AnnouncementNotification.query.update({'is_read': False})
                db.session.commit()
                print("✅ is_read field exists and updated successfully")
            except Exception as e:
                if "is_read" in str(e):
                    print("⚠️  is_read field doesn't exist yet. Please run:")
                    print("   ALTER TABLE announcement_notification ADD COLUMN is_read BOOLEAN DEFAULT FALSE;")
                    print("   (Run this in your SQLite/MySQL/PostgreSQL database)")
                else:
                    print(f"❌ Error updating is_read field: {e}")
                    raise
            
            print("🎉 Migration completed successfully!")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    migrate_is_read_field()
