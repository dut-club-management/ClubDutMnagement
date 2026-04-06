#!/usr/bin/env python3
"""
Database connection test for Render deployment
"""
import os
from app import create_app
from app import db

def test_db_connection():
    """Test database connection"""
    app = create_app('production')
    
    with app.app_context():
        try:
            # Test basic database connection
            db.engine.execute("SELECT 1")
            print("✅ Database connection successful")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False

if __name__ == "__main__":
    test_db_connection()
