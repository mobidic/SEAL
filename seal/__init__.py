from flask import Flask, render_template, flash, redirect, url_for
from forms.registration import LoginForm
app = Flask(__name__)

app.config['SECRET_KEY'] = '78486cd05859fc8c6baa29c430f06638'


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
