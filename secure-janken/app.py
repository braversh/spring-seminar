from flask import (
    Flask,
    request,
    render_template,
    redirect,
    session,
    jsonify,
    abort,
    flash,
)
from datetime import timedelta
import sqlite3
import random

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.permanent_session_lifetime = timedelta(minutes=30)


DATABASE = "app.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def get_medal(medals):
    if medals == 1:
        return "🥉"
    elif medals == 2:
        return "🥈"
    elif medals == 3:
        return "🥇"


app.jinja_env.filters['get_medal_emoji'] = get_medal

@app.route("/", methods=["GET"])
def index():
    if session.get("medals") == 0:
        return render_template("index.html", user=session.get("user"))
    else:
        return render_template("index.html", 
                               user=session.get("user"), 
                               medals=get_medal(session.get("medals")))



@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form["name"]
        password = request.form["password"]

        query = f"SELECT * FROM users WHERE name = '{name}' AND password = '{password}'"

        conn = get_db()
        cur = conn.cursor()
        cur.execute(query)
        user = cur.fetchone()
        conn.close()

        if user:
            session.permanent = True
            session["user"] = user["name"]
            session["medals"] = user["medals"]
            return redirect("/", code=303)
        else:
            flash("ユーザ名またはパスワードが違います。", "error")

    return render_template("login.html")


@app.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return redirect("/", code=303)


@app.route("/play", methods=["GET", "POST"])
def play():
    if "user" not in session:
        return redirect("/login", code=303)

    if request.method == "GET":
        cpu_hand = random.randint(0, 2)
        session["cpu_hand"] = cpu_hand
        return render_template("play.html")

    elif request.method == "POST":
        user_hand = int(request.json.get("hand"))
        cpu_hand = session.get("cpu_hand")

        result = (cpu_hand - user_hand) % 3
        if result == 1:
            outcome = "勝ち"
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                "UPDATE users SET wins = wins + 1, points = points + 3 WHERE name = ?",
                (session["user"],),
            )
            conn.commit()
            conn.close()
        elif result == 2:
            outcome = "負け"
        else:
            outcome = "引き分け"

        return jsonify(
            {"user_hand": user_hand, "cpu_hand": cpu_hand, "outcome": outcome}
        )


@app.route("/reset_game", methods=["POST"])
def reset_game():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    session["cpu_hand"] = random.randint(0, 2)

    return jsonify({"message": "CPU hand reset!"})


@app.route("/status", methods=["GET"])
def status():
    if "user" not in session:
        return redirect("/login", code=303)

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT wins, points FROM users WHERE name = ?", (session["user"],))
    user_data = cur.fetchone()
    conn.close()

    if user_data:
        return render_template(
            "status.html", wins=user_data["wins"], points=user_data["points"]
        )
    else:
        return abort(404)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()

        try:
            cur.execute(
                "INSERT INTO users (name, password, wins, points) VALUES (?, ?, 0, 0)",
                (name, password),
            )
            conn.commit()
            flash("ユーザー登録が完了しました！", "success")
            return redirect("/login", code=303)
        except sqlite3.IntegrityError:
            flash("このユーザー名はすでに使用されています。", "error")
            return render_template("register.html")

        finally:
            conn.close()

    return render_template("register.html")


@app.route("/ranking", methods=["GET"])
def ranking():
    search_query = request.args.get("q", "")
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT name, wins FROM users ORDER BY wins DESC LIMIT 20")
    ranking_data = cur.fetchall()

    if search_query:
        cur.execute(
            "SELECT COUNT(*) + 1 FROM users WHERE wins > (SELECT wins FROM users WHERE name = ?)",
            (search_query,),
        )
        rank = cur.fetchone()[0]

        if rank:
            return render_template(
                "search_result.html", search_query=search_query, rank=rank
            )

        return render_template(
            "search_result.html", search_query=search_query, rank=None
        )

    conn.close()
    return render_template(
        "ranking.html", ranking_data=ranking_data, search_query=search_query
    )


@app.route("/shop", methods=["GET", "POST"])
def shop():
    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT points FROM users WHERE name = ?", (session["user"],))
    user_data = cur.fetchone()
    user_points = user_data["points"] if user_data else 0

    items = {"bronze_medal": 10, "silver_medal": 100, "gold_medal": 1000}

    if request.method == "POST":
        try:
            item = request.form.get("item", "")
            price = int(request.form.get("price", 0))

            if item in items and price in [10, 100, 1000]:
                if user_points >= price:
                    cur.execute(
                        "UPDATE users SET points = points - ? WHERE name = ?",
                        (price, session["user"]),
                    )
                    if item == "bronze_medal":
                        user_medals = 1
                    elif item == "silver_medal":
                        user_medals = 2
                    elif item == "gold_medal":
                        user_medals = 3
                    cur.execute(
                        "UPDATE users SET medals = ? WHERE name = ?",
                        (user_medals, session["user"]),
                    )

                    conn.commit()
                    user_points -= price
                    session["medals"] = user_medals
                    message = f"{item.replace('_', ' ').title()} を購入しました。"
                else:
                    message = "ポイントが足りません。"
            else:
                message = "無効な商品です。"
        except ValueError:
            message = "無効な入力です。"
    else:
        message = None

    conn.close()
    return render_template(
        "shop.html",
        user=session["user"],
        points=user_points,
        message=message,
        items=items,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
