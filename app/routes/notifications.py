"""
Notification Routes
In-app notifications and alerts
"""
from flask import Blueprint, request, jsonify
from app import db
from app.models import Notification
from app.services.auth import login_required
from datetime import datetime

bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')

@bp.route('', methods=['GET'])
@login_required
def get_notifications(current_user):
    """
    Get notifications for current user
    
    Query parameters:
        - unread_only: Get only unread notifications (true/false)
        - limit: Number of notifications to return (default: 50)
    """
    query = Notification.query.filter_by(user_id=current_user.id)
    
    # Filter unread only
    if request.args.get('unread_only') == 'true':
        query = query.filter_by(is_read=False)
    
    # Limit
    limit = request.args.get('limit', 50, type=int)
    
    notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()
    
    return jsonify({
        'notifications': [n.to_dict() for n in notifications],
        'unread_count': Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    }), 200

@bp.route('/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_as_read(current_user, notification_id):
    """Mark notification as read"""
    notification = db.session.get(Notification, notification_id)
    
    if not notification:
        return jsonify({'error': 'Notification not found'}), 404
    
    if notification.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    notification.is_read = True
    notification.read_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'message': 'Notification marked as read'}), 200

@bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_as_read(current_user):
    """Mark all notifications as read"""
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({
        'is_read': True,
        'read_at': datetime.utcnow()
    })
    db.session.commit()
    
    return jsonify({'message': 'All notifications marked as read'}), 200

@bp.route('/<int:notification_id>', methods=['DELETE'])
@login_required
def delete_notification(current_user, notification_id):
    """Delete notification"""
    notification = db.session.get(Notification, notification_id)
    
    if not notification:
        return jsonify({'error': 'Notification not found'}), 404
    
    if notification.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    db.session.delete(notification)
    db.session.commit()
    
    return jsonify({'message': 'Notification deleted'}), 200
