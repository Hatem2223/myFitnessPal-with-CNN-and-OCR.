from flask import Blueprint, jsonify, g
from sqlalchemy import func

from ..extensions import db
from ..rbac import roles_required
from ..models.user import UserRole
from ..models.student import Student, Application


bp = Blueprint("dashboard", __name__)


@bp.get("/kpis")
@roles_required({UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.COUNSELLOR, UserRole.LOGISTICS, UserRole.UNIVERSITY, UserRole.STUDENT})
def kpis():
    role = g.current_user.role
    data = {}
    if role in {UserRole.SUPER_ADMIN, UserRole.ADMIN}:
        total_students = db.session.query(func.count(Student.id)).scalar() or 0
        total_apps = db.session.query(func.count(Application.id)).scalar() or 0
        data = {"total_students": total_students, "total_applications": total_apps}
    elif role == UserRole.COUNSELLOR:
        my_students = db.session.query(func.count(Student.id)).filter(Student.counsellor_id == g.current_user.id).scalar() or 0
        data = {"my_students": my_students}
    else:
        data = {"message": "limited"}
    return jsonify(data)
