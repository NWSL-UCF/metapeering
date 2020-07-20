from .extension import db, login_manager
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.String(500))
    date_created = db.Column(db.DateTime, default=datetime.now)
    is_solved = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return "<User name: {} with email: {} feedback: {}>".format(
            self.fullname, self.email, self.message
        )


class User(UserMixin):
    id = ""

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
