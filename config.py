import os
SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))


# Connect to the database

class Config(object):
    # Debug mode.
    DEBUG = False

    # TESTING = False
    # SECRET_KEY = "B\xb2?.\xdf\x9f\xa7m\xf8\x8a%,\xf7\xc4\xfa\x91"

    # DB_NAME = "production-db"
    # DB_USERNAME = "admin"
    # DB_PASSWORD = "example"

    # IMAGE_UPLOADS = "/home/username/app/app/static/images/uploads"

    # SESSION_COOKIE_SECURE = True

class ProductionConfig(Config):
    pass


# inherits from Config Class
class DevelopmentConfig(Config):
    """ Class we will use for FYYUR PROJECT
    """
    # Enable debugging mode
    DEBUG = True
    # set secret key
    SECRET_KEY = "testing_secret_key"
    
    # TODO IMPLEMENT DATABASE URL
    # connect to db so we can use real data
    SQLALCHEMY_DATABASE_URI = 'postgresql://jaimeaznar@localhost:5432/fyyur'
    # If set to True, Flask-SQLAlchemy will track modifications of objects and emit signals.
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class TestingConfig(Config):
    pass
    # TESTING = True

    # DB_NAME = "development-db"
    # DB_USERNAME = "admin"
    # DB_PASSWORD = "example"

    # SESSION_COOKIE_SECURE = False