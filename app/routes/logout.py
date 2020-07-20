from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, logout_user

Logout = Blueprint("logout", __name__, static_folder="static", template_folder="template")


@Logout.route("/")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home.querry"))
