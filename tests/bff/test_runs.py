from pathlib import Path

from tests.bff.test_configurations import FORM

ICAL = (Path(__file__).parent.parent / "goslar-sitzung.ical").read_text()


def test_preview(client, seeder, utils, app, db, requests_mock):
    from project.models import Configuration, Run

    user_id, _, configuration_id = seeder.setup_base(title="Before")
    utils.login(user_id)
    requests_mock.get("https://example.com/feed.ics", text=ICAL)

    response = utils.post_json(
        f"/bff/configurations/{configuration_id}/preview",
        {**FORM, "organizer_name": 'Stadt {{ standard["place_name"] }}'},
    )

    assert response.status_code == 200
    data = response.json
    assert data["status"] == "success"
    assert len(data["log_entries"]) == 84
    entry = data["log_entries"][0]
    assert entry["type"] == "vevent"
    assert entry["id"] is None
    context = entry["context"]
    assert context["vevent"].startswith("BEGIN:VEVENT")
    assert context["event"]["organizer_name"].startswith("Stadt ")
    assert context["errors"] == []
    # dates are serialized like in a stored run
    assert isinstance(context["standard"]["start"], str)

    # a dry run stores nothing, not even the form values
    with app.app_context():
        assert db.session.get(Configuration, configuration_id).title == "Before"
        assert Run.query.count() == 0


def test_preview_reports_template_errors(client, seeder, utils, requests_mock):
    user_id, _, configuration_id = seeder.setup_base()
    utils.login(user_id)
    requests_mock.get("https://example.com/feed.ics", text=ICAL)

    response = utils.post_json(
        f"/bff/configurations/{configuration_id}/preview",
        {**FORM, "name": "{{ broken"},
    )

    assert response.status_code == 200
    assert response.json["status"] == "failure"
    assert response.json["failure_event_count"] == 84
    assert response.json["log_entries"][0]["context"]["errors"][0]["key"] == "name"


def test_preview_with_unreachable_url(client, seeder, utils, requests_mock):
    user_id, _, configuration_id = seeder.setup_base()
    utils.login(user_id)
    requests_mock.get("https://example.com/feed.ics", exc=ConnectionError("down"))

    response = utils.post_json(f"/bff/configurations/{configuration_id}/preview", FORM)

    assert response.status_code == 200
    assert response.json["status"] == "failure"
    assert "Error loading url" in response.json["log_entries"][0]["message"]


def test_run_job(client, seeder, utils, mocker):
    user_id, _, configuration_id = seeder.setup_base()
    utils.login(user_id)
    apply_async = mocker.patch("project.celery_tasks.perform_run_task.apply_async")

    response = utils.post_json(f"/bff/configurations/{configuration_id}/run-jobs")

    assert response.status_code == 202
    job_id = response.json["id"]
    assert job_id.startswith(f"run-{configuration_id}-")
    apply_async.assert_called_once_with((configuration_id,), task_id=job_id)

    poll = mocker.patch(
        "project.celery_init.get_celery_poll_result",
        return_value={"ready": True, "successful": True, "value": None},
    )
    response = client.get(f"/bff/configurations/{configuration_id}/run-jobs/{job_id}")

    assert response.status_code == 200
    assert response.json == {"ready": True, "successful": True}
    poll.assert_called_once_with(job_id)


def test_run_job_status_only_for_own_jobs(client, seeder, utils, mocker):
    user_id, installation_id, configuration_id = seeder.setup_base()
    other_id = seeder.create_configuration(installation_id)
    utils.login(user_id)
    poll = mocker.patch("project.celery_init.get_celery_poll_result")

    response = client.get(
        f"/bff/configurations/{configuration_id}/run-jobs/run-{other_id}-abc"
    )

    assert response.status_code == 404
    poll.assert_not_called()


def test_run_read(client, seeder, utils):
    user_id, _, configuration_id = seeder.setup_base(title="Mine")
    run_id = seeder.create_run(
        configuration_id, configuration_settings={"url": "https://example.com"}
    )
    utils.login(user_id)

    response = client.get(f"/bff/configurations/{configuration_id}/runs/{run_id}")

    assert response.status_code == 200
    data = response.json
    assert data["configuration_title"] == "Mine"
    assert data["configuration_settings"] == {"url": "https://example.com"}
    assert data["status"] == "success"
    assert data["unchanged_event_count"] == 0
    assert data["log_entries"][0]["message"] == "Event importiert"
    assert data["log_entries"][0]["context"] == {"a": 1}
    assert data["log_entries"][0]["created_at"].endswith("Z")


def test_run_read_of_another_configuration(client, seeder, utils):
    user_id, installation_id, configuration_id = seeder.setup_base()
    other_installation_id = seeder.create_app_installation(name="Other")
    foreign_id = seeder.create_configuration(other_installation_id)
    foreign_run_id = seeder.create_run(foreign_id)
    utils.login(user_id)

    # neither through the foreign configuration nor through an own one
    assert (
        client.get(
            f"/bff/configurations/{foreign_id}/runs/{foreign_run_id}"
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"/bff/configurations/{configuration_id}/runs/{foreign_run_id}"
        ).status_code
        == 404
    )


def test_preview_reads_a_feed_with_a_bare_carriage_return(
    client, seeder, utils, requests_mock
):
    # e.g. https://oveda.de/organizations/<id>/ical with such a description
    feed = "\r\n".join(
        [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//test//",
            "BEGIN:VEVENT",
            "UID:1@test",
            "DTSTART:20261019T080000Z",
            "SUMMARY:Spaziergang",
            "DESCRIPTION:Start: 10.00 Uhr\r..",
            "END:VEVENT",
            "END:VCALENDAR",
            "",
        ]
    )
    user_id, _, configuration_id = seeder.setup_base()
    utils.login(user_id)
    requests_mock.get("https://example.com/feed.ics", text=feed)

    response = utils.post_json(f"/bff/configurations/{configuration_id}/preview", FORM)

    assert response.status_code == 200
    assert response.json["status"] == "success"
    context = response.json["log_entries"][0]["context"]
    assert context["standard"]["name"] == "Spaziergang"
    assert context["standard"]["description"] == "Start: 10.00 Uhr\n.."
