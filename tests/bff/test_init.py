import pytest
from flask_wtf.csrf import CSRFError


def test_anonymous_gets_json_401(client):
    response = client.get("/bff/configurations")

    assert response.status_code == 401
    assert response.json["name"] == "Unauthorized"


def test_unsafe_method_without_csrf_token(client, seeder, utils):
    user_id, installation_id, _ = seeder.setup_base()
    utils.login(user_id)

    response = client.post(
        "/bff/configurations", json={"app_installation_id": installation_id}
    )

    assert response.status_code == 400
    assert response.json["message"]


def test_safe_method_skips_csrf(app):
    from project.bff import _protect_unsafe_methods

    with app.test_request_context("/bff/configurations", method="GET"):
        assert _protect_unsafe_methods() is None

    with app.test_request_context("/bff/configurations", method="POST"):
        with pytest.raises(CSRFError):
            _protect_unsafe_methods()


def test_unknown_route_is_json_404(client, seeder, utils):
    user_id, _, _ = seeder.setup_base()
    utils.login(user_id)

    response = client.get("/bff/configurations/999")

    assert response.status_code == 404
    assert response.json["name"] == "Not Found"


def test_rejected_token_ends_the_session(client, seeder, utils, db, app, mocker):
    from authlib.integrations.base_client.errors import OAuthError

    from project import oauth
    from project.models import User

    user_id, _, _ = seeder.setup_base()
    with app.app_context():
        db.session.get(User, user_id).last_token_check = None
        db.session.commit()
    utils.login(user_id)
    mocker.patch.object(oauth.eventcally, "userinfo", side_effect=OAuthError("nope"))

    assert client.get("/bff/configurations").status_code == 401

    # the shell sends the browser to the login
    response = client.get("/configurations")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_stale_token_is_checked_and_installations_synced(
    client, seeder, utils, db, app, mocker
):
    from project import oauth
    from project.models import User

    user_id, _, _ = seeder.setup_base()
    with app.app_context():
        user = db.session.get(User, user_id)
        user.last_token_check = None
        user.last_app_installations_sync = None
        db.session.commit()
    utils.login(user_id)
    userinfo = mocker.patch.object(oauth.eventcally, "userinfo")
    sync = mocker.patch("project.utils.load_user_app_installations")

    assert client.get("/bff/configurations").status_code == 200

    userinfo.assert_called_once()
    sync.assert_called_once()
    with app.app_context():
        assert db.session.get(User, user_id).last_token_check is not None
