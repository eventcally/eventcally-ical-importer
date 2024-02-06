import os
from functools import wraps

from flask import Flask, g, redirect, session, url_for


def get_user():
    # Prevents circular import
    from project.models import User

    # Ensure has session
    if "user_id" not in session:
        if hasattr(g, "_cached_user"):
            del g._cached_user
        return None

    # If not cached - look it up and cache it
    if not hasattr(g, "_cached_user"):
        g._cached_user = User.query.filter(
            User.id == session.get("user_id", None)
        ).first()

        if not hasattr(g, "_cached_user"):
            session.clear()
            return None

    return g._cached_user


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        from project import current_user

        if not current_user:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return wrapper


def getenv_bool(name: str, default: str = "False"):
    return os.getenv(name, default).lower() in ("true", "1", "t")


def set_env_to_app(app: Flask, key: str, default: str = None):
    if key in os.environ and os.environ[key]:  # pragma: no cover
        app.config[key] = os.environ[key]
        return

    if default:
        app.config[key] = default
