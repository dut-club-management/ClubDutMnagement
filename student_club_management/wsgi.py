#!/usr/bin/env python3
"""
WSGI entry point for production deployment
"""

from app import create_app
import os

# Get configuration from environment
config_name = os.environ.get('FLASK_CONFIG', 'production')

# Create app
app = create_app(config_name)

if __name__ == "__main__":
    app.run()
