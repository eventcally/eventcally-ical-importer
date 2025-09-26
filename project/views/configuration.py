from flask import redirect, render_template, request, url_for

from project import app, current_user, db
from project.models import (
    AppInstallation,
    Configuration,
    Run,
    User,
    UserAppInstallations,
)
from project.utils import login_required


def get_configurations_query():
    return Configuration.query.join(
        AppInstallation, AppInstallation.id == Configuration.app_installation_id
    ).filter(AppInstallation.users.any(User.id == current_user.id))


@app.route("/configurations")
@login_required
def configurations():
    configurations = get_configurations_query().all()
    return render_template("configurations/index.html", configurations=configurations)


@app.route("/configurations/create/<app_installation_id>", methods=("GET", "POST"))
@login_required
def configurations_create(
    app_installation_id,
):
    UserAppInstallations.query.filter(
        UserAppInstallations.app_installation_id == app_installation_id
    ).filter(UserAppInstallations.user_id == current_user.id).first_or_404()

    configuration = Configuration()
    configuration.app_installation_id = app_installation_id

    db.session.add(configuration)
    db.session.commit()

    return redirect(url_for("configurations_update", id=configuration.id))


@app.route("/configurations/<id>")
@login_required
def configuration(id):
    configuration = (
        get_configurations_query().filter(Configuration.id == id).first_or_404()
    )

    return render_template(
        "configurations/read.html",
        configuration=configuration,
    )


@app.route("/configurations/<configuration_id>/runs/<run_id>")
@login_required
def run(configuration_id, run_id):
    run = Run.query.get_or_404(run_id)

    configuration = (
        get_configurations_query()
        .filter(Configuration.id == configuration_id)
        .first_or_404()
    )

    return render_template(
        "runs/read.html",
        configuration=configuration,
        run=run,
    )


@app.route("/configurations/<id>/update")
@login_required
def configurations_update(id):
    configuration = (
        get_configurations_query().filter(Configuration.id == id).first_or_404()
    )

    return render_template(
        "configurations/update.html",
        configuration=configuration,
    )


@app.route("/configurations/<id>/update/js/save", methods=("PUT",))
@login_required
def configurations_update_js_save(id):
    configuration = (
        get_configurations_query().filter(Configuration.id == id).first_or_404()
    )

    configuration.update_with_kwargs(**request.form)
    db.session.commit()

    return ""


@app.route("/configurations/<id>/update/js/delete", methods=("DELETE",))
@login_required
def configurations_update_js_delete(id):
    configuration = (
        get_configurations_query().filter(Configuration.id == id).first_or_404()
    )

    db.session.delete(configuration)
    db.session.commit()

    return ""


@app.route("/configurations/<id>/update/js/preview", methods=["POST"])
@login_required
def configurations_update_js_preview(id):
    from project.api import RunSchema
    from project.ical_importer import IcalImporter

    configuration = (
        get_configurations_query().filter(Configuration.id == id).first_or_404()
    )

    for attr in Configuration._mapper_attrs:
        if attr in request.form:
            value = request.form.get(attr)
            setattr(configuration, attr, value)

    configuration.url = request.form.get("url")

    importer = IcalImporter()
    importer.dry = True
    importer.perform(configuration)

    schema = RunSchema()
    result = schema.dump(importer.run)
    return result


@app.route("/configurations/<id>/update/js/import", methods=["GET", "POST"])
@login_required
def configurations_update_js_import(id):
    from project.celery import get_celery_poll_result
    from project.celery_tasks import perform_run_task

    configuration = (
        get_configurations_query().filter(Configuration.id == id).first_or_404()
    )

    if "poll" in request.args:
        return get_celery_poll_result(request.args["poll"])

    result = perform_run_task.delay(configuration.id)
    return {"id": result.id}
