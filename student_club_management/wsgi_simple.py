#!/usr/bin/env python3
"""
Simple WSGI entry point for Render deployment - No complex imports
"""

import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Simple Flask app for testing
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return "Club Management System - Working!"

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'message': 'Club Management System is running'})

if __name__ == "__main__":
    app.run()

# For Gunicorn
application = app
