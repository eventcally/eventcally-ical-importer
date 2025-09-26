import os
from functools import wraps

from authlib.integrations.base_client.errors import OAuthError
from flask import Flask, abort, g, redirect, request, session, url_for


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
        import datetime

        from project import current_user, db, oauth
        from project.dateutils import is_datetime_older_than_seconds

        if not current_user:
            return redirect(url_for("login"))

        if is_datetime_older_than_seconds(current_user.last_token_check, 60):
            try:
                oauth.eventcally.userinfo()
            except OAuthError:
                session.pop("user_id", None)

                if request.headers.get("X-Requested-With") == "Ajax":
                    abort(401)
                else:
                    return redirect(url_for("login"))

            current_user.last_token_check = datetime.datetime.utcnow()
            db.session.commit()

        if is_datetime_older_than_seconds(current_user.last_app_installations_sync, 60):
            load_user_app_installations()

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


def load_app_installations():
    import datetime

    from project import db, eventcally_app_id, oauth, oauth_kid, oauth_private_key
    from project.api_client import ApiClient
    from project.json_client import JsonClient
    from project.models import AppInstallation

    api_client = ApiClient(
        JsonClient(
            oauth.eventcally,
            oauth_private_key=oauth_private_key,
            oauth_kid=oauth_kid,
            app_id=eventcally_app_id,
        )
    )

    settings = get_or_create_settings()
    ec_app_installations = api_client.get_app_installations(
        settings.last_app_installations_sync
    )

    for ec_installation in ec_app_installations:
        eventcally_id = str(ec_installation["id"])
        app_installation = AppInstallation.query.filter(
            AppInstallation.eventcally_id == eventcally_id
        ).first()

        if not app_installation:
            app_installation = AppInstallation()
            app_installation.eventcally_id = eventcally_id
            db.session.add(app_installation)

        app_installation.permissions = ",".join(ec_installation["permissions"])
        app_installation.organization_id = str(ec_installation["organization"]["id"])
        app_installation.organization_name = ec_installation["organization"]["name"]

    settings.last_app_installations_sync = datetime.datetime.utcnow()
    db.session.commit()


def load_user_app_installations():
    import datetime

    from project import db, oauth
    from project.api_client import ApiClient
    from project.json_client import JsonClient
    from project.models import AppInstallation

    user = get_user()
    api_client = ApiClient(
        JsonClient(
            oauth.eventcally,
            user=user,
        )
    )
    ec_app_installations = api_client.get_user_app_installations()
    ec_app_installation_ids = session["user_app_installation_ids"] = [
        str(i["id"]) for i in ec_app_installations
    ]

    app_installations = AppInstallation.query.filter(
        AppInstallation.eventcally_id.in_(ec_app_installation_ids)
    ).all()

    if len(app_installations) < len(ec_app_installation_ids):
        load_app_installations()
        app_installations = AppInstallation.query.filter(
            AppInstallation.eventcally_id.in_(ec_app_installation_ids)
        ).all()

    user.app_installations = app_installations
    user.last_app_installations_sync = datetime.datetime.utcnow()
    db.session.commit()


def get_or_create_settings():
    from project import db
    from project.models import Settings

    settings = Settings.query.first()

    if not settings:
        settings = Settings()
        db.session.add(settings)

    return settings
