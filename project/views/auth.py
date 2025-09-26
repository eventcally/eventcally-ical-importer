import datetime

from flask import redirect, session, url_for

from project import app, db, oauth
from project.i18n import get_locale_from_request
from project.models import User
from project.utils import load_user_app_installations, login_required


@app.route("/login")
def login():
    redirect_uri = url_for("authorize", _external=True)
    return oauth.eventcally.authorize_redirect(redirect_uri)


@app.route("/authorize")
def authorize():
    token = oauth.eventcally.authorize_access_token()
    userinfo = oauth.eventcally.userinfo(token=token)
    eventcally_id = userinfo["sub"]

    user = User.query.filter(User.eventcally_id == eventcally_id).first()

    if not user:
        user = User(eventcally_id=eventcally_id)
        db.session.add(user)

    user.email = userinfo["email"]

    if not user.locale:
        user.locale = get_locale_from_request()

    user.token_type = token["token_type"]
    user.access_token = token["access_token"]
    user.refresh_token = token.get("refresh_token")
    user.expires_at = token["expires_at"]
    user.token_created_at = datetime.datetime.utcnow()
    user.last_token_check = datetime.datetime.utcnow()
    db.session.commit()

    session["user_id"] = user.id
    session.permanent = True
    return redirect(url_for("user_update_app_installations"))


@app.route("/user/update_app_installations")
@login_required
def user_update_app_installations():
    load_user_app_installations()
    return redirect(url_for("configurations"))


@app.route("/logout")
@login_required
def logout():
    session.pop("user_id", None)
    return redirect(url_for("index"))
