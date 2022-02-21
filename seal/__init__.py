from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_apscheduler import APScheduler
from flask_wtf import CSRFProtect
import os


app = Flask(__name__)
scheduler = APScheduler()
csrf = CSRFProtect()


# Configure application option
app.config['SECRET_KEY'] = '78486cd05859fc8c6baa29c430f06638'
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql:///seal"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SCHEDULER_API_ENABLED'] = True
app.config['SCHEDULER_JOB_DEFAULTS'] = {"coalesce": False, "max_instances": 2}
if os.environ.get("API_KEY_MD"):
    app.config["API_KEY_MD"] = os.environ.get("API_KEY_MD")

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
scheduler.init_app(app)
scheduler.start()
csrf.init_app(app)

app.logger.info(app.config)


from seal import routes
from seal import schedulers
from seal import admin
