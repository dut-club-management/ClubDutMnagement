#!/usr/bin/env python3
import os, sys

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from app import create_app, db, bcrypt
from models.user import User

def reset_database():
    """Clear database and keep only admin user"""
    app = create_app()
    
    with app.app_context():
        print("🗑️  Clearing database completely...")
        
        # Drop all tables
        db.drop_all()
        print("✅ All tables dropped")
        
        # Create all tables
        db.create_all()
        print("✅ All tables created")
        
        # Create admin user
        admin = User(
            student_number='ADMIN001',
            email='admin@dut.ac.za',
            first_name='Admin',
            last_name='User',
            password_hash=bcrypt.generate_password_hash('admin123').decode('utf-8'),
            role='admin',
            is_active=True,
            email_verified=True
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin user created")
        
        # Create leader users
        leaders_data = [
            ('LEADER001', 'leader1@dut.ac.za', 'John', 'Smith'),
            ('LEADER002', 'leader2@dut.ac.za', 'Sarah', 'Johnson'),
            ('LEADER003', 'leader3@dut.ac.za', 'Mike', 'Wilson'),
            ('LEADER004', 'leader4@dut.ac.za', 'Emily', 'Brown'),
            ('LEADER005', 'leader5@dut.ac.za', 'David', 'Lee')
        ]
        
        for student_num, email, first, last in leaders_data:
            leader = User(
                student_number=student_num,
                email=email,
                first_name=first,
                last_name=last,
                password_hash=bcrypt.generate_password_hash('leader123').decode('utf-8'),
                role='leader',
                is_active=True,
                email_verified=True
            )
            db.session.add(leader)
        
        db.session.commit()
        print("✅ 5 leader users created")
        
        print("\n🎉 Database reset completed!")
        print("\n📋 Login Credentials:")
        print("=" * 50)
        print("🔑 Admin: admin@dut.ac.za / admin123")
        print("👑 Leaders:")
        for i in range(1, 6):
            print(f"   leader{i}@dut.ac.za / leader123")
        print("=" * 50)
        print("\n🚀 You can now login and create students/users!")

if __name__ == '__main__':
    reset_database()
