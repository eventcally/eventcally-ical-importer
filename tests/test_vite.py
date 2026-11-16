import json


def _write_manifest(app, tmp_path, monkeypatch, manifest):
    import project.vite as vite

    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest))
    monkeypatch.setattr(vite, "_manifest_file", lambda: str(path))
    monkeypatch.setattr(vite, "_manifest_cache", {})


def test_built_entry_renders_css_preload_and_script(app, tmp_path, monkeypatch):
    from project.vite import vite_entry

    _write_manifest(
        app,
        tmp_path,
        monkeypatch,
        {
            "src/apps/importer/main.ts": {
                "file": "assets/importer-abc.js",
                "name": "importer",
                "isEntry": True,
                "css": ["assets/importer-abc.css"],
                "imports": ["_shared.js"],
            },
            "_shared.js": {"file": "assets/shared-def.js"},
        },
    )

    with app.test_request_context("/"):
        html = str(vite_entry("importer"))

    assert '<link rel="stylesheet" href="/static/dist/assets/importer-abc.css">' in html
    assert '<link rel="modulepreload" href="/static/dist/assets/shared-def.js">' in html
    assert (
        '<script type="module" src="/static/dist/assets/importer-abc.js"></script>'
        in html
    )


def test_missing_build_renders_a_comment(app, tmp_path, monkeypatch):
    import project.vite as vite
    from project.vite import vite_entry

    monkeypatch.setattr(vite, "_manifest_file", lambda: str(tmp_path / "missing.json"))
    monkeypatch.setattr(vite, "_manifest_cache", {})

    with app.test_request_context("/"):
        assert "not built" in str(vite_entry("importer"))


def test_dev_server_serves_the_sources(app, monkeypatch):
    from project.vite import vite_entry

    monkeypatch.setitem(app.config, "VITE_DEV_SERVER_URL", "http://localhost:5175/")

    with app.test_request_context("/"):
        html = str(vite_entry("importer"))

    assert "http://localhost:5175/static/dist/@vite/client" in html
    assert "http://localhost:5175/static/dist/src/apps/importer/main.ts" in html
