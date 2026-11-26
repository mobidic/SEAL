# (c) 2025, Charles VAN GOETHEM <c-vangoethem (at) chu-montpellier (dot) fr>
#
# This file is part of SEAL
#
# SEAL db - Simple, Efficient And Lite database for NGS
# Copyright (C) 2025  Charles VAN GOETHEM - MoBiDiC - CHU Montpellier
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
import subprocess
import time
import yaml
from pathlib import Path
from datetime import timedelta

from flask import Flask, session, g, request, redirect, url_for, Blueprint
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect


app = Flask(__name__)

with open(Path(app.root_path).joinpath("config.yaml"), "r") as config_file:
    config = yaml.safe_load(config_file)

app.config.update(config['FLASK'])
app.permanent_session_lifetime = timedelta(minutes=20)


# Plugins initialization
csrf = CSRFProtect()
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
csrf.init_app(app)
migrate = Migrate(app, db, compare_type=True)


app.logger.info(app.config)


for key, value in config["BP"].items():
    data_bp = Blueprint(
        key,
        __name__,
        static_folder=value["folder"],
        static_url_path=value["path"]
    )
    app.register_blueprint(data_bp)


def get_asset_version():
    """
    Returns an identifier for the current code deployment (git description
    of the repository, or a timestamp if git is not available).
    """
    try:
        return subprocess.check_output(
            ["git", "describe", "--tags", "--always"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        return str(int(time.time()))


app.config["ASSET_VERSION"] = get_asset_version()


# Maintenance mode shared between processes.
# The web workers and the scheduler process (see scheduler.py) do not share
# memory: a flag set in app.config by one process is invisible to the others.
# A flag file on disk is used instead, next to the existing VCF lock file.
MAINTENANCE_FLAG = Path(app.root_path).joinpath('static/temp/.maintenance')


def set_maintenance(reason=""):
    """Switch on maintenance mode for every process (web workers + scheduler)."""
    MAINTENANCE_FLAG.write_text(reason)


def clear_maintenance():
    """Switch off maintenance mode set by set_maintenance()."""
    try:
        MAINTENANCE_FLAG.unlink()
    except FileNotFoundError:
        pass


def get_maintenance():
    """
    Returns:
        tuple(bool, str): (is the website under maintenance, reason)
    """
    if app.config.get("MAINTENANCE"):
        return True, app.config.get("MAINTENANCE_REASON", "")
    try:
        return True, MAINTENANCE_FLAG.read_text()
    except FileNotFoundError:
        return False, None


@app.url_defaults
def add_static_version(endpoint, values):
    """
    Appends a version parameter to all static file URLs, so that browsers
    fetch updated assets after each new deployment, even if they are cached
    by the client or by a reverse proxy (e.g. nginx).
    """
    if endpoint == 'static' or endpoint.endswith('.static'):
        if 'filename' in values:
            values.setdefault('v', app.config["ASSET_VERSION"])


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
    if get_maintenance()[0] and request.path != url_for('maintenance'):
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


if 'GENOME' not in config or config['GENOME'] not in ['grch37', 'grch38']:
    app.logger.warning("Genome version not recognize : use default version 'grch38'")
    config['GENOME'] = 'grch38'


from seal import routes
# from seal import schedulers
from seal import admin
