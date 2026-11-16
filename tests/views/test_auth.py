from urllib.parse import parse_qs, urlparse

METADATA = {
    "issuer": "http://eventcally.test",
    "authorization_endpoint": "http://eventcally.test/oauth/authorize",
    "token_endpoint": "http://eventcally.test/oauth/token",
    "userinfo_endpoint": "http://eventcally.test/oauth/userinfo",
}


def test_login_flow(client, app, db, requests_mock, mocker):
    from project.models import User

    requests_mock.get(
        "http://eventcally.test/.well-known/openid-configuration", json=METADATA
    )
    requests_mock.post(
        "http://eventcally.test/oauth/token",
        json={
            "token_type": "Bearer",
            "access_token": "access-1",
            "refresh_token": "refresh-1",
            "expires_in": 3600,
        },
    )
    requests_mock.get(
        "http://eventcally.test/oauth/userinfo",
        json={"sub": "42", "email": "new@test.de"},
    )
    sync = mocker.patch("project.views.auth.load_user_app_installations")
    mocker.patch("project.utils.load_user_app_installations")

    response = client.get("/login")

    assert response.status_code == 302
    location = urlparse(response.headers["Location"])
    assert location.path == "/oauth/authorize"
    query = parse_qs(location.query)
    assert query["client_id"] == ["client-id"]
    assert query["redirect_uri"] == ["http://localhost/authorize"]
    assert "organization.events:write" in query["scope"][0]

    response = client.get(f"/authorize?code=abc&state={query['state'][0]}")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/user/update_app_installations")
    with app.app_context():
        user = User.query.one()
        assert user.eventcally_id == "42"
        assert user.email == "new@test.de"
        assert user.access_token == "access-1"
        assert user.refresh_token == "refresh-1"
        assert user.expires_at
        assert user.locale in ("de", "en")

    # logged in: the sync runs and lands on the configurations
    response = client.get("/user/update_app_installations")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/configurations")
    sync.assert_called()

    response = client.get("/logout")
    assert response.status_code == 302
    assert client.get("/configurations").headers["Location"].endswith("/login")
