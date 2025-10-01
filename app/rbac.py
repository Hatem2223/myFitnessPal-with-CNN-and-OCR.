from functools import wraps
from typing import Iterable, Optional
from flask import jsonify, g
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from .models import User, UserRole


def load_current_user() -> Optional[User]:
    identity = get_jwt_identity()
    if not identity:
        return None
    return User.query.get(identity.get("id"))


def roles_required(allowed_roles: Iterable[UserRole]):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user = load_current_user()
            if not user or not user.is_active:
                return jsonify({"message": "Unauthorized"}), 401
            if user.role not in allowed_roles:
                return jsonify({"message": "Forbidden"}), 403
            g.current_user = user
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def scope_query_to_user(query, user: User, *, student_owner_field=None, department_field=None):
    """
    Apply RBAC scoping to a SQLAlchemy query according to role.
    - Super Admin: no restriction
    - Admin: restricted by department if provided
    - Counsellor: assigned to them via student_owner_field
    - University: filtered by university ownership (handled at route level)
    - Logistics: filtered to non-PII projection (handled at route level)
    - Student: filtered to own records (handled at route level)
    """
    role = user.role
    if role == UserRole.SUPER_ADMIN:
        return query
    if role == UserRole.ADMIN:
        if department_field is not None and user.department:
            return query.filter(department_field == user.department)
        return query
    if role == UserRole.COUNSELLOR:
        if student_owner_field is not None:
            return query.filter(student_owner_field == user.id)
        return query.filter_by(id=-1)  # deny if we cannot scope safely
    return query
