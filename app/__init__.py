from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config, get_db_connection, print_db_config

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # データベース接続情報を出力
    print_db_config()

    # データベースに接続
    conn = get_db_connection()
    if conn:
        # SQLAlchemyのエンジンを作成
        app.config['SQLALCHEMY_DATABASE_URI'] = Config.get_sqlalchemy_database_uri()
        db.init_app(app)
        login_manager.init_app(app)
        login_manager.login_view = 'routes.login'

        with app.app_context():
            from . import routes, models
            app.register_blueprint(routes.routes)  # ここでBlueprintを登録
            db.create_all()

    return app


@login_manager.user_loader
def load_user(user_id):
    from .models import User
