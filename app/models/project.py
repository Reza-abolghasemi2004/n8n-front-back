import secrets
import string
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.dialects.postgresql import JSONB
from app.extensions import db


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def generate_intake_id() -> str:
    """Generate a unique Airtable/Intake-style identifier (e.g., INT-recgWMUE97Yjoxy4E)."""
    alphabet = string.ascii_letters + string.digits
    token = "".join(secrets.choice(alphabet) for _ in range(14))
    return f"INT-rec{token}"


PROJECT_STATUSES = [
    "New",
    "Validated",
    "Queued",
    "In Progress",
    "Completed",
    "On Hold",
    "Failed",
]

ACTIVE_PROJECT_STATUSES = ("New", "Validated", "Queued", "In Progress")

PROJECT_PRIORITIES = [
    "Low",
    "Medium",
    "High",
    "Critical",
]

AVAILABLE_SERVICES = [
    "Content",
    "Lead Generation",
    "SEO",
    "Paid Ads",
    "Email Automation",
    "AI Workflow",
    "CRM Integration",
    "Web Analytics",
    "Social Media",
]

COMMON_INDUSTRIES = [
    "Technology",
    "SaaS",
    "E-Commerce",
    "Healthcare",
    "FinTech",
    "Real Estate",
    "Manufacturing",
    "Education",
    "Logistics",
    "Professional Services",
    "Media & Entertainment",
    "Other",
]


class Project(db.Model):
    """Main project/intake record processed by n8n workflows."""

    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    intake_id = db.Column(
        db.String(64),
        unique=True,
        nullable=False,
        index=True,
        default=generate_intake_id,
    )
    company_name = db.Column(db.String(200), nullable=False, index=True)
    website = db.Column(db.String(255), nullable=True)
    industry = db.Column(db.String(120), nullable=True, index=True)
    contact_name = db.Column(db.String(150), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(64), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    monthly_budget = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    goal = db.Column(db.String(255), nullable=True)
    services = db.Column(JSONB, nullable=False, default=list)
    priority = db.Column(
        db.String(32),
        nullable=False,
        default="Medium",
        index=True,
    )
    deadline = db.Column(db.Date, nullable=True)
    attachments = db.Column(JSONB, nullable=False, default=list)
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(
        db.String(50),
        nullable=False,
        default="New",
        index=True,
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        index=True,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    executions = db.relationship(
        "Execution",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="desc(Execution.started_at)",
        lazy="select",
    )
    outputs = db.relationship(
        "Output",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="desc(Output.created_at)",
        lazy="select",
    )

    @property
    def formatted_budget(self) -> str:
        val = self.monthly_budget if self.monthly_budget is not None else Decimal("0.00")
        return f"${val:,.2f}"

    @property
    def services_list(self) -> list[str]:
        if isinstance(self.services, list):
            return [str(s) for s in self.services if s]
        return []

    @property
    def attachments_list(self) -> list[dict]:
        if isinstance(self.attachments, list):
            normalized = []
            for item in self.attachments:
                if isinstance(item, dict):
                    normalized.append(item)
                elif isinstance(item, str) and item.strip():
                    normalized.append({"name": item.strip(), "url": item.strip(), "type": "link"})
            return normalized
        return []

    def to_n8n_payload(self) -> dict:
        """Serialize project record into a clean JSON payload for n8n."""
        return {
            "project_id": self.id,
            "intake_id": self.intake_id,
            "company_name": self.company_name,
            "website": self.website,
            "industry": self.industry,
            "contact_name": self.contact_name,
            "email": self.email,
            "phone": self.phone,
            "country": self.country,
            "monthly_budget": float(self.monthly_budget or 0.0),
            "formatted_budget": self.formatted_budget,
            "goal": self.goal,
            "services": self.services_list,
            "priority": self.priority,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "attachments": self.attachments_list,
            "notes": self.notes,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<Project {self.intake_id} ({self.company_name})>"
