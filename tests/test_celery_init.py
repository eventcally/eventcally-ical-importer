import io
import json
import logging
from types import SimpleNamespace

from celery.app.task import Context

from app_logging import bind_log_context, get_log_context, reset_log_context
from project.celery_init import (
    bind_task_log_context,
    pass_request_id,
    reset_task_log_context,
    setup_logger,
)


def test_celery_loggers_use_our_format(monkeypatch):
    logger = logging.getLogger("test.celery_logger")
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    logger.addHandler(handler)
    logger.propagate = False

    monkeypatch.setenv("LOG_FORMAT", "json")

    try:
        setup_logger(logger=logger)
        logger.warning("worker line")
    finally:
        logger.removeHandler(handler)

    assert json.loads(stream.getvalue())["event"] == "worker line"


def test_queued_task_carries_the_request_id():
    headers = {}
    pass_request_id(headers=headers)
    assert headers == {}

    tokens = bind_log_context(request_id="r1")
    try:
        pass_request_id(headers=headers)
        pass_request_id(headers=None)
    finally:
        reset_log_context(tokens)

    assert headers == {"request_id": "r1"}


def test_task_log_context():
    task = SimpleNamespace(name="project.test_task", request=Context(request_id="r2"))

    bind_task_log_context(task_id="t1", task=task)
    assert get_log_context() == {
        "task_id": "t1",
        "task_name": "project.test_task",
        "request_id": "r2",
    }

    reset_task_log_context(task=task)
    reset_task_log_context(task=task)
    assert get_log_context() == {}

    task.request = Context()
    bind_task_log_context(task_id="t2", task=task)
    assert "request_id" not in get_log_context()
    reset_task_log_context(task=task)
    assert get_log_context() == {}


def test_eager_task_keeps_the_request_context(app):
    from celery.signals import task_prerun

    from project.celery_tasks import delete_outdated_runs_task

    seen = {}
    tokens = bind_log_context(request_id="r3")

    def remember(**kwargs):
        seen.update(get_log_context())

    try:
        task_prerun.connect(remember, weak=False)
        try:
            delete_outdated_runs_task.apply()
        finally:
            task_prerun.disconnect(remember)

        assert get_log_context() == {"request_id": "r3"}
    finally:
        reset_log_context(tokens)

    assert seen["request_id"] == "r3"
    assert seen["task_name"] == delete_outdated_runs_task.name
    assert seen["task_id"]
