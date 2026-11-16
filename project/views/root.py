import os

from flask import (
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from sqlalchemy import text

from project import app, current_user, db


@app.route("/")
def index():
    if current_user:
        return redirect(url_for("configurations"))

    return render_template("index.html")


@app.route("/favicon.ico")
def favicon_ico():
    return send_from_directory(app.static_folder, request.path[1:])


@app.route("/up")
def up():
    """Health check (the compose deployment curls it): database and, if used, the broker."""
    from project import celery

    with db.engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    if app.config.get("REDIS_URL"):  # pragma: no cover
        celery.control.ping()

    tags = os.getenv("APP_TAGS", "")

    return jsonify(
        {
            "status": "OK",
            "tag-names": [tag for tag in tags.split(",") if tag],
        }
    )
