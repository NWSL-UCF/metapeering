from .extension import db
from datetime import datetime

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.String(500))
    date_created = db.Column(db.DateTime, default=datetime.now)
    is_solved = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return '<User name: {} with email: {}>'.format(self.fullname, self.email)