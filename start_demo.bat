@echo off
echo 🚀 Starting DUT Club Management System...
echo.

echo 📦 Installing dependencies...
pip install -r requirements.txt

echo.
echo 🔧 Setting up environment...
set FLASK_APP=student_club_management.wsgi:app
set FLASK_ENV=development

echo.
echo 🌐 Starting server...
echo 📱 Demo will be available at: http://localhost:5000
echo 📺 Share this link for presentation demo
echo.
echo 🛑 Press Ctrl+C to stop server
echo.

python run.py
