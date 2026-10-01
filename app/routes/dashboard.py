from flask import Blueprint, jsonify, render_template
from flask_login import login_required
from sqlalchemy import func, text
from app.extensions import db
from app.models.execution import Execution
from app.models.output import Output
from app.models.project import ACTIVE_PROJECT_STATUSES, Project

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    total_projects = db.session.query(func.count(Project.id)).scalar() or 0
    active_projects = (
        db.session.query(func.count(Project.id))
        .filter(Project.status.in_(ACTIVE_PROJECT_STATUSES))
        .scalar()
        or 0
    )
    running_executions = (
        db.session.query(func.count(Execution.id))
        .filter(Execution.status.in_(("running", "queued")))
        .scalar()
        or 0
    )
    successful_executions = (
        db.session.query(func.count(Execution.id))
        .filter(Execution.status == "success")
        .scalar()
        or 0
    )
    failed_executions = (
        db.session.query(func.count(Execution.id))
        .filter(Execution.status == "failed")
        .scalar()
        or 0
    )
    total_outputs = db.session.query(func.count(Output.id)).scalar() or 0

    recent_projects = (
        Project.query.order_by(Project.created_at.desc()).limit(8).all()
    )
    recent_executions = (
        Execution.query.options(db.joinedload(Execution.project))
        .order_by(Execution.started_at.desc())
        .limit(8)
        .all()
    )
    recent_outputs = (
        Output.query.options(db.joinedload(Output.project))
        .order_by(Output.created_at.desc())
        .limit(5)
        .all()
    )

    stats = {
        "total_projects": total_projects,
        "active_projects": active_projects,
        "running_executions": running_executions,
        "successful_executions": successful_executions,
        "failed_executions": failed_executions,
        "total_outputs": total_outputs,
    }

    return render_template(
        "dashboard/index.html",
        stats=stats,
        recent_projects=recent_projects,
        recent_executions=recent_executions,
        recent_outputs=recent_outputs,
    )


@dashboard_bp.route("/health")
def health():
    """Healthcheck endpoint for Docker and reverse proxy monitoring."""
    try:
        db.session.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    status_code = 200 if db_ok else 503
    return jsonify({"status": "healthy" if db_ok else "degraded", "database": db_ok}), status_code
