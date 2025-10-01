from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    set_access_cookies,
    set_refresh_cookies,
    unset_jwt_cookies,
    jwt_required,
    get_jwt_identity,
)
from marshmallow import Schema, fields, ValidationError

from ..extensions import db
from ..models import User


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True)


bp = Blueprint("auth", __name__)


@bp.post("/login")
def login():
    try:
        payload = LoginSchema().load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    user: User | None = User.query.filter_by(email=payload["email"].lower()).first()
    if user is None or not user.is_active or not user.check_password(payload["password"]):
        return jsonify({"message": "Invalid credentials"}), 401

    identity = {"id": user.id, "role": user.role.value}
    access_token = create_access_token(identity=identity, fresh=True)
    refresh_token = create_refresh_token(identity=identity)

    resp = jsonify({"user": user.to_safe_dict()})
    set_access_cookies(resp, access_token)
    set_refresh_cookies(resp, refresh_token)
    return resp, 200


@bp.post("/logout")
def logout():
    resp = jsonify({"message": "Logged out"})
    unset_jwt_cookies(resp)
    return resp, 200


@bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity, fresh=False)
    resp = jsonify({"message": "refreshed"})
    set_access_cookies(resp, access_token)
    return resp, 200


@bp.get("/me")
@jwt_required()
def me():
    identity = get_jwt_identity()
    user = User.query.get(identity["id"]) if identity else None
    if not user:
        return jsonify({"message": "Not found"}), 404
    return jsonify({"user": user.to_safe_dict()}), 200
