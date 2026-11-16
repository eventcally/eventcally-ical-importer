def test_index_shows_the_login_button(client):
    response = client.get("/")

    assert response.status_code == 200
    assert 'href="/login"' in response.get_data(as_text=True)


def test_index_redirects_a_user_to_the_configurations(client, seeder, utils):
    user_id, _, _ = seeder.setup_base()
    utils.login(user_id)

    response = client.get("/")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/configurations")


def test_up(client, monkeypatch):
    monkeypatch.setenv("APP_TAGS", "1.2.3,1.2")

    response = client.get("/up")

    assert response.status_code == 200
    assert response.json == {"status": "OK", "tag-names": ["1.2.3", "1.2"]}


def test_index_is_translated(client):
    german = client.get("/", headers={"Accept-Language": "de"}).get_data(as_text=True)
    english = client.get("/", headers={"Accept-Language": "en"}).get_data(as_text=True)

    assert "Mit EventCally anmelden" in german
    assert "Login with EventCally" in english
