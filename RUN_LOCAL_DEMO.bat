@echo off
echo 🚀 DUT Club Management - Local Demo Setup
echo.

echo 🔧 Navigating to project directory...
cd /d "c:\Users\DELL\Desktop\ClubManagement\student_club_management"

echo 🔧 Installing PostgreSQL dependency...
python -m pip install psycopg2-binary

echo.
echo 📦 Installing Flask dependencies...
python -m pip install Flask==3.0.0 Flask-SQLAlchemy==3.1.1 Flask-Login==0.6.3 Flask-Bcrypt==1.0.1 Flask-Mail==0.9.1 Flask-WTF==1.2.1 Flask-Caching==2.1.0 Flask-Migrate==4.0.5 python-dotenv==1.0.0 APScheduler==3.10.4 gunicorn==22.0.0 requests==2.32.5 WTForms==3.1.1 email-validator==2.1.1 bleach==6.1.0 qrcode==8.0 Pillow==10.4.0 cryptography==43.0.1 blinker==1.9.0 cachelib==0.9.0 charset-normalizer==3.4.6 certifi==2026.2.25 idna==3.11 urllib3==2.6.3 pytz==2026.1.post1 greenlet==3.3.2 typing-extensions==4.15.0 Mako==1.3.10 packaging==26.0 pycparser==3.0 dnspython==2.8.0 python-dateutil==2.9.0.post0 scramp==1.4.8 asn1crypto==1.5.1 six==1.17.0 webencodings==0.5.1 itsdangerous==2.1.2 werkzeug==3.0.0 Jinja2==3.1.2 click==8.1.7 MarkupSafe==2.1.1

echo.
echo 🔧 Setting environment variables...
set FLASK_APP=student_club_management.wsgi:app
set FLASK_ENV=development
set DATABASE_URL=sqlite:///club_management.db

echo.
echo 🗄️ Creating database if not exists...
if not exist "club_management.db" (
    echo 📁 Creating SQLite database...
    python -c "import sys; sys.path.append('.'); from app import create_app; app = create_app(); from app import db; db.create_all(); print('✅ Database created successfully')"
)

echo.
echo 🌐 Starting local server...
echo 📱 Demo will be available at: http://localhost:5000
echo 📺 Perfect for screen sharing during presentation
echo 🛑 Press Ctrl+C to stop server
echo.

python run.py

pause
