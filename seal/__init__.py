import os
from datetime import timedelta

from flask import Flask, session, g, request, render_template, redirect, url_for
from flask_apscheduler import APScheduler
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from apscheduler.schedulers.background import BackgroundScheduler


app = Flask(__name__)
scheduler = APScheduler()
csrf = CSRFProtect()


# Configure application option
app.config['SECRET_KEY'] = '78486cd05859fc8c6baa29c430f06638'
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql:///seal"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SCHEDULER_API_ENABLED'] = True
app.config['SCHEDULER_TIMEZONE'] = "Europe/Paris"
app.config['SCHEDULER_JOB_DEFAULTS'] = {"coalesce": False, "max_instances": 2}
if os.environ.get("API_KEY_MD"):
    app.config["API_KEY_MD"] = os.environ.get("API_KEY_MD")
app.config["SEAL_MAINTENANCE"] = os.environ.get("SEAL_MAINTENANCE") if os.environ.get("SEAL_MAINTENANCE") else False

# Plugins initialization
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
scheduler.init_app(app)
scheduler.start()
csrf.init_app(app)
migrate = Migrate(app, db)

app.logger.info(app.config)


# Configure Timeout
@app.before_request
def before_request():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=20)
    session.modified = True
    g.user = current_user
    print(app.config["SEAL_MAINTENANCE"])
    if app.config["SEAL_MAINTENANCE"] and request.path != url_for('maintenance'): 
        return redirect(url_for('maintenance'))


from seal import routes
from seal import schedulers
from seal import admin
