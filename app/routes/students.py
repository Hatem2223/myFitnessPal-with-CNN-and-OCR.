from flask import Blueprint, request, jsonify, g
from marshmallow import Schema, fields, ValidationError
from flask_jwt_extended import jwt_required

from ..extensions import db
from ..models.student import Student, ApplicationStage
from ..rbac import roles_required, scope_query_to_user
from ..models.user import UserRole


class StudentSchema(Schema):
    full_name = fields.String(required=True)
    email = fields.Email(required=False, allow_none=True)
    phone = fields.String(required=False, allow_none=True)
    nationality = fields.String(required=False, allow_none=True)
    department = fields.String(required=False, allow_none=True)
    counsellor_id = fields.Integer(required=False, allow_none=True)
    current_stage = fields.String(required=False, allow_none=True)


bp = Blueprint("students", __name__)


@bp.get("")
@roles_required({UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.COUNSELLOR})
def list_students():
    query = Student.query
    query = scope_query_to_user(query, g.current_user, student_owner_field=Student.counsellor_id, department_field=Student.department)
    students = query.order_by(Student.id.desc()).limit(200).all()
    return jsonify({"items": [s.id for s in students], "count": len(students)})


@bp.post("")
@roles_required({UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.COUNSELLOR})
def create_student():
    try:
        payload = StudentSchema().load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400
    student = Student(**payload)
    db.session.add(student)
    db.session.commit()
    return jsonify({"id": student.id}), 201


@bp.get("/<int:student_id>")
@roles_required({UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.COUNSELLOR, UserRole.STUDENT})
def get_student(student_id: int):
    query = Student.query.filter_by(id=student_id)
    query = scope_query_to_user(query, g.current_user, student_owner_field=Student.counsellor_id, department_field=Student.department)
    student = query.first()
    if not student:
        return jsonify({"message": "Not found"}), 404
    return jsonify({
        "id": student.id,
        "full_name": student.full_name,
        "email": student.email,
        "phone": student.phone,
        "nationality": student.nationality,
        "department": student.department,
        "counsellor_id": student.counsellor_id,
        "current_stage": student.current_stage.value if student.current_stage else None,
    })


@bp.put("/<int:student_id>")
@roles_required({UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.COUNSELLOR})
def update_student(student_id: int):
    query = Student.query.filter_by(id=student_id)
    query = scope_query_to_user(query, g.current_user, student_owner_field=Student.counsellor_id, department_field=Student.department)
    student = query.first()
    if not student:
        return jsonify({"message": "Not found"}), 404
    try:
        payload = StudentSchema().load(request.get_json() or {}, partial=True)
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400
    for k, v in payload.items():
        setattr(student, k, v)
    db.session.commit()
    return jsonify({"message": "updated"})


@bp.delete("/<int:student_id>")
@roles_required({UserRole.SUPER_ADMIN, UserRole.ADMIN})
def delete_student(student_id: int):
    student = Student.query.get(student_id)
    if not student:
        return jsonify({"message": "Not found"}), 404
    db.session.delete(student)
    db.session.commit()
    return jsonify({"message": "deleted"}), 200
