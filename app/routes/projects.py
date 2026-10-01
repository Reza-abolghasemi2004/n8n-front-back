from decimal import Decimal
from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import or_
from app.extensions import db
from app.forms import OutputForm, ProjectForm, ProjectStatusForm
from app.integrations.n8n import trigger_workflow
from app.models.project import (
    AVAILABLE_SERVICES,
    COMMON_INDUSTRIES,
    PROJECT_PRIORITIES,
    PROJECT_STATUSES,
    Project,
    generate_intake_id,
)

projects_bp = Blueprint("projects", __name__, url_prefix="/projects")


def _format_attachments_for_textarea(attachments: list[dict] | None) -> str:
    if not attachments:
        return ""
    lines = []
    for item in attachments:
        if isinstance(item, dict):
            name = item.get("name") or ""
            url = item.get("url") or ""
            att_type = item.get("type") or "document"
            if name and url and name != url:
                lines.append(f"{name} | {url} | {att_type}")
            else:
                lines.append(url or name)
        elif isinstance(item, str):
            lines.append(item)
    return "\n".join(lines)


@projects_bp.route("", methods=["GET"])
@projects_bp.route("/", methods=["GET"])
@login_required
def index():
    search_query = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "").strip()
    priority_filter = request.args.get("priority", "").strip()
    service_filter = request.args.get("service", "").strip()
    page = max(1, request.args.get("page", 1, type=int))
    per_page = current_app.config.get("ITEMS_PER_PAGE", 10)

    query = Project.query

    if search_query:
        like_pattern = f"%{search_query}%"
        query = query.filter(
            or_(
                Project.intake_id.ilike(like_pattern),
                Project.company_name.ilike(like_pattern),
                Project.industry.ilike(like_pattern),
                Project.contact_name.ilike(like_pattern),
                Project.email.ilike(like_pattern),
                Project.goal.ilike(like_pattern),
                Project.country.ilike(like_pattern),
            )
        )

    if status_filter and status_filter in PROJECT_STATUSES:
        query = query.filter(Project.status == status_filter)

    if priority_filter and priority_filter in PROJECT_PRIORITIES:
        query = query.filter(Project.priority == priority_filter)

    if service_filter:
        query = query.filter(Project.services.contains([service_filter]))

    pagination = query.order_by(Project.created_at.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False,
    )

    return render_template(
        "projects/index.html",
        projects=pagination.items,
        pagination=pagination,
        search_query=search_query,
        status_filter=status_filter,
        priority_filter=priority_filter,
        service_filter=service_filter,
        statuses=PROJECT_STATUSES,
        priorities=PROJECT_PRIORITIES,
        available_services=AVAILABLE_SERVICES,
    )


@projects_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    form = ProjectForm()
    if request.method == "GET" and not form.intake_id.data:
        form.intake_id.data = generate_intake_id()

    if form.validate_on_submit():
        intake_id = (form.intake_id.data or "").strip() or generate_intake_id()
        existing = Project.query.filter_by(intake_id=intake_id).first()
        if existing:
            form.intake_id.errors.append("A project with this Intake ID already exists.")
            return render_template(
                "projects/create.html",
                form=form,
                industries=COMMON_INDUSTRIES,
            )

        project = Project(
            intake_id=intake_id,
            company_name=form.company_name.data.strip(),
            website=(form.website.data or "").strip() or None,
            industry=(form.industry.data or "").strip() or None,
            contact_name=(form.contact_name.data or "").strip() or None,
            email=(form.email.data or "").strip() or None,
            phone=(form.phone.data or "").strip() or None,
            country=(form.country.data or "").strip() or None,
            monthly_budget=form.monthly_budget.data
            if form.monthly_budget.data is not None
            else Decimal("0.00"),
            goal=(form.goal.data or "").strip() or None,
            services=form.get_merged_services(),
            priority=form.priority.data,
            deadline=form.deadline.data,
            attachments=form.get_parsed_attachments(),
            notes=(form.notes.data or "").strip() or None,
            status=form.status.data,
        )
        db.session.add(project)
        db.session.commit()

        flash(f"Project '{project.company_name}' ({project.intake_id}) created.", "success")

        if form.trigger_n8n.data:
            result = trigger_workflow(project, trigger_source="create_hook")
            if result["ok"]:
                flash("n8n automation workflow triggered.", "info")
            else:
                flash(
                    f"Project saved, but n8n webhook could not be reached: {result['error']}",
                    "warning",
                )

        return redirect(url_for("projects.detail", project_id=project.id))

    return render_template(
        "projects/create.html",
        form=form,
        industries=COMMON_INDUSTRIES,
    )


@projects_bp.route("/<int:project_id>", methods=["GET"])
@login_required
def detail(project_id: int):
    project = db.get_or_404(Project, project_id)
    status_form = ProjectStatusForm(status=project.status)
    output_form = OutputForm()

    return render_template(
        "projects/detail.html",
        project=project,
        status_form=status_form,
        output_form=output_form,
        statuses=PROJECT_STATUSES,
    )


@projects_bp.route("/<int:project_id>/edit", methods=["GET", "POST"])
@login_required
def edit(project_id: int):
    project = db.get_or_404(Project, project_id)
    form = ProjectForm(obj=project)

    if request.method == "GET":
        current_services = project.services_list
        known = [s for s in current_services if s in AVAILABLE_SERVICES]
        custom = [s for s in current_services if s not in AVAILABLE_SERVICES]
        form.services.data = known
        form.custom_services.data = ", ".join(custom)
        form.attachments_text.data = _format_attachments_for_textarea(project.attachments_list)

    if form.validate_on_submit():
        new_intake_id = (form.intake_id.data or "").strip() or project.intake_id
        conflict = Project.query.filter(
            Project.intake_id == new_intake_id,
            Project.id != project.id,
        ).first()
        if conflict:
            form.intake_id.errors.append("Another project already uses this Intake ID.")
            return render_template(
                "projects/edit.html",
                form=form,
                project=project,
                industries=COMMON_INDUSTRIES,
            )

        project.intake_id = new_intake_id
        project.company_name = form.company_name.data.strip()
        project.website = (form.website.data or "").strip() or None
        project.industry = (form.industry.data or "").strip() or None
        project.contact_name = (form.contact_name.data or "").strip() or None
        project.email = (form.email.data or "").strip() or None
        project.phone = (form.phone.data or "").strip() or None
        project.country = (form.country.data or "").strip() or None
        project.monthly_budget = (
            form.monthly_budget.data
            if form.monthly_budget.data is not None
            else Decimal("0.00")
        )
        project.goal = (form.goal.data or "").strip() or None
        project.services = form.get_merged_services()
        project.priority = form.priority.data
        project.deadline = form.deadline.data
        project.attachments = form.get_parsed_attachments()
        project.notes = (form.notes.data or "").strip() or None
        project.status = form.status.data

        db.session.commit()
        flash(f"Project '{project.company_name}' updated.", "success")

        if form.trigger_n8n.data:
            result = trigger_workflow(project, trigger_source="edit_hook")
            if result["ok"]:
                flash("n8n automation workflow triggered.", "info")
            else:
                flash(
                    f"Changes saved, but n8n webhook could not be reached: {result['error']}",
                    "warning",
                )

        return redirect(url_for("projects.detail", project_id=project.id))

    return render_template(
        "projects/edit.html",
        form=form,
        project=project,
        industries=COMMON_INDUSTRIES,
    )


@projects_bp.route("/<int:project_id>/status", methods=["POST"])
@login_required
def change_status(project_id: int):
    project = db.get_or_404(Project, project_id)
    new_status = request.form.get("status", "").strip()

    if new_status not in PROJECT_STATUSES:
        flash("Invalid project status selected.", "danger")
        return redirect(url_for("projects.detail", project_id=project.id))

    old_status = project.status
    project.status = new_status
    db.session.commit()
    flash(
        f"Status for '{project.company_name}' updated from {old_status} to {new_status}.",
        "success",
    )

    next_url = request.form.get("next")
    if next_url and next_url.startswith("/"):
        return redirect(next_url)
    return redirect(url_for("projects.detail", project_id=project.id))


@projects_bp.route("/<int:project_id>/trigger", methods=["POST"])
@login_required
def trigger(project_id: int):
    project = db.get_or_404(Project, project_id)
    result = trigger_workflow(project, trigger_source="manual")

    if result["ok"]:
        flash(
            f"n8n workflow dispatched for {project.company_name} (Execution #{result['execution'].id}).",
            "success",
        )
    else:
        flash(
            f"Execution #{result['execution'].id} recorded as failed — n8n unreachable ({result['error']}).",
            "warning",
        )

    next_url = request.form.get("next")
    if next_url and next_url.startswith("/"):
        return redirect(next_url)
    return redirect(url_for("projects.detail", project_id=project.id))


@projects_bp.route("/<int:project_id>/delete", methods=["POST"])
@login_required
def delete(project_id: int):
    project = db.get_or_404(Project, project_id)
    company_name = project.company_name
    intake_id = project.intake_id

    db.session.delete(project)
    db.session.commit()
    flash(f"Project '{company_name}' ({intake_id}) has been deleted.", "info")
    return redirect(url_for("projects.index"))
