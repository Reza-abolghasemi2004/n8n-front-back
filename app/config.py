import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


def normalize_database_url(raw_url: str | None) -> str:
    """Ensure the PostgreSQL URL uses the psycopg v3 SQLAlchemy driver."""
    if not raw_url:
        pg_user = os.getenv("POSTGRES_USER", "agent_platform")
        pg_password = os.getenv("POSTGRES_PASSWORD", "CHANGE_ME")
        pg_host = os.getenv("POSTGRES_HOST", "postgres")
        pg_port = os.getenv("POSTGRES_PORT", "5432")
        pg_db = os.getenv("POSTGRES_DB", "agent_platform")
        return f"postgresql+psycopg://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"

    url = raw_url.strip()
    if url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url[len("postgres://") :]
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


class Config:
    """Base production-first configuration."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-fallback-change-in-production-immediately")
    FLASK_ENV = os.getenv("FLASK_ENV", "production")
    DEBUG = os.getenv("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")
    TESTING = False

    # PostgreSQL Database
    SQLALCHEMY_DATABASE_URI = normalize_database_url(os.getenv("DATABASE_URL"))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # Session & Cookie Security
    SESSION_COOKIE_NAME = "agent_platform_session"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() in (
        "1",
        "true",
        "yes",
    )
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)

    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600

    # n8n Integration
    N8N_BASE_URL = os.getenv("N8N_BASE_URL", "http://n8n:5678").rstrip("/")
    N8N_API_KEY = os.getenv("N8N_API_KEY", "")
    N8N_WEBHOOK_PATH = os.getenv("N8N_WEBHOOK_PATH", "/webhook/project-intake")
    N8N_TIMEOUT = int(os.getenv("N8N_TIMEOUT", "15"))

    # Pagination defaults
    ITEMS_PER_PAGE = int(os.getenv("ITEMS_PER_PAGE", "10"))


class DevelopmentConfig(Config):
    FLASK_ENV = "development"
    DEBUG = False
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False


class ProductionConfig(Config):
    FLASK_ENV = "production"
    DEBUG = False


class TestingConfig(Config):
    FLASK_ENV = "testing"
    TESTING = True
    DEBUG = False
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False


CONFIG_MAP = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": Config,
}
