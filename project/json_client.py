from typing import Any

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
    def __init__(self, oauth_client, token):
        self.oauth_client = oauth_client
        self.token = token

    def complete_url(self, url: str) -> str:
        return "/api/v1" + url

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
        response = self.oauth_client.get(url, token=self.token)
        self.status_code_or_raise(response, 200)
        return response

    def post(self, url: str, data: Any) -> Response:
        url = self.complete_url(url)
        body = app.json.dumps(data)
        app.logger.debug(f"POST {url}\n{body}")
        response = self.oauth_client.post(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            token=self.token,
        )
        self.status_code_or_raise(response, 201)
        return response

    def put(self, url: str, data: Any) -> Response:
        url = self.complete_url(url)
        body = app.json.dumps(data)
        app.logger.debug(f"PUT {url}\n{body}")
        response = self.oauth_client.put(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            token=self.token,
        )
        self.status_code_or_raise(response, 204)
        return response

    def patch(self, url: str, data: Any) -> Response:
        url = self.complete_url(url)
        body = app.json.dumps(data)
        app.logger.debug(f"PATCH {url}\n{body}")
        response = self.oauth_client.patch(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            token=self.token,
        )
        self.status_code_or_raise(response, 204)
        return response

    def delete(self, url: str) -> Response:
        url = self.complete_url(url)
        app.logger.debug(f"DELETE {url}")
        response = self.oauth_client.delete(url, token=self.token)
        self.status_code_or_raise(response, 204)
        return response
