from flask import redirect, render_template, request, url_for

from project import app, current_user, db
from project.models import Configuration, Run
from project.utils import login_required


@app.route("/configurations")
@login_required
def configurations():
    return render_template("configurations/index.html")


@app.route("/configurations/create", methods=("GET", "POST"))
@login_required
def configurations_create():
    configuration = Configuration()
    configuration.user_id = current_user.id

    db.session.add(configuration)
    db.session.commit()

    return redirect(url_for("configurations_update", id=configuration.id))


@app.route("/configurations/<id>")
@login_required
def configuration(id):
    configuration = Configuration.query.filter(
        Configuration.id == id,
        Configuration.user_id == current_user.id,
    ).first_or_404(id)

    return render_template(
        "configurations/read.html",
        configuration=configuration,
    )


@app.route("/configurations/<configuration_id>/runs/<run_id>")
@login_required
def run(configuration_id, run_id):
    run = Run.query.get_or_404(run_id)

    configuration = Configuration.query.filter(
        Configuration.id == configuration_id,
        Configuration.user_id == current_user.id,
    ).first_or_404(id)

    return render_template(
        "runs/read.html",
        configuration=configuration,
        run=run,
    )


@app.route("/configurations/<id>/update")
@login_required
def configurations_update(id):
    configuration = Configuration.query.filter(
        Configuration.id == id,
        Configuration.user_id == current_user.id,
    ).first_or_404(id)

    return render_template(
        "configurations/update.html",
        configuration=configuration,
    )


@app.route("/configurations/<id>/update/js/save", methods=("PUT",))
@login_required
def configurations_update_js_save(id):
    configuration = Configuration.query.filter(
        Configuration.id == id,
        Configuration.user_id == current_user.id,
    ).first_or_404(id)

    configuration.update_with_kwargs(**request.form)
    db.session.commit()

    return ""


@app.route("/configurations/<id>/update/js/reset", methods=("POST",))
@login_required
def configurations_update_js_reset(id):
    configuration = Configuration.query.filter(
        Configuration.id == id,
        Configuration.user_id == current_user.id,
    ).first_or_404(id)

    configuration.imported_events = None
    db.session.commit()

    return ""


@app.route("/configurations/<id>/update/js/delete", methods=("DELETE",))
@login_required
def configurations_update_js_delete(id):
    configuration = Configuration.query.filter(
        Configuration.id == id,
        Configuration.user_id == current_user.id,
    ).first_or_404(id)

    db.session.delete(configuration)
    db.session.commit()

    return ""


@app.route("/configurations/<id>/update/js/preview", methods=["POST"])
@login_required
def configurations_update_js_preview(id):
    from project.api import RunSchema
    from project.ical_importer import IcalImporter

    configuration = Configuration.query.filter(
        Configuration.id == id,
        Configuration.user_id == current_user.id,
    ).first_or_404(id)

    for attr in Configuration._mapper_attrs:
        if attr in request.form:
            value = request.form.get(attr)
            setattr(configuration, attr, value)

    configuration.organization_id = request.form.get("organization_id")
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

    configuration = Configuration.query.filter(
        Configuration.id == id,
        Configuration.user_id == current_user.id,
    ).first_or_404(id)

    if "poll" in request.args:
        return get_celery_poll_result(request.args["poll"])

    result = perform_run_task.delay(configuration.id)
    return {"id": result.id}
