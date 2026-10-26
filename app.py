"""Local entry point. Run with --setup once to create your login."""
import argparse
import getpass
import sqlite3
from contextlib import closing

from werkzeug.security import generate_password_hash
from student_ci import create_app

app = create_app()


def setup_admin():
    username = input("Choose a username: ").strip()
    password = getpass.getpass("Choose a password (at least 8 characters; typing is hidden): ")
    confirmation = getpass.getpass("Repeat password: ")
    if not username or len(password) < 8 or password != confirmation:
        raise SystemExit("Not saved. Username is required; passwords must match and have at least 8 characters.")
    with closing(sqlite3.connect(app.config["DATABASE"])) as db:
        db.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?) "
            "ON CONFLICT(username) DO UPDATE SET password_hash=excluded.password_hash",
            (username, generate_password_hash(password)),
        )
        db.commit()
    print("Login saved. Use this username and password in your browser.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--setup", action="store_true", help="Create or reset a local login")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()
    if args.setup:
        setup_admin()
    else:
        with closing(sqlite3.connect(app.config["DATABASE"])) as db:
            has_user = db.execute("SELECT 1 FROM users LIMIT 1").fetchone()
        if not has_user:
            print("First launch: create your login.")
            setup_admin()
        print("Open http://127.0.0.1:" + str(args.port))
        app.run(host="127.0.0.1", port=args.port, debug=False)
