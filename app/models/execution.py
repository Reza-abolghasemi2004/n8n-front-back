from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import JSONB
from app.extensions import db


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


EXECUTION_STATUSES = [
    "queued",
    "running",
    "success",
    "failed",
    "canceled",
]


class Execution(db.Model):
    """n8n workflow execution record linked to a Project."""

    __tablename__ = "executions"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    n8n_execution_id = db.Column(db.String(128), nullable=True, index=True)
    workflow_id = db.Column(db.String(128), nullable=True)
    workflow_name = db.Column(
        db.String(200),
        nullable=False,
        default="Project Intake Automation",
    )
    trigger_source = db.Column(db.String(64), nullable=False, default="manual")
    status = db.Column(
        db.String(32),
        nullable=False,
        default="running",
        index=True,
    )
    error_message = db.Column(db.Text, nullable=True)
    payload = db.Column(JSONB, nullable=False, default=dict)
    response_data = db.Column(JSONB, nullable=False, default=dict)
    started_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        index=True,
    )
    finished_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    project = db.relationship("Project", back_populates="executions")
    outputs = db.relationship(
        "Output",
        back_populates="execution",
        lazy="select",
    )

    @property
    def duration_seconds(self) -> float | None:
        if not self.started_at:
            return None
        end = self.finished_at
        if not end:
            if self.status in ("running", "queued"):
                end = utc_now()
            else:
                return None
        start = self.started_at
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        delta = (end - start).total_seconds()
        return max(0.0, round(delta, 2))

    @property
    def duration_display(self) -> str:
        secs = self.duration_seconds
        if secs is None:
            return "—"
        if secs < 1:
            return f"{int(secs * 1000)}ms"
        if secs < 60:
            return f"{secs:.1f}s"
        minutes = int(secs // 60)
        rem_secs = int(secs % 60)
        return f"{minutes}m {rem_secs}s"

    def __repr__(self) -> str:
        return f"<Execution #{self.id} project={self.project_id} status={self.status}>"
