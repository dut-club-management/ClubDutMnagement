#!/usr/bin/env python
from app_fixed import create_app, db
from models import *
from database import init_db

app = create_app()
with app.app_context():
    db.drop_all()
    db.create_all()
    print('Database reset & initialized')

