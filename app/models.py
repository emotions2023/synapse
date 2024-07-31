from . import db
from flask_sqlalchemy import SQLAlchemy

class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    
    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)
    
class Profile(db.Model):
    __tablename__ = 'profile'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    birth = db.Column(db.String(50), nullable=False)
    death = db.Column(db.String(50), nullable=False)
    cemetery = db.Column(db.String(100), nullable=False)
    business = db.Column(db.String(50), nullable=False)
    language = db.Column(db.String(50), nullable=False)
    nationality = db.Column(db.String(50), nullable=False)
    education = db.Column(db.String(100), nullable=False)
    last_education = db.Column(db.Text, nullable=False)
    period_of_activity = db.Column(db.String(100), nullable=False)
    genre = db.Column(db.String(50), nullable=False)
    upbringing = db.Column(db.Text, nullable=False)
    death_details = db.Column(db.Text, nullable=False)
    others = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    delete_flag = db.Column(db.Boolean, nullable=False)
    image_url = db.Column(db.String(200), nullable=False)

class FeaturedArticle(db.Model):
    __tablename__ = 'featured_articles'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

class DailyImage(db.Model):
    __tablename__ = 'daily_images'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

class DailyEvent(db.Model):
    __tablename__ = 'daily_events'  # テーブル名を明示的に設定
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    event = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)