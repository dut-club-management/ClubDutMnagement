#!/usr/bin/env python3
"""
Simple WSGI entry point for Render deployment - Database connection tested at runtime
"""

import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, jsonify
import os

app = Flask(__name__)

# Basic configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

# Database configuration - don't initialize SQLAlchemy at import time
database_url = os.environ.get('DATABASE_URL')

# Test database connection at runtime (not import time)
def test_database_connection():
    if not database_url:
        return False, "DATABASE_URL not set"
    
    try:
        # Use pg8000 instead of psycopg2 for Python 3.14 compatibility
        import pg8000
        
        # Parse database URL and test connection
        import urllib.parse
        
        parsed = urllib.parse.urlparse(database_url)
        
        # Connect to PostgreSQL
        conn = pg8000.connect(
            user=parsed.username,
            password=parsed.password,
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path.lstrip('/')
        )
        
        # Test simple query
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        
        return True, "Connected to PostgreSQL database"
    except Exception as e:
        return False, f"Database error: {str(e)}"

# Test database connection
@app.route('/')
def index():
    db_connected, db_status = test_database_connection()
    
    return f"""
    <h1>🎉 Club Management System</h1>
    <h2>📊 Database Status: {db_status}</h2>
    <h3>🔧 Environment Variables:</h3>
    <ul>
        <li>DATABASE_URL: {'✅ Set' if database_url else '❌ Missing'}</li>
        <li>SECRET_KEY: {'✅ Set' if os.environ.get('SECRET_KEY') else '❌ Missing'}</li>
        <li>FLASK_ENV: {os.environ.get('FLASK_ENV', 'Not set')}</li>
    </ul>
    <h3>🚀 Next Steps:</h3>
    <p>{'Database connected! Ready for club management features.' if db_connected else 'Add DATABASE_URL environment variable in Render dashboard to connect to PostgreSQL!'}</p>
    """

@app.route('/health')
def health():
    db_connected, db_status = test_database_connection()
    
    if db_connected:
        return jsonify({
            'status': 'healthy', 
            'message': 'Club Management System is running',
            'database': 'connected'
        })
    else:
        return jsonify({
            'status': 'unhealthy', 
            'message': db_status,
            'database': 'not connected'
        }), 500

@app.route('/api/test')
def api_test():
    """Test API endpoint"""
    return jsonify({
        'message': 'API is working',
        'database_url': 'Set' if database_url else 'Not set',
        'flask_env': os.environ.get('FLASK_ENV', 'Not set')
    })

if __name__ == "__main__":
    app.run()

# For Gunicorn
application = app
