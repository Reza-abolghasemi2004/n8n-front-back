from datetime import datetime, timezone
from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import or_
from app.extensions import db
from app.integrations.n8n import sync_execution_status
from app.models.execution import EXECUTION_STATUSES, Execution
from app.models.project import Project

executions_bp = Blueprint("executions", __name__, url_prefix="/executions")


@executions_bp.route("", methods=["GET"])
@executions_bp.route("/", methods=["GET"])
@login_required
def index():
    search_query = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "").strip()
    project_id = request.args.get("project_id", type=int)
    page = max(1, request.args.get("page", 1, type=int))
    per_page = current_app.config.get("ITEMS_PER_PAGE", 10)

    query = Execution.query.join(Project, Execution.project_id == Project.id)

    if search_query:
        like_pattern = f"%{search_query}%"
        query = query.filter(
            or_(
                Execution.n8n_execution_id.ilike(like_pattern),
                Execution.workflow_name.ilike(like_pattern),
                Project.company_name.ilike(like_pattern),
                Project.intake_id.ilike(like_pattern),
            )
        )

    if status_filter and status_filter in EXECUTION_STATUSES:
        query = query.filter(Execution.status == status_filter)

    if project_id:
        query = query.filter(Execution.project_id == project_id)

    pagination = (
        query.options(db.contains_eager(Execution.project))
        .order_by(Execution.started_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    projects_list = Project.query.order_by(Project.company_name.asc()).all()

    return render_template(
        "executions/index.html",
        executions=pagination.items,
        pagination=pagination,
        search_query=search_query,
        status_filter=status_filter,
        project_id=project_id,
        statuses=EXECUTION_STATUSES,
        projects_list=projects_list,
    )


@executions_bp.route("/<int:execution_id>", methods=["GET"])
@login_required
def detail(execution_id: int):
    execution = db.get_or_404(Execution, execution_id)
    return render_template(
        "executions/detail.html",
        execution=execution,
        statuses=EXECUTION_STATUSES,
    )


@executions_bp.route("/<int:execution_id>/sync", methods=["POST"])
@login_required
def sync(execution_id: int):
    execution = db.get_or_404(Execution, execution_id)
    result = sync_execution_status(execution)

    if result["ok"]:
        flash(
            f"Execution #{execution.id} synced with n8n (status: {execution.status}).",
            "success",
        )
    else:
        flash(f"Could not sync execution from n8n: {result['error']}", "warning")

    return redirect(url_for("executions.detail", execution_id=execution.id))


@executions_bp.route("/<int:execution_id>/status", methods=["POST"])
@login_required
def update_status(execution_id: int):
    execution = db.get_or_404(Execution, execution_id)
    new_status = request.form.get("status", "").strip().lower()

    if new_status not in EXECUTION_STATUSES:
        flash("Invalid execution status.", "danger")
        return redirect(url_for("executions.detail", execution_id=execution.id))

    execution.status = new_status
    if new_status in ("success", "failed", "canceled") and not execution.finished_at:
        execution.finished_at = datetime.now(timezone.utc)
    elif new_status in ("running", "queued"):
        execution.finished_at = None

    db.session.commit()
    flash(f"Execution #{execution.id} status updated to '{new_status}'.", "success")
    return redirect(url_for("executions.detail", execution_id=execution.id))
