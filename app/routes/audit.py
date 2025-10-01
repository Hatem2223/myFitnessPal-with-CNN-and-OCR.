"""
Audit Log Routes
View and filter audit logs for compliance and security
"""
from flask import Blueprint, request, jsonify
from app.models import AuditLog, UserRole
from app.services.auth import role_required
from datetime import datetime

bp = Blueprint('audit', __name__, url_prefix='/api/audit')

@bp.route('/logs', methods=['GET'])
@role_required(UserRole.SUPER_ADMIN, UserRole.ADMIN)
def get_audit_logs(current_user):
    """
    Get audit logs with filtering
    
    Query parameters:
        - page: Page number (default: 1)
        - per_page: Results per page (default: 50)
        - event_type: Filter by event type
        - category: Filter by event category
        - user_id: Filter by user ID
        - student_id: Filter by student ID
        - date_from: Filter by date from (ISO format)
        - date_to: Filter by date to (ISO format)
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    query = AuditLog.query
    
    # Apply filters
    event_type = request.args.get('event_type')
    if event_type:
        query = query.filter_by(event_type=event_type)
    
    category = request.args.get('category')
    if category:
        query = query.filter_by(event_category=category)
    
    user_id = request.args.get('user_id', type=int)
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    student_id = request.args.get('student_id', type=int)
    if student_id:
        query = query.filter_by(student_id=student_id)
    
    date_from = request.args.get('date_from')
    if date_from:
        query = query.filter(AuditLog.timestamp >= datetime.fromisoformat(date_from))
    
    date_to = request.args.get('date_to')
    if date_to:
        query = query.filter(AuditLog.timestamp <= datetime.fromisoformat(date_to))
    
    # Paginate
    pagination = query.order_by(AuditLog.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'logs': [log.to_dict() for log in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200

@bp.route('/event-types', methods=['GET'])
@role_required(UserRole.SUPER_ADMIN, UserRole.ADMIN)
def get_event_types(current_user):
    """Get list of all event types in the system"""
    event_types = AuditLog.query.with_entities(AuditLog.event_type).distinct().all()
    categories = AuditLog.query.with_entities(AuditLog.event_category).distinct().all()
    
    return jsonify({
        'event_types': [et[0] for et in event_types],
        'categories': [c[0] for c in categories]
    }), 200

@bp.route('/stats', methods=['GET'])
@role_required(UserRole.SUPER_ADMIN)
def get_audit_stats(current_user):
    """Get audit log statistics"""
    total_logs = AuditLog.query.count()
    
    # Get counts by category
    from sqlalchemy import func
    category_stats = {}
    categories = AuditLog.query.with_entities(
        AuditLog.event_category,
        func.count(AuditLog.id)
    ).group_by(AuditLog.event_category).all()
    
    for category, count in categories:
        category_stats[category] = count
    
    # Get recent critical events
    critical_events = AuditLog.query.filter(
        AuditLog.event_category.in_(['security', 'authorization'])
    ).order_by(AuditLog.timestamp.desc()).limit(20).all()
    
    return jsonify({
        'total_logs': total_logs,
        'category_stats': category_stats,
        'recent_critical_events': [log.to_dict() for log in critical_events]
    }), 200
