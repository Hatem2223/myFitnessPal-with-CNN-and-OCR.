"""
Document Management Routes
Encrypted document upload, download, and management with RBAC
"""
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from app import db
from app.models import Document, Student, DocumentStatus
from app.services.auth import login_required, check_student_access, check_document_access
from app.services.encryption import encryption_service
from app.services.audit import AuditService
from app.services.notification import notification_service
import os
import uuid
from datetime import datetime

bp = Blueprint('documents', __name__, url_prefix='/api/documents')

UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', './secure_storage')
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx', 'txt'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/upload', methods=['POST'])
@login_required
def upload_document(current_user):
    """
    Upload encrypted document
    
    Form data:
        - file: Document file
        - student_id: Student ID
        - document_type: Type of document (passport, transcript, etc.)
        - expiry_date: Optional expiry date
        - notes: Optional notes
    """
    # Check if file is present
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': f'File type not allowed. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
    
    # Get form data
    student_id = request.form.get('student_id', type=int)
    document_type = request.form.get('document_type')
    expiry_date = request.form.get('expiry_date')
    notes = request.form.get('notes', '')
    
    if not student_id or not document_type:
        return jsonify({'error': 'Student ID and document type are required'}), 400
    
    # Get student and check access
    student = db.session.get(Student, student_id)
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    
    if not check_student_access(current_user, student):
        AuditService.log_access_denied(current_user.id, 'student', student_id)
        return jsonify({'error': 'Access denied'}), 403
    
    # Save file temporarily
    original_filename = secure_filename(file.filename)
    temp_path = os.path.join(UPLOAD_FOLDER, f'temp_{uuid.uuid4().hex}')
    file.save(temp_path)
    
    # Get file size
    file_size = os.path.getsize(temp_path)
    
    # Encrypt file
    encrypted_filename = f'{uuid.uuid4().hex}.enc'
    encrypted_path = os.path.join(UPLOAD_FOLDER, encrypted_filename)
    
    success, encrypted_size = encryption_service.encrypt_file(temp_path, encrypted_path)
    
    # Remove temp file
    os.remove(temp_path)
    
    if not success:
        return jsonify({'error': 'Encryption failed'}), 500
    
    # Get MIME type
    mime_type = file.content_type
    
    # Check for existing document version
    existing_doc = Document.query.filter_by(
        student_id=student_id,
        document_type=document_type
    ).order_by(Document.version.desc()).first()
    
    version = existing_doc.version + 1 if existing_doc else 1
    
    # Create document record
    document = Document(
        student_id=student_id,
        document_type=document_type,
        original_filename=original_filename,
        encrypted_filename=encrypted_filename,
        file_size=file_size,
        mime_type=mime_type,
        status=DocumentStatus.UPLOADED,
        version=version,
        expiry_date=datetime.fromisoformat(expiry_date).date() if expiry_date else None,
        uploaded_by_id=current_user.id,
        notes=notes
    )
    
    db.session.add(document)
    db.session.commit()
    
    # Log event
    AuditService.log_document_upload(current_user.id, student_id, document.id, document_type)
    
    # Notify assigned counsellors (if uploaded by student)
    if student.user_id == current_user.id:
        for counsellor in student.assigned_counsellors:
            notification_service.notify_document_uploaded(counsellor, student, document_type)
    
    return jsonify({
        'message': 'Document uploaded successfully',
        'document': document.to_dict()
    }), 201

@bp.route('/<int:document_id>', methods=['GET'])
@login_required
def get_document_info(current_user, document_id):
    """Get document information (not the file itself)"""
    document = db.session.get(Document, document_id)
    
    if not document:
        return jsonify({'error': 'Document not found'}), 404
    
    # Check access
    if not check_document_access(current_user, document):
        AuditService.log_access_denied(current_user.id, 'document', document_id)
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify(document.to_dict()), 200

@bp.route('/<int:document_id>/download', methods=['GET'])
@login_required
def download_document(current_user, document_id):
    """Download and decrypt document"""
    document = db.session.get(Document, document_id)
    
    if not document:
        return jsonify({'error': 'Document not found'}), 404
    
    # Check access
    if not check_document_access(current_user, document):
        AuditService.log_access_denied(current_user.id, 'document', document_id)
        return jsonify({'error': 'Access denied'}), 403
    
    # Path to encrypted file
    encrypted_path = os.path.join(UPLOAD_FOLDER, document.encrypted_filename)
    
    if not os.path.exists(encrypted_path):
        return jsonify({'error': 'File not found on server'}), 404
    
    # Decrypt to temporary file
    decrypted_path = os.path.join(UPLOAD_FOLDER, f'temp_decrypt_{uuid.uuid4().hex}')
    
    success = encryption_service.decrypt_file(encrypted_path, decrypted_path)
    
    if not success:
        return jsonify({'error': 'Decryption failed'}), 500
    
    # Log event
    AuditService.log_document_download(
        current_user.id, 
        document.student_id, 
        document.id, 
        document.document_type
    )
    
    # Send file
    try:
        response = send_file(
            decrypted_path,
            as_attachment=True,
            download_name=document.original_filename,
            mimetype=document.mime_type
        )
        
        # Clean up temp file after sending
        @response.call_on_close
        def cleanup():
            try:
                os.remove(decrypted_path)
            except:
                pass
        
        return response
    
    except Exception as e:
        # Clean up on error
        if os.path.exists(decrypted_path):
            os.remove(decrypted_path)
        return jsonify({'error': str(e)}), 500

@bp.route('/student/<int:student_id>', methods=['GET'])
@login_required
def get_student_documents(current_user, student_id):
    """Get all documents for a student"""
    student = db.session.get(Student, student_id)
    
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    
    # Check access
    if not check_student_access(current_user, student):
        AuditService.log_access_denied(current_user.id, 'student', student_id)
        return jsonify({'error': 'Access denied'}), 403
    
    # Get documents
    documents = Document.query.filter_by(student_id=student_id).order_by(
        Document.document_type, Document.version.desc()
    ).all()
    
    return jsonify({
        'documents': [doc.to_dict() for doc in documents]
    }), 200

@bp.route('/<int:document_id>/verify', methods=['POST'])
@login_required
def verify_document(current_user, document_id):
    """
    Verify/approve document
    
    Request body:
        {
            "status": "verified" or "rejected",
            "notes": "Optional verification notes"
        }
    """
    document = db.session.get(Document, document_id)
    
    if not document:
        return jsonify({'error': 'Document not found'}), 404
    
    # Check access
    if not check_document_access(current_user, document):
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    status = data.get('status')
    notes = data.get('notes', '')
    
    if status not in ['verified', 'rejected']:
        return jsonify({'error': 'Invalid status. Must be "verified" or "rejected"'}), 400
    
    document.status = DocumentStatus.VERIFIED if status == 'verified' else DocumentStatus.REJECTED
    document.verified_by_id = current_user.id
    document.verified_at = datetime.utcnow()
    
    if notes:
        document.notes = notes
    
    db.session.commit()
    
    # Log event
    AuditService.log_event(
        event_type='document_verified',
        description=f"Document {status}: {document.document_type}",
        user_id=current_user.id,
        student_id=document.student_id,
        document_id=document.id,
        category='workflow'
    )
    
    return jsonify({
        'message': f'Document {status} successfully',
        'document': document.to_dict()
    }), 200

@bp.route('/<int:document_id>', methods=['DELETE'])
@login_required
def delete_document(current_user, document_id):
    """Delete document"""
    document = db.session.get(Document, document_id)
    
    if not document:
        return jsonify({'error': 'Document not found'}), 404
    
    # Check access
    if not check_document_access(current_user, document):
        return jsonify({'error': 'Access denied'}), 403
    
    # Delete encrypted file
    encrypted_path = os.path.join(UPLOAD_FOLDER, document.encrypted_filename)
    if os.path.exists(encrypted_path):
        os.remove(encrypted_path)
    
    # Log event before deletion
    AuditService.log_document_delete(
        current_user.id,
        document.student_id,
        document.id,
        document.document_type
    )
    
    db.session.delete(document)
    db.session.commit()
    
    return jsonify({'message': 'Document deleted successfully'}), 200
