from typing import Any

from authlib.common.urls import urlparse
from authlib.integrations.requests_client import OAuth2Session
from requests import Response

from project import app


class UnprocessableEntityError(ValueError):
    def __init__(self, message, response):
        self.json = response.json()
        super().__init__(message)

    def __str__(self):
        return str(self.json) + "\n" + super().__str__()


class NotFoundError(ValueError):
    pass


class JsonClient:
    def __init__(self, oauth_client, user):
        self.oauth_client = oauth_client
        self.user = user
        self.token = self.user.to_token()

        metadata = oauth_client.load_server_metadata()
        client_kwargs = oauth_client.client_kwargs
        client_kwargs.update(metadata)

        self.session = OAuth2Session(
            oauth_client.client_id,
            oauth_client.client_secret,
            token=self.token,
            update_token=self._update_token,
            **client_kwargs,
        )

    def _update_token(self, token, refresh_token=None, access_token=None):
        from project import db

        self.user.access_token = token["access_token"]
        self.user.refresh_token = token.get("refresh_token")
        self.user.expires_at = token["expires_at"]
        db.session.commit()

    def complete_url(self, url: str) -> str:
        return urlparse.urljoin(self.oauth_client.api_base_url, "/api/v1" + url)

    def status_code_or_raise(self, response: Response, code: int):
        app.logger.debug(f"Response: {response.status_code} {response.content}")
        if response.status_code == code:
            return

        msg = f"Expected {code}, but was {response.status_code}"

        if response.status_code == 422:
            raise UnprocessableEntityError(msg, response)

        if response.status_code == 404:
            raise NotFoundError(msg, response)

        raise ValueError(msg, response)

    def get(self, url: str) -> Response:
        url = self.complete_url(url)
        app.logger.debug(f"GET {url}")
        response = self.session.get(url)
        self.status_code_or_raise(response, 200)
        return response

    def post(self, url: str, data: Any) -> Response:
        url = self.complete_url(url)
        body = app.json.dumps(data)
        app.logger.debug(f"POST {url}\n{body}")
        response = self.session.post(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
        )
        self.status_code_or_raise(response, 201)
        return response

    def put(self, url: str, data: Any) -> Response:
        url = self.complete_url(url)
        body = app.json.dumps(data)
        app.logger.debug(f"PUT {url}\n{body}")
        response = self.session.put(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
        )
        self.status_code_or_raise(response, 204)
        return response

    def patch(self, url: str, data: Any) -> Response:
        url = self.complete_url(url)
        body = app.json.dumps(data)
        app.logger.debug(f"PATCH {url}\n{body}")
        response = self.session.patch(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
        )
        self.status_code_or_raise(response, 204)
        return response

    def delete(self, url: str) -> Response:
        url = self.complete_url(url)
        app.logger.debug(f"DELETE {url}")
        response = self.session.delete(url)
        self.status_code_or_raise(response, 204)
        return response
