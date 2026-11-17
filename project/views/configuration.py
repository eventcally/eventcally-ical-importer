from flask import render_template, url_for
from flask_babel import get_locale
from flask_wtf.csrf import generate_csrf

from project import app, current_user
from project.bff.configurations import get_configuration_or_404
from project.models import Run
from project.utils import login_required

# Every page here is a GET-only shell of the Vue app (frontend/src/apps/importer): the
# shell keeps the URL, the endpoint name and the login / 404 guard, the data comes
# from /bff.


def build_boot_data() -> dict:
    """The JSON the shell hands to the Vue app (`#boot`)."""
    return {
        "base": "/",
        "bffBase": "/bff",
        "locale": str(get_locale() or "en").split("_")[0],
        "csrfToken": generate_csrf(),
        "user": {"email": current_user.email} if current_user else None,
        "loginUrl": url_for("login"),
        "eventcallySiteName": app.config["EVENTCALLY_SITE_NAME"],
    }


def render_shell():
    return render_template("shell.html", entry="importer", boot=build_boot_data())


@app.route("/configurations")
@login_required
def configurations():
    return render_shell()


@app.route("/configurations/<int:id>")
@login_required
def configuration(id):
    get_configuration_or_404(id)
    return render_shell()


@app.route("/configurations/<int:configuration_id>/runs/<int:run_id>")
@login_required
def run(configuration_id, run_id):
    configuration = get_configuration_or_404(configuration_id)
    Run.query.filter(
        Run.id == run_id, Run.configuration_id == configuration.id
    ).first_or_404()
    return render_shell()


@app.route("/configurations/<int:id>/update")
@login_required
def configurations_update(id):
    get_configuration_or_404(id)
    return render_shell()
