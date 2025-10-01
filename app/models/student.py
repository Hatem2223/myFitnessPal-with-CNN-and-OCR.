import enum
from ..extensions import db
from .core import TimestampMixin


class ApplicationStage(str, enum.Enum):
    INQUIRY = "inquiry"
    DOCUMENTS = "documents"
    OFFER = "offer"
    VISA = "visa"
    ARRIVAL = "arrival"


class Student(TimestampMixin, db.Model):
    __tablename__ = "students"
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=True, index=True)
    phone = db.Column(db.String(50), nullable=True)
    nationality = db.Column(db.String(120), nullable=True)
    department = db.Column(db.String(120), nullable=True, index=True)
    counsellor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    current_stage = db.Column(db.Enum(ApplicationStage), nullable=False, default=ApplicationStage.INQUIRY)


class Application(TimestampMixin, db.Model):
    __tablename__ = "applications"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False, index=True)
    university_name = db.Column(db.String(255), nullable=True)
    program_name = db.Column(db.String(255), nullable=True)
    intake = db.Column(db.String(64), nullable=True)
    status = db.Column(db.String(64), nullable=True, index=True)  # pending/accepted/rejected


class Document(TimestampMixin, db.Model):
    __tablename__ = "documents"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False, index=True)
    kind = db.Column(db.String(120), nullable=False)
    version = db.Column(db.Integer, nullable=False, default=1)
    filename = db.Column(db.String(255), nullable=False)
    storage_path = db.Column(db.String(512), nullable=False)
    content_type = db.Column(db.String(120), nullable=True)
    size_bytes = db.Column(db.Integer, nullable=False, default=0)
    encryption_key_id = db.Column(db.String(64), nullable=False)
    encryption_context = db.Column(db.String(128), nullable=False)  # e.g., f"doc:{student_id}:{kind}:{version}"
    validation_status = db.Column(db.String(64), nullable=True)  # pending/valid/invalid
    uploaded_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)


class LogisticsItem(TimestampMixin, db.Model):
    __tablename__ = "logistics_items"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False, index=True)
    item_type = db.Column(db.String(64), nullable=False)  # airport_pickup/housing/medical
    scheduled_at = db.Column(db.DateTime(timezone=True), nullable=True)
    assigned_to = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    details = db.Column(db.Text, nullable=True)


class AuditEvent(TimestampMixin, db.Model):
    __tablename__ = "audit_events"
    id = db.Column(db.Integer, primary_key=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    event_type = db.Column(db.String(64), nullable=False)
    target_table = db.Column(db.String(64), nullable=True)
    target_id = db.Column(db.Integer, nullable=True)
    metadata_json = db.Column(db.JSON, nullable=True)
