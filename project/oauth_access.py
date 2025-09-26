from authlib.common.urls import add_params_to_qs
from authlib.oauth2.rfc7523 import PrivateKeyJWT


class CustomPrivateKeyJWT(PrivateKeyJWT):
    def __call__(self, auth, method, uri, headers, body):
        token_endpoint = self.token_endpoint
        if not token_endpoint:
            token_endpoint = uri

        client_assertion = self.sign(auth, token_endpoint)
        body = add_params_to_qs(
            body or "",
            [
                ("grant_type", "urn:ietf:params:oauth:grant-type:jwt-bearer"),
                ("assertion", client_assertion),
            ],
        )
        return uri, headers, body
