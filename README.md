# 🏫 DUT Club Management System - Railway Ready

[![Railway](https://railway.app/button.svg)](https://railway.app/new)

## 🚀 Live Demo
Connect to Railway for instant deploy.

## ✨ Features
- 👥 Student Registration/Login
- 🏢 Club Management
- 📅 Events & Calendar (QR Attendance)
- 💬 Real-time Chat
- 🔔 Notifications
- 📢 Announcements
- 👑 Admin Dashboard
- 🔐 Password Reset
- 🎨 Responsive UI

## 🛠 Tech Stack
Backend: Flask 3.0 + SQLAlchemy + APScheduler
Frontend: Jinja2 + Bootstrap5
Database: SQLite (test) / PostgreSQL (prod)
Deployment: Railway (Procfile + root requirements.txt)

## 📋 Local Setup
```powershell
# Root
pip install -r requirements.txt
python app.py  # PORT-aware

# Or inner dev
cd student_club_management
python -m venv venv
venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
python run.py
```

## 🌐 Railway Deployment
1. railway.app/new → GitHub repo
2. Add SECRET_KEY var
3. Add Postgres plugin (optional)
4. Deploy!

Procfile: `web: gunicorn --bind 0.0.0.0:$PORT student_club_management.app:create_app()`

## 📂 Structure
```
.
├── app.py (PORT entry)
├── Procfile (Railway)
├── requirements.txt (deps)
├── railway-env.example
├── student_club_management/ (core)
└── static/
```

## 🤝 Contributing
Fork, edit, push → Railway auto-deploys!

THis the hidden comment here

**Railway-only, clean, ready!**
