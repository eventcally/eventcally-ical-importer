from flask import request
from flask_babel import Locale

from project import app, current_user


def get_locale():
    try:
        if (
            current_user
            and current_user.is_authenticated
            and current_user.locale
            and Locale.parse(current_user.locale)
        ):
            return current_user.locale
    except Exception:
        pass

    if not request:
        return app.config["BABEL_DEFAULT_LOCALE"]

    return get_locale_from_request()


def get_locale_from_request():
    if not request:  # pragma: no cover
        return None

    return request.accept_languages.best_match(
        app.config["LANGUAGES"], app.config["BABEL_DEFAULT_LOCALE"]
    )
