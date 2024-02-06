from flask import redirect, session, url_for

from project import app, db, oauth
from project.i18n import get_locale_from_request
from project.models import User
from project.utils import login_required


@app.route("/login")
def login():
    redirect_uri = url_for("authorize", _external=True)
    return oauth.eventcally.authorize_redirect(redirect_uri)


@app.route("/authorize")
def authorize():
    token = oauth.eventcally.authorize_access_token()
    userinfo = oauth.eventcally.userinfo(token=token)
    email = userinfo["email"]

    user = User.query.filter(User.email == email).first()

    if not user:
        user = User(email=email)
        db.session.add(user)

    if not user.locale:
        user.locale = get_locale_from_request()

    user.token_type = token["token_type"]
    user.access_token = token["access_token"]
    user.refresh_token = token.get("refresh_token")
    user.expires_at = token["expires_at"]
    db.session.commit()

    session["user_id"] = user.id
    session.permanent = True
    return redirect(url_for("index"))


@app.route("/logout")
@login_required
def logout():
    session.pop("user_id", None)
    return redirect(url_for("index"))
