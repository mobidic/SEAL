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


# from: https://stackoverflow.com/questions/63116419/evaluate-boolean-environment-variable-in-python
def getenv_bool(name: str, default: bool = None) -> bool:
    true_ = ('true', '1', 't', 'on')  # Add more entries if you want, like: `y`, `yes`, `on`, ...
    false_ = ('false', '0', 'f', 'off')  # Add more entries if you want, like: `n`, `no`, `off`, ...
    value = os.getenv(name, None)
    if value is None:
        if default is None:
            raise ValueError(f'Variable `{name}` not set!')
        else:
            value = str(default)
    if value.lower() not in true_ + false_:
        raise ValueError(f'Invalid value `{value}` for variable `{name}`')
    
    return value.lower() in true_


# Configure application option
app.config['SECRET_KEY'] = '78486cd05859fc8c6baa29c430f06638'
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql:///seal"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SCHEDULER_API_ENABLED'] = True
app.config['SCHEDULER_TIMEZONE'] = "Europe/Paris"
app.config['SCHEDULER_JOB_DEFAULTS'] = {"coalesce": False, "max_instances": 1}
app.config["SEAL_MAINTENANCE"] = getenv_bool("SEAL_MAINTENANCE", False)
app.config["DEBUG_FLASK"] = getenv_bool("DEBUG_FLASK", True)

# Plugins initialization
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
scheduler.init_app(app)
scheduler.start()
csrf.init_app(app)
migrate = Migrate(app, db, compare_type=True)

app.logger.info(app.config)


# Configure Timeout
@app.before_request
def before_request():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=20)
    session.modified = True
    g.user = current_user
    if app.config["SEAL_MAINTENANCE"] and request.path != url_for('maintenance'): 
        return redirect(url_for('maintenance'))

@app.context_processor
def inject_debug():
    return dict(DEBUG_FLASK=app.config["DEBUG_FLASK"])

from seal import routes
from seal import schedulers
from seal import admin
