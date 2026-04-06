@echo off
echo 🚀 DUT Club Management - Local Demo Setup
echo.

echo 🔧 Fixing PostgreSQL dependency issue...
echo 📦 Installing psycopg2-binary instead of psycopg2...
pip install psycopg2-binary

echo.
echo 📦 Installing remaining dependencies...
pip install Flask-SQLAlchemy Flask-Login Flask-Bcrypt Flask-Mail Flask-WTF Flask-Caching Flask-Migrate python-dotenv APScheduler gunicorn requests WTForms email-validator bleach qrcode Pillow cryptography blinker cachelib charset-normalizer certifi idna urllib3 pytz greenlet typing-extensions Mako packaging pycparser dnspython python-dateutil scramp asn1crypto six webencodings itsdangerous werkzeug Jinja2 click MarkupSafe

echo.
echo 🔧 Setting environment variables...
set FLASK_APP=student_club_management.wsgi:app
set FLASK_ENV=development
set DATABASE_URL=sqlite:///club_management.db

echo.
echo 🗄️ Creating database if not exists...
if not exist "club_management.db" (
    echo 📁 Creating SQLite database...
    python -c "from app import create_app; app = create_app(); from app import db; db.create_all(); print('✅ Database created successfully')"
)

echo.
echo 🌐 Starting local server...
echo 📱 Demo will be available at: http://localhost:5000
echo 📺 Perfect for screen sharing during presentation
echo 🛑 Press Ctrl+C to stop server
echo.

python run.py
