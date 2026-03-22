#!/usr/bin/env python3
"""
WSGI entry point for the DUT Club Management System
Using the existing complete application
"""

import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app

# Create the application using the factory pattern
app = create_app('production')

# Configure for Render deployment
if __name__ == "__main__":
    app.run(debug=True)

# For Gunicorn/Render
application = app
