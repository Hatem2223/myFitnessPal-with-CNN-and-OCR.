# Student CRM System - Quick Start Guide

Get up and running in 5 minutes!

## Prerequisites Check

```bash
# Check Python (need 3.8+)
python3 --version

# Check PostgreSQL (need 12+)
psql --version

# Check pip
pip --version
```

## Option 1: Automated Setup (Recommended)

```bash
# Run the automated setup script
./setup.sh
```

This will:
1. Create virtual environment
2. Install dependencies
3. Generate secure keys
4. Set up database
5. Initialize with sample data

## Option 2: Manual Setup

### Step 1: Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows

# Install packages
pip install -r requirements.txt
```

### Step 2: Create Database

```bash
# Using psql
psql -U postgres
CREATE DATABASE student_crm;
\q
```

### Step 3: Configure Environment

```bash
# Copy template
cp .env.example .env

# Generate encryption key
python3 -c "import os, base64; print(base64.b64encode(os.urandom(32)).decode())"

# Edit .env and set:
# - DATABASE_URL
# - SECRET_KEY
# - JWT_SECRET_KEY
# - ENCRYPTION_KEY (from above)
```

### Step 4: Initialize Database

```bash
python init_db.py
```

### Step 5: Run Application

```bash
python run.py
```

## Access the Application

Open your browser and navigate to:

```
http://localhost:5000
```

## Default Login Credentials

### Super Admin
- **Email:** admin@studentcrm.com
- **Password:** admin123

### Try Different Roles

| Role | Email | Password |
|------|-------|----------|
| Super Admin | admin@studentcrm.com | admin123 |
| Department Admin | dept.admin@studentcrm.com | admin123 |
| Counsellor | counsellor1@studentcrm.com | counsellor123 |
| Logistics Staff | logistics@studentcrm.com | logistics123 |
| University Staff | uni.staff@um.edu.my | university123 |

⚠️ **Change these passwords immediately in production!**

## Quick Feature Tour

### 1. Dashboard
- View statistics and KPIs
- See recent students
- Monitor application stages

### 2. Students
- Create new student profiles
- View and edit student details
- Track application progress
- Assign counsellors

### 3. Documents
- Upload encrypted documents
- Verify/reject documents
- Download with automatic decryption
- Track document versions

### 4. Logistics
- Create arrival arrangements
- Assign pickup staff
- Manage housing
- Schedule medical screenings

### 5. Notifications
- View alerts and messages
- Mark as read
- Filter by priority

### 6. Admin Panel
- Manage users and roles
- Configure universities
- System settings

### 7. Audit Logs
- View all system events
- Filter by user, date, type
- Compliance reporting

### 8. Backup & Restore
- Create manual backups
- Download backup files
- Restore from backup

## Testing the API

### Using cURL

```bash
# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@studentcrm.com","password":"admin123"}' \
  -c cookies.txt

# Get students
curl http://localhost:5000/api/students -b cookies.txt

# Upload document
curl -X POST http://localhost:5000/api/documents/upload \
  -b cookies.txt \
  -F "file=@document.pdf" \
  -F "student_id=1" \
  -F "document_type=passport"
```

### Using Postman

1. Import the API endpoints from `API_DOCUMENTATION.md`
2. Set base URL: `http://localhost:5000/api`
3. Login to get tokens
4. Use cookies or Authorization header

## Common Issues

### Database Connection Error

```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Start if needed
sudo systemctl start postgresql
```

### Port Already in Use

```bash
# Change port in .env
FLASK_PORT=5001

# Or kill process using port 5000
lsof -ti:5000 | xargs kill -9
```

### Module Not Found

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Permission Denied (Linux)

```bash
# Make setup script executable
chmod +x setup.sh
```

## Environment Variables

### Required

```env
DATABASE_URL=postgresql://user:pass@localhost:5432/student_crm
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
ENCRYPTION_KEY=base64-encoded-32-bytes
```

### Optional

```env
# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# AWS S3 Backup
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_BACKUP_BUCKET=bucket-name
```

## Project Structure

```
student-crm/
├── app/                    # Application code
│   ├── routes/            # API endpoints
│   ├── services/          # Business logic
│   └── models.py          # Database models
├── static/                # Frontend assets
│   ├── css/
│   └── js/
├── templates/             # HTML templates
├── secure_storage/        # Encrypted documents
├── backups/              # Database backups
├── init_db.py            # Database setup
├── run.py                # Application entry
└── requirements.txt       # Dependencies
```

## Next Steps

1. ✅ Change default passwords
2. ✅ Configure email settings
3. ✅ Set up SSL/HTTPS
4. ✅ Configure automated backups
5. ✅ Review audit logs
6. ✅ Customize for your needs

## Documentation

- 📖 **README.md** - Full documentation
- 📡 **API_DOCUMENTATION.md** - API reference
- ✅ **VERIFICATION_CHECKLIST.md** - Feature verification

## Support

For detailed information, refer to:
- Full documentation in `README.md`
- API documentation in `API_DOCUMENTATION.md`
- Verification checklist in `VERIFICATION_CHECKLIST.md`

## Security Notes

⚠️ Before going to production:

1. Change ALL default passwords
2. Generate new encryption keys
3. Enable HTTPS/SSL
4. Configure firewall
5. Set up automated backups
6. Review RBAC permissions
7. Enable rate limiting
8. Set up monitoring

## Quick Commands

```bash
# Start application
python run.py

# Initialize database
python init_db.py

# Create backup
curl -X POST http://localhost:5000/api/backup/create \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"backup_type":"full"}'

# Run with custom port
FLASK_PORT=5001 python run.py
```

## Success!

You should now have a fully functional Student CRM System running!

🎉 **Happy managing students!**

For questions or issues, refer to the comprehensive documentation in the README.md file.
