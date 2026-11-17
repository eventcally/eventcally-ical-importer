import re

from app_logging import get_log_context
from project.request_id import REQUEST_ID_HEADER


def test_response_has_a_generated_request_id(client):
    response = client.get("/up")

    assert re.fullmatch(r"[0-9a-f]{32}", response.headers[REQUEST_ID_HEADER])


def test_valid_incoming_request_id_is_echoed(client):
    response = client.get("/up", headers={REQUEST_ID_HEADER: "abc-123.x_y"})

    assert response.headers[REQUEST_ID_HEADER] == "abc-123.x_y"


def test_invalid_incoming_request_id_is_replaced(client):
    response = client.get("/up", headers={REQUEST_ID_HEADER: "bad id!"})

    assert response.headers[REQUEST_ID_HEADER] != "bad id!"
    assert re.fullmatch(r"[0-9a-f]{32}", response.headers[REQUEST_ID_HEADER])


def test_request_id_is_in_the_log_context_during_the_request(app):
    with app.test_request_context("/up", headers={REQUEST_ID_HEADER: "r1"}):
        app.preprocess_request()
        seen = dict(get_log_context())

    # leaving the request context runs the teardown, which resets the log context
    assert seen == {"request_id": "r1"}
    assert get_log_context() == {}
