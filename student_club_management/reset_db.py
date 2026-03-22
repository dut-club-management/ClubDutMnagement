#!/usr/bin/env python
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db

def reset_database():
    app = create_app()
    with app.app_context():
        # Drop all tables
        db.drop_all()
        # Create all tables
        db.create_all()
        print("✅ Database reset complete!")
        print("👤 Run `python create_admin.py` next")

if __name__ == '__main__':
    reset_database()
