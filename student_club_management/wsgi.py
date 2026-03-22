#!/usr/bin/env python3
"""
Simple WSGI entry point for Render deployment
"""

import os
import sys

# Add the student_club_management directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'student_club_management'))

# Now import the app
from app import create_app

# Get configuration from environment
config_name = os.environ.get('FLASK_CONFIG', 'production')

# Create app
app = create_app(config_name)

if __name__ == "__main__":
    app.run()
