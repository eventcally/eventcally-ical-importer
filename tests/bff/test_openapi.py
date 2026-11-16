import json
from pathlib import Path

FRONTEND = Path(__file__).parent.parent.parent / "frontend"


def test_committed_openapi_document_is_up_to_date(app):
    """After changing a BFF model run:

    flask bff openapi > frontend/openapi.json && npm run gen:api --prefix frontend
    """
    from project.bff.openapi import build_openapi

    committed = json.loads((FRONTEND / "openapi.json").read_text())

    assert committed == json.loads(json.dumps(build_openapi()))


def test_cli_prints_the_document(app):
    result = app.test_cli_runner().invoke(args=["bff", "openapi"])

    assert result.exit_code == 0
    document = json.loads(result.output)
    assert document["openapi"] == "3.1.0"
    assert "/bff/configurations/{id}/runs/{run_id}" in document["paths"]
    operation = document["paths"]["/bff/configurations/{id}"]["put"]
    assert operation["operationId"] == "bff_configuration_update"
    assert "204" in operation["responses"]
    assert operation["parameters"] == [
        {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
    ]
