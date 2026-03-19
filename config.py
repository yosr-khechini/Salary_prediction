import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'd14d42cb71e1da0efec8b229c32d7ac5db2c501ee748a672300d4c2d03d004c9'
    # SQLite for offline use - no MySQL server needed
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance', 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
