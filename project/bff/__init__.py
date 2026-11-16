from flask import Blueprint, Flask, jsonify, request
from flask_wtf.csrf import CSRFError
from pydantic import ValidationError
from werkzeug.exceptions import HTTPException

bff_bp = Blueprint("bff", __name__, url_prefix="/bff")

_UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

_UNPROCESSABLE_MESSAGE = (
    "The request was well-formed but was unable to be followed due to semantic errors."
)


def _error_response(name: str, message: str, code: int):
    from project.bff.schemas import ErrorResponse

    payload = ErrorResponse(name=name, message=message).model_dump(mode="json")
    return jsonify(payload), code


@bff_bp.before_request
def _require_session_user():
    from project.utils import check_session_user

    # JSON clients never get the login redirect; the frontend sends the browser there.
    if not check_session_user():
        return _error_response("Unauthorized", "Authentication required.", 401)


@bff_bp.before_request
def _protect_unsafe_methods():
    from project import csrf

    # CSRF is opt-in app-wide (WTF_CSRF_CHECK_DEFAULT = False).
    if request.method in _UNSAFE_METHODS:
        csrf.protect()


@bff_bp.errorhandler(ValidationError)
def _handle_validation_error(err: ValidationError):
    from project.bff.schemas import FieldError, ValidationErrorResponse

    errors = [
        FieldError(loc=[str(part) for part in e["loc"]], msg=e["msg"])
        for e in err.errors()
    ]
    payload = ValidationErrorResponse(
        name="Unprocessable Entity",
        message=_UNPROCESSABLE_MESSAGE,
        errors=errors,
    )
    return jsonify(payload.model_dump(mode="json")), 422


@bff_bp.errorhandler(CSRFError)
def _handle_csrf_error(err: CSRFError):
    return _error_response(err.name, err.description, 400)


@bff_bp.errorhandler(HTTPException)
def _handle_http_exception(err: HTTPException):
    return _error_response(err.name, err.description or "", err.code or 500)


# The route modules register themselves on `bff_bp` when imported.
from project.bff import configurations, runs  # noqa: E402, F401


def init_bff(app: Flask):
    """Initialize the BFF channel: view-shaped JSON for the Vue frontend."""
    app.register_blueprint(bff_bp)
