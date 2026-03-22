#!/usr/bin/env python3
import os, sys

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from app import create_app, db
from models.user import User
from flask_bcrypt import Bcrypt

app = create_app()
bcrypt = Bcrypt(app)

with app.app_context():
    from database import init_db
    init_db(app)
    
    # Create admin if not exists
    admin_email = 'admin@dut.ac.za'
    if not User.query.filter_by(email=admin_email).first():
        admin = User(
            student_number='ADMIN001',
            email=admin_email,
            first_name='Admin',
            last_name='User',
            password_hash=bcrypt.generate_password_hash('admin123').decode('utf-8'),
            role='admin',
            is_active=True,
            email_verified=True
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin created: admin@dut.ac.za / admin123")
    else:
        print("✅ Admin user already exists")

print("🚀 Server starting on http://127.0.0.1:5000")
print("📝 To seed the database with sample data, run: python seed_data.py")
print("=" * 60)
app.run(debug=True, host='127.0.0.1', port=5000)
