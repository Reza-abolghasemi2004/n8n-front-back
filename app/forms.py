import json
from decimal import Decimal, InvalidOperation
from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    DecimalField,
    PasswordField,
    SelectField,
    SelectMultipleField,
    StringField,
    TextAreaField,
     widgets,
)
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional, ValidationError
from app.models.output import OUTPUT_STATUSES, OUTPUT_TYPES
from app.models.project import (
    AVAILABLE_SERVICES,
    PROJECT_PRIORITIES,
    PROJECT_STATUSES,
)


class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class LoginForm(FlaskForm):
    identifier = StringField(
        "Username or Email",
        validators=[DataRequired(message="Please enter your username or email."), Length(max=255)],
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(message="Please enter your password."), Length(min=4, max=128)],
    )
    remember_me = BooleanField("Keep me signed in", default=False)


class ProjectForm(FlaskForm):
    intake_id = StringField(
        "Intake ID",
        validators=[Optional(), Length(max=64)],
    )
    company_name = StringField(
        "Company Name",
        validators=[
            DataRequired(message="Company Name is required."),
            Length(min=2, max=200),
        ],
    )
    website = StringField(
        "Website",
        validators=[Optional(), Length(max=255)],
    )
    industry = StringField(
        "Industry",
        validators=[Optional(), Length(max=120)],
    )
    contact_name = StringField(
        "Contact Name",
        validators=[Optional(), Length(max=150)],
    )
    email = StringField(
        "Email",
        validators=[Optional(), Email(message="Please enter a valid email address."), Length(max=255)],
    )
    phone = StringField(
        "Phone",
        validators=[Optional(), Length(max=64)],
    )
    country = StringField(
        "Country",
        validators=[Optional(), Length(max=100)],
    )
    monthly_budget = DecimalField(
        "Monthly Budget ($)",
        places=2,
        default=Decimal("0.00"),
        validators=[
            Optional(),
            NumberRange(min=0, message="Monthly budget cannot be negative."),
        ],
    )
    goal = StringField(
        "Primary Goal",
        validators=[Optional(), Length(max=255)],
    )
    services = MultiCheckboxField(
        "Services",
        choices=[(s, s) for s in AVAILABLE_SERVICES],
        validators=[Optional()],
    )
    custom_services = StringField(
        "Additional Services (comma-separated)",
        validators=[Optional(), Length(max=500)],
    )
    priority = SelectField(
        "Priority",
        choices=[(p, p) for p in PROJECT_PRIORITIES],
        default="Medium",
        validators=[DataRequired()],
    )
    deadline = DateField(
        "Deadline",
        format="%Y-%m-%d",
        validators=[Optional()],
    )
    attachments_text = TextAreaField(
        "Attachments (One URL or Name|URL per line, or JSON array)",
        validators=[Optional(), Length(max=5000)],
    )
    notes = TextAreaField(
        "Notes",
        validators=[Optional(), Length(max=10000)],
    )
    status = SelectField(
        "Status",
        choices=[(s, s) for s in PROJECT_STATUSES],
        default="New",
        validators=[DataRequired()],
    )
    trigger_n8n = BooleanField(
        "Trigger n8n workflow immediately after saving",
        default=False,
    )

    def get_merged_services(self) -> list[str]:
        selected = list(self.services.data or [])
        if self.custom_services.data:
            extras = [
                item.strip()
                for item in self.custom_services.data.split(",")
                if item.strip()
            ]
            for extra in extras:
                if extra not in selected:
                    selected.append(extra)
        return selected

    def get_parsed_attachments(self) -> list[dict]:
        raw = (self.attachments_text.data or "").strip()
        if not raw:
            return []

        if raw.startswith("["):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    result = []
                    for item in parsed:
                        if isinstance(item, dict):
                            name = str(item.get("name") or item.get("url") or "Attachment").strip()
                            url = str(item.get("url") or "").strip()
                            att_type = str(item.get("type") or "document").strip()
                            result.append({"name": name, "url": url, "type": att_type})
                        elif isinstance(item, str) and item.strip():
                            result.append({"name": item.strip(), "url": item.strip(), "type": "link"})
                    return result
            except ValueError:
                pass

        attachments = []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            if "|" in line:
                parts = [p.strip() for p in line.split("|", 2)]
                name = parts[0] or "Attachment"
                url = parts[1] if len(parts) > 1 else ""
                att_type = parts[2] if len(parts) > 2 else "document"
                attachments.append({"name": name, "url": url, "type": att_type})
            else:
                name = line.split("/")[-1] if "/" in line else line
                attachments.append({"name": name or line, "url": line, "type": "link"})
        return attachments


class ProjectStatusForm(FlaskForm):
    status = SelectField(
        "Status",
        choices=[(s, s) for s in PROJECT_STATUSES],
        validators=[DataRequired()],
    )


class OutputForm(FlaskForm):
    title = StringField(
        "Output Title",
        validators=[DataRequired(), Length(min=2, max=255)],
    )
    output_type = SelectField(
        "Output Type",
        choices=[(t, t.replace("_", " ").title()) for t in OUTPUT_TYPES],
        default="report",
        validators=[DataRequired()],
    )
    status = SelectField(
        "Status",
        choices=[(s, s.title()) for s in OUTPUT_STATUSES],
        default="generated",
        validators=[DataRequired()],
    )
    summary = TextAreaField(
        "Executive Summary",
        validators=[Optional(), Length(max=2000)],
    )
    content = TextAreaField(
        "Generated Content / Deliverable",
        validators=[Optional(), Length(max=50000)],
    )
    data_json = TextAreaField(
        "Structured Data (JSONB)",
        validators=[Optional(), Length(max=50000)],
    )

    def validate_data_json(self, field):
        raw = (field.data or "").strip()
        if not raw:
            return
        try:
            parsed = json.loads(raw)
            if not isinstance(parsed, dict):
                raise ValidationError("Structured data must be a JSON object (e.g. {\"key\": \"value\"}).")
        except ValueError as exc:
            raise ValidationError(f"Invalid JSON syntax: {exc}")
