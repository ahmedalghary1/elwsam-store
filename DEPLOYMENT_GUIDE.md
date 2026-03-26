# 🚀 Deployment Guide - متجر الوسام

## 📋 Pre-Deployment Checklist

### 1. Environment Variables
Create a `.env` file (copy from `.env.example`):
```bash
cp .env.example .env
```

Update the following:
- `DJANGO_SECRET_KEY`: Generate a new secret key
- `DJANGO_DEBUG`: Set to `False` for production
- `DJANGO_ALLOWED_HOSTS`: Add your domain(s)

### 2. Database Migration
```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Create Superuser
```bash
python manage.py createsuperuser
```

### 4. Collect Static Files
```bash
python manage.py collectstatic --noinput
```

## 🔒 Security Checklist

- [ ] Change `SECRET_KEY` to a unique, random value
- [ ] Set `DEBUG = False`
- [ ] Configure `ALLOWED_HOSTS` with your domain
- [ ] Use HTTPS in production
- [ ] Set up proper database (PostgreSQL recommended)
- [ ] Configure email backend for notifications
- [ ] Enable CSRF protection (already configured)
- [ ] Review and update CORS settings if using API

## 📦 Production Server Setup

### Option 1: Using Gunicorn + Nginx

1. Install Gunicorn:
```bash
pip install gunicorn
```

2. Run Gunicorn:
```bash
gunicorn project.wsgi:application --bind 0.0.0.0:8000
```

3. Configure Nginx as reverse proxy

### Option 2: Using Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN python manage.py collectstatic --noinput
CMD ["gunicorn", "project.wsgi:application", "--bind", "0.0.0.0:8000"]
```

## 🗄️ Database Recommendations

For production, use PostgreSQL instead of SQLite:

```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
```

## 📧 Email Configuration

Configure email for order notifications:

```python
# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL')
```

## 🔄 Continuous Deployment

### GitHub Actions Example

```yaml
name: Deploy

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to server
        run: |
          # Your deployment commands
```

## 📊 Monitoring

Recommended tools:
- **Sentry**: Error tracking
- **New Relic**: Performance monitoring
- **Google Analytics**: User analytics

## 🔧 Maintenance

### Backup Database
```bash
python manage.py dumpdata > backup.json
```

### Restore Database
```bash
python manage.py loaddata backup.json
```

### Clear Cache (if using)
```bash
python manage.py clear_cache
```

## 🌐 CDN for Static Files

Consider using AWS S3 or Cloudflare for static files in production.

## ✅ Post-Deployment Testing

- [ ] Test guest checkout flow
- [ ] Test authenticated user checkout
- [ ] Verify cart persistence
- [ ] Test mobile responsiveness
- [ ] Check all forms and validations
- [ ] Test payment integration (if applicable)
- [ ] Verify email notifications
- [ ] Check admin panel access
- [ ] Test product search
- [ ] Verify order management

## 🆘 Troubleshooting

### Static files not loading
```bash
python manage.py collectstatic --clear
```

### Database connection errors
- Check database credentials
- Verify database server is running
- Check firewall rules

### 500 Internal Server Error
- Check server logs
- Verify DEBUG=False settings
- Check ALLOWED_HOSTS configuration
