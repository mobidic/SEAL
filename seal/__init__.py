from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
@app.route("/home")
def index():
    return render_template(
        "essentials/home.html",
        title="Home"
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
