import sqlite3
import os

def add_is_read_field():
    db_path = os.path.join(os.path.dirname(__file__), 'club_management.db')
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(announcement_notification)")
        columns = [row[1] for row in cursor.fetchall()]
        column_names = [col[1] for col in columns]
        
        print(f"Current columns: {column_names}")
        
        if 'is_read' not in column_names:
            print("🔄 Adding is_read field to announcement_notification table...")
            cursor.execute("ALTER TABLE announcement_notification ADD COLUMN is_read BOOLEAN DEFAULT FALSE")
            conn.commit()
            print("✅ is_read field added successfully!")
        else:
            print("✅ is_read field already exists")
        
        conn.close()
        print("🎉 Database migration completed!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    add_is_read_field()
