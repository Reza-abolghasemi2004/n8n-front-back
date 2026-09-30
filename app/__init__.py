import json
import os
from datetime import date, datetime
from decimal import Decimal
from flask import Flask, render_template
from app.cli import register_cli_commands
from app.config import CONFIG_MAP, Config, normalize_database_url
from app.extensions import csrf, db, login_manager, migrate


def create_app(config_name: str | type | dict | None = None) -> Flask:
    """Application factory for the Automation Platform Admin Dashboard."""
    app = Flask(__name__)

    if config_name is None:
        env_name = os.getenv("FLASK_ENV", "production").lower()
        app.config.from_object(CONFIG_MAP.get(env_name, Config))
    elif isinstance(config_name, str):
        app.config.from_object(CONFIG_MAP.get(config_name.lower(), Config))
    elif isinstance(config_name, dict):
        app.config.from_object(Config)
        app.config.update(config_name)
    else:
        app.config.from_object(config_name)

    app.config["SQLALCHEMY_DATABASE_URI"] = normalize_database_url(
        app.config.get("SQLALCHEMY_DATABASE_URI")
    )

    # Initialize Flask extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Ensure models are imported for SQLAlchemy & Flask-Migrate
    from app import models  # noqa: F401

    # Register blueprints
    from app.routes import (
        auth_bp,
        dashboard_bp,
        executions_bp,
        outputs_bp,
        projects_bp,
    )

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(executions_bp)
    app.register_blueprint(outputs_bp)

    # Register Jinja template filters & globals
    _register_template_helpers(app)

    # Register error handlers & security headers
    _register_error_handlers(app)
    _register_security_headers(app)

    # Register CLI commands
    register_cli_commands(app)

    return app


def _register_template_helpers(app: Flask) -> None:
    @app.template_filter("datetime_fmt")
    def datetime_fmt(value: datetime | None) -> str:
        if not value:
            return "—"
        return value.strftime("%d/%m/%Y %I:%M%p").lstrip("0").replace(" 0", " ").lower()

    @app.template_filter("date_fmt")
    def date_fmt(value: date | datetime | None) -> str:
        if not value:
            return "—"
        return f"{value.day}/{value.month}/{value.year}"

    @app.template_filter("currency_fmt")
    def currency_fmt(value: Decimal | float | int | None) -> str:
        if value is None:
            return "$0.00"
        return f"${float(value):,.2f}"

    @app.template_filter("pretty_json")
    def pretty_json(value) -> str:
        if value is None:
            return "{}"
        try:
            return json.dumps(value, indent=2, default=str)
        except TypeError:
            return str(value)

    @app.template_filter("status_badge")
    def status_badge(status: str | None) -> str:
        mapping = {
            "New": "badge-info",
            "Validated": "badge-indigo",
            "Queued": "badge-amber",
            "In Progress": "badge-cyan",
            "Completed": "badge-emerald",
            "On Hold": "badge-slate",
            "Failed": "badge-rose",
        }
        return mapping.get(status or "", "badge-slate")

    @app.template_filter("priority_badge")
    def priority_badge(priority: str | None) -> str:
        mapping = {
            "Low": "badge-slate",
            "Medium": "badge-info",
            "High": "badge-amber",
            "Critical": "badge-rose",
        }
        return mapping.get(priority or "", "badge-slate")

    @app.template_filter("exec_badge")
    def exec_badge(status: str | None) -> str:
        mapping = {
            "queued": "badge-amber",
            "running": "badge-cyan badge-pulse",
            "success": "badge-emerald",
            "failed": "badge-rose",
            "canceled": "badge-slate",
        }
        return mapping.get((status or "").lower(), "badge-slate")

    @app.template_filter("output_badge")
    def output_badge(status: str | None) -> str:
        mapping = {
            "generated": "badge-info",
            "reviewed": "badge-amber",
            "approved": "badge-emerald",
            "archived": "badge-slate",
        }
        return mapping.get((status or "").lower(), "badge-slate")

    @app.context_processor
    def inject_globals():
        return {
            "n8n_base_url": app.config.get("N8N_BASE_URL", "http://n8n:5678"),
            "n8n_webhook_path": app.config.get("N8N_WEBHOOK_PATH", "/webhook/project-intake"),
        }


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template("errors/500.html"), 500


def _register_security_headers(app: Flask) -> None:
    @app.after_request
    def set_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        return response
