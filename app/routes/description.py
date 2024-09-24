from flask import Blueprint, render_template

Description = Blueprint("description", __name__, static_folder="static", template_folder="template")

@Description.route("/")
def glossary():
    # description.html in the templates folder is where the html page is 
    return render_template("description.html", title="Description")