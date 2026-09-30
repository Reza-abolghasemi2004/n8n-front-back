from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from app.extensions import db, login_manager


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AdminUser(UserMixin, db.Model):
    """Single-role Administrator account for managing the platform."""

    __tablename__ = "admin_users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(150), nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    is_active_user = db.Column("is_active", db.Boolean, nullable=False, default=True)
    last_login_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    @property
    def is_active(self) -> bool:
        return bool(self.is_active_user)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def display_name(self) -> str:
        return self.full_name or self.username

    def __repr__(self) -> str:
        return f"<AdminUser {self.username}>"


@login_manager.user_loader
def load_user(user_id: str) -> AdminUser | None:
    try:
        return db.session.get(AdminUser, int(user_id))
    except (TypeError, ValueError):
        return None
