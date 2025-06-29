import logging
import os
from datetime import timedelta

import flask
from authlib.integrations.flask_client import OAuth
from flask import Flask
from flask_babel import Babel
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import MetaData
from werkzeug.local import LocalProxy

from project.utils import get_user, getenv_bool

current_user = LocalProxy(lambda: get_user())


# Create app
app = Flask(__name__)
app.config["SESSION_COOKIE_NAME"] = "session_eventcally_ical_importer"
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
app.config["REDIS_URL"] = os.getenv("REDIS_URL")
app.config["EVENTCALLY_URL"] = os.environ["EVENTCALLY_URL"]
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECURITY_REGISTERABLE"] = False
app.config["SECURITY_SEND_REGISTER_EMAIL"] = False
app.config["SECURITY_RECOVERABLE"] = False
app.config["SECURITY_CHANGEABLE"] = False
app.config["LANGUAGES"] = ["en", "de"]
app.config["SERVER_NAME"] = os.getenv("SERVER_NAME")
app.config["FLASK_DEBUG"] = getenv_bool("FLASK_DEBUG", "False")
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=180)

# Proxy handling
if os.getenv("PREFERRED_URL_SCHEME"):  # pragma: no cover
    app.config["PREFERRED_URL_SCHEME"] = os.getenv("PREFERRED_URL_SCHEME")

    if app.config["PREFERRED_URL_SCHEME"] == "https":
        app.config["SESSION_COOKIE_SECURE"] = True
        app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
        app.config["REMEMBER_COOKIE_SECURE"] = True
        app.config["REMEMBER_COOKIE_SAMESITE"] = "Lax"

from project.reverse_proxied import ReverseProxied

app.wsgi_app = ReverseProxied(app.wsgi_app)


# Celery
task_always_eager = "REDIS_URL" not in app.config or not app.config["REDIS_URL"]
app.config.update(
    CELERY_CONFIG={
        "broker_url": app.config["REDIS_URL"],
        "result_backend": app.config["REDIS_URL"],
        "result_expires": timedelta(hours=1),
        "timezone": "Europe/Berlin",
        "broker_transport_options": {
            "queue_order_strategy": "priority",
            "priority_steps": list(range(3)),
            "sep": ":",
            "queue_order_strategy": "priority",
        },
        "task_default_priority": 1,  # 0=high, 1=normal, 2=low priority
        "task_always_eager": task_always_eager,
    }
)


from project.celery import create_celery

celery = create_celery(app)

# Generate a nice key using secrets.token_urlsafe()
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "G_j9Hp_FuyNjATRBRjFCHQPUGWr5qcW4GTovFa6FrlI"
)


# Gunicorn logging
if __name__ != "__main__":
    gunicorn_logger = logging.getLogger("gunicorn.error")
    if gunicorn_logger.hasHandlers():
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)

# One line logging
from project.one_line_formatter import init_logger_with_one_line_formatter

init_logger_with_one_line_formatter(logging.getLogger())
init_logger_with_one_line_formatter(app.logger)


# i18n
from project.i18n import get_locale

app.config["BABEL_DEFAULT_LOCALE"] = "de"
app.config["BABEL_DEFAULT_TIMEZONE"] = "Europe/Berlin"
babel = Babel(app, locale_selector=get_locale)

# CRSF protection
csrf = CSRFProtect(app)
app.config["WTF_CSRF_CHECK_DEFAULT"] = False


# Create db
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
metadata = MetaData(naming_convention=convention)
db = SQLAlchemy(
    app, metadata=metadata, engine_options={"json_serializer": flask.json.dumps}
)
migrate = Migrate(app, db, render_as_batch=False)

# JSON
from project.json_encoder import CustomJsonProvider

app.json_provider_class = CustomJsonProvider


@app.context_processor
def get_context_processors():
    return dict(current_user=current_user)


# OAuth client
from project.models import User


def fetch_eventcally_token():
    return current_user.to_token() if current_user else None


def update_token(token, refresh_token=None, access_token=None):
    if refresh_token:
        user = User.query.filter(User.refresh_token == refresh_token).first()
    elif access_token:
        user = User.query.filter(User.access_token == access_token).first()
    else:
        return

    # update old token
    user.access_token = token["access_token"]
    user.refresh_token = token.get("refresh_token")
    user.expires_at = token["expires_at"]
    db.session.commit()


oauth = OAuth(app)
oauth.register(
    "eventcally",
    client_id=os.getenv("EVENTCALLY_CLIENT_ID"),
    client_secret=os.getenv("EVENTCALLY_CLIENT_SECRET"),
    api_base_url=app.config["EVENTCALLY_URL"],
    server_metadata_url=f"{app.config['EVENTCALLY_URL']}/.well-known/openid-configuration",
    client_kwargs={
        "scope": "profile organization.events:read organization.events:write organization.event_organizers:read organization.event_organizers:write organization.event_places:read organization.event_places:write"
    },
    fetch_token=fetch_eventcally_token,
    update_token=update_token,
)


import project.api
from project import celery_tasks, cli, jinja_filters

# Routes
from project.views import auth, configuration, root

if __name__ == "__main__":  # pragma: no cover
    app.run()
