import datetime
import json
import os
import re

import pytest
from dotenv import load_dotenv

load_dotenv()


def _configure_environment():
    """Point the app at the test database before `project` is imported."""
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        raise RuntimeError("TEST_DATABASE_URL is not set (see doc/development.md)")
    if "test" not in url.rsplit("/", 1)[-1]:
        # Every test truncates all tables.
        raise RuntimeError("TEST_DATABASE_URL must name a test database")

    os.environ["DATABASE_URL"] = url
    # No broker: Celery runs eagerly, the tests mock the task calls.
    os.environ.pop("REDIS_URL", None)
    os.environ.pop("SERVER_NAME", None)
    os.environ.pop("PREFERRED_URL_SCHEME", None)
    os.environ.pop("VITE_DEV_SERVER_URL", None)
    # The tests expect the default site name; a local .env may set another one.
    os.environ.pop("EVENTCALLY_SITE_NAME", None)
    os.environ["SECRET_KEY"] = "test"
    os.environ["EVENTCALLY_URL"] = "http://eventcally.test"
    os.environ["EVENTCALLY_CLIENT_ID"] = "client-id"
    os.environ["EVENTCALLY_CLIENT_SECRET"] = "client-secret"
    os.environ["EVENTCALLY_PRIVATE_KEY"] = "private-key"
    os.environ["EVENTCALLY_KID"] = "kid"
    os.environ["EVENTCALLY_APP_ID"] = "1"


_configure_environment()


@pytest.fixture(scope="session")
def app():
    from project import app, db

    app.config["TESTING"] = True

    with app.app_context():
        db.drop_all()
        db.create_all()

    yield app

    with app.app_context():
        db.drop_all()


@pytest.fixture(autouse=True)
def clean_database(app):
    from project import db

    yield

    with app.app_context():
        db.session.remove()
        with db.engine.begin() as connection:
            tables = ", ".join(f'"{t.name}"' for t in db.metadata.sorted_tables)
            connection.execute(db.text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))


@pytest.fixture
def db(app):
    from project import db

    return db


@pytest.fixture
def client(app):
    return app.test_client()


class Seeder:
    def __init__(self, app, db):
        self._app = app
        self._db = db

    def create_user(self, email="user@test.de") -> int:
        from project.models import User

        with self._app.app_context():
            now = datetime.datetime.utcnow()
            user = User(
                eventcally_id=email,
                email=email,
                token_type="Bearer",
                access_token="access",
                refresh_token="refresh",
                expires_at=int(now.timestamp()) + 3600,
                # fresh: the login check neither calls EventCally nor syncs
                last_token_check=now,
                last_app_installations_sync=now,
            )
            self._db.session.add(user)
            self._db.session.commit()
            return user.id

    def create_app_installation(self, user_id=None, name="Organization") -> int:
        from project.models import AppInstallation, User

        with self._app.app_context():
            installation = AppInstallation(
                eventcally_id=f"installation-{name}",
                organization_id="7",
                organization_name=name,
                permissions="",
            )
            self._db.session.add(installation)
            if user_id:
                user = self._db.session.get(User, user_id)
                user.app_installations.append(installation)
            self._db.session.commit()
            return installation.id

    def create_configuration(self, app_installation_id, **kwargs) -> int:
        from project.models import Configuration

        with self._app.app_context():
            configuration = Configuration(
                app_installation_id=app_installation_id, **kwargs
            )
            self._db.session.add(configuration)
            self._db.session.commit()
            return configuration.id

    def create_run(self, configuration_id, **kwargs) -> int:
        from project.models import LogEntry, Run

        with self._app.app_context():
            run = Run(configuration_id=configuration_id, status="success", **kwargs)
            run.log_entries.append(
                LogEntry(message="Event importiert", type="vevent", context={"a": 1})
            )
            self._db.session.add(run)
            self._db.session.commit()
            return run.id

    def setup_base(self, **configuration_kwargs):
        """A user, their organization and one configuration: `(user, installation, configuration)` ids."""
        user_id = self.create_user()
        installation_id = self.create_app_installation(user_id)
        configuration_id = self.create_configuration(
            installation_id, **configuration_kwargs
        )
        return user_id, installation_id, configuration_id


@pytest.fixture
def seeder(app, db):
    return Seeder(app, db)


class Utils:
    def __init__(self, client):
        self._client = client
        self._csrf_token = None

    def login(self, user_id: int):
        with self._client.session_transaction() as session:
            session["user_id"] = user_id
        self._csrf_token = None

    def get_boot(self, url="/configurations") -> dict:
        response = self._client.get(url)
        assert response.status_code == 200, response.status_code
        match = re.search(
            r'<script id="boot" type="application/json">(.*?)</script>',
            response.get_data(as_text=True),
            re.S,
        )
        return json.loads(match.group(1))

    def csrf_headers(self) -> dict:
        if self._csrf_token is None:
            self._csrf_token = self.get_boot()["csrfToken"]
        return {"X-CSRFToken": self._csrf_token}

    def post_json(self, url, data=None):
        return self._client.post(url, json=data or {}, headers=self.csrf_headers())

    def put_json(self, url, data):
        return self._client.put(url, json=data, headers=self.csrf_headers())


@pytest.fixture
def utils(client):
    return Utils(client)
