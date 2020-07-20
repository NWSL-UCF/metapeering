import time
from flask import (
    Flask,
    make_response,
    render_template,
    request,
    redirect,
    url_for,
    abort
)
from flask_bootstrap import Bootstrap
from flask_s3 import FlaskS3
import boto3

from app.config import (
    AWS_STORAGE_BUCKET_NAME,
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    DATABASE_URI,
    USER1_PW,
    USER2_PW,
    USER3_PW,
)

from app.commands import create_tables
from app.extension import db, login_manager
from app.models import Feedback, User

from app.routes.glossary import Glossary
from app.routes.home import Home
from app.routes.success import Success
from app.routes.logout import Logout
from app.routes.custom import Custom
from app.routes.user import LoginUser
from app.routes.feedback import FeedbackPage
from app.routes.error import Error


s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)

app = Flask(__name__)
app.config["SECRET_KEY"] = "metapeering"
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
Bootstrap(app)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI

db.init_app(app)
app.cli.add_command(create_tables)

app.config["USER1_PW"] = USER1_PW
app.config["USER2_PW"] = USER2_PW
app.config["USER3_PW"] = USER3_PW
login_manager.init_app(app)

app.register_blueprint(Home, url_prefix="")
app.register_blueprint(Glossary, url_prefix="/glossary")
app.register_blueprint(FeedbackPage, url_prefix="/feedback")
app.register_blueprint(Custom, url_prefix="/custom")
app.register_blueprint(Success, url_prefix="/success")
app.register_blueprint(Logout, url_prefix="/logout")
app.register_blueprint(LoginUser, url_prefix="/user")
app.register_blueprint(Error)

@app.route('/json')
def json():
    return render_template('json.html')

#background process happening without any refreshing
@app.route('/background_process_test')
def background_process_test():
    print ("Hello")
    return

@app.after_request
def after_request(response):
    # Issue with Safari. Going back will still show the contents, but clears the session anyway.
    response.cache_control.no_store = True
    response.cache_control.no_cache = True
    response.cache_control.must_revalidate = True
    response.cache_control.max_age = 0
    return response
