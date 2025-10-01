# Student CRM System - Production Deployment Guide

This guide provides step-by-step instructions for deploying the Student CRM System to a production environment.

## 📋 Pre-Deployment Checklist

### Server Requirements
- [ ] Linux server (Ubuntu 20.04+ recommended)
- [ ] Python 3.8 or higher
- [ ] PostgreSQL 12 or higher
- [ ] Nginx or Apache web server
- [ ] SSL certificate (Let's Encrypt recommended)
- [ ] Minimum 2GB RAM, 20GB storage
- [ ] Domain name configured

### Security Requirements
- [ ] Firewall configured
- [ ] SSH key authentication enabled
- [ ] Root login disabled
- [ ] Automatic security updates enabled
- [ ] Backup strategy in place

## 🚀 Deployment Steps

### Step 1: Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3-pip python3-venv postgresql postgresql-contrib nginx certbot python3-certbot-nginx

# Create application user
sudo adduser studentcrm --disabled-password
sudo usermod -aG sudo studentcrm
```

### Step 2: PostgreSQL Configuration

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE student_crm_prod;
CREATE USER studentcrm_user WITH PASSWORD 'SECURE_PASSWORD_HERE';
GRANT ALL PRIVILEGES ON DATABASE student_crm_prod TO studentcrm_user;
\q

# Configure PostgreSQL for production
sudo nano /etc/postgresql/12/main/postgresql.conf
# Set: max_connections = 100
# Set: shared_buffers = 256MB

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### Step 3: Application Deployment

```bash
# Switch to application user
sudo su - studentcrm

# Clone or upload application
cd /home/studentcrm
# Upload your application files here

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn  # WSGI server for production
```

### Step 4: Environment Configuration

```bash
# Create production .env file
nano .env
```

**Production .env Configuration:**

```env
# Database
DATABASE_URL=postgresql://studentcrm_user:SECURE_PASSWORD@localhost:5432/student_crm_prod

# Security Keys (GENERATE NEW ONES!)
SECRET_KEY=<generate-with-python-secrets>
JWT_SECRET_KEY=<generate-with-python-secrets>
ENCRYPTION_KEY=<generate-with-base64-urandom-32>

# Session Configuration
JWT_ACCESS_TOKEN_EXPIRES=3600
JWT_REFRESH_TOKEN_EXPIRES=2592000

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-production-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
SMTP_FROM=noreply@yourdomain.com

# AWS S3 for Backups
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_BACKUP_BUCKET=studentcrm-backups-prod
AWS_REGION=ap-southeast-1

# Application
FLASK_ENV=production
FLASK_DEBUG=False
FLASK_HOST=127.0.0.1
FLASK_PORT=8000
MAX_CONTENT_LENGTH=52428800
UPLOAD_FOLDER=/home/studentcrm/secure_storage
BACKUP_DIR=/home/studentcrm/backups
```

**Generate Secure Keys:**

```python
# Run this to generate keys
python3 << EOF
import secrets
import os
import base64

print("SECRET_KEY=" + secrets.token_hex(32))
print("JWT_SECRET_KEY=" + secrets.token_hex(32))
print("ENCRYPTION_KEY=" + base64.b64encode(os.urandom(32)).decode())
EOF
```

### Step 5: Initialize Database

```bash
# Activate virtual environment
source venv/bin/activate

# Initialize database
python init_db.py

# IMPORTANT: Change default passwords immediately!
```

### Step 6: Gunicorn Configuration

Create Gunicorn configuration:

```bash
nano /home/studentcrm/gunicorn_config.py
```

```python
# Gunicorn configuration file
bind = "127.0.0.1:8000"
workers = 4  # (2 x CPU cores) + 1
worker_class = "sync"
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "/home/studentcrm/logs/access.log"
errorlog = "/home/studentcrm/logs/error.log"
loglevel = "info"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
```

### Step 7: Systemd Service

Create systemd service file:

```bash
sudo nano /etc/systemd/system/studentcrm.service
```

```ini
[Unit]
Description=Student CRM System
After=network.target postgresql.service

[Service]
Type=notify
User=studentcrm
Group=studentcrm
WorkingDirectory=/home/studentcrm
Environment="PATH=/home/studentcrm/venv/bin"
ExecStart=/home/studentcrm/venv/bin/gunicorn -c /home/studentcrm/gunicorn_config.py run:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable studentcrm
sudo systemctl start studentcrm
sudo systemctl status studentcrm
```

### Step 8: Nginx Configuration

Create Nginx configuration:

```bash
sudo nano /etc/nginx/sites-available/studentcrm
```

```nginx
# Rate limiting
limit_req_zone $binary_remote_addr zone=login:10m rate=10r/m;
limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;

# Upstream application
upstream studentcrm_app {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Max upload size
    client_max_body_size 50M;
    
    # Static files
    location /static/ {
        alias /home/studentcrm/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # API endpoints with rate limiting
    location /api/auth/login {
        limit_req zone=login burst=5 nodelay;
        proxy_pass http://studentcrm_app;
        include proxy_params;
    }
    
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://studentcrm_app;
        include proxy_params;
    }
    
    # Application
    location / {
        proxy_pass http://studentcrm_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
    
    # Logging
    access_log /var/log/nginx/studentcrm_access.log;
    error_log /var/log/nginx/studentcrm_error.log;
}
```

Enable site and restart Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/studentcrm /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 9: SSL Certificate (Let's Encrypt)

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### Step 10: Firewall Configuration

```bash
# Enable UFW
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Check status
sudo ufw status
```

### Step 11: Automated Backups

Create backup script:

```bash
nano /home/studentcrm/backup_script.sh
```

```bash
#!/bin/bash
# Automated backup script

# Configuration
BACKUP_DIR="/home/studentcrm/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="student_crm_prod"
DB_USER="studentcrm_user"

# Create backup directory if not exists
mkdir -p $BACKUP_DIR

# Database backup
pg_dump -U $DB_USER $DB_NAME > $BACKUP_DIR/db_backup_$DATE.sql

# Compress
gzip $BACKUP_DIR/db_backup_$DATE.sql

# Upload to S3 (if configured)
if command -v aws &> /dev/null; then
    aws s3 cp $BACKUP_DIR/db_backup_$DATE.sql.gz s3://studentcrm-backups-prod/
fi

# Delete backups older than 30 days
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +30 -delete

echo "Backup completed: db_backup_$DATE.sql.gz"
```

Make executable:

```bash
chmod +x /home/studentcrm/backup_script.sh
```

Add to crontab:

```bash
crontab -e
# Add this line for daily backups at 2 AM
0 2 * * * /home/studentcrm/backup_script.sh >> /home/studentcrm/logs/backup.log 2>&1
```

### Step 12: Monitoring Setup

Install monitoring tools:

```bash
sudo apt install -y fail2ban

# Configure fail2ban
sudo nano /etc/fail2ban/jail.local
```

```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true

[nginx-http-auth]
enabled = true
```

```bash
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

## 🔒 Security Hardening

### 1. Change Default Passwords

Log in to the application and immediately change all default passwords.

### 2. Configure PostgreSQL Security

```bash
sudo nano /etc/postgresql/12/main/pg_hba.conf
# Ensure only local connections are allowed
# local   all   all   peer
# host    all   all   127.0.0.1/32   md5
```

### 3. Set Proper File Permissions

```bash
chmod 700 /home/studentcrm/secure_storage
chmod 700 /home/studentcrm/backups
chmod 600 /home/studentcrm/.env
```

### 4. Configure Log Rotation

```bash
sudo nano /etc/logrotate.d/studentcrm
```

```
/home/studentcrm/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 studentcrm studentcrm
    sharedscripts
    postrotate
        systemctl reload studentcrm
    endscript
}
```

## 📊 Monitoring & Maintenance

### Check Application Status

```bash
# Service status
sudo systemctl status studentcrm

# View logs
sudo journalctl -u studentcrm -f

# Nginx logs
sudo tail -f /var/log/nginx/studentcrm_access.log
sudo tail -f /var/log/nginx/studentcrm_error.log
```

### Database Maintenance

```bash
# Vacuum database (weekly)
sudo -u postgres psql -d student_crm_prod -c "VACUUM ANALYZE;"

# Check database size
sudo -u postgres psql -d student_crm_prod -c "SELECT pg_size_pretty(pg_database_size('student_crm_prod'));"
```

### Update Application

```bash
# Backup first!
/home/studentcrm/backup_script.sh

# Update code
cd /home/studentcrm
# Pull new code or upload updated files

# Install new dependencies if any
source venv/bin/activate
pip install -r requirements.txt

# Run database migrations if any
# (Add migration commands here)

# Restart application
sudo systemctl restart studentcrm
```

## 🚨 Troubleshooting

### Application Won't Start

```bash
# Check service logs
sudo journalctl -u studentcrm -n 50

# Check Gunicorn logs
cat /home/studentcrm/logs/error.log

# Verify Python environment
/home/studentcrm/venv/bin/python --version
```

### Database Connection Issues

```bash
# Test database connection
psql -U studentcrm_user -d student_crm_prod -h localhost

# Check PostgreSQL status
sudo systemctl status postgresql
```

### Nginx Issues

```bash
# Test configuration
sudo nginx -t

# Check error logs
sudo tail -f /var/log/nginx/error.log
```

## 📈 Performance Optimization

### Database Optimization

```sql
-- Create indexes
CREATE INDEX idx_students_email ON students(email);
CREATE INDEX idx_students_student_number ON students(student_number);
CREATE INDEX idx_documents_student_id ON documents(student_id);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
```

### Nginx Caching

Add to Nginx configuration:

```nginx
# Cache static files
location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

## 🔄 Disaster Recovery

### Restore from Backup

```bash
# Stop application
sudo systemctl stop studentcrm

# Restore database
gunzip -c /home/studentcrm/backups/db_backup_YYYYMMDD_HHMMSS.sql.gz | \
  psql -U studentcrm_user -d student_crm_prod

# Start application
sudo systemctl start studentcrm
```

### Recovery Testing

Schedule regular recovery drills to ensure backups are working properly.

## 📝 Post-Deployment Checklist

- [ ] All default passwords changed
- [ ] SSL certificate installed and working
- [ ] Automated backups configured and tested
- [ ] Monitoring tools installed
- [ ] Log rotation configured
- [ ] Firewall rules active
- [ ] Application accessible via HTTPS
- [ ] Database backups tested
- [ ] Email notifications working
- [ ] Audit logs recording events
- [ ] Performance acceptable
- [ ] Security headers present
- [ ] Rate limiting functional
- [ ] Documentation updated

## 🎯 Success Metrics

Monitor these metrics:
- Application uptime (target: 99.9%)
- Response time (target: < 500ms)
- Error rate (target: < 0.1%)
- Database query time (target: < 100ms)
- Backup success rate (target: 100%)

---

**🎉 Congratulations! Your Student CRM System is now deployed in production!**

For ongoing support and updates, maintain this documentation and keep your team informed of any changes.
