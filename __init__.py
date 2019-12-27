import os
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from .config import app_config, base_dir

# app = flask(__name__)
# app.config.from_object(Config)


login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "You must be logged in to view this page"
login_manager.login_message_category = "info"
db = SQLAlchemy()

import logging
logger = logging.basicConfig(level=logging.DEBUG)

def create_app(config_name):
	app = Flask(__name__, template_folder='templates')
	app.config.from_object(app_config[config_name])
	app.config.from_pyfile('config.py')
	login_manager.init_app(app)
	login_manager.login_message = "you must be logged in to access this page."
	login_manager.login_view = "auth.login"
	db.init_app(app)
	migrate = Migrate(app, db)

	# with app.app_context():
	# 	db.create_all()
	Bootstrap(app)

	from . import models

	from .auth import auth as auth_blueprint
	app.register_blueprint(auth_blueprint)

	from .admin import admin as admin_blueprint
	app.register_blueprint(admin_blueprint, url_prefix='/admin')

	from .dashboard import dashboard as dashboard_blueprint
	app.register_blueprint(dashboard_blueprint)

	return app