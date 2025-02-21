from flask import Flask, request, render_template

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def hello_spring_seminar():
    if request.method == "POST":
        name = request.form.get("name")
        greeting = f"スプリングセミナーへようこそ、{name}さん！ "
        return render_template("index.html", greeting=greeting)
    return render_template("index.html")
