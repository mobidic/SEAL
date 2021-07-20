from flask import render_template, flash, redirect, url_for
from seal import app, db, bcrypt
from seal.forms import LoginForm
from seal.models import User, Team
from flask_login import login_user, current_user, logout_user


@app.route("/")
@app.route("/home")
def index():
    return render_template(
        "essentials/home.html",
        title="Home"
    )


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('about'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            flash(f'You are logged as: {user.username}!', 'success')
            login_user(user, remember=form.remember.data)
            return redirect(url_for('index'))
        else:
            flash('Login unsucessful. Please check the username and/or password!', 'error')
    return render_template(
        "essentials/login.html",
        title="Login",
        form=form
    )


@app.route("/logout", methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('index'))


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
