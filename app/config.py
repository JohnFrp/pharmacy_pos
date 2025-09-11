import os

# Database URI
DATABASE_URI = "postgresql://db_dasj_user:iqn93AGlEdoI90oPNWKOzCcQzxJTsFKd@dpg-d31e9ct6ubrc73cd4cr0-a.singapore-postgres.render.com/db_dasj"

SECRET_KEY = os.environ.get('SECRET_KEY', 'pharmacy-pos-secret-key')
SQLALCHEMY_DATABASE_URI = DATABASE_URI
SQLALCHEMY_TRACK_MODIFICATIONS = False