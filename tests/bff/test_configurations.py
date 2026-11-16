FORM = {
    "title": "Sitzungen",
    "identifier_tag": "tag-1",
    "url": "https://example.com/feed.ics",
    "name": '{{ standard["name"] }}',
    "organizer_name": "Stadt Goslar",
    "place_name": '{{ standard["place_name"] }}',
    "start": '{{ standard["start"] }}',
    "description": '{{ standard["description"] }}',
    "end": '{{ standard["end"] }}',
    "allday": '{{ standard["allday"] }}',
    "external_link": "",
    "tags": "",
    "categories": "",
    "photo_url": "",
    "photo_copyright_text": "",
}


def test_list(client, seeder, utils):
    user_id, installation_id, configuration_id = seeder.setup_base(title="Mine")
    other_installation_id = seeder.create_app_installation(name="Other")
    seeder.create_configuration(other_installation_id, title="Foreign")
    utils.login(user_id)

    response = client.get("/bff/configurations")

    assert response.status_code == 200
    assert response.json == {
        "configurations": [
            {
                "id": configuration_id,
                "title": "Mine",
                "organization_name": "Organization",
            }
        ],
        "app_installations": [
            {"id": installation_id, "organization_name": "Organization"}
        ],
    }


def test_create(client, seeder, utils, app, db):
    from project.models import Configuration

    user_id, installation_id, _ = seeder.setup_base()
    utils.login(user_id)

    response = utils.post_json(
        "/bff/configurations", {"app_installation_id": installation_id}
    )

    assert response.status_code == 201
    with app.app_context():
        configuration = db.session.get(Configuration, response.json["id"])
        assert configuration.app_installation_id == installation_id
        assert configuration.name == '{{ standard["name"] }}'
        assert configuration.identifier_tag


def test_create_for_foreign_installation(client, seeder, utils):
    user_id, _, _ = seeder.setup_base()
    other_installation_id = seeder.create_app_installation(name="Other")
    utils.login(user_id)

    response = utils.post_json(
        "/bff/configurations", {"app_installation_id": other_installation_id}
    )

    assert response.status_code == 404


def test_create_validates_the_body(client, seeder, utils):
    user_id, _, _ = seeder.setup_base()
    utils.login(user_id)

    response = utils.post_json("/bff/configurations", {})

    assert response.status_code == 422
    assert response.json["errors"][0]["loc"] == ["app_installation_id"]


def test_read(client, seeder, utils, app, db):
    from project.models import Configuration, ImportedEvent

    user_id, _, configuration_id = seeder.setup_base(
        title="Mine", url="https://example.com/feed.ics"
    )
    run_id = seeder.create_run(configuration_id)
    with app.app_context():
        configuration = db.session.get(Configuration, configuration_id)
        configuration.imported_events.append(
            ImportedEvent(vevent_uid="uid-1", eventcally_event_id="12", event={"a": 1})
        )
        db.session.commit()
    utils.login(user_id)

    response = client.get(f"/bff/configurations/{configuration_id}")

    assert response.status_code == 200
    data = response.json
    assert data["title"] == "Mine"
    assert data["url"] == "https://example.com/feed.ics"
    assert data["organization_name"] == "Organization"
    assert data["runs"][0]["id"] == run_id
    assert data["runs"][0]["status"] == "success"
    assert data["runs"][0]["new_event_count"] == 0
    # naive UTC in the database, explicit offset on the wire
    assert data["runs"][0]["created_at"].endswith("Z")
    assert data["imported_events"] == [
        {
            "id": 1,
            "vevent_uid": "uid-1",
            "eventcally_event_id": "12",
            "eventcally_url": "http://eventcally.test/event/12",
            "event": {"a": 1},
        }
    ]


def test_read_foreign_configuration(client, seeder, utils):
    user_id, _, _ = seeder.setup_base()
    other_installation_id = seeder.create_app_installation(name="Other")
    foreign_id = seeder.create_configuration(other_installation_id)
    utils.login(user_id)

    assert client.get(f"/bff/configurations/{foreign_id}").status_code == 404
    assert client.get(f"/bff/configurations/{foreign_id}/form").status_code == 404
    assert utils.put_json(f"/bff/configurations/{foreign_id}", FORM).status_code == 404
    assert (
        utils.post_json(f"/bff/configurations/{foreign_id}/delete").status_code == 404
    )


def test_form(client, seeder, utils):
    user_id, _, configuration_id = seeder.setup_base(identifier_tag="tag-1")
    utils.login(user_id)

    response = client.get(f"/bff/configurations/{configuration_id}/form")

    assert response.status_code == 200
    data = response.json
    assert data["organization_name"] == "Organization"
    assert data["values"]["title"] is None
    assert data["values"]["identifier_tag"] == "tag-1"
    assert data["values"]["start"] == '{{ standard["start"] }}'
    assert data["mapper_fields"][0] == "name"
    assert set(data["mapper_fields"]) < set(data["values"])


def test_update(client, seeder, utils, app, db):
    from project.models import Configuration

    user_id, _, configuration_id = seeder.setup_base()
    utils.login(user_id)

    response = utils.put_json(f"/bff/configurations/{configuration_id}", FORM)

    assert response.status_code == 204
    with app.app_context():
        configuration = db.session.get(Configuration, configuration_id)
        assert configuration.title == "Sitzungen"
        assert configuration.url == "https://example.com/feed.ics"
        assert configuration.organizer_name == "Stadt Goslar"
        assert configuration.external_link == ""


def test_update_refuses_unknown_fields(client, seeder, utils, app, db):
    from project.models import Configuration

    user_id, installation_id, configuration_id = seeder.setup_base()
    other_installation_id = seeder.create_app_installation(name="Other")
    utils.login(user_id)

    response = utils.put_json(
        f"/bff/configurations/{configuration_id}",
        {**FORM, "app_installation_id": other_installation_id},
    )

    assert response.status_code == 422
    with app.app_context():
        configuration = db.session.get(Configuration, configuration_id)
        assert configuration.app_installation_id == installation_id


def test_update_requires_the_identifier_tag(client, seeder, utils):
    user_id, _, configuration_id = seeder.setup_base()
    utils.login(user_id)

    response = utils.put_json(
        f"/bff/configurations/{configuration_id}", {**FORM, "identifier_tag": ""}
    )

    assert response.status_code == 422
    assert response.json["errors"][0]["loc"] == ["identifier_tag"]


def test_delete(client, seeder, utils, app, db):
    from project.models import Configuration, Run

    user_id, _, configuration_id = seeder.setup_base()
    seeder.create_run(configuration_id)
    utils.login(user_id)

    response = utils.post_json(f"/bff/configurations/{configuration_id}/delete")

    assert response.status_code == 204
    with app.app_context():
        assert db.session.get(Configuration, configuration_id) is None
        assert Run.query.count() == 0
