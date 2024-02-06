from flask import redirect, render_template, request, send_from_directory, url_for

from project import app, current_user


@app.route("/")
def index():
    if current_user:
        return redirect(url_for("configurations"))

    return render_template("index.html")


@app.route("/favicon.ico")
def favicon_ico():
    return send_from_directory(app.static_folder, request.path[1:])
