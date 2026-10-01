from datetime import datetime, timezone
from urllib.parse import urlsplit
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func, or_
from app.extensions import db
from app.forms import LoginForm
from app.models.user import AdminUser

auth_bp = Blueprint("auth", __name__)


def _is_safe_next_url(target: str | None) -> bool:
    if not target:
        return False
    split = urlsplit(target)
    return not split.scheme and not split.netloc and target.startswith("/")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = LoginForm()
    if form.validate_on_submit():
        identifier = form.identifier.data.strip()
        user = AdminUser.query.filter(
            or_(
                func.lower(AdminUser.username) == identifier.lower(),
                func.lower(AdminUser.email) == identifier.lower(),
            )
        ).first()

        if user and user.is_active and user.check_password(form.password.data):
            user.last_login_at = datetime.now(timezone.utc)
            db.session.commit()
            session.permanent = bool(form.remember_me.data)
            login_user(user, remember=bool(form.remember_me.data))
            flash(f"Welcome back, {user.display_name}.", "success")

            next_page = request.args.get("next")
            if _is_safe_next_url(next_page):
                return redirect(next_page)
            return redirect(url_for("dashboard.index"))

        flash("Invalid credentials. Please verify your username/email and password.", "danger")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    flash("You have been signed out of the Admin Dashboard.", "info")
    return redirect(url_for("auth.login"))
