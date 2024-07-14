from . import db
from flask_sqlalchemy import SQLAlchemy

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    birth = db.Column(db.String(50), nullable=False)
    death = db.Column(db.String(50), nullable=False)
    cemetery = db.Column(db.String(100), nullable=False)
    business = db.Column(db.String(50), nullable=False)
    language = db.Column(db.String(50), nullable=False)
    nationality = db.Column(db.String(50), nullable=False)
    education = db.Column(db.String(100), nullable=False)
    last_education = db.Column(db.String(100), nullable=False)
    period_of_activity = db.Column(db.String(100), nullable=False)
    genre = db.Column(db.String(50), nullable=False)
    upbringing = db.Column(db.String(100), nullable=False)
    death_details = db.Column(db.String(100), nullable=False)
    others = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    delete_flag = db.Column(db.Boolean, nullable=False)
    image_url = db.Column(db.String(200), nullable=False)
