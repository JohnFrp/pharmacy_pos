import os

# Database URI
DATABASE_URI = "postgresql://db_8r3u_user:DGDcY0ZgPDAuokXtbbYfkuiiKr8FerKl@dpg-d340a9mr433s738tss8g-a.singapore-postgres.render.com/db_8r3u"

SECRET_KEY = os.environ.get('SECRET_KEY', 'pharmacy-pos-secret-key')
SQLALCHEMY_DATABASE_URI = DATABASE_URI
SQLALCHEMY_TRACK_MODIFICATIONS = False