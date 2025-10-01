"""
Authentication and Authorization Service
JWT token management and RBAC enforcement
"""
import jwt
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, make_response
from app.models import User, UserRole

JWT_SECRET = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
JWT_ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))  # 1 hour
REFRESH_TOKEN_EXPIRES = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 2592000))  # 30 days

class AuthService:
    """Authentication and authorization service"""
    
    @staticmethod
    def generate_access_token(user_id, role):
        """Generate JWT access token"""
        payload = {
            'user_id': user_id,
            'role': role,
            'type': 'access',
            'exp': datetime.utcnow() + timedelta(seconds=ACCESS_TOKEN_EXPIRES),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    @staticmethod
    def generate_refresh_token(user_id):
        """Generate JWT refresh token"""
        payload = {
            'user_id': user_id,
            'type': 'refresh',
            'exp': datetime.utcnow() + timedelta(seconds=REFRESH_TOKEN_EXPIRES),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    @staticmethod
    def verify_token(token, token_type='access'):
        """
        Verify and decode JWT token
        
        Returns:
            dict: Decoded token payload or None if invalid
        """
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            if payload.get('type') != token_type:
                return None
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    @staticmethod
    def set_auth_cookies(response, access_token, refresh_token):
        """Set JWT tokens as HttpOnly cookies"""
        # Access token cookie
        response.set_cookie(
            'access_token',
            value=access_token,
            httponly=True,
            secure=True,  # Set to True in production with HTTPS
            samesite='Strict',
            max_age=ACCESS_TOKEN_EXPIRES
        )
        
        # Refresh token cookie
        response.set_cookie(
            'refresh_token',
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite='Strict',
            max_age=REFRESH_TOKEN_EXPIRES
        )
        
        return response
    
    @staticmethod
    def clear_auth_cookies(response):
        """Clear authentication cookies"""
        response.set_cookie('access_token', '', expires=0)
        response.set_cookie('refresh_token', '', expires=0)
        return response

def get_current_user():
    """
    Extract and verify current user from request cookies
    
    Returns:
        tuple: (user_object, error_response)
    """
    from app import db
    
    # Try to get token from cookie
    token = request.cookies.get('access_token')
    
    # Fallback to Authorization header
    if not token:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
    
    if not token:
        return None, {'error': 'Authentication required', 'code': 'NO_TOKEN'}, 401
    
    # Verify token
    payload = AuthService.verify_token(token)
    if not payload:
        return None, {'error': 'Invalid or expired token', 'code': 'INVALID_TOKEN'}, 401
    
    # Get user from database
    user = db.session.get(User, payload['user_id'])
    if not user or not user.is_active:
        return None, {'error': 'User not found or inactive', 'code': 'USER_NOT_FOUND'}, 401
    
    return user, None, None

def login_required(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user, error, status = get_current_user()
        if error:
            return jsonify(error), status
        return f(user, *args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    """
    Decorator to require specific roles
    
    Usage:
        @role_required(UserRole.SUPER_ADMIN, UserRole.ADMIN)
        def some_function(current_user):
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user, error, status = get_current_user()
            if error:
                return jsonify(error), status
            
            # Check if user has required role
            if user.role not in allowed_roles:
                return jsonify({
                    'error': 'Insufficient permissions',
                    'code': 'FORBIDDEN',
                    'required_roles': [role.value for role in allowed_roles]
                }), 403
            
            return f(user, *args, **kwargs)
        return decorated_function
    return decorator

def check_student_access(user, student):
    """
    Check if user has access to a specific student
    
    Args:
        user: Current user object
        student: Student object to check access for
    
    Returns:
        bool: True if user has access, False otherwise
    """
    # Super admin has access to all
    if user.role == UserRole.SUPER_ADMIN:
        return True
    
    # Admin has access to students in their department
    if user.role == UserRole.ADMIN:
        return student.department == user.department
    
    # Counsellor has access to assigned students
    if user.role == UserRole.COUNSELLOR:
        return student in user.assigned_students.all()
    
    # Student can only access their own profile
    if user.role == UserRole.STUDENT:
        return student.user_id == user.id
    
    # University staff can access students with applications to their university
    if user.role == UserRole.UNIVERSITY_STAFF:
        return any(app.university_id == user.university_id for app in student.applications)
    
    # Logistics team has limited access
    if user.role == UserRole.LOGISTICS_TEAM:
        return student.logistics is not None
    
    return False

def check_document_access(user, document):
    """
    Check if user has access to a specific document
    
    Args:
        user: Current user object
        document: Document object to check access for
    
    Returns:
        bool: True if user has access, False otherwise
    """
    return check_student_access(user, document.student)
