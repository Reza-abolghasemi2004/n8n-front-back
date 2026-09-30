from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import JSONB
from app.extensions import db


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


OUTPUT_TYPES = [
    "strategy",
    "content",
    "lead_list",
    "seo_audit",
    "campaign_plan",
    "report",
    "json_payload",
]

OUTPUT_STATUSES = [
    "generated",
    "reviewed",
    "approved",
    "archived",
]


class Output(db.Model):
    """Generated output/result produced by n8n for a Project."""

    __tablename__ = "outputs"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    execution_id = db.Column(
        db.Integer,
        db.ForeignKey("executions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title = db.Column(db.String(255), nullable=False)
    output_type = db.Column(
        db.String(64),
        nullable=False,
        default="report",
        index=True,
    )
    summary = db.Column(db.Text, nullable=True)
    content = db.Column(db.Text, nullable=True)
    data = db.Column(JSONB, nullable=False, default=dict)
    status = db.Column(
        db.String(32),
        nullable=False,
        default="generated",
        index=True,
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        index=True,
    )

    project = db.relationship("Project", back_populates="outputs")
    execution = db.relationship("Execution", back_populates="outputs")

    def __repr__(self) -> str:
        return f"<Output #{self.id} project={self.project_id} type={self.output_type}>"
