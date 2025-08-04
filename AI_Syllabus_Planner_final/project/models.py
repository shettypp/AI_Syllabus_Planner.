from flask_login import UserMixin
from . import db
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    tasks = db.relationship('Task', backref='user', lazy=True, cascade="all, delete-orphan")

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(100), nullable=False)
    topic = db.Column(db.String(200), nullable=False)
    due_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    start_time = db.Column(db.Time, nullable=True)
    end_time = db.Column(db.Time, nullable=True)
    is_complete = db.Column(db.Boolean, default=False, nullable=False)
    notes = db.Column(db.Text, nullable=True) 
    task_type = db.Column(db.String(20), nullable=False, default='study')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)