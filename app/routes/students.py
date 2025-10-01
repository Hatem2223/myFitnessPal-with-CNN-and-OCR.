"""
Student Management Routes
CRUD operations for student profiles with RBAC enforcement
"""
from flask import Blueprint, request, jsonify
from app import db
from app.models import Student, User, UserRole, Application, ApplicationStage
from app.services.auth import login_required, role_required, check_student_access
from app.services.audit import AuditService
from app.services.notification import notification_service
from datetime import datetime
import uuid

bp = Blueprint('students', __name__, url_prefix='/api/students')

@bp.route('', methods=['GET'])
@login_required
def get_students(current_user):
    """
    Get list of students based on user role and permissions
    
    Query parameters:
        - page: Page number (default: 1)
        - per_page: Results per page (default: 20)
        - search: Search term for name or student number
        - stage: Filter by application stage
        - department: Filter by department
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')
    stage = request.args.get('stage', '')
    department = request.args.get('department', '')
    
    # Build query based on role
    query = Student.query
    
    if current_user.role == UserRole.SUPER_ADMIN:
        # Super admin sees all
        pass
    elif current_user.role == UserRole.ADMIN:
        # Admin sees only their department
        query = query.filter_by(department=current_user.department)
    elif current_user.role == UserRole.COUNSELLOR:
        # Counsellor sees only assigned students
        query = query.join(Student.assigned_counsellors).filter(User.id == current_user.id)
    elif current_user.role == UserRole.STUDENT:
        # Students see only themselves
        query = query.filter_by(user_id=current_user.id)
    elif current_user.role == UserRole.UNIVERSITY_STAFF:
        # University staff see students with applications to their university
        query = query.join(Student.applications).filter(Application.university_id == current_user.university_id)
    elif current_user.role == UserRole.LOGISTICS_TEAM:
        # Logistics see students with logistics arrangements
        query = query.filter(Student.logistics.isnot(None))
    else:
        return jsonify({'error': 'Access denied'}), 403
    
    # Apply filters
    if search:
        query = query.filter(
            (Student.full_name.ilike(f'%{search}%')) |
            (Student.student_number.ilike(f'%{search}%')) |
            (Student.email.ilike(f'%{search}%'))
        )
    
    if stage:
        try:
            stage_enum = ApplicationStage(stage)
            query = query.filter_by(current_stage=stage_enum)
        except ValueError:
            pass
    
    if department and current_user.role in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        query = query.filter_by(department=department)
    
    # Paginate
    pagination = query.order_by(Student.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'students': [s.to_dict() for s in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200

@bp.route('/<int:student_id>', methods=['GET'])
@login_required
def get_student(current_user, student_id):
    """Get detailed student information"""
    student = db.session.get(Student, student_id)
    
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    
    # Check access
    if not check_student_access(current_user, student):
        AuditService.log_access_denied(current_user.id, 'student', student_id)
        return jsonify({'error': 'Access denied'}), 403
    
    # Include sensitive data for authorized roles
    include_sensitive = current_user.role in [
        UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.COUNSELLOR
    ] or (current_user.role == UserRole.STUDENT and student.user_id == current_user.id)
    
    student_data = student.to_dict(include_sensitive=include_sensitive)
    
    # Add related data
    if current_user.role != UserRole.LOGISTICS_TEAM:
        student_data['applications'] = [app.to_dict() for app in student.applications]
        student_data['counsellors'] = [c.to_dict() for c in student.assigned_counsellors]
    
    if student.logistics and current_user.role in [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.COUNSELLOR, UserRole.LOGISTICS_TEAM]:
        student_data['logistics'] = student.logistics.to_dict()
    
    return jsonify(student_data), 200

@bp.route('', methods=['POST'])
@role_required(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.COUNSELLOR)
def create_student(current_user):
    """
    Create new student profile
    
    Request body:
        {
            "full_name": "John Doe",
            "email": "john@example.com",
            "phone": "+60123456789",
            "nationality": "Malaysia",
            "date_of_birth": "2000-01-01",
            "gender": "male",
            "passport_number": "A12345678",
            "passport_expiry": "2030-12-31",
            "address": "123 Main St",
            "emergency_contact_name": "Jane Doe",
            "emergency_contact_phone": "+60987654321",
            "emergency_contact_relationship": "Mother",
            "department": "Engineering"
        }
    """
    data = request.get_json()
    
    if not data or not data.get('full_name') or not data.get('email'):
        return jsonify({'error': 'Full name and email are required'}), 400
    
    # Check if email already exists
    if Student.query.filter_by(email=data['email'].lower()).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    # Generate unique student number
    student_number = f"STU{datetime.utcnow().year}{uuid.uuid4().hex[:6].upper()}"
    
    # Determine department
    department = data.get('department')
    if current_user.role == UserRole.ADMIN and not department:
        department = current_user.department
    elif current_user.role == UserRole.COUNSELLOR:
        department = current_user.department
    
    # Create student
    student = Student(
        student_number=student_number,
        full_name=data['full_name'],
        email=data['email'].lower(),
        phone=data.get('phone'),
        nationality=data.get('nationality'),
        date_of_birth=datetime.fromisoformat(data['date_of_birth']) if data.get('date_of_birth') else None,
        gender=data.get('gender'),
        passport_number=data.get('passport_number'),
        passport_expiry=datetime.fromisoformat(data['passport_expiry']).date() if data.get('passport_expiry') else None,
        address=data.get('address'),
        emergency_contact_name=data.get('emergency_contact_name'),
        emergency_contact_phone=data.get('emergency_contact_phone'),
        emergency_contact_relationship=data.get('emergency_contact_relationship'),
        department=department,
        created_by_id=current_user.id,
        current_stage=ApplicationStage.INQUIRY
    )
    
    db.session.add(student)
    db.session.commit()
    
    # Auto-assign counsellor if creator is counsellor
    if current_user.role == UserRole.COUNSELLOR:
        student.assigned_counsellors.append(current_user)
        db.session.commit()
    
    # Log event
    AuditService.log_student_created(current_user.id, student.id, student.full_name)
    
    return jsonify({
        'message': 'Student created successfully',
        'student': student.to_dict(include_sensitive=True)
    }), 201

@bp.route('/<int:student_id>', methods=['PUT'])
@login_required
def update_student(current_user, student_id):
    """Update student profile"""
    student = db.session.get(Student, student_id)
    
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    
    # Check access
    if not check_student_access(current_user, student):
        AuditService.log_access_denied(current_user.id, 'student', student_id)
        return jsonify({'error': 'Access denied'}), 403
    
    # Students can only update limited fields
    if current_user.role == UserRole.STUDENT:
        allowed_fields = ['phone', 'address', 'emergency_contact_name', 'emergency_contact_phone']
    else:
        allowed_fields = None  # All fields allowed for staff
    
    data = request.get_json()
    fields_changed = []
    
    # Update fields
    for key, value in data.items():
        if allowed_fields and key not in allowed_fields:
            continue
        
        if hasattr(student, key) and key not in ['id', 'student_number', 'created_by_id', 'user_id']:
            # Handle date fields
            if key in ['date_of_birth', 'passport_expiry'] and value:
                value = datetime.fromisoformat(value)
                if key == 'passport_expiry':
                    value = value.date()
            
            setattr(student, key, value)
            fields_changed.append(key)
    
    db.session.commit()
    
    # Log event
    if fields_changed:
        AuditService.log_student_updated(current_user.id, student.id, fields_changed)
    
    return jsonify({
        'message': 'Student updated successfully',
        'student': student.to_dict(include_sensitive=True)
    }), 200

@bp.route('/<int:student_id>/stage', methods=['PUT'])
@role_required(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.COUNSELLOR)
def update_student_stage(current_user, student_id):
    """
    Update student application stage
    
    Request body:
        {
            "stage": "documents_collection"
        }
    """
    student = db.session.get(Student, student_id)
    
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    
    # Check access
    if not check_student_access(current_user, student):
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    new_stage = data.get('stage')
    
    if not new_stage:
        return jsonify({'error': 'Stage is required'}), 400
    
    try:
        new_stage_enum = ApplicationStage(new_stage)
    except ValueError:
        return jsonify({'error': 'Invalid stage'}), 400
    
    old_stage = student.current_stage.value
    student.current_stage = new_stage_enum
    db.session.commit()
    
    # Log event
    AuditService.log_status_change(current_user.id, student.id, old_stage, new_stage)
    
    # Notify assigned counsellors
    for counsellor in student.assigned_counsellors:
        notification_service.notify_status_change(counsellor, student, old_stage, new_stage)
    
    # Notify student if they have an account
    if student.user_account:
        notification_service.notify_status_change(student.user_account, student, old_stage, new_stage)
    
    return jsonify({
        'message': 'Stage updated successfully',
        'old_stage': old_stage,
        'new_stage': new_stage
    }), 200

@bp.route('/<int:student_id>/assign-counsellor', methods=['POST'])
@role_required(UserRole.SUPER_ADMIN, UserRole.ADMIN)
def assign_counsellor(current_user, student_id):
    """
    Assign counsellor to student
    
    Request body:
        {
            "counsellor_id": 5
        }
    """
    student = db.session.get(Student, student_id)
    
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    
    # Check department access for admins
    if current_user.role == UserRole.ADMIN and student.department != current_user.department:
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    counsellor_id = data.get('counsellor_id')
    
    if not counsellor_id:
        return jsonify({'error': 'Counsellor ID is required'}), 400
    
    counsellor = db.session.get(User, counsellor_id)
    
    if not counsellor or counsellor.role != UserRole.COUNSELLOR:
        return jsonify({'error': 'Invalid counsellor'}), 400
    
    # Check if already assigned
    if counsellor in student.assigned_counsellors:
        return jsonify({'error': 'Counsellor already assigned'}), 400
    
    # Assign counsellor
    student.assigned_counsellors.append(counsellor)
    db.session.commit()
    
    # Log event
    AuditService.log_event(
        event_type='counsellor_assigned',
        description=f"Counsellor {counsellor.full_name} assigned to student {student.full_name}",
        user_id=current_user.id,
        student_id=student.id,
        category='workflow'
    )
    
    return jsonify({
        'message': 'Counsellor assigned successfully'
    }), 200

@bp.route('/<int:student_id>', methods=['DELETE'])
@role_required(UserRole.SUPER_ADMIN, UserRole.ADMIN)
def delete_student(current_user, student_id):
    """Delete student profile (soft delete recommended in production)"""
    student = db.session.get(Student, student_id)
    
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    
    # Check department access for admins
    if current_user.role == UserRole.ADMIN and student.department != current_user.department:
        return jsonify({'error': 'Access denied'}), 403
    
    # Log event before deletion
    AuditService.log_event(
        event_type='student_deleted',
        description=f"Student profile deleted: {student.full_name}",
        user_id=current_user.id,
        student_id=student.id,
        category='data_modification'
    )
    
    student_name = student.full_name
    db.session.delete(student)
    db.session.commit()
    
    return jsonify({
        'message': f'Student {student_name} deleted successfully'
    }), 200

@bp.route('/dashboard', methods=['GET'])
@login_required
def get_dashboard(current_user):
    """
    Get dashboard statistics based on user role
    """
    stats = {}
    
    # Build base query
    query = Student.query
    
    if current_user.role == UserRole.ADMIN:
        query = query.filter_by(department=current_user.department)
    elif current_user.role == UserRole.COUNSELLOR:
        query = query.join(Student.assigned_counsellors).filter(User.id == current_user.id)
    elif current_user.role == UserRole.STUDENT:
        return jsonify({'error': 'Not available for students'}), 403
    
    # Get stage counts
    stats['total_students'] = query.count()
    stats['by_stage'] = {}
    
    for stage in ApplicationStage:
        count = query.filter_by(current_stage=stage).count()
        stats['by_stage'][stage.value] = count
    
    # Recent students
    recent_students = query.order_by(Student.created_at.desc()).limit(5).all()
    stats['recent_students'] = [s.to_dict() for s in recent_students]
    
    return jsonify(stats), 200
