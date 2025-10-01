"""
Notification Service
Handle email and in-app notifications
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from app import db
from app.models import Notification, NotificationPriority

class NotificationService:
    """Service for sending notifications"""
    
    def __init__(self):
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.smtp_from = os.getenv('SMTP_FROM', 'noreply@studentcrm.com')
    
    def send_email(self, to_email, subject, body_html, body_text=None):
        """
        Send email notification
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body_html: HTML body content
            body_text: Plain text body (optional)
        
        Returns:
            bool: Success status
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_from
            msg['To'] = to_email
            
            # Add text and HTML parts
            if body_text:
                part1 = MIMEText(body_text, 'plain')
                msg.attach(part1)
            
            part2 = MIMEText(body_html, 'html')
            msg.attach(part2)
            
            # Send email
            if self.smtp_username and self.smtp_password:
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_username, self.smtp_password)
                    server.send_message(msg)
                return True
            else:
                print(f"Email would be sent to {to_email}: {subject}")
                print(f"(SMTP not configured - set SMTP credentials in .env)")
                return False
        
        except Exception as e:
            print(f"Email sending error: {str(e)}")
            return False
    
    def create_notification(self, user_id, title, message, priority=NotificationPriority.MEDIUM,
                          notification_type=None, student_id=None):
        """
        Create in-app notification
        
        Args:
            user_id: User to notify
            title: Notification title
            message: Notification message
            priority: Priority level
            notification_type: Type of notification
            student_id: Related student ID
        
        Returns:
            Notification: Created notification object
        """
        try:
            notification = Notification(
                user_id=user_id,
                title=title,
                message=message,
                priority=priority,
                notification_type=notification_type,
                student_id=student_id
            )
            
            db.session.add(notification)
            db.session.commit()
            
            return notification
        
        except Exception as e:
            print(f"Notification creation error: {str(e)}")
            db.session.rollback()
            return None
    
    def notify_missing_document(self, user, student, document_type):
        """Notify about missing document"""
        title = f"Missing Document: {document_type}"
        message = f"Student {student.full_name} is missing {document_type}. Please request upload."
        
        self.create_notification(
            user_id=user.id,
            title=title,
            message=message,
            priority=NotificationPriority.HIGH,
            notification_type='document',
            student_id=student.id
        )
        
        # Send email
        email_body = f"""
        <html>
        <body>
            <h2>Missing Document Alert</h2>
            <p>Dear {user.full_name},</p>
            <p>Student <strong>{student.full_name}</strong> ({student.student_number}) is missing the following document:</p>
            <p><strong>{document_type}</strong></p>
            <p>Please follow up and request the student to upload this document.</p>
            <p>Best regards,<br>Student CRM System</p>
        </body>
        </html>
        """
        
        self.send_email(user.email, title, email_body)
    
    def notify_status_change(self, user, student, old_status, new_status):
        """Notify about application status change"""
        title = f"Application Status Updated"
        message = f"Student {student.full_name}'s status changed from {old_status} to {new_status}"
        
        self.create_notification(
            user_id=user.id,
            title=title,
            message=message,
            priority=NotificationPriority.MEDIUM,
            notification_type='status_change',
            student_id=student.id
        )
        
        # Send email
        email_body = f"""
        <html>
        <body>
            <h2>Application Status Update</h2>
            <p>Dear {user.full_name},</p>
            <p>The application status for <strong>{student.full_name}</strong> ({student.student_number}) has been updated:</p>
            <ul>
                <li>Previous Status: <strong>{old_status}</strong></li>
                <li>New Status: <strong>{new_status}</strong></li>
            </ul>
            <p>Please log in to the system for more details.</p>
            <p>Best regards,<br>Student CRM System</p>
        </body>
        </html>
        """
        
        self.send_email(user.email, title, email_body)
    
    def notify_document_uploaded(self, user, student, document_type):
        """Notify about document upload"""
        title = f"New Document Uploaded"
        message = f"Student {student.full_name} uploaded {document_type}"
        
        self.create_notification(
            user_id=user.id,
            title=title,
            message=message,
            priority=NotificationPriority.MEDIUM,
            notification_type='document',
            student_id=student.id
        )
    
    def notify_deadline_approaching(self, user, student, deadline_description, days_remaining):
        """Notify about approaching deadline"""
        title = f"Deadline Approaching"
        message = f"{deadline_description} for {student.full_name} is due in {days_remaining} days"
        
        priority = NotificationPriority.URGENT if days_remaining <= 3 else NotificationPriority.HIGH
        
        self.create_notification(
            user_id=user.id,
            title=title,
            message=message,
            priority=priority,
            notification_type='deadline',
            student_id=student.id
        )
        
        # Send email
        email_body = f"""
        <html>
        <body>
            <h2>Deadline Alert</h2>
            <p>Dear {user.full_name},</p>
            <p><strong>Important:</strong> A deadline is approaching for student <strong>{student.full_name}</strong> ({student.student_number}):</p>
            <ul>
                <li>Task: <strong>{deadline_description}</strong></li>
                <li>Days Remaining: <strong>{days_remaining}</strong></li>
            </ul>
            <p>Please take necessary action to meet this deadline.</p>
            <p>Best regards,<br>Student CRM System</p>
        </body>
        </html>
        """
        
        self.send_email(user.email, title, email_body)
    
    def notify_offer_received(self, student, university_name, program_name):
        """Notify student about offer letter"""
        if not student.user_account:
            return
        
        user = student.user_account
        title = f"Offer Letter Received!"
        message = f"Congratulations! You have received an offer from {university_name} for {program_name}"
        
        self.create_notification(
            user_id=user.id,
            title=title,
            message=message,
            priority=NotificationPriority.HIGH,
            notification_type='message',
            student_id=student.id
        )
        
        # Send email
        email_body = f"""
        <html>
        <body>
            <h2>Congratulations!</h2>
            <p>Dear {student.full_name},</p>
            <p>We are pleased to inform you that you have received an offer letter from:</p>
            <ul>
                <li>University: <strong>{university_name}</strong></li>
                <li>Program: <strong>{program_name}</strong></li>
            </ul>
            <p>Please log in to your student portal to view the offer letter and next steps.</p>
            <p>Best regards,<br>Student CRM Team</p>
        </body>
        </html>
        """
        
        self.send_email(student.email, title, email_body)
    
    def notify_task_assigned(self, user, task, student):
        """Notify user about assigned task"""
        title = f"New Task Assigned"
        message = f"You have been assigned a new task for {student.full_name}: {task.title}"
        
        self.create_notification(
            user_id=user.id,
            title=title,
            message=message,
            priority=task.priority,
            notification_type='message',
            student_id=student.id
        )

# Global notification service instance
notification_service = NotificationService()
