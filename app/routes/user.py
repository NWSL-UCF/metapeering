from flask import Blueprint, render_template, redirect, url_for, abort, request, flash, current_app
from flask_login import current_user, login_required, login_user
from app.models import Feedback, User
from app.forms import LoginForm
from app.extension import login_manager


LoginUser = Blueprint("user", __name__, static_folder="static", template_folder="template")

@LoginUser.route("/<username>")
@login_required
def user(username):
    issues = get_issues()
    return render_template(
        "user.html", title="Internal User", username=username, issues=issues
    )


@LoginUser.route("/<username>/login", methods=["GET", "POST"])
def login(username):
    if current_user.is_authenticated:
        return redirect(url_for("user.login", username=username))
    if username not in ["murat", "shahzeb", "prasun"]:
        return abort(404)
    login_form = LoginForm()
    if request.method == "POST" and login_form.validate_on_submit():
        if not login_success(request.form, username):
            flash("Invalid username or password.")
            return redirect(url_for("user.login", username=username))
        user = User()
        user.id = username
        login_user(user)
        return redirect(url_for("user.user", username=username))
    return render_template("login.html", title="Login", form=login_form)

def get_issues():
    try:
        issues = Feedback.query.all()
        return issues
    except:
        return None


def login_success(request, username):
    form_username = request["username"]
    password = request["password"]
    if form_username not in uname_dict or form_username != username:
        return False
    return current_app.config[uname_dict[username].upper() + "_PW"] == password

uname_dict = {
    "my": "user3",
    "sm": "user2",
    "pkd": "user1",
    "murat": "user3",
    "shahzeb": "user2",
    "prasun": "user1",
}

@login_manager.user_loader
def user_loader(username):
    if username not in uname_dict:
        return

    user = User()
    user.id = username
    return user


@login_manager.unauthorized_handler
def unauthorized_handler():
    username = request.path.split("/")[-1]
    if username in uname_dict:
        return redirect(url_for("user.login", username=username))
    else:
        return abort(401)    