from celery import group
from celery.schedules import crontab

from project import celery


@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(crontab(minute=0, hour="*/8"), schedule_runs_task)
    sender.add_periodic_task(crontab(hour=0, minute=30), delete_outdated_runs_task)


@celery.task(
    acks_late=True,
    reject_on_worker_lost=True,
)
def schedule_runs_task():
    from project.models import Configuration

    configurations = Configuration.query.all()

    if not configurations:
        return

    group(perform_run_task.s(c.id) for c in configurations).delay()


@celery.task(
    acks_late=True,
    reject_on_worker_lost=True,
)
def perform_run_task(id):
    from project import db
    from project.ical_importer import IcalImporter
    from project.models import Configuration

    configuration = Configuration.query.get(id)

    if not configuration:
        return

    importer = IcalImporter()
    importer.dry = False
    importer.perform(configuration)

    db.session.commit()


@celery.task(
    acks_late=True,
    reject_on_worker_lost=True,
)
def delete_outdated_runs_task():
    import datetime

    from project import db
    from project.models import Run

    due = datetime.datetime.utcnow() - datetime.timedelta(days=3)
    Run.query.filter(Run.created_at < due).delete()
    db.session.commit()
