"""
Authentication Routes
Login, logout, token refresh, and session management
"""
from flask import Blueprint, request, jsonify, make_response
from app import db
from app.models import User
from app.services.auth import AuthService, login_required, get_current_user
from app.services.audit import AuditService
from datetime import datetime

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@bp.route('/login', methods=['POST'])
def login():
    """
    User login endpoint
    
    Request body:
        {
            "email": "user@example.com",
            "password": "password123"
        }
    """
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400
    
    # Find user
    user = User.query.filter_by(email=data['email'].lower()).first()
    
    if not user or not user.check_password(data['password']):
        AuditService.log_login(None, success=False)
        return jsonify({'error': 'Invalid credentials'}), 401
    
    if not user.is_active:
        return jsonify({'error': 'Account is inactive'}), 403
    
    # Generate tokens
    access_token = AuthService.generate_access_token(user.id, user.role.value)
    refresh_token = AuthService.generate_refresh_token(user.id)
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    # Log successful login
    AuditService.log_login(user.id, success=True)
    
    # Create response with cookies
    response = make_response(jsonify({
        'message': 'Login successful',
        'user': user.to_dict(),
        'access_token': access_token,
        'refresh_token': refresh_token
    }))
    
    AuthService.set_auth_cookies(response, access_token, refresh_token)
    
    return response, 200

@bp.route('/logout', methods=['POST'])
@login_required
def logout(current_user):
    """Logout endpoint - clears authentication cookies"""
    AuditService.log_logout(current_user.id)
    
    response = make_response(jsonify({'message': 'Logout successful'}))
    AuthService.clear_auth_cookies(response)
    
    return response, 200

@bp.route('/refresh', methods=['POST'])
def refresh():
    """
    Refresh access token using refresh token
    """
    # Get refresh token from cookie or body
    refresh_token = request.cookies.get('refresh_token') or request.json.get('refresh_token')
    
    if not refresh_token:
        return jsonify({'error': 'Refresh token required'}), 401
    
    # Verify refresh token
    payload = AuthService.verify_token(refresh_token, token_type='refresh')
    if not payload:
        return jsonify({'error': 'Invalid or expired refresh token'}), 401
    
    # Get user
    user = db.session.get(User, payload['user_id'])
    if not user or not user.is_active:
        return jsonify({'error': 'User not found or inactive'}), 401
    
    # Generate new access token
    access_token = AuthService.generate_access_token(user.id, user.role.value)
    
    response = make_response(jsonify({
        'message': 'Token refreshed',
        'access_token': access_token
    }))
    
    # Update access token cookie
    response.set_cookie(
        'access_token',
        value=access_token,
        httponly=True,
        secure=True,
        samesite='Strict',
        max_age=AuthService.ACCESS_TOKEN_EXPIRES if hasattr(AuthService, 'ACCESS_TOKEN_EXPIRES') else 3600
    )
    
    return response, 200

@bp.route('/me', methods=['GET'])
@login_required
def get_me(current_user):
    """Get current user information"""
    return jsonify({
        'user': current_user.to_dict()
    }), 200

@bp.route('/change-password', methods=['POST'])
@login_required
def change_password(current_user):
    """
    Change user password
    
    Request body:
        {
            "current_password": "old_password",
            "new_password": "new_password"
        }
    """
    data = request.get_json()
    
    if not data or not data.get('current_password') or not data.get('new_password'):
        return jsonify({'error': 'Current and new password required'}), 400
    
    # Verify current password
    if not current_user.check_password(data['current_password']):
        return jsonify({'error': 'Current password is incorrect'}), 401
    
    # Validate new password
    if len(data['new_password']) < 8:
        return jsonify({'error': 'New password must be at least 8 characters'}), 400
    
    # Set new password
    current_user.set_password(data['new_password'])
    db.session.commit()
    
    # Log event
    AuditService.log_event(
        event_type='password_change',
        description='User changed their password',
        user_id=current_user.id,
        category='security'
    )
    
    return jsonify({'message': 'Password changed successfully'}), 200
