import sqlite3
import random
import string

DATABASE = "app.db"

USER_NAMES = [
    "taro",
    "hanako",
    "alex",
    "sakura",
    "john",
    "mike",
    "emily",
    "ryota",
    "lisa",
    "kevin",
    "nana",
    "james",
    "yuki",
    "maria",
    "david",
    "shota",
    "sophie",
    "ken",
    "anna",
    "hiro",
    "KING",
]


def generate_random_password(length=8):
    characters = string.ascii_letters + string.digits
    return "".join(random.choice(characters) for _ in range(length))


def init_db():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()

    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        wins INTEGER NOT NULL,
        points INTEGER NOT NULL,
        medals INTEGER NOT NULL DEFAULT 0
    )
    """
    )

    try:
        password = generate_random_password()
        cur.execute(
            "INSERT INTO users (name, password, wins, points, medals) VALUES ('admin', ?, 0, 0, 0)",
            (password,),
        )
    except sqlite3.IntegrityError:
        pass

    for name in USER_NAMES:
        password = generate_random_password()
        wins = random.randint(0, 99)
        points = random.randint(0, 99)

        try:
            if name == "KING":
                cur.execute(
                    "INSERT INTO users (name, password, wins, points, medals) VALUES (?, ?, 100, 200, 2)",
                    (name, password),
                )
            else:
                cur.execute(
                    "INSERT INTO users (name, password, wins, points, medals) VALUES (?, ?, ?, ?, 0)",
                    (name, password, wins, points),
                )
        except sqlite3.IntegrityError:
            continue

    conn.commit()
    conn.close()
    print("[INFO] Database initialized successfully.")


if __name__ == "__main__":
    init_db()
