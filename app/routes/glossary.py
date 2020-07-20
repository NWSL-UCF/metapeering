from flask import Blueprint, render_template

Glossary = Blueprint("glossary", __name__, static_folder="static", template_folder="template")

@Glossary.route("/")
def glossary():
    return render_template("glossary.html", title="Glossary")