import os

# Database URI
DATABASE_URI = "postgresql://db_ebsl_user:lpUNVkJAuqLjlvjPry2WjB3RJyS3wl1i@dpg-d33u4uer433s738s8p40-a.singapore-postgres.render.com/db_ebsl"

SECRET_KEY = os.environ.get('SECRET_KEY', 'pharmacy-pos-secret-key')
SQLALCHEMY_DATABASE_URI = DATABASE_URI
SQLALCHEMY_TRACK_MODIFICATIONS = False