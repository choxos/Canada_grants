# Canada Grants Tracker - VPS Deployment Guide

## Server Specifications
- **Domain**: cgt.xeradb.com  
- **Port**: 8014
- **Database**: PostgreSQL
- **Database Name**: cgt_production
- **Database User**: cgt_user
- **Database Password**: Choxos10203040

## Prerequisites
- Ubuntu 20.04+ VPS with root access
- Domain pointing to your VPS IP
- At least 2GB RAM recommended

---

## Step 1: Initial Server Setup

### 1.1 Update System
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git vim htop
```

### 1.2 Create Application User
```bash
sudo adduser cgt
sudo usermod -aG sudo cgt
su - cgt
```

### 1.3 Setup Firewall
```bash
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 8014
sudo ufw enable
```

---

## Step 2: Install Dependencies

### 2.1 Install Python and Dependencies
```bash
sudo apt install -y python3 python3-pip python3-venv python3-dev
sudo apt install -y build-essential libpq-dev nginx supervisor
```

### 2.2 Install PostgreSQL
```bash
sudo apt install -y postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 2.3 Install Node.js (for any frontend assets)
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

---

## Step 3: PostgreSQL Database Setup

### 3.1 Create Database and User
```bash
sudo -u postgres psql
```

In PostgreSQL shell:
```sql
CREATE DATABASE cgt_production;
CREATE USER cgt_user WITH PASSWORD 'Choxos10203040';
GRANT ALL PRIVILEGES ON DATABASE cgt_production TO cgt_user;
ALTER USER cgt_user CREATEDB;
\q
```

### 3.2 Test Database Connection
```bash
psql -h localhost -U cgt_user -d cgt_production
# Enter password when prompted
\q
```

---

## Step 4: Deploy Application

### 4.1 Clone Repository
```bash
cd /var/www/cgt
git clone https://github.com/choxos/Canada_grants.git .
```

### 4.2 Create Python Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

### 4.3 Install Python Dependencies
```bash
pip install -r requirements.txt
pip install psycopg2-binary gunicorn
```

---

## Step 5: Configure Django Settings

### 5.1 Create Production Settings
```bash
cp grants_project/settings.py grants_project/settings_production.py
```

### 5.2 Create Production Settings
```bash
nano grants_project/settings_production.py
```

Add/modify the following:

```python
import os
from decouple import config
from .settings import *

# Production settings
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='cgt.xeradb.com,www.cgt.xeradb.com,localhost,127.0.0.1').split(',')

# Database Configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# Security Settings
SECRET_KEY = config('SECRET_KEY')
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)

# Static Files
STATIC_ROOT = config('STATIC_ROOT', default='/var/www/cgt/staticfiles')
STATIC_URL = '/static/'

# Media Files
MEDIA_ROOT = config('MEDIA_ROOT', default='/var/www/cgt/media')
MEDIA_URL = '/media/'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': config('LOG_FILE', default='/var/www/cgt/logs/django.log'),
        },
    },
    'root': {
        'handlers': ['file'],
    },
}
```

### 5.3 Create Environment File
```bash
# Copy the example file and customize it
cp env.example .env
nano .env
```

Update the .env file with your actual values:
```bash
# Django Settings
SECRET_KEY=your-super-secret-production-key-here-make-it-long-and-random-50-characters
DJANGO_SETTINGS_MODULE=grants_project.settings_production
DEBUG=False

# Database Configuration
DB_NAME=cgt_production
DB_USER=cgt_user
DB_PASSWORD=Choxos10203040
DB_HOST=localhost
DB_PORT=5432

# Domain Configuration
ALLOWED_HOSTS=cgt.xeradb.com,www.cgt.xeradb.com,localhost,127.0.0.1

# Security Settings
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# File Paths
STATIC_ROOT=/var/www/cgt/staticfiles
MEDIA_ROOT=/var/www/cgt/media
LOG_FILE=/var/www/cgt/logs/django.log
```

**⚠️ Security Notes**: 
- Generate a unique SECRET_KEY:
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(50))"
  ```
- Never commit the .env file to version control
- The env.example file shows the required structure without sensitive values

### 5.4 Create Directories
```bash
mkdir -p logs staticfiles media
```

---

## Step 6: Database Migration and Setup

### 6.1 Apply Migrations
```bash
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=grants_project.settings_production
python manage.py makemigrations
python manage.py migrate
```

### 6.2 Create Superuser
```bash
python manage.py createsuperuser
```

### 6.3 Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### 6.4 Import Grant Data
```bash
# Import domestic grants if you have CSV files
python manage.py import_grants

# Import GAC grants
python manage.py import_gac_grants --csv-dir csv/GFC_data

# Setup tax data
python manage.py setup_tax_data
```

---

## Step 7: Configure Gunicorn

### 7.1 Create Gunicorn Configuration
```bash
nano /var/www/cgt/gunicorn_config.py
```

Add:
```python
bind = "127.0.0.1:8014"
workers = 3
worker_class = "sync"
timeout = 60
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
reload = False
```

### 7.2 Test Gunicorn
```bash
cd /var/www/cgt/
source venv/bin/activate
gunicorn --config gunicorn_config.py grants_project.wsgi:application
```

Test in another terminal:
```bash
curl http://127.0.0.1:8014
```

---

## Step 8: Setup Supervisor

### 8.1 Create Supervisor Configuration
```bash
sudo nano /etc/supervisor/conf.d/cgt.conf
```

Add:
```ini
[program:cgt]
command=/var/www/cgt/venv/bin/gunicorn --config /var/www/cgt/gunicorn_config.py grants_project.wsgi:application
directory=/var/www/cgt
user=xeradb
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/www/cgt/logs/gunicorn.log
environment=DJANGO_SETTINGS_MODULE=grants_project.settings_production
```

### 8.2 Start Supervisor
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start cgt
sudo supervisorctl status
```

---

## Step 9: Configure Nginx

### 9.1 Create Nginx Configuration
```bash
sudo nano /etc/nginx/sites-available/cgt.xeradb.com
```

Add this **HTTP-only configuration first**:
```nginx
server {
    listen 80;
    server_name cgt.xeradb.com www.cgt.xeradb.com;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # Static files
    location /static/ {
        alias /home/cgt/Canada_grants/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files
    location /media/ {
        alias /home/cgt/Canada_grants/media/;
        expires 7d;
    }
    
    # Main application
    location / {
        proxy_pass http://127.0.0.1:8014;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
}
```

**⚠️ Note**: This is the initial HTTP-only configuration. HTTPS will be added automatically by Certbot in Step 10.

### 9.2 Enable Site
```bash
sudo ln -s /etc/nginx/sites-available/cgt.xeradb.com /etc/nginx/sites-enabled/
sudo nginx -t
```

---

## Step 10: SSL Certificate Setup

### 10.1 Install Certbot
```bash
sudo apt install -y certbot python3-certbot-nginx
```

### 10.2 Start Nginx with HTTP Configuration
```bash
sudo systemctl start nginx
sudo systemctl enable nginx
sudo systemctl reload nginx
```

Test that your site works on HTTP:
```bash
curl -I http://cgt.xeradb.com
```

### 10.3 Get SSL Certificate (Automatic Nginx Update)
```bash
sudo certbot --nginx -d cgt.xeradb.com -d www.cgt.xeradb.com
```

**What Certbot does automatically:**
- ✅ Obtains SSL certificate from Let's Encrypt
- ✅ **Automatically updates your Nginx configuration** to add HTTPS  
- ✅ Adds HTTP to HTTPS redirect
- ✅ Configures SSL settings and security headers
- ✅ Sets up automatic certificate renewal

### 10.4 Verify HTTPS Works
```bash
sudo systemctl reload nginx
```

Test HTTPS:
```bash
curl -I https://cgt.xeradb.com
```

Your site should now automatically redirect HTTP to HTTPS!

---

## Step 11: Final Setup and Testing

### 11.1 Set Proper Permissions
```bash
sudo chown -R cgt:cgt /var/www/cgt
chmod -R 755 /var/www/cgt
```

### 11.2 Create Backup Script
```bash
nano /home/cgt/backup_database.sh
```

Add:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/cgt/backups"
mkdir -p $BACKUP_DIR

pg_dump -h localhost -U cgt_user -d cgt_production > $BACKUP_DIR/cgt_backup_$DATE.sql
gzip $BACKUP_DIR/cgt_backup_$DATE.sql

# Keep only last 7 backups
find $BACKUP_DIR -name "cgt_backup_*.sql.gz" -mtime +7 -delete
```

Make executable:
```bash
chmod +x /home/cgt/backup_database.sh
```

### 11.3 Setup Cron Job
```bash
crontab -e
```

Add:
```bash
# Backup database daily at 2 AM
0 2 * * * /home/cgt/backup_database.sh

# Collect static files weekly
0 3 * * 0 cd /var/www/cgt && source venv/bin/activate && python manage.py collectstatic --noinput
```

---

## Step 12: Monitoring and Maintenance

### 12.1 Check Application Status
```bash
sudo supervisorctl status cgt
sudo systemctl status nginx
sudo systemctl status postgresql
```

### 12.2 View Logs
```bash
# Application logs
tail -f /var/www/cgt/logs/gunicorn.log
tail -f /var/www/cgt/logs/django.log

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 12.3 Update Application
```bash
cd /var/www/cgt
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo supervisorctl restart cgt
```

---

## Step 13: Security Checklist

- [ ] Firewall configured (UFW)
- [ ] SSL certificate installed
- [ ] Database password is secure
- [ ] Django SECRET_KEY is unique and secure
- [ ] DEBUG = False in production
- [ ] Regular backups scheduled
- [ ] Server updates automated
- [ ] Non-root user for application
- [ ] Proper file permissions set

---

## Troubleshooting

### Common Issues:

1. **502 Bad Gateway**: Check if Gunicorn is running
   ```bash
   sudo supervisorctl status cgt
   sudo supervisorctl restart cgt
   ```

2. **Database Connection Error**: Check PostgreSQL service
   ```bash
   sudo systemctl status postgresql
   psql -h localhost -U cgt_user -d cgt_production
   ```

3. **Static Files Not Loading**: Collect static files
   ```bash
   cd /var/www/cgt
   source venv/bin/activate
   python manage.py collectstatic --noinput
   ```

4. **Permission Denied**: Fix permissions
   ```bash
   sudo chown -R cgt:cgt /var/www/cgt
   ```

---

## Access Your Application

Once deployed, your application will be available at:
- **HTTPS**: https://cgt.xeradb.com
- **HTTP** (redirects to HTTPS): http://cgt.xeradb.com

The application runs on port 8014 internally but is served through Nginx on standard ports 80/443.

---

## Support

If you encounter issues during deployment, check:
1. All services are running
2. Firewall allows necessary ports
3. DNS is properly configured
4. SSL certificate is valid
5. Database credentials are correct

Good luck with your deployment! 🚀
