from flask import Flask, render_template, flash, redirect, url_for
from seal.forms import LoginForm
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = '78486cd05859fc8c6baa29c430f06638'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)

teams = db.Table(
    'teams',
    db.Column(
        'team_ID', db.Integer,
        db.ForeignKey('team.id'), primary_key=True
    ),
    db.Column(
        'user_ID', db.Integer,
        db.ForeignKey('user.id'), primary_key=True
    )
)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    image_file = db.Column(
        db.String(20), unique=True,
        nullable=False, default='default.jpg')
    password = db.Column(db.String(60), unique=True, nullable=False)
    teams = db.relationship(
        'Team', secondary=teams, lazy='subquery',
        backref=db.backref('members', lazy=True)
    )

    def __repr__(self):
        return f"User('{self.username}', '{self.image_file}')"


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teamname = db.Column(db.String(20), unique=True, nullable=False)

    def __repr__(self):
        return f"Team('{self.teamname}')"


@app.route("/")
@app.route("/home")
def index():
    return render_template(
        "essentials/home.html",
        title="Home"
    )


@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash(f'{form.username.data} logged!', 'success')
        redirect(url_for('index'))
    return render_template(
        "essentials/login.html",
        title="Login",
        form=form
    )


@app.route("/about")
def about():
    return render_template(
        "essentials/about.html",
        title="About"
    )


@app.route("/contact")
def contact():
    return render_template(
        "essentials/contact.html",
        title="Contact"
    )


if __name__ == '__main__':
    app.run(debug=True)
