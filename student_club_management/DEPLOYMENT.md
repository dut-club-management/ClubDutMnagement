# 🚀 Deployment Guide

## 📋 Prerequisites
- Python 3.8+
- PostgreSQL (for production)
- Redis (optional, for caching)
- Domain name (for production)

## 🛠️ Setup Instructions

### 1. Environment Setup
```bash
# Clone and navigate to project
cd student_club_management

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements_prod.txt
```

### 2. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env
```

### 3. Database Setup
```bash
# For PostgreSQL (recommended for production)
sudo -u postgres createdb clubmanagement_prod

# Or use SQLite (for development/testing)
# Edit DATABASE_URL in .env to use sqlite
```

### 4. Initialize Database
```bash
# Run database migrations
python -c "from app_working import create_app; from database import init_db; app = create_app('production'); init_db(app)"

# Seed with sample data (optional)
python seed_data.py
```

### 5. Test the Application
```bash
# Run in development mode first
python launch_app.py

# Test at http://localhost:5000
```

## 🌐 Production Deployment Options

### Option 1: Gunicorn (Recommended)
```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn --bind 0.0.0.0:5000 wsgi:app

# Or with workers for better performance
gunicorn --bind 0.0.0.0:5000 --workers 4 wsgi:app
```

### Option 2: Docker
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements_prod.txt .
RUN pip install -r requirements_prod.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "wsgi:app"]
```

```bash
# Build and run
docker build -t club-management .
docker run -p 5000:5000 club-management
```

### Option 3: Railway/Heroku
```bash
# Deploy to Railway
railway login
railway init
railway up

# Or Heroku
heroku create your-app-name
heroku config:set FLASK_ENV=production
git push heroku main
```

## 🔧 Configuration Notes

### Security Settings
- Change `SECRET_KEY` in production
- Use HTTPS in production
- Set up proper database credentials
- Configure mail server settings

### Performance Optimization
- Use PostgreSQL instead of SQLite
- Enable Redis caching
- Use CDN for static files
- Configure proper logging

### Monitoring
- Set up error tracking (Sentry)
- Monitor application performance
- Set up backups for database

## 📝 Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `FLASK_ENV` | Flask environment | `production` |
| `SECRET_KEY` | Flask secret key | `super-secret-key` |
| `DATABASE_URL` | Database connection | `postgresql://...` |
| `MAIL_USERNAME` | Email username | `your-email@gmail.com` |
| `MAIL_PASSWORD` | Email password | `app-password` |

## 🔄 Maintenance

### Regular Tasks
- Database backups
- Update dependencies
- Monitor logs
- Security updates

### Scaling
- Add more Gunicorn workers
- Use load balancer
- Database replication
- Caching strategy

## 🐛 Troubleshooting

### Common Issues
1. **Database connection errors** - Check DATABASE_URL
2. **Permission errors** - Check file permissions
3. **Import errors** - Check Python path
4. **Template errors** - Check template directories

### Debug Mode
```bash
# Enable debug mode temporarily
export FLASK_ENV=development
python launch_app.py
```

## 📞 Support

For deployment issues:
1. Check logs: `tail -f logs/app.log`
2. Test database connection
3. Verify environment variables
4. Check network connectivity

---

**🎉 Your Club Management System is now ready for deployment!**
