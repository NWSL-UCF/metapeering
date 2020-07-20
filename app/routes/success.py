from flask import Blueprint, render_template

Success = Blueprint("success", __name__, static_folder="static", template_folder="template")


@Success.route("/", methods=("GET", "POST"))
def success():
    return render_template("success.html")
