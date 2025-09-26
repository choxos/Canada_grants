# 🚀 Canada Grants Tracker - Quick VPS Setup

## Server: cgt.xeradb.com | Port: 8014

### Prerequisites
- Ubuntu VPS with root access
- Domain pointing to your server IP

---

## 1️⃣ Initial Server Setup (as root)

```bash
# Update system
apt update && apt upgrade -y

# Install dependencies
apt install -y python3 python3-pip python3-venv python3-dev build-essential 
apt install -y libpq-dev nginx supervisor postgresql postgresql-contrib
apt install -y curl wget git vim htop ufw

# Create user
adduser cgt
usermod -aG sudo cgt

# Setup firewall
ufw allow ssh
ufw allow 80
ufw allow 443  
ufw allow 8014
ufw enable

# Switch to application user
su - cgt
```

---

## 2️⃣ Database Setup (as cgt user)

```bash
# Configure PostgreSQL
sudo -u postgres psql << EOF
CREATE DATABASE cgt_production;
CREATE USER cgt_user WITH PASSWORD 'Choxos10203040';
GRANT ALL PRIVILEGES ON DATABASE cgt_production TO cgt_user;
ALTER USER cgt_user CREATEDB;
\q
EOF

# Test database connection
psql -h localhost -U cgt_user -d cgt_production -c "\q"
```

---

## 3️⃣ Deploy Application

```bash
# Clone repository
cd /home/cgt
git clone https://github.com/[YOUR_USERNAME]/Canada_grants.git
cd Canada_grants

# Run deployment script
./deploy.sh
```

The deploy script will automatically:
- ✅ Create Python virtual environment
- ✅ Install dependencies
- ✅ Configure Django settings
- ✅ Setup Gunicorn
- ✅ Configure Supervisor
- ✅ Setup Nginx
- ✅ Create backup scripts

---

## 4️⃣ SSL Certificate

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d cgt.xeradb.com -d www.cgt.xeradb.com

# Reload services
sudo systemctl reload nginx
sudo supervisorctl restart cgt
```

---

## 5️⃣ Final Setup

```bash
# Create Django superuser
cd /home/cgt/Canada_grants
source venv/bin/activate
python manage.py createsuperuser

# Import grant data (if you have CSV files)
python manage.py import_grants
python manage.py import_gac_grants --csv-dir csv/GFC_data
python manage.py setup_tax_data

# Setup automated backups
(crontab -l 2>/dev/null; echo "0 2 * * * /home/cgt/Canada_grants/backup_database.sh") | crontab -
```

---

## 🌐 Access Your Site

**URL**: https://cgt.xeradb.com  
**Admin**: https://cgt.xeradb.com/admin/

---

## 📊 Monitoring Commands

```bash
# Check application status
sudo supervisorctl status cgt

# View logs
tail -f /home/cgt/Canada_grants/logs/gunicorn.log
sudo tail -f /var/log/nginx/error.log

# Restart services
sudo supervisorctl restart cgt
sudo systemctl reload nginx

# Update application
cd /home/cgt/Canada_grants
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo supervisorctl restart cgt
```

---

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| 502 Bad Gateway | `sudo supervisorctl restart cgt` |
| Static files not loading | `python manage.py collectstatic --noinput` |
| Database error | Check PostgreSQL: `sudo systemctl status postgresql` |
| SSL issues | Run certbot again: `sudo certbot --nginx -d cgt.xeradb.com` |

---

## 🎯 Expected Result

✅ **Website**: https://cgt.xeradb.com  
✅ **Features**: All grant data, search, statistics, world map  
✅ **Performance**: Fast loading with Nginx + Gunicorn  
✅ **Security**: SSL certificate, secure headers  
✅ **Monitoring**: Automated logs and backups

**Total setup time**: ~30 minutes  
**Difficulty**: Intermediate  

🎉 **Your Canada Grants Tracker is now live!**
