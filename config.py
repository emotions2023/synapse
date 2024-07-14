import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') + "?client_encoding=utf8"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GOOGLE_CLOUD_KEYFILE = os.getenv('GOOGLE_CLOUD_KEYFILE')
    GOOGLE_CLOUD_BUCKET = os.getenv('GOOGLE_CLOUD_BUCKET')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
