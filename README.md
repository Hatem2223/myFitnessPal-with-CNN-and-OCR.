# Student Registration CRM System for Malaysia

A comprehensive web-based Customer Relationship Management (CRM) system designed to manage the entire student registration lifecycle for agencies working with international students coming to Malaysia.

## 🌟 Features

### 🔐 Security Features
- **JWT Authentication** with HttpOnly cookies
- **AES-256 Encryption** for all document storage
- **Role-Based Access Control (RBAC)** with 6 user roles
- **Comprehensive Audit Logging** for compliance
- **Automatic Session Management** with token refresh
- **Encrypted Backup System** with cloud storage support

### 👥 User Roles

1. **Super Admin** - Full system control and configuration
2. **Admin** - Department-level management and oversight
3. **Student Counsellor** - Student case management
4. **University Staff** - Application processing and offer letters
5. **Logistics Team** - Arrival coordination and logistics
6. **Student** - Personal dashboard and document upload

### 📊 Core Modules

- **Student Management** - Complete student lifecycle tracking
- **Document Management** - Encrypted document storage with versioning
- **Application Tracking** - Multi-university application management
- **Logistics Coordination** - Airport pickup, housing, medical screening
- **Notification System** - Email and in-app notifications
- **Audit Trail** - Complete security and compliance logging
- **Backup & Restore** - Automated backup with disaster recovery

### ♿ Accessibility (WCAG 2.1 AA Compliant)
- Semantic HTML structure
- ARIA labels and roles
- Keyboard navigation support
- Screen reader compatibility
- High contrast color schemes
- Focus indicators
- Skip navigation links

## 🛠️ Technology Stack

### Backend
- **Python 3.8+**
- **Flask** - Web framework
- **PostgreSQL** - Database
- **SQLAlchemy** - ORM
- **PyJWT** - Authentication
- **Cryptography** - AES-256 encryption
- **Bcrypt** - Password hashing

### Frontend
- **HTML5 + CSS3 + JavaScript**
- **Canvas API** for dynamic visualizations
- **Fetch API** for AJAX requests
- **WCAG 2.1 AA compliant**

## 📋 Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher
- pip (Python package manager)
- Virtual environment tool (optional but recommended)

## 🚀 Installation

### 1. Clone or Download the Repository

```bash
cd /workspace
```

### 2. Set Up Virtual Environment (Recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up PostgreSQL Database

```bash
# Create database
createdb student_crm

# Or using psql
psql -U postgres
CREATE DATABASE student_crm;
\q
```

### 5. Configure Environment Variables

Copy the example environment file and configure:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/student_crm

# Security Keys (Generate secure keys for production!)
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here
ENCRYPTION_KEY=your-32-byte-base64-encoded-key

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

**Generate Encryption Key:**
```python
import os
import base64
key = base64.b64encode(os.urandom(32)).decode()
print(f"ENCRYPTION_KEY={key}")
```

### 6. Initialize Database

```bash
python init_db.py
```

This will:
- Create all database tables
- Seed initial data (universities, users, sample students)
- Display default credentials

### 7. Run the Application

```bash
python run.py
```

The application will be available at: **http://localhost:5000**

## 🔑 Default Credentials

After initialization, you can log in with:

### Super Admin
- **Email:** admin@studentcrm.com
- **Password:** admin123

### Department Admin
- **Email:** dept.admin@studentcrm.com
- **Password:** admin123

### Counsellor
- **Email:** counsellor1@studentcrm.com
- **Password:** counsellor123

### Logistics Staff
- **Email:** logistics@studentcrm.com
- **Password:** logistics123

### University Staff
- **Email:** uni.staff@um.edu.my
- **Password:** university123

**⚠️ Change these passwords in production!**

## 📁 Project Structure

```
student-crm/
├── app/
│   ├── __init__.py              # Application factory
│   ├── models.py                # Database models
│   ├── routes/                  # API endpoints
│   │   ├── auth.py              # Authentication
│   │   ├── students.py          # Student management
│   │   ├── documents.py         # Document handling
│   │   ├── logistics.py         # Logistics management
│   │   ├── notifications.py     # Notifications
│   │   ├── admin.py             # Admin functions
│   │   ├── audit.py             # Audit logs
│   │   └── backup.py            # Backup/restore
│   └── services/                # Business logic
│       ├── auth.py              # Auth service
│       ├── encryption.py        # Encryption service
│       ├── audit.py             # Audit service
│       └── notification.py      # Notification service
├── static/
│   ├── css/
│   │   └── styles.css           # WCAG compliant styles
│   └── js/
│       └── app.js               # Frontend application
├── templates/
│   ├── index.html               # Main application
│   └── login.html               # Login page
├── secure_storage/              # Encrypted documents
├── backups/                     # Database backups
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
├── init_db.py                   # Database initialization
├── run.py                       # Application entry point
└── README.md                    # This file
```

## 🔒 Security Features

### Authentication
- JWT tokens with automatic expiry
- HttpOnly cookies for XSS protection
- Refresh token mechanism
- Secure password hashing with bcrypt

### Authorization
- Role-Based Access Control (RBAC)
- Principle of least privilege
- Department-level data isolation
- Resource-level permission checks

### Data Protection
- AES-256 encryption for all documents
- Encrypted data at rest and in transit
- Secure key management
- Database-level access control

### Audit & Compliance
- Complete audit trail of all actions
- IP address and user agent logging
- Event categorization for analysis
- Compliance reporting capabilities

## 📡 API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current user
- `POST /api/auth/change-password` - Change password

### Students
- `GET /api/students` - List students (role-filtered)
- `GET /api/students/<id>` - Get student details
- `POST /api/students` - Create student
- `PUT /api/students/<id>` - Update student
- `PUT /api/students/<id>/stage` - Update application stage
- `DELETE /api/students/<id>` - Delete student
- `GET /api/students/dashboard` - Dashboard statistics

### Documents
- `POST /api/documents/upload` - Upload encrypted document
- `GET /api/documents/<id>` - Get document info
- `GET /api/documents/<id>/download` - Download document
- `GET /api/documents/student/<id>` - List student documents
- `POST /api/documents/<id>/verify` - Verify/reject document
- `DELETE /api/documents/<id>` - Delete document

### Logistics
- `GET /api/logistics` - List logistics arrangements
- `GET /api/logistics/student/<id>` - Get student logistics
- `POST /api/logistics/student/<id>` - Create arrangement
- `PUT /api/logistics/<id>` - Update arrangement
- `POST /api/logistics/<id>/assign-pickup` - Assign pickup staff

### Notifications
- `GET /api/notifications` - Get user notifications
- `POST /api/notifications/<id>/read` - Mark as read
- `POST /api/notifications/mark-all-read` - Mark all as read

### Admin
- `GET /api/admin/users` - List users
- `POST /api/admin/users` - Create user
- `PUT /api/admin/users/<id>` - Update user
- `DELETE /api/admin/users/<id>` - Delete user
- `GET /api/admin/universities` - List universities
- `POST /api/admin/universities` - Create university

### Audit
- `GET /api/audit/logs` - Get audit logs (filtered)
- `GET /api/audit/event-types` - List event types
- `GET /api/audit/stats` - Audit statistics

### Backup
- `POST /api/backup/create` - Create backup
- `GET /api/backup/list` - List backups
- `GET /api/backup/<id>/download` - Download backup
- `POST /api/backup/<id>/restore` - Restore from backup

## 🧪 Testing

### Manual Testing

1. **Authentication Flow**
   - Login with different roles
   - Test token refresh
   - Test logout

2. **Student Management**
   - Create, read, update students
   - Test role-based access
   - Test department filtering

3. **Document Security**
   - Upload documents
   - Verify encryption
   - Test download and decryption

4. **Accessibility**
   - Test keyboard navigation
   - Test with screen reader
   - Verify WCAG compliance

## 🔧 Configuration

### Email Notifications

Configure SMTP settings in `.env`:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@studentcrm.com
```

### Cloud Backup (AWS S3)

For cloud backups, configure AWS credentials:

```env
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_BACKUP_BUCKET=student-crm-backups
AWS_REGION=ap-southeast-1
```

## 📊 Database Schema

The system uses PostgreSQL with the following main tables:

- `users` - User accounts with roles
- `students` - Student profiles
- `universities` - Partner universities
- `applications` - University applications
- `documents` - Encrypted document metadata
- `logistics_arrangements` - Arrival coordination
- `notifications` - In-app notifications
- `audit_logs` - Comprehensive audit trail
- `system_backups` - Backup tracking

## 🐛 Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql -U postgres -d student_crm
```

### Encryption Key Issues

If you see encryption warnings, generate a proper key:

```python
import os, base64
print(base64.b64encode(os.urandom(32)).decode())
```

### Port Already in Use

Change the port in `.env`:

```env
FLASK_PORT=5001
```

## 📝 License

This project is provided as-is for educational and commercial use.

## 👥 Support

For issues or questions, please refer to the documentation or contact the system administrator.

## 🎯 Production Deployment Checklist

Before deploying to production:

- [ ] Change all default passwords
- [ ] Generate secure encryption keys
- [ ] Configure SSL/HTTPS
- [ ] Set up database backups
- [ ] Configure email server
- [ ] Enable cloud backup
- [ ] Review audit log retention
- [ ] Set up monitoring and alerts
- [ ] Configure firewall rules
- [ ] Review RBAC permissions
- [ ] Test disaster recovery
- [ ] Enable rate limiting
- [ ] Set up CDN for static files
- [ ] Configure logging service

## 🚀 Future Enhancements

- Two-factor authentication (2FA)
- Real-time chat between counsellors and students
- Mobile application
- Advanced analytics and reporting
- Integration with university APIs
- Visa tracking integration
- Payment processing
- Document OCR and validation
- Multi-language support
- SMS notifications

---

**Built with ❤️ for Malaysian Education Agencies**
