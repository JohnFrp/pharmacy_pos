import os
from urllib.parse import quote_plus

# Database URI
DATABASE_URI = "postgresql://db_7xk8_user:GJqN6o43COFJFcaX7ZsbmBnPoZk2O6bu@dpg-d30ojvemcj7s73eabu8g-a.singapore-postgres.render.com/db_7xk8"

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'pharmacy-pos-secret-key')
    SQLALCHEMY_DATABASE_URI = DATABASE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False