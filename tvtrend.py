from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))

app.config.update(
    SQLALCHEMY_DATABASE_URI="sqlite:///" + os.path.join(basedir, "app.db"),
    SQLALCHEMY_ECHO=False,
    SECRET_KEY="tvtrend",
)

app.config.from_pyfile('config.py')

db = SQLAlchemy(app)

import views, models

if not os.path.exists(os.path.join(basedir, "app.db")):
    db.create_all()