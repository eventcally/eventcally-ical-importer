from urllib.parse import parse_qs

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from tests.views.test_auth import METADATA


def _private_key_pem() -> str:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()


def test_app_installation_session_uses_a_signed_jwt_bearer_grant(app, requests_mock):
    """The importer authenticates as an app installation with a JWT signed by the app key."""
    from joserfc import jwt
    from joserfc.jwk import RSAKey

    from project import oauth
    from project.api_client import ApiClient
    from project.json_client import JsonClient

    pem = _private_key_pem()
    requests_mock.get(
        "http://eventcally.test/.well-known/openid-configuration", json=METADATA
    )
    token = requests_mock.post(
        "http://eventcally.test/oauth/token",
        json={"token_type": "Bearer", "access_token": "app-token", "expires_in": 3600},
    )
    categories = requests_mock.get(
        "http://eventcally.test/api/v1/event-categories?per_page=50",
        json={"items": [{"id": 1, "name": "Art"}]},
    )

    with app.app_context():
        client = ApiClient(
            JsonClient(
                oauth.eventcally,
                oauth_private_key=pem,
                oauth_kid="kid-1",
                app_installation_id="5",
            )
        )
        assert client.get_categories() == [{"id": 1, "name": "Art"}]

    body = parse_qs(token.last_request.text)
    # Authlib and `CustomPrivateKeyJWT` both add the grant type (EventCally accepts that).
    assert set(body["grant_type"]) == {"urn:ietf:params:oauth:grant-type:jwt-bearer"}
    token_data = jwt.decode(body["assertion"][0], RSAKey.import_key(pem))
    assert token_data.claims["iss"] == "client-id"
    assert token_data.claims["sub"] == "app_installation:5"
    assert token_data.header["kid"] == "kid-1"
    assert token_data.header["alg"] == "RS256"
    assert categories.last_request.headers["Authorization"] == "Bearer app-token"


def test_app_installations_are_requested_since_the_last_sync(app, mocker):
    import datetime

    from project.api_client import ApiClient

    json_client = mocker.Mock()
    json_client.get.return_value.json.return_value = {"items": [], "has_next": False}

    with app.app_context():
        ApiClient(json_client).get_app_installations(
            datetime.datetime(2026, 1, 17, 16, 5, 0)
        )

    # naive UTC minus the 5 minutes overlap, as an ISO timestamp with offset
    url = json_client.get.call_args_list[0].args[0]
    assert "last_modified_at_from=2026-01-17T16%3A00%3A00%2B00%3A00" in url
