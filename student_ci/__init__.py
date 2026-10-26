import os
import secrets
import sqlite3
from contextlib import closing
from functools import wraps
from pathlib import Path

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
        DATABASE=os.environ.get("STUDENT_DATABASE", str(Path(app.instance_path) / "students.db")),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        MAX_CONTENT_LENGTH=1024 * 1024,
    )
    if test_config:
        app.config.update(test_config)
    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(app.config["DATABASE"])) as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY, password_hash TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL, roll_number TEXT NOT NULL UNIQUE,
                course TEXT NOT NULL
            );
        """)
        db.commit()

    def csrf_token():
        if "csrf" not in session:
            session["csrf"] = secrets.token_hex(32)
        return session["csrf"]

    app.jinja_env.globals["csrf_token"] = csrf_token

    @app.before_request
    def protect_forms():
        if request.method == "POST":
            actual = request.form.get("csrf_token", "")
            expected = session.get("csrf", "")
            if not expected or not secrets.compare_digest(actual, expected):
                abort(400, description="Form expired. Refresh the page and try again.")

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get("user"):
                return redirect(url_for("login"))
            return view(*args, **kwargs)
        return wrapped

    def fetch_students(query=""):
        with closing(sqlite3.connect(app.config["DATABASE"])) as db:
            db.row_factory = sqlite3.Row
            if query:
                return db.execute(
                    "SELECT * FROM students WHERE instr(lower(name), lower(?)) > 0 "
                    "OR instr(lower(roll_number), lower(?)) > 0 ORDER BY id DESC",
                    (query, query),
                ).fetchall()
            return db.execute("SELECT * FROM students ORDER BY id DESC").fetchall()

    def get_student(student_id):
        with closing(sqlite3.connect(app.config["DATABASE"])) as db:
            db.row_factory = sqlite3.Row
            student = db.execute("SELECT * FROM students WHERE id=?", (student_id,)).fetchone()
        if student is None:
            abort(404)
        return student

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            with closing(sqlite3.connect(app.config["DATABASE"])) as db:
                user = db.execute("SELECT password_hash FROM users WHERE username=?", (username,)).fetchone()
            if user and check_password_hash(user[0], request.form.get("password", "")):
                session.clear()
                session["user"] = username
                return redirect(url_for("home"))
            return render_template("login.html", error="Incorrect username or password."), 401
        return render_template("login.html")

    @app.post("/logout")
    @login_required
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.get("/")
    @login_required
    def home():
        query = request.args.get("q", "").strip()
        return render_template("index.html", students=fetch_students(query), query=query)

    def save_student(student_id=None):
        if student_id is not None:
            get_student(student_id)
        fields = {key: request.form.get(key, "").strip() for key in ("name", "roll_number", "course")}
        error = None
        if not all(fields.values()):
            error = "Please fill in all fields."
        elif any(len(value) > 100 for value in fields.values()):
            error = "Each field must contain 100 characters or fewer."
        if not error:
            try:
                with closing(sqlite3.connect(app.config["DATABASE"])) as db:
                    values = (fields["name"], fields["roll_number"], fields["course"])
                    if student_id is None:
                        db.execute("INSERT INTO students (name, roll_number, course) VALUES (?, ?, ?)", values)
                    else:
                        db.execute("UPDATE students SET name=?, roll_number=?, course=? WHERE id=?", values + (student_id,))
                    db.commit()
            except sqlite3.IntegrityError:
                error = "This roll number already exists."
        if error:
            return render_template("form.html", student=fields, student_id=student_id, error=error), 400
        flash("Student added successfully." if student_id is None else "Student updated successfully.")
        return redirect(url_for("home"))

    @app.route("/students/new", methods=["GET", "POST"])
    @login_required
    def add_student():
        if request.method == "POST":
            return save_student()
        return render_template("form.html", student={}, student_id=None)

    @app.route("/students/<int:student_id>/edit", methods=["GET", "POST"])
    @login_required
    def edit_student(student_id):
        if request.method == "POST":
            return save_student(student_id)
        return render_template("form.html", student=get_student(student_id), student_id=student_id)

    @app.post("/students/<int:student_id>/delete")
    @login_required
    def delete_student(student_id):
        get_student(student_id)
        with closing(sqlite3.connect(app.config["DATABASE"])) as db:
            db.execute("DELETE FROM students WHERE id=?", (student_id,))
            db.commit()
        flash("Student deleted successfully.")
        return redirect(url_for("home"))

    @app.errorhandler(400)
    @app.errorhandler(404)
    def friendly_error(error):
        return render_template("error.html", error=error), error.code

    return app
