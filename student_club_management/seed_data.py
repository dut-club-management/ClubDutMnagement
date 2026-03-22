#!/usr/bin/env python3
import os, sys
import random
from datetime import datetime, timedelta

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from app import create_app, db, bcrypt
from models.user import User
from models.club import Club
from models.event import Event
from models.membership import Membership
from models.announcement import Announcement

def seed_database():
    """Seed the database with sample data"""
    app = create_app()
    
    with app.app_context():
        print("🌱 Starting database seeding...")
        
        # Clear existing data
        print("🗑️  Clearing existing data...")
        db.session.query(Membership).delete()
        db.session.query(Announcement).delete()
        db.session.query(Event).delete()
        db.session.query(Club).delete()
        db.session.query(User).delete()
        db.session.commit()
        
        # Create users
        print("👥 Creating users...")
        users = []
        
        # Admin user
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
        users.append(admin)
        
        # Club leaders
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
            users.append(leader)
        
        # Regular students
        student_data = [
            ('STUD001', 'student1@dut.ac.za', 'Alice', 'Williams'),
            ('STUD002', 'student2@dut.ac.za', 'Bob', 'Jones'),
            ('STUD003', 'student3@dut.ac.za', 'Carol', 'Davis'),
            ('STUD004', 'student4@dut.ac.za', 'Daniel', 'Miller'),
            ('STUD005', 'student5@dut.ac.za', 'Emma', 'Garcia'),
            ('STUD006', 'student6@dut.ac.za', 'Frank', 'Martinez'),
            ('STUD007', 'student7@dut.ac.za', 'Grace', 'Rodriguez'),
            ('STUD008', 'student8@dut.ac.za', 'Henry', 'Anderson'),
            ('STUD009', 'student9@dut.ac.za', 'Isla', 'Taylor'),
            ('STUD010', 'student10@dut.ac.za', 'Jack', 'Thomas')
        ]
        
        for student_num, email, first, last in student_data:
            student = User(
                student_number=student_num,
                email=email,
                first_name=first,
                last_name=last,
                password_hash=bcrypt.generate_password_hash('student123').decode('utf-8'),
                role='student',
                is_active=True,
                email_verified=True
            )
            users.append(student)
        
        # Add all users
        for user in users:
            db.session.add(user)
        db.session.commit()
        print(f"✅ Created {len(users)} users")
        
        # Create clubs
        print("🏫 Creating clubs...")
        clubs_data = [
            ('Computer Science Club', 'Explore programming, algorithms, and technology', 'Academic', 'Every Friday 3PM'),
            ('Debate Society', 'Develop public speaking and critical thinking skills', 'Academic', 'Wednesday 4PM'),
            ('Drama Club', 'Express yourself through theater and performance', 'Arts', 'Tuesday 5PM'),
            ('Sports Club', 'Promote fitness and team sports', 'Sports', 'Daily 6AM'),
            ('Music Society', 'Share and develop musical talents', 'Arts', 'Thursday 6PM'),
            ('Photography Club', 'Capture moments and learn photography skills', 'Arts', 'Saturday 10AM'),
            ('Business Club', 'Learn entrepreneurship and business skills', 'Professional', 'Monday 5PM'),
            ('Environmental Club', 'Promote sustainability and environmental awareness', 'Social', 'Friday 2PM')
        ]
        
        clubs = []
        for i, (name, desc, category, schedule) in enumerate(clubs_data):
            club = Club(
                club_name=name,
                description=desc,
                category=category,
                meeting_schedule=schedule,
                created_by=users[i+1].id,  # Leaders start from index 1
                status='active',
                max_members=30
            )
            clubs.append(club)
            db.session.add(club)
        
        db.session.commit()
        print(f"✅ Created {len(clubs)} clubs")
        
        # Create memberships (leaders as members of their own clubs)
        print("🤝 Creating memberships...")
        for i, club in enumerate(clubs):
            # Add leader as member
            membership = Membership(
                user_id=users[i+1].id,  # Leader
                club_id=club.id,
                role='leader',
                status='active'
            )
            db.session.add(membership)
            
            # Add some random students to each club
            for j in range(3, 8):  # Add 5 students per club
                if i + j < len(users):
                    student_membership = Membership(
                        user_id=users[i + j].id,
                        club_id=club.id,
                        role='member',
                        status='active'
                    )
                    db.session.add(student_membership)
        
        db.session.commit()
        print("✅ Created memberships")
        
        # Create events
        print("📅 Creating events...")
        events_data = [
            ('Programming Workshop', 'Learn Python basics', datetime.now() + timedelta(days=7), 'Lab 101'),
            ('Debate Competition', 'Annual debate tournament', datetime.now() + timedelta(days=14), 'Auditorium'),
            ('Drama Performance', 'Spring play showcase', datetime.now() + timedelta(days=21), 'Theater'),
            ('Basketball Tournament', 'Inter-club basketball championship', datetime.now() + timedelta(days=10), 'Sports Hall'),
            ('Music Concert', 'End of semester concert', datetime.now() + timedelta(days=28), 'Concert Hall'),
            ('Photo Exhibition', 'Student photography showcase', datetime.now() + timedelta(days=35), 'Gallery')
        ]
        
        events = []
        for i, (name, desc, event_date, location) in enumerate(events_data):
            event = Event(
                event_name=name,
                description=desc,
                event_date=event_date,
                location=location,
                created_by=users[i+1].id,  # Club leaders
                status='approved'
            )
            events.append(event)
            db.session.add(event)
        
        db.session.commit()
        print(f"✅ Created {len(events)} events")
        
        # Create announcements
        print("📢 Creating announcements...")
        announcements_data = [
            ('Welcome to Computer Science Club!', 'Join us for exciting coding sessions and workshops.'),
            ('Debate Society Meeting', 'Weekly debate practice session this Wednesday.'),
            ('Drama Club Auditions', 'Auditions for the spring play are now open!'),
            ('Sports Club Registration', 'Sign up for the basketball tournament.'),
            ('Music Society Jam Session', 'Come jam with us this Thursday evening.'),
        ]
        
        for i, (title, content) in enumerate(announcements_data):
            announcement = Announcement(
                title=title,
                content=content,
                club_id=clubs[i].id,
                created_by=users[i+1].id,
                priority='normal'
            )
            db.session.add(announcement)
        
        db.session.commit()
        print(f"✅ Created {len(announcements_data)} announcements")
        
        print("\n🎉 Database seeding completed successfully!")
        print("\n📋 Login Credentials:")
        print("=" * 50)
        print("🔑 Admin: admin@dut.ac.za / admin123")
        print("👑 Leaders: leader[1-5]@dut.ac.za / leader123")
        print("👥 Students: student[1-10]@dut.ac.za / student123")
        print("=" * 50)

if __name__ == '__main__':
    seed_database()
