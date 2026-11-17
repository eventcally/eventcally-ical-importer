import pytest


def test_shells_need_a_login(client, seeder):
    _, _, configuration_id = seeder.setup_base()

    for url in ("/configurations", f"/configurations/{configuration_id}"):
        response = client.get(url)
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/login")


def test_shell_shows_the_legal_links(client, seeder, utils):
    user_id, _, _ = seeder.setup_base()
    utils.login(user_id)

    html = client.get("/configurations").get_data(as_text=True)

    for path in ("tos", "legal_notice", "contact", "privacy"):
        assert f'href="http://eventcally.test/{path}"' in html


def test_shell_hands_the_boot_data_to_the_app(client, seeder, utils):
    user_id, _, _ = seeder.setup_base()
    utils.login(user_id)

    response = client.get("/configurations")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert '<div id="app"></div>' in html
    assert "bootstrap.5.3.3.min.css" in html
    assert "user@test.de" in html
    boot = utils.get_boot()
    assert boot["bffBase"] == "/bff"
    assert boot["user"] == {"email": "user@test.de"}
    assert boot["loginUrl"] == "/login"
    assert boot["locale"] in ("de", "en")
    assert boot["csrfToken"]
    assert boot["eventcallySiteName"] == "EventCally"


def test_shells_keep_the_page_urls(client, seeder, utils):
    user_id, _, configuration_id = seeder.setup_base()
    run_id = seeder.create_run(configuration_id)
    utils.login(user_id)

    for url in (
        f"/configurations/{configuration_id}",
        f"/configurations/{configuration_id}/update",
        f"/configurations/{configuration_id}/runs/{run_id}",
    ):
        assert client.get(url).status_code == 200, url


def test_shells_answer_404_for_foreign_objects(client, seeder, utils):
    user_id, _, configuration_id = seeder.setup_base()
    other_installation_id = seeder.create_app_installation(name="Other")
    foreign_id = seeder.create_configuration(other_installation_id)
    foreign_run_id = seeder.create_run(foreign_id)
    utils.login(user_id)

    for url in (
        f"/configurations/{foreign_id}",
        f"/configurations/{foreign_id}/update",
        f"/configurations/{foreign_id}/runs/{foreign_run_id}",
        f"/configurations/{configuration_id}/runs/{foreign_run_id}",
        "/configurations/999",
    ):
        assert client.get(url).status_code == 404, url


@pytest.mark.parametrize(
    "method,url",
    [
        ("get", "/configurations/create/{installation}"),
        ("put", "/configurations/{configuration}/update/js/save"),
        ("delete", "/configurations/{configuration}/update/js/delete"),
        ("post", "/configurations/{configuration}/update/js/preview"),
        ("post", "/configurations/{configuration}/update/js/import"),
    ],
)
def test_legacy_form_urls_are_gone(client, seeder, utils, method, url):
    user_id, installation_id, configuration_id = seeder.setup_base()
    utils.login(user_id)

    response = getattr(client, method)(
        url.format(installation=installation_id, configuration=configuration_id)
    )

    assert response.status_code == 404
