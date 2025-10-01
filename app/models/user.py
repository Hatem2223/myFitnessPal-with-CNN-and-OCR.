import enum
from datetime import datetime
from sqlalchemy import func
from werkzeug.security import gen_salt
from passlib.hash import bcrypt

from ..extensions import db


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    COUNSELLOR = "counsellor"
    UNIVERSITY = "university"
    LOGISTICS = "logistics"
    STUDENT = "student"


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False, index=True)
    department = db.Column(db.String(120), nullable=True, index=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # For students, link to their own record later; for now optional fields
    external_ref = db.Column(db.String(64), unique=True, default=lambda: gen_salt(16))

    def set_password(self, password: str) -> None:
        self.password_hash = bcrypt.hash(password)

    def check_password(self, password: str) -> bool:
        try:
            return bcrypt.verify(password, self.password_hash)
        except Exception:
            return False

    def to_safe_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role.value if self.role else None,
            "department": self.department,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
