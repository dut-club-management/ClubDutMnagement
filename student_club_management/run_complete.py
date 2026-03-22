#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

print('Initializing app...')
from app import create_app
from database import init_db

app = create_app()
with app.app_context():
    init_db(app)
print('DB ready. Starting server...')
app.run(debug=True, host='0.0.0.0', port=5000)
