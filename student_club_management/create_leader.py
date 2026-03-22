#!/usr/bin/env python
"""Create a leader user"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db, bcrypt
from models.user import User

def create_leader():
    app = create_app()
    with app.app_context():
        leader = User.query.filter_by(email='leader@dut.ac.za').first()
        if leader:
            print("Leader exists!")
            return
        
        hashed_pw = bcrypt.generate_password_hash('leader@123').decode('utf-8')
        leader_user = User(
            student_number='LEADER001',
            email='leader@dut.ac.za',
            first_name='Club',
            last_name='Leader',
            password_hash=hashed_pw,
            role='leader',
            is_active=True,
            email_verified=True
        )
        db.session.add(leader_user)
        db.session.commit()
        print("✅ Leader created: leader@dut.ac.za / leader@123")

if __name__ == '__main__':
    create_leader()
