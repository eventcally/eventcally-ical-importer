import json
import uuid

from flask import abort

from project.bff import bff_bp
from project.bff.configurations import apply_form, get_configuration_or_404
from project.bff.routing import bff_route
from project.bff.schemas import (
    ConfigurationForm,
    LogEntryItem,
    RunDetail,
    RunJob,
    RunJobStatus,
    RunPreview,
)


def _job_prefix(configuration_id: int) -> str:
    # A status poll only answers for the jobs of the configuration in the URL.
    return f"run-{configuration_id}-"


def _log_entries(run) -> list[LogEntryItem]:
    from project import app

    return [
        LogEntryItem(
            id=entry.id,
            created_at=entry.created_at,
            message=entry.message,
            type=entry.type,
            # A dry run is never stored: serialize the context like the JSONB column
            # would (dates as ISO strings).
            context=(
                json.loads(app.json.dumps(entry.context))
                if entry.context is not None
                else None
            ),
        )
        for entry in run.log_entries
    ]


@bff_route(
    bff_bp,
    "/configurations/<int:id>/preview",
    method="POST",
    body=ConfigurationForm,
    response=RunPreview,
    summary="Dry run with the given (unsaved) form values",
)
def configuration_preview(id: int, body: ConfigurationForm):
    from project import db
    from project.ical_importer import IcalImporter

    configuration = get_configuration_or_404(id)

    with db.session.no_autoflush:
        apply_form(configuration, body)

        importer = IcalImporter()
        importer.dry = True
        importer.perform(configuration)

        run = importer.run
        result = RunPreview(
            **{
                name: getattr(run, name)
                for name in RunPreview.model_fields
                if name != "log_entries"
            },
            log_entries=_log_entries(run),
        )

    # The form values were only applied for the dry run.
    db.session.rollback()
    return result


@bff_route(
    bff_bp,
    "/configurations/<int:id>/run-jobs",
    method="POST",
    response=RunJob,
    status=202,
    summary="Start an import run in the background",
)
def run_job_create(id: int):
    from project.celery_tasks import perform_run_task

    configuration = get_configuration_or_404(id)
    job_id = _job_prefix(configuration.id) + uuid.uuid4().hex
    perform_run_task.apply_async((configuration.id,), task_id=job_id)
    return RunJob(id=job_id)


@bff_route(
    bff_bp,
    "/configurations/<int:id>/run-jobs/<job_id>",
    response=RunJobStatus,
)
def run_job_status(id: int, job_id: str):
    from project.celery_init import get_celery_poll_result

    configuration = get_configuration_or_404(id)

    if not job_id.startswith(_job_prefix(configuration.id)):
        abort(404)

    result = get_celery_poll_result(job_id)
    return RunJobStatus(ready=result["ready"], successful=result["successful"])


@bff_route(
    bff_bp,
    "/configurations/<int:id>/runs/<int:run_id>",
    response=RunDetail,
)
def run_read(id: int, run_id: int):
    from project.models import Run

    configuration = get_configuration_or_404(id)
    run = Run.query.filter(
        Run.id == run_id, Run.configuration_id == configuration.id
    ).first_or_404()

    return RunDetail(
        id=run.id,
        configuration_id=configuration.id,
        configuration_title=configuration.title,
        created_at=run.created_at,
        configuration_settings=run.configuration_settings,
        status=run.status,
        failure_event_count=run.failure_event_count,
        skipped_event_count=run.skipped_event_count,
        new_event_count=run.new_event_count,
        updated_event_count=run.updated_event_count,
        unchanged_event_count=run.unchanged_event_count,
        deleted_event_count=run.deleted_event_count,
        log_entries=_log_entries(run),
    )
