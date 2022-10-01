from flask import Blueprint, render_template

Interpret = Blueprint("interpret", __name__, static_folder="static", template_folder="template")

@Interpret.route("/")
def interpret():
    return render_template("interpret.html", title="Interpret Your Results")
