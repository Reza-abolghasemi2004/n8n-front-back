from app.routes.auth import auth_bp
from app.routes.dashboard import dashboard_bp
from app.routes.executions import executions_bp
from app.routes.outputs import outputs_bp
from app.routes.projects import projects_bp

__all__ = [
    "auth_bp",
    "dashboard_bp",
    "projects_bp",
    "executions_bp",
    "outputs_bp",
]
