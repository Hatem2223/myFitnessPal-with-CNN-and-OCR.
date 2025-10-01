"""
Audit Logging Service
Track all critical system events for compliance and security
"""
from app import db
from app.models import AuditLog
from flask import request
import json

class AuditService:
    """Service for creating audit log entries"""
    
    @staticmethod
    def log_event(event_type, description, user_id=None, student_id=None, 
                  document_id=None, category='general', additional_data=None):
        """
        Create an audit log entry
        
        Args:
            event_type: Type of event (login, document_upload, role_change, etc.)
            description: Human-readable description
            user_id: ID of user who performed the action
            student_id: Related student ID (if applicable)
            document_id: Related document ID (if applicable)
            category: Event category (authentication, authorization, data_access, etc.)
            additional_data: Dictionary of additional context data
        
        Returns:
            AuditLog: Created audit log entry
        """
        try:
            # Get request context
            ip_address = request.remote_addr if request else None
            user_agent = request.headers.get('User-Agent') if request else None
            
            # Create audit log
            audit_log = AuditLog(
                user_id=user_id,
                event_type=event_type,
                event_category=category,
                description=description,
                ip_address=ip_address,
                user_agent=user_agent,
                student_id=student_id,
                document_id=document_id,
                additional_data=json.dumps(additional_data) if additional_data else None
            )
            
            db.session.add(audit_log)
            db.session.commit()
            
            return audit_log
        
        except Exception as e:
            print(f"Audit logging error: {str(e)}")
            db.session.rollback()
            return None
    
    @staticmethod
    def log_login(user_id, success=True):
        """Log user login attempt"""
        event_type = 'login_success' if success else 'login_failed'
        description = f"User login {'successful' if success else 'failed'}"
        return AuditService.log_event(
            event_type=event_type,
            description=description,
            user_id=user_id if success else None,
            category='authentication'
        )
    
    @staticmethod
    def log_logout(user_id):
        """Log user logout"""
        return AuditService.log_event(
            event_type='logout',
            description="User logged out",
            user_id=user_id,
            category='authentication'
        )
    
    @staticmethod
    def log_role_change(admin_user_id, target_user_id, old_role, new_role):
        """Log user role change"""
        return AuditService.log_event(
            event_type='role_change',
            description=f"User role changed from {old_role} to {new_role}",
            user_id=admin_user_id,
            category='authorization',
            additional_data={
                'target_user_id': target_user_id,
                'old_role': old_role,
                'new_role': new_role
            }
        )
    
    @staticmethod
    def log_document_upload(user_id, student_id, document_id, document_type):
        """Log document upload"""
        return AuditService.log_event(
            event_type='document_upload',
            description=f"Document uploaded: {document_type}",
            user_id=user_id,
            student_id=student_id,
            document_id=document_id,
            category='data_access'
        )
    
    @staticmethod
    def log_document_download(user_id, student_id, document_id, document_type):
        """Log document download"""
        return AuditService.log_event(
            event_type='document_download',
            description=f"Document downloaded: {document_type}",
            user_id=user_id,
            student_id=student_id,
            document_id=document_id,
            category='data_access'
        )
    
    @staticmethod
    def log_document_delete(user_id, student_id, document_id, document_type):
        """Log document deletion"""
        return AuditService.log_event(
            event_type='document_delete',
            description=f"Document deleted: {document_type}",
            user_id=user_id,
            student_id=student_id,
            document_id=document_id,
            category='data_modification'
        )
    
    @staticmethod
    def log_student_created(user_id, student_id, student_name):
        """Log student profile creation"""
        return AuditService.log_event(
            event_type='student_created',
            description=f"Student profile created: {student_name}",
            user_id=user_id,
            student_id=student_id,
            category='data_modification'
        )
    
    @staticmethod
    def log_student_updated(user_id, student_id, fields_changed):
        """Log student profile update"""
        return AuditService.log_event(
            event_type='student_updated',
            description=f"Student profile updated",
            user_id=user_id,
            student_id=student_id,
            category='data_modification',
            additional_data={'fields_changed': fields_changed}
        )
    
    @staticmethod
    def log_status_change(user_id, student_id, old_status, new_status):
        """Log application status change"""
        return AuditService.log_event(
            event_type='status_change',
            description=f"Application status changed from {old_status} to {new_status}",
            user_id=user_id,
            student_id=student_id,
            category='workflow'
        )
    
    @staticmethod
    def log_access_denied(user_id, resource_type, resource_id):
        """Log access denial"""
        return AuditService.log_event(
            event_type='access_denied',
            description=f"Access denied to {resource_type} (ID: {resource_id})",
            user_id=user_id,
            category='security',
            additional_data={
                'resource_type': resource_type,
                'resource_id': resource_id
            }
        )
    
    @staticmethod
    def log_backup_created(user_id, backup_id, backup_type):
        """Log system backup"""
        return AuditService.log_event(
            event_type='backup_created',
            description=f"System backup created: {backup_type}",
            user_id=user_id,
            category='system',
            additional_data={'backup_id': backup_id}
        )
    
    @staticmethod
    def log_backup_restored(user_id, backup_id):
        """Log system restore"""
        return AuditService.log_event(
            event_type='backup_restored',
            description=f"System restored from backup",
            user_id=user_id,
            category='system',
            additional_data={'backup_id': backup_id}
        )
