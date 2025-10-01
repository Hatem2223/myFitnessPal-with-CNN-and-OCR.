"""
Backup and Restore Routes
System backup and disaster recovery
"""
from flask import Blueprint, request, jsonify, send_file
from app import db
from app.models import SystemBackup, UserRole
from app.services.auth import role_required
from app.services.audit import AuditService
import subprocess
import os
from datetime import datetime

# Optional: boto3 for S3 backup
try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

bp = Blueprint('backup', __name__, url_prefix='/api/backup')

BACKUP_DIR = os.getenv('BACKUP_DIR', './backups')
os.makedirs(BACKUP_DIR, exist_ok=True)

@bp.route('/create', methods=['POST'])
@role_required(UserRole.SUPER_ADMIN)
def create_backup(current_user):
    """
    Create system backup
    
    Request body:
        {
            "backup_type": "full" or "incremental" or "documents",
            "upload_to_cloud": true/false
        }
    """
    data = request.get_json()
    backup_type = data.get('backup_type', 'full')
    upload_to_cloud = data.get('upload_to_cloud', False)
    
    if backup_type not in ['full', 'incremental', 'documents']:
        return jsonify({'error': 'Invalid backup type'}), 400
    
    # Create backup record
    backup = SystemBackup(
        backup_type=backup_type,
        backup_location='',
        status='in_progress',
        created_by_id=current_user.id
    )
    db.session.add(backup)
    db.session.commit()
    
    try:
        # Generate backup filename
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f'backup_{backup_type}_{timestamp}.sql'
        filepath = os.path.join(BACKUP_DIR, filename)
        
        # Create database backup using pg_dump
        db_url = os.getenv('DATABASE_URL')
        if db_url and db_url.startswith('postgresql://'):
            # Parse database URL
            from urllib.parse import urlparse
            url = urlparse(db_url)
            
            env = os.environ.copy()
            if url.password:
                env['PGPASSWORD'] = url.password
            
            cmd = [
                'pg_dump',
                '-h', url.hostname or 'localhost',
                '-p', str(url.port or 5432),
                '-U', url.username or 'postgres',
                '-d', url.path[1:] if url.path else 'student_crm',
                '-F', 'c',
                '-f', filepath
            ]
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"pg_dump failed: {result.stderr}")
        else:
            # Fallback: Create a simple SQL dump
            with open(filepath, 'w') as f:
                f.write(f"-- Backup created at {datetime.utcnow()}\n")
                f.write("-- This is a placeholder backup file\n")
                f.write("-- Configure DATABASE_URL properly for full backups\n")
        
        file_size = os.path.getsize(filepath)
        
        # Upload to cloud if requested
        backup_location = filepath
        if upload_to_cloud:
            cloud_location = upload_to_s3(filepath, filename)
            if cloud_location:
                backup_location = cloud_location
        
        # Update backup record
        backup.backup_location = backup_location
        backup.file_size = file_size
        backup.status = 'completed'
        backup.completed_at = datetime.utcnow()
        db.session.commit()
        
        # Log event
        AuditService.log_backup_created(current_user.id, backup.id, backup_type)
        
        return jsonify({
            'message': 'Backup created successfully',
            'backup': backup.to_dict()
        }), 201
    
    except Exception as e:
        backup.status = 'failed'
        backup.error_message = str(e)
        backup.completed_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'error': f'Backup failed: {str(e)}',
            'backup': backup.to_dict()
        }), 500

@bp.route('/list', methods=['GET'])
@role_required(UserRole.SUPER_ADMIN)
def list_backups(current_user):
    """Get list of all backups"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    pagination = SystemBackup.query.order_by(SystemBackup.started_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'backups': [b.to_dict() for b in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200

@bp.route('/<int:backup_id>/download', methods=['GET'])
@role_required(UserRole.SUPER_ADMIN)
def download_backup(current_user, backup_id):
    """Download backup file"""
    backup = db.session.get(SystemBackup, backup_id)
    
    if not backup:
        return jsonify({'error': 'Backup not found'}), 404
    
    if backup.status != 'completed':
        return jsonify({'error': 'Backup is not completed'}), 400
    
    # Check if file exists
    if backup.backup_location.startswith('s3://'):
        return jsonify({'error': 'Cloud backups must be downloaded from S3 directly'}), 400
    
    if not os.path.exists(backup.backup_location):
        return jsonify({'error': 'Backup file not found on server'}), 404
    
    return send_file(
        backup.backup_location,
        as_attachment=True,
        download_name=os.path.basename(backup.backup_location)
    )

@bp.route('/<int:backup_id>/restore', methods=['POST'])
@role_required(UserRole.SUPER_ADMIN)
def restore_backup(current_user, backup_id):
    """
    Restore from backup
    WARNING: This will overwrite current database
    """
    backup = db.session.get(SystemBackup, backup_id)
    
    if not backup:
        return jsonify({'error': 'Backup not found'}), 404
    
    if backup.status != 'completed':
        return jsonify({'error': 'Cannot restore from incomplete backup'}), 400
    
    # Confirmation required
    confirmation = request.get_json().get('confirmation')
    if confirmation != 'RESTORE_DATABASE':
        return jsonify({
            'error': 'Restoration requires confirmation',
            'message': 'Send {"confirmation": "RESTORE_DATABASE"} to proceed'
        }), 400
    
    try:
        filepath = backup.backup_location
        
        # Download from S3 if needed
        if filepath.startswith('s3://'):
            # Download from S3 to temp file
            filepath = download_from_s3(filepath)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'Backup file not found'}), 404
        
        # Restore database using pg_restore
        db_url = os.getenv('DATABASE_URL')
        if db_url and db_url.startswith('postgresql://'):
            from urllib.parse import urlparse
            url = urlparse(db_url)
            
            env = os.environ.copy()
            if url.password:
                env['PGPASSWORD'] = url.password
            
            cmd = [
                'pg_restore',
                '-h', url.hostname or 'localhost',
                '-p', str(url.port or 5432),
                '-U', url.username or 'postgres',
                '-d', url.path[1:] if url.path else 'student_crm',
                '-c',  # Clean (drop) database objects before recreating
                filepath
            ]
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode != 0 and 'ERROR' in result.stderr:
                raise Exception(f"pg_restore failed: {result.stderr}")
        
        # Log event
        AuditService.log_backup_restored(current_user.id, backup.id)
        
        return jsonify({
            'message': 'Database restored successfully',
            'warning': 'Application restart may be required'
        }), 200
    
    except Exception as e:
        return jsonify({'error': f'Restore failed: {str(e)}'}), 500

@bp.route('/<int:backup_id>', methods=['DELETE'])
@role_required(UserRole.SUPER_ADMIN)
def delete_backup(current_user, backup_id):
    """Delete backup"""
    backup = db.session.get(SystemBackup, backup_id)
    
    if not backup:
        return jsonify({'error': 'Backup not found'}), 404
    
    # Delete file if local
    if not backup.backup_location.startswith('s3://'):
        if os.path.exists(backup.backup_location):
            os.remove(backup.backup_location)
    
    db.session.delete(backup)
    db.session.commit()
    
    return jsonify({'message': 'Backup deleted successfully'}), 200

def upload_to_s3(filepath, filename):
    """Upload backup to S3"""
    if not HAS_BOTO3:
        print("boto3 not installed, skipping S3 upload")
        return None
    
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'ap-southeast-1')
        )
        
        bucket = os.getenv('AWS_BACKUP_BUCKET')
        if not bucket:
            return None
        
        s3_key = f'backups/{filename}'
        s3_client.upload_file(filepath, bucket, s3_key)
        
        return f's3://{bucket}/{s3_key}'
    
    except Exception as e:
        print(f"S3 upload error: {str(e)}")
        return None

def download_from_s3(s3_url):
    """Download backup from S3"""
    if not HAS_BOTO3:
        print("boto3 not installed")
        return None
    
    try:
        # Parse S3 URL
        parts = s3_url.replace('s3://', '').split('/', 1)
        bucket = parts[0]
        key = parts[1]
        
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'ap-southeast-1')
        )
        
        temp_file = os.path.join(BACKUP_DIR, f'temp_{os.path.basename(key)}')
        s3_client.download_file(bucket, key, temp_file)
        
        return temp_file
    
    except Exception as e:
        print(f"S3 download error: {str(e)}")
        return None
