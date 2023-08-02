# (c) 2023, Charles VAN GOETHEM <c-vangoethem (at) chu-montpellier (dot) fr>
#
# This file is part of SEAL
# 
# SEAL db - Simple, Efficient And Lite database for NGS
# Copyright (C) 2023  Charles VAN GOETHEM - MoBiDiC - CHU Montpellier
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
from datetime import timedelta
import yaml

from flask import Flask, session, g, request, redirect, url_for
from flask_apscheduler import APScheduler
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from wtforms.fields import HiddenField


app = Flask(__name__)

with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), "config.yaml"), "r") as config_file:
    config = yaml.safe_load(config_file)

app.config.update(config['FLASK'])
app.permanent_session_lifetime = timedelta(minutes=20)


# Plugins initialization
scheduler = APScheduler()
csrf = CSRFProtect()
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
scheduler.init_app(app)
scheduler.start()
csrf.init_app(app)
migrate = Migrate(app, db, compare_type=True)


################################################################
# from https://github.com/mbr/flask-bootstrap
def is_hidden_field_filter(field):
    return isinstance(field, HiddenField)

app.jinja_env.globals['is_hidden_field'] = is_hidden_field_filter
################################################################


app.logger.info(app.config)


@app.before_request
def before_request():
    """
    Set session and user information before processing the request.
    Check if the website is under maintenance, and redirect the maintenance
    page if so.

    Returns:
        Redirect to the maintenance page if needed
    """
    session.permanent = True
    session.modified = True
    g.user = current_user
    if app.config["MAINTENANCE"] and request.path != url_for('maintenance'): 
        return redirect(url_for('maintenance'))


@app.context_processor
def inject_config():
    """
    This function injects the Flask application's configurations as a dict
    variable in the context.

    Returns:
        dict: a dict containining app.config
    """
    return dict(app.config)



from seal import routes
from seal import schedulers
from seal import admin
