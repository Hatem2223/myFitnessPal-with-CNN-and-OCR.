"""
Admin Routes
User management, role management, and system configuration
"""
from flask import Blueprint, request, jsonify
from app import db
from app.models import User, UserRole, University, SystemSetting
from app.services.auth import role_required
from app.services.audit import AuditService

bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# User Management
@bp.route('/users', methods=['GET'])
@role_required(UserRole.SUPER_ADMIN, UserRole.ADMIN)
def get_users(current_user):
    """Get list of users"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    role = request.args.get('role', '')
    
    query = User.query
    
    # Admins can only see users in their department
    if current_user.role == UserRole.ADMIN:
        query = query.filter(
            (User.department == current_user.department) |
            (User.role == UserRole.STUDENT)
        )
    
    if role:
        try:
            role_enum = UserRole(role)
            query = query.filter_by(role=role_enum)
        except ValueError:
            pass
    
    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'users': [u.to_dict() for u in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200

@bp.route('/users', methods=['POST'])
@role_required(UserRole.SUPER_ADMIN, UserRole.ADMIN)
def create_user(current_user):
    """
    Create new user
    
    Request body:
        {
            "email": "user@example.com",
            "password": "password123",
            "full_name": "John Doe",
            "role": "counsellor",
            "department": "Engineering",
            "phone": "+60123456789"
        }
    """
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password') or not data.get('full_name') or not data.get('role'):
        return jsonify({'error': 'Email, password, full name, and role are required'}), 400
    
    # Check if email already exists
    if User.query.filter_by(email=data['email'].lower()).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    # Validate role
    try:
        role = UserRole(data['role'])
    except ValueError:
        return jsonify({'error': 'Invalid role'}), 400
    
    # Admins can only create users in their department
    department = data.get('department')
    if current_user.role == UserRole.ADMIN:
        if role not in [UserRole.COUNSELLOR, UserRole.STUDENT]:
            return jsonify({'error': 'Admins can only create counsellors and students'}), 403
        department = current_user.department
    
    # Create user
    user = User(
        email=data['email'].lower(),
        full_name=data['full_name'],
        role=role,
        department=department,
        phone=data.get('phone'),
        university_id=data.get('university_id')
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    # Log event
    AuditService.log_event(
        event_type='user_created',
        description=f"User created: {user.full_name} ({user.role.value})",
        user_id=current_user.id,
        category='user_management'
    )
    
    return jsonify({
        'message': 'User created successfully',
        'user': user.to_dict()
    }), 201

@bp.route('/users/<int:user_id>', methods=['PUT'])
@role_required(UserRole.SUPER_ADMIN, UserRole.ADMIN)
def update_user(current_user, user_id):
    """Update user information"""
    user = db.session.get(User, user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Admins can only update users in their department
    if current_user.role == UserRole.ADMIN and user.department != current_user.department:
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    old_role = user.role.value
    
    # Update fields
    if 'full_name' in data:
        user.full_name = data['full_name']
    
    if 'phone' in data:
        user.phone = data['phone']
    
    if 'department' in data and current_user.role == UserRole.SUPER_ADMIN:
        user.department = data['department']
    
    if 'is_active' in data:
        user.is_active = data['is_active']
    
    if 'role' in data and current_user.role == UserRole.SUPER_ADMIN:
        try:
            new_role = UserRole(data['role'])
            user.role = new_role
        except ValueError:
            return jsonify({'error': 'Invalid role'}), 400
    
    db.session.commit()
    
    # Log role change if applicable
    if 'role' in data and old_role != user.role.value:
        AuditService.log_role_change(current_user.id, user.id, old_role, user.role.value)
    
    return jsonify({
        'message': 'User updated successfully',
        'user': user.to_dict()
    }), 200

@bp.route('/users/<int:user_id>', methods=['DELETE'])
@role_required(UserRole.SUPER_ADMIN)
def delete_user(current_user, user_id):
    """Delete user (Super Admin only)"""
    if user_id == current_user.id:
        return jsonify({'error': 'Cannot delete your own account'}), 400
    
    user = db.session.get(User, user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Log event before deletion
    AuditService.log_event(
        event_type='user_deleted',
        description=f"User deleted: {user.full_name} ({user.role.value})",
        user_id=current_user.id,
        category='user_management'
    )
    
    user_name = user.full_name
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({
        'message': f'User {user_name} deleted successfully'
    }), 200

# University Management
@bp.route('/universities', methods=['GET'])
@role_required(UserRole.SUPER_ADMIN, UserRole.ADMIN)
def get_universities(current_user):
    """Get list of partner universities"""
    universities = University.query.order_by(University.name).all()
    return jsonify({
        'universities': [u.to_dict() for u in universities]
    }), 200

@bp.route('/universities', methods=['POST'])
@role_required(UserRole.SUPER_ADMIN)
def create_university(current_user):
    """
    Create new partner university
    
    Request body:
        {
            "name": "University of Malaysia",
            "code": "UM",
            "location": "Kuala Lumpur",
            "contact_email": "admissions@um.edu.my",
            "contact_phone": "+60312345678"
        }
    """
    data = request.get_json()
    
    if not data or not data.get('name') or not data.get('code'):
        return jsonify({'error': 'Name and code are required'}), 400
    
    # Check if code already exists
    if University.query.filter_by(code=data['code']).first():
        return jsonify({'error': 'University code already exists'}), 400
    
    university = University(
        name=data['name'],
        code=data['code'],
        location=data.get('location'),
        contact_email=data.get('contact_email'),
        contact_phone=data.get('contact_phone')
    )
    
    db.session.add(university)
    db.session.commit()
    
    # Log event
    AuditService.log_event(
        event_type='university_created',
        description=f"University created: {university.name}",
        user_id=current_user.id,
        category='system_configuration'
    )
    
    return jsonify({
        'message': 'University created successfully',
        'university': university.to_dict()
    }), 201

@bp.route('/universities/<int:university_id>', methods=['PUT'])
@role_required(UserRole.SUPER_ADMIN)
def update_university(current_user, university_id):
    """Update university information"""
    university = db.session.get(University, university_id)
    
    if not university:
        return jsonify({'error': 'University not found'}), 404
    
    data = request.get_json()
    
    if 'name' in data:
        university.name = data['name']
    
    if 'location' in data:
        university.location = data['location']
    
    if 'contact_email' in data:
        university.contact_email = data['contact_email']
    
    if 'contact_phone' in data:
        university.contact_phone = data['contact_phone']
    
    if 'is_active' in data:
        university.is_active = data['is_active']
    
    db.session.commit()
    
    return jsonify({
        'message': 'University updated successfully',
        'university': university.to_dict()
    }), 200

# System Settings
@bp.route('/settings', methods=['GET'])
@role_required(UserRole.SUPER_ADMIN)
def get_settings(current_user):
    """Get system settings"""
    settings = SystemSetting.query.all()
    return jsonify({
        'settings': [s.to_dict() for s in settings]
    }), 200

@bp.route('/settings', methods=['POST'])
@role_required(UserRole.SUPER_ADMIN)
def update_setting(current_user):
    """
    Update or create system setting
    
    Request body:
        {
            "key": "setting_key",
            "value": "setting_value",
            "description": "Setting description",
            "is_encrypted": false
        }
    """
    data = request.get_json()
    
    if not data or not data.get('key'):
        return jsonify({'error': 'Key is required'}), 400
    
    setting = SystemSetting.query.filter_by(key=data['key']).first()
    
    if setting:
        setting.value = data.get('value', setting.value)
        setting.description = data.get('description', setting.description)
        setting.updated_by_id = current_user.id
    else:
        setting = SystemSetting(
            key=data['key'],
            value=data.get('value'),
            description=data.get('description'),
            is_encrypted=data.get('is_encrypted', False),
            updated_by_id=current_user.id
        )
        db.session.add(setting)
    
    db.session.commit()
    
    return jsonify({
        'message': 'Setting updated successfully',
        'setting': setting.to_dict()
    }), 200
