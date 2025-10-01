"""
Database Models for Student CRM System
Implements RBAC and complete student lifecycle tracking
"""
from app import db
from datetime import datetime
from enum import Enum
import bcrypt

class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    COUNSELLOR = "counsellor"
    UNIVERSITY_STAFF = "university_staff"
    LOGISTICS_TEAM = "logistics_team"
    STUDENT = "student"

class ApplicationStage(str, Enum):
    INQUIRY = "inquiry"
    DOCUMENTS_COLLECTION = "documents_collection"
    APPLICATION_SUBMITTED = "application_submitted"
    OFFER_RECEIVED = "offer_received"
    VISA_PROCESSING = "visa_processing"
    VISA_APPROVED = "visa_approved"
    ARRIVAL_SCHEDULED = "arrival_scheduled"
    ARRIVED = "arrived"
    ENROLLED = "enrolled"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class DocumentStatus(str, Enum):
    PENDING = "pending"
    UPLOADED = "uploaded"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"

class NotificationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

# Association table for counsellor-student assignments
counsellor_student_assignment = db.Table('counsellor_student_assignment',
    db.Column('counsellor_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('student_id', db.Integer, db.ForeignKey('students.id'), primary_key=True),
    db.Column('assigned_at', db.DateTime, default=datetime.utcnow)
)

class User(db.Model):
    """User model with role-based access control"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False)
    department = db.Column(db.String(100))  # For admin department scope
    university_id = db.Column(db.Integer, db.ForeignKey('universities.id'))  # For university staff
    is_active = db.Column(db.Boolean, default=True)
    phone = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    assigned_students = db.relationship('Student', secondary=counsellor_student_assignment, 
                                       backref='assigned_counsellors', lazy='dynamic')
    created_students = db.relationship('Student', foreign_keys='Student.created_by_id', 
                                      backref='creator', lazy='dynamic')
    notifications = db.relationship('Notification', backref='recipient', lazy='dynamic')
    audit_logs = db.relationship('AuditLog', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        """Verify password"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def to_dict(self):
        """Serialize user data"""
        return {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role.value,
            'department': self.department,
            'university_id': self.university_id,
            'is_active': self.is_active,
            'phone': self.phone,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class University(db.Model):
    """Partner University model"""
    __tablename__ = 'universities'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False)
    location = db.Column(db.String(255))
    contact_email = db.Column(db.String(255))
    contact_phone = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    staff = db.relationship('User', backref='university', lazy='dynamic')
    applications = db.relationship('Application', backref='university', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'location': self.location,
            'contact_email': self.contact_email,
            'contact_phone': self.contact_phone,
            'is_active': self.is_active
        }

class Student(db.Model):
    """Student profile and information"""
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)  # Link to user account
    student_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    
    # Personal Information
    full_name = db.Column(db.String(255), nullable=False)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(20))
    nationality = db.Column(db.String(100))
    passport_number = db.Column(db.String(100))
    passport_expiry = db.Column(db.Date)
    
    # Contact Information
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(50))
    address = db.Column(db.Text)
    emergency_contact_name = db.Column(db.String(255))
    emergency_contact_phone = db.Column(db.String(50))
    emergency_contact_relationship = db.Column(db.String(100))
    
    # Application Information
    current_stage = db.Column(db.Enum(ApplicationStage), default=ApplicationStage.INQUIRY)
    department = db.Column(db.String(100))  # For department-based access control
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user_account = db.relationship('User', foreign_keys=[user_id], backref='student_profile')
    applications = db.relationship('Application', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    documents = db.relationship('Document', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    notes = db.relationship('StudentNote', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    tasks = db.relationship('Task', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    logistics = db.relationship('LogisticsArrangement', backref='student', uselist=False, cascade='all, delete-orphan')
    
    def to_dict(self, include_sensitive=False):
        data = {
            'id': self.id,
            'student_number': self.student_number,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'nationality': self.nationality,
            'current_stage': self.current_stage.value,
            'department': self.department,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_sensitive:
            data.update({
                'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
                'gender': self.gender,
                'passport_number': self.passport_number,
                'passport_expiry': self.passport_expiry.isoformat() if self.passport_expiry else None,
                'address': self.address,
                'emergency_contact_name': self.emergency_contact_name,
                'emergency_contact_phone': self.emergency_contact_phone
            })
        
        return data

class Application(db.Model):
    """University application tracking"""
    __tablename__ = 'applications'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    university_id = db.Column(db.Integer, db.ForeignKey('universities.id'), nullable=False)
    
    # Application Details
    program_name = db.Column(db.String(255), nullable=False)
    intake = db.Column(db.String(50))  # e.g., "September 2024"
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Status
    status = db.Column(db.String(50), default='pending')  # pending, submitted, offer_received, accepted, rejected
    offer_letter_document_id = db.Column(db.Integer, db.ForeignKey('documents.id'))
    decision_date = db.Column(db.DateTime)
    decision_notes = db.Column(db.Text)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'university_id': self.university_id,
            'university_name': self.university.name if self.university else None,
            'program_name': self.program_name,
            'intake': self.intake,
            'status': self.status,
            'application_date': self.application_date.isoformat() if self.application_date else None,
            'decision_date': self.decision_date.isoformat() if self.decision_date else None,
            'decision_notes': self.decision_notes
        }

class Document(db.Model):
    """Encrypted document storage with versioning"""
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    
    # Document Information
    document_type = db.Column(db.String(100), nullable=False)  # passport, transcript, certificate, etc.
    original_filename = db.Column(db.String(255), nullable=False)
    encrypted_filename = db.Column(db.String(255), nullable=False)  # Stored encrypted on disk
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    
    # Status and Validation
    status = db.Column(db.Enum(DocumentStatus), default=DocumentStatus.UPLOADED)
    version = db.Column(db.Integer, default=1)
    expiry_date = db.Column(db.Date)  # For documents like passports that expire
    
    # Metadata
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    verified_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    
    # Relationships
    uploaded_by = db.relationship('User', foreign_keys=[uploaded_by_id])
    verified_by = db.relationship('User', foreign_keys=[verified_by_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'document_type': self.document_type,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'status': self.status.value,
            'version': self.version,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'uploaded_by': self.uploaded_by.full_name if self.uploaded_by else None,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'notes': self.notes
        }

class StudentNote(db.Model):
    """Internal notes and comments about students"""
    __tablename__ = 'student_notes'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    content = db.Column(db.Text, nullable=False)
    is_private = db.Column(db.Boolean, default=False)  # Private notes only visible to author and admins
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    author = db.relationship('User', backref='notes')
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'author': self.author.full_name if self.author else None,
            'content': self.content,
            'is_private': self.is_private,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Task(db.Model):
    """Task management for student cases"""
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    priority = db.Column(db.Enum(NotificationPriority), default=NotificationPriority.MEDIUM)
    due_date = db.Column(db.DateTime)
    is_completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id])
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'title': self.title,
            'description': self.description,
            'priority': self.priority.value,
            'assigned_to': self.assigned_to.full_name if self.assigned_to else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'is_completed': self.is_completed,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class LogisticsArrangement(db.Model):
    """Logistics tracking for student arrival"""
    __tablename__ = 'logistics_arrangements'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, unique=True)
    
    # Arrival Information
    arrival_date = db.Column(db.DateTime)
    arrival_flight = db.Column(db.String(50))
    arrival_airport = db.Column(db.String(100))
    
    # Airport Pickup
    pickup_required = db.Column(db.Boolean, default=False)
    pickup_assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    pickup_status = db.Column(db.String(50), default='pending')  # pending, assigned, completed
    pickup_notes = db.Column(db.Text)
    
    # Housing
    housing_required = db.Column(db.Boolean, default=False)
    housing_address = db.Column(db.Text)
    housing_checkin_date = db.Column(db.Date)
    housing_status = db.Column(db.String(50), default='pending')
    
    # Medical Screening
    medical_screening_required = db.Column(db.Boolean, default=True)
    medical_appointment_date = db.Column(db.DateTime)
    medical_status = db.Column(db.String(50), default='pending')
    medical_notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    pickup_assigned_to = db.relationship('User', foreign_keys=[pickup_assigned_to_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'arrival_date': self.arrival_date.isoformat() if self.arrival_date else None,
            'arrival_flight': self.arrival_flight,
            'arrival_airport': self.arrival_airport,
            'pickup_required': self.pickup_required,
            'pickup_assigned_to': self.pickup_assigned_to.full_name if self.pickup_assigned_to else None,
            'pickup_status': self.pickup_status,
            'housing_required': self.housing_required,
            'housing_address': self.housing_address,
            'housing_status': self.housing_status,
            'medical_screening_required': self.medical_screening_required,
            'medical_appointment_date': self.medical_appointment_date.isoformat() if self.medical_appointment_date else None,
            'medical_status': self.medical_status
        }

class Notification(db.Model):
    """In-app notifications for users"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    priority = db.Column(db.Enum(NotificationPriority), default=NotificationPriority.MEDIUM)
    notification_type = db.Column(db.String(50))  # deadline, document, status_change, message
    
    # Related entities
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'))
    
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'priority': self.priority.value,
            'notification_type': self.notification_type,
            'student_id': self.student_id,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class AuditLog(db.Model):
    """Comprehensive audit trail for security and compliance"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Event Information
    event_type = db.Column(db.String(50), nullable=False, index=True)  # login, role_change, document_upload, etc.
    event_category = db.Column(db.String(50), index=True)  # authentication, authorization, data_access, etc.
    description = db.Column(db.Text, nullable=False)
    
    # Context
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(255))
    
    # Related entities
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'))
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'))
    
    # Metadata
    additional_data = db.Column(db.Text)  # JSON string for additional context
    
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user': self.user.full_name if self.user else 'System',
            'event_type': self.event_type,
            'event_category': self.event_category,
            'description': self.description,
            'ip_address': self.ip_address,
            'student_id': self.student_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

class SystemBackup(db.Model):
    """Track system backups for disaster recovery"""
    __tablename__ = 'system_backups'
    
    id = db.Column(db.Integer, primary_key=True)
    
    backup_type = db.Column(db.String(50), nullable=False)  # full, incremental, documents
    backup_location = db.Column(db.String(500), nullable=False)  # S3 URL or local path
    file_size = db.Column(db.BigInteger)
    
    status = db.Column(db.String(50), default='in_progress')  # in_progress, completed, failed
    error_message = db.Column(db.Text)
    
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    created_by = db.relationship('User')
    
    def to_dict(self):
        return {
            'id': self.id,
            'backup_type': self.backup_type,
            'backup_location': self.backup_location,
            'file_size': self.file_size,
            'status': self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_by': self.created_by.full_name if self.created_by else None
        }

class SystemSetting(db.Model):
    """System configuration and settings"""
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.String(255))
    is_encrypted = db.Column(db.Boolean, default=False)
    
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value if not self.is_encrypted else '***encrypted***',
            'description': self.description
        }
