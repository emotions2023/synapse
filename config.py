import os
import psycopg2
import traceback
from dotenv import load_dotenv, find_dotenv

# .envファイルを読み込む
load_dotenv(find_dotenv())

# Configクラスの定義
class Config:
    DATABASE = os.getenv('DB_NAME')
    USER = os.getenv('DB_USER')
    PASSWORD = os.getenv('DB_PASSWORD')
    HOST = os.getenv('DB_HOST')
    PORT = int(os.getenv('DB_PORT'))
    SSL_CONTEXT = True
    TIMEOUT = 30

    @staticmethod
    def get_db_config():
        return {
            'dbname': Config.DATABASE,
            'user': Config.USER,
            'password': Config.PASSWORD,
            'host': Config.HOST,
            'port': Config.PORT,
        }

    @staticmethod
    def get_sqlalchemy_database_uri():
        return f"postgresql://{Config.USER}:{Config.PASSWORD}@{Config.HOST}:{Config.PORT}/{Config.DATABASE}"

# データベース接続情報を出力（パスワードは隠蔽）
def print_db_config():
    db_config = Config.get_db_config()
    for key, value in db_config.items():
        if key != 'password':
            print(f"{key}: {value}")
        else:
            print(f"{key}: ********")

# データベース接続を確立する関数
def get_db_connection():
    db_config = Config.get_db_config()
    try:
        print("Attempting to connect to the database...")
        conn = psycopg2.connect(**db_config)
        print("Connection successful")
        return conn
    except Exception as e:
        print(f"Connection failed: {e}")
        print("Detailed error information:")
        print(traceback.format_exc())
        return None
