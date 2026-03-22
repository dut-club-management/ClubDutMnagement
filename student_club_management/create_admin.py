#!/usr/bin/env python
"""Create an admin user for the DUT Club Management System"""

import sys
import os
sys.path.insert(0, '.')

from app import create_app, db, bcrypt
from models.user import User

def create_admin():
    """Create an admin user with default credentials"""
    app = create_app()
    with app.app_context():
        # Check if admin already exists
        admin = User.query.filter_by(email='admin@dut.ac.za').first()
        if admin:
            print("❌ Admin user already exists!")
            print(f"Email: admin@dut.ac.za")
            print(f"Password: admin@123")
            return
        
        # Hash password
        hashed_pw = bcrypt.generate_password_hash('admin@123').decode('utf-8')
        
        # Create new admin
        admin_user = User(
            student_number='ADMIN001',
            email='admin@dut.ac.za',
            first_name='Administrator',
            last_name='System',
            password_hash=hashed_pw,
            role='admin',
            is_active=True,
            email_verified=True
        )
        
        db.session.add(admin_user)
        db.session.commit()
        
        print("✅ Admin user created successfully!")
        print("\n" + "="*50)
        print("ADMIN CREDENTIALS")
        print("="*50)
        print(f"Email: admin@dut.ac.za")
        print(f"Student Number: ADMIN001")
        print(f"Password: admin@123")
        print("="*50)
        print("\n⚠️  SECURITY WARNING:")
        print("Change this password immediately after first login!")
        print("="*50)

if __name__ == '__main__':
    create_admin()
