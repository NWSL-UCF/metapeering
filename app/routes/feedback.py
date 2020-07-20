from flask import Blueprint, render_template, request, redirect, url_for
from app.forms import ContactUsForm
from app.models import Feedback
from app.extension import db

FeedbackPage = Blueprint("feedback", __name__, static_folder="static", template_folder="template")

@FeedbackPage.route("/", methods=["GET", "POST"])
def feedback():
    form = ContactUsForm()
    if request.method == "POST" and form.validate_on_submit():
        feedback_form_handler(request.form)
        return redirect(url_for("success.success"))
    return render_template("feedback.html", title="Feedback", form=form)


def feedback_form_handler(request):
    fullname = request["name"]
    email = request["email"]
    message = request["body"]

    feedback = Feedback(fullname=fullname, email=email, message=message)

    db.session.add(feedback)
    db.session.commit()
    return
