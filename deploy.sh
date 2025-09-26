#!/bin/bash

# Canada Grants Tracker - Quick Deploy Script
# Run this script on your VPS as the cgt user

set -e  # Exit on any error

echo "🚀 Canada Grants Tracker - VPS Deployment Script"
echo "================================================="

# Configuration
DOMAIN="cgt.xeradb.com"
DB_NAME="cgt_production"
DB_USER="cgt_user"
DB_PASS="Choxos10203040"
APP_PORT="8014"
APP_DIR="/home/cgt/Canada_grants"

echo "📋 Configuration:"
echo "   Domain: $DOMAIN"
echo "   Database: $DB_NAME"
echo "   User: $DB_USER"
echo "   Port: $APP_PORT"
echo ""

# Check if running as cgt user
if [ "$USER" != "cgt" ]; then
    echo "❌ Please run this script as the 'cgt' user"
    echo "   sudo su - cgt"
    echo "   ./deploy.sh"
    exit 1
fi

echo "1️⃣  Creating application directory..."
mkdir -p $APP_DIR
cd $APP_DIR

echo "2️⃣  Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

echo "3️⃣  Installing Python dependencies..."
pip install --upgrade pip
pip install psycopg2-binary gunicorn

# If requirements.txt exists, install from it
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    # Install basic Django dependencies
    pip install Django django-decouple whitenoise
fi

echo "4️⃣  Creating production settings..."
cat > grants_project/settings_production.py << 'EOF'
import os
from decouple import config
from .settings import *

# Production settings
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',')

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
STATIC_ROOT = config('STATIC_ROOT', default='/tmp/staticfiles')
STATIC_URL = '/static/'

# Media Files
MEDIA_ROOT = config('MEDIA_ROOT', default='/tmp/media')
MEDIA_URL = '/media/'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': config('LOG_FILE', default='/tmp/django.log'),
        },
    },
    'root': {
        'handlers': ['file'],
    },
}
EOF

echo "5️⃣  Creating environment file..."
SECRET_KEY_GENERATED=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")

cat > .env << EOF
# Django Settings
SECRET_KEY=$SECRET_KEY_GENERATED
DJANGO_SETTINGS_MODULE=grants_project.settings_production
DEBUG=False

# Database Configuration
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASS
DB_HOST=localhost
DB_PORT=5432

# Domain Configuration
ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN,localhost,127.0.0.1

# Security Settings
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# File Paths
STATIC_ROOT=$APP_DIR/staticfiles
MEDIA_ROOT=$APP_DIR/media
LOG_FILE=$APP_DIR/logs/django.log
EOF

echo "6️⃣  Creating necessary directories..."
mkdir -p logs staticfiles media backups

echo "7️⃣  Creating Gunicorn configuration..."
cat > gunicorn_config.py << EOF
bind = "127.0.0.1:$APP_PORT"
workers = 3
worker_class = "sync"
timeout = 60
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
reload = False
EOF

echo "8️⃣  Setting up database (requires manual PostgreSQL setup)..."
export DJANGO_SETTINGS_MODULE=grants_project.settings_production

echo "   Testing database connection..."
python -c "
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grants_project.settings_production')
django.setup()
from django.db import connection
try:
    connection.ensure_connection()
    print('   ✅ Database connection successful')
except Exception as e:
    print(f'   ❌ Database connection failed: {e}')
    exit(1)
"

echo "9️⃣  Running Django setup..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput
python manage.py collectstatic --noinput

echo "🔟  Creating Supervisor configuration..."
sudo tee /etc/supervisor/conf.d/cgt.conf > /dev/null << EOF
[program:cgt]
command=$APP_DIR/venv/bin/gunicorn --config $APP_DIR/gunicorn_config.py grants_project.wsgi:application
directory=$APP_DIR
user=cgt
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=$APP_DIR/logs/gunicorn.log
environment=DJANGO_SETTINGS_MODULE=grants_project.settings_production
EOF

echo "1️⃣1️⃣  Creating Nginx configuration (HTTP only - SSL added later)..."
sudo tee /etc/nginx/sites-available/$DOMAIN > /dev/null << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # Static files
    location /static/ {
        alias $APP_DIR/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files
    location /media/ {
        alias $APP_DIR/media/;
        expires 7d;
    }
    
    # Main application
    location / {
        proxy_pass http://127.0.0.1:$APP_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
}
EOF

# Enable the site
sudo ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
sudo nginx -t

echo "1️⃣2️⃣  Creating backup script..."
cat > backup_database.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/cgt/backups"
mkdir -p $BACKUP_DIR

export PGPASSWORD="Choxos10203040"
pg_dump -h localhost -U cgt_user -d cgt_production > $BACKUP_DIR/cgt_backup_$DATE.sql
gzip $BACKUP_DIR/cgt_backup_$DATE.sql

# Keep only last 7 backups
find $BACKUP_DIR -name "cgt_backup_*.sql.gz" -mtime +7 -delete
EOF

chmod +x backup_database.sh

echo "1️⃣3️⃣  Starting services..."
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start cgt

echo "1️⃣4️⃣  Setting file permissions..."
sudo chown -R cgt:cgt $APP_DIR
chmod -R 755 $APP_DIR

echo ""
echo "🎉 Deployment script completed!"
echo ""
echo "📝 Next steps:"
echo "   1. Test HTTP site: curl -I http://$DOMAIN"
echo "   2. Get SSL certificate: sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN"
echo "   3. Create Django superuser: python manage.py createsuperuser"
echo "   4. Import grant data if you have CSV files"
echo "   5. Setup cron jobs for backups"
echo ""
echo "🌐 Your application is available at:"
echo "   http://$DOMAIN (currently HTTP only)"
echo ""
echo "🔒 After running Certbot:"
echo "   https://$DOMAIN (HTTPS with automatic redirect)"
echo ""
echo "🔧 Useful commands:"
echo "   Check status: sudo supervisorctl status cgt"
echo "   Restart app:  sudo supervisorctl restart cgt"
echo "   View logs:    tail -f $APP_DIR/logs/gunicorn.log"
echo "   Test site:    curl -I http://$DOMAIN"
echo ""
echo "🚀 Happy deploying!"
