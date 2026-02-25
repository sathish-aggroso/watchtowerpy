from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from models import Base

db = SQLAlchemy(model_class=Base)
migrate = Migrate()


def init_migrations(app: Flask):
    db.init_app(app)
    migrate.init_app(app, db)
