import json
from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import or_
from app.extensions import db
from app.forms import OutputForm
from app.models.output import OUTPUT_STATUSES, OUTPUT_TYPES, Output
from app.models.project import Project

outputs_bp = Blueprint("outputs", __name__, url_prefix="/outputs")


@outputs_bp.route("", methods=["GET"])
@outputs_bp.route("/", methods=["GET"])
@login_required
def index():
    search_query = request.args.get("q", "").strip()
    type_filter = request.args.get("output_type", "").strip()
    status_filter = request.args.get("status", "").strip()
    project_id = request.args.get("project_id", type=int)
    page = max(1, request.args.get("page", 1, type=int))
    per_page = current_app.config.get("ITEMS_PER_PAGE", 10)

    query = Output.query.join(Project, Output.project_id == Project.id)

    if search_query:
        like_pattern = f"%{search_query}%"
        query = query.filter(
            or_(
                Output.title.ilike(like_pattern),
                Output.summary.ilike(like_pattern),
                Output.content.ilike(like_pattern),
                Project.company_name.ilike(like_pattern),
                Project.intake_id.ilike(like_pattern),
            )
        )

    if type_filter and type_filter in OUTPUT_TYPES:
        query = query.filter(Output.output_type == type_filter)

    if status_filter and status_filter in OUTPUT_STATUSES:
        query = query.filter(Output.status == status_filter)

    if project_id:
        query = query.filter(Output.project_id == project_id)

    pagination = (
        query.options(db.contains_eager(Output.project), db.joinedload(Output.execution))
        .order_by(Output.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    projects_list = Project.query.order_by(Project.company_name.asc()).all()

    return render_template(
        "outputs/index.html",
        outputs=pagination.items,
        pagination=pagination,
        search_query=search_query,
        type_filter=type_filter,
        status_filter=status_filter,
        project_id=project_id,
        output_types=OUTPUT_TYPES,
        output_statuses=OUTPUT_STATUSES,
        projects_list=projects_list,
    )


@outputs_bp.route("/<int:output_id>", methods=["GET"])
@login_required
def detail(output_id: int):
    output = db.get_or_404(Output, output_id)
    return render_template(
        "outputs/detail.html",
        output=output,
        output_statuses=OUTPUT_STATUSES,
    )


@outputs_bp.route("/project/<int:project_id>/create", methods=["POST"])
@login_required
def create_for_project(project_id: int):
    project = db.get_or_404(Project, project_id)
    form = OutputForm()

    if form.validate_on_submit():
        raw_json = (form.data_json.data or "").strip()
        parsed_data = json.loads(raw_json) if raw_json else {}

        latest_execution = project.executions[0] if project.executions else None
        output = Output(
            project_id=project.id,
            execution_id=latest_execution.id if latest_execution else None,
            title=form.title.data.strip(),
            output_type=form.output_type.data,
            status=form.status.data,
            summary=(form.summary.data or "").strip() or None,
            content=(form.content.data or "").strip() or None,
            data=parsed_data,
        )
        db.session.add(output)
        db.session.commit()
        flash(f"Output '{output.title}' added to {project.company_name}.", "success")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", "danger")

    return redirect(url_for("projects.detail", project_id=project.id))


@outputs_bp.route("/<int:output_id>/status", methods=["POST"])
@login_required
def update_status(output_id: int):
    output = db.get_or_404(Output, output_id)
    new_status = request.form.get("status", "").strip().lower()

    if new_status not in OUTPUT_STATUSES:
        flash("Invalid output status selected.", "danger")
        return redirect(url_for("outputs.detail", output_id=output.id))

    output.status = new_status
    db.session.commit()
    flash(f"Output '{output.title}' status updated to '{new_status}'.", "success")
    return redirect(url_for("outputs.detail", output_id=output.id))


@outputs_bp.route("/<int:output_id>/delete", methods=["POST"])
@login_required
def delete(output_id: int):
    output = db.get_or_404(Output, output_id)
    project_id = output.project_id
    title = output.title

    db.session.delete(output)
    db.session.commit()
    flash(f"Output '{title}' deleted.", "info")

    next_url = request.form.get("next")
    if next_url and next_url.startswith("/"):
        return redirect(next_url)
    return redirect(url_for("projects.detail", project_id=project_id))
