#!/usr/bin/env python3
import os, sys
import random
from datetime import datetime, timedelta

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from app import create_app, db, bcrypt
from models.user import User, PreRegisteredStudent
from models.club import Club
from models.event import Event
from models.membership import Membership
from models.announcement import Announcement
from models.attendance import EventAttendance

def create_sample_data():
    """Create comprehensive sample data for testing all functionality"""
    app = create_app()
    
    with app.app_context():
        print("🌱 Creating comprehensive sample data...")
        
        # Create sample pre-registered students
        print("👥 Creating pre-registered students...")
        students_data = [
            ('STUD001', '9001010001001', 'Alice', 'Williams', 'alice@student.dut.ac.za'),
            ('STUD002', '9001010001002', 'Bob', 'Jones', 'bob@student.dut.ac.za'),
            ('STUD003', '9001010001003', 'Carol', 'Davis', 'carol@student.dut.ac.za'),
            ('STUD004', '9001010001004', 'Daniel', 'Miller', 'daniel@student.dut.ac.za'),
            ('STUD005', '9001010001005', 'Emma', 'Garcia', 'emma@student.dut.ac.za'),
            ('STUD006', '9001010001006', 'Frank', 'Martinez', 'frank@student.dut.ac.za'),
            ('STUD007', '9001010001007', 'Grace', 'Rodriguez', 'grace@student.dut.ac.za'),
            ('STUD008', '9001010001008', 'Henry', 'Anderson', 'henry@student.dut.ac.za'),
            ('STUD009', '9001010001009', 'Isla', 'Taylor', 'isla@student.dut.ac.za'),
            ('STUD010', '9001010001010', 'Jack', 'Thomas', 'jack@student.dut.ac.za'),
        ]
        
        for student_num, id_num, first, last, email in students_data:
            pre_student = PreRegisteredStudent(
                student_number=student_num,
                id_number=id_num,
                first_name=first,
                last_name=last,
                email=email
            )
            db.session.add(pre_student)
        
        db.session.commit()
        print(f"✅ Created {len(students_data)} pre-registered students")
        
        # Create clubs (leaders already exist)
        print("🏫 Creating clubs...")
        clubs_data = [
            ('Computer Science Club', 'Explore programming, algorithms, and technology', 'Academic', 'Every Friday 3PM', 1),
            ('Debate Society', 'Develop public speaking and critical thinking skills', 'Academic', 'Wednesday 4PM', 2),
            ('Drama Club', 'Express yourself through theater and performance', 'Arts', 'Tuesday 5PM', 3),
            ('Sports Club', 'Promote fitness and team sports', 'Sports', 'Daily 6AM', 4),
            ('Music Society', 'Share and develop musical talents', 'Arts', 'Thursday 6PM', 5),
        ]
        
        clubs = []
        for name, desc, category, schedule, leader_id in clubs_data:
            club = Club(
                club_name=name,
                description=desc,
                category=category,
                meeting_schedule=schedule,
                created_by=leader_id,
                status='active',
                max_members=30
            )
            clubs.append(club)
            db.session.add(club)
        
        db.session.commit()
        print(f"✅ Created {len(clubs)} clubs")
        
        # Create events
        print("📅 Creating events...")
        events_data = [
            ('Programming Workshop', 'Learn Python basics', datetime.now() + timedelta(days=7), 'Lab 101', 1),
            ('Debate Competition', 'Annual debate tournament', datetime.now() + timedelta(days=14), 'Auditorium', 2),
            ('Drama Performance', 'Spring play showcase', datetime.now() + timedelta(days=21), 'Theater', 3),
            ('Basketball Tournament', 'Inter-club basketball championship', datetime.now() + timedelta(days=10), 'Sports Hall', 4),
            ('Music Concert', 'End of semester concert', datetime.now() + timedelta(days=28), 'Concert Hall', 5),
        ]
        
        events = []
        for name, desc, event_date, location, leader_id in events_data:
            event = Event(
                event_name=name,
                description=desc,
                event_date=event_date,
                location=location,
                created_by=leader_id,
                status='approved'
            )
            events.append(event)
            db.session.add(event)
        
        db.session.commit()
        print(f"✅ Created {len(events)} events")
        
        # Create some sample announcements
        print("📢 Creating announcements...")
        announcements_data = [
            ('Welcome to Computer Science Club!', 'Join us for exciting coding sessions and workshops.', 1, 1),
            ('Debate Society Meeting', 'Weekly debate practice session this Wednesday.', 2, 2),
            ('Drama Club Auditions', 'Auditions for the spring play are now open!', 3, 3),
            ('Sports Club Registration', 'Sign up for the basketball tournament.', 4, 4),
            ('Music Society Jam Session', 'Come jam with us this Thursday evening.', 5, 5),
        ]
        
        for title, content, club_id, leader_id in announcements_data:
            announcement = Announcement(
                title=title,
                content=content,
                club_id=club_id,
                created_by=leader_id,
                priority='normal'
            )
            db.session.add(announcement)
        
        db.session.commit()
        print(f"✅ Created {len(announcements_data)} announcements")
        
        print("\n🎉 Sample data creation completed!")
        print("\n📋 What you can now test:")
        print("=" * 60)
        print("🔑 Admin: admin@dut.ac.za / admin123")
        print("👑 Leaders: leader[1-5]@dut.ac.za / leader123")
        print("🎓 Students: Register with student numbers STUD001-STUD010")
        print("=" * 60)
        print("\n🧪 Test these features:")
        print("✅ Student creation in admin panel")
        print("✅ Student registration (use STUD001-STUD010)")
        print("✅ Club management and membership")
        print("✅ Event creation and QR code generation")
        print("✅ Announcements system")
        print("✅ Chat functionality")
        print("✅ Notifications and alerts")
        print("✅ QR code check-in system")

if __name__ == '__main__':
    create_sample_data()
