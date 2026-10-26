import sqlite3
from contextlib import closing

import pytest
from werkzeug.security import generate_password_hash
from student_ci import create_app


@pytest.fixture
def app(tmp_path):
    app = create_app({"TESTING": True, "SECRET_KEY": "test-only-key",
                      "DATABASE": str(tmp_path / "test.db")})
    with closing(sqlite3.connect(app.config["DATABASE"])) as db:
        db.execute("INSERT INTO users VALUES (?, ?)",
                   ("tester", generate_password_hash("TestPassword123")))
        db.commit()
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def post(client, url, data=None):
    client.get("/login")
    with client.session_transaction() as session:
        token = session["csrf"]
    return client.post(url, data={**(data or {}), "csrf_token": token}, follow_redirects=True)


def login(client):
    return post(client, "/login", {"username": "tester", "password": "TestPassword123"})


def add(client, roll="TEST001", name="Test Student"):
    return post(client, "/students/new", {"name": name, "roll_number": roll, "course": "Engineering"})


def records(app):
    with closing(sqlite3.connect(app.config["DATABASE"])) as db:
        return db.execute("SELECT name, roll_number, course FROM students ORDER BY id").fetchall()


def test_login_page(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Welcome back" in response.data


def test_valid_login(client):
    assert b"Student records" in login(client).data
    with client.session_transaction() as session:
        assert session["user"] == "tester"


def test_invalid_login(client):
    response = post(client, "/login", {"username": "tester", "password": "wrong"})
    assert response.status_code == 401
    assert b"Incorrect username or password" in response.data


@pytest.mark.parametrize("url", ["/", "/students/new", "/students/1/edit"])
def test_pages_require_login(client, url):
    response = client.get(url)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_add_and_view_student(client, app):
    login(client)
    response = add(client)
    assert response.status_code == 200
    assert b"TEST001" in response.data
    assert records(app) == [("Test Student", "TEST001", "Engineering")]


@pytest.mark.parametrize("field", ["name", "roll_number", "course"])
def test_required_fields(client, app, field):
    login(client)
    data = {"name": "Student", "roll_number": "R1", "course": "CS"}
    data[field] = "   "
    response = post(client, "/students/new", data)
    assert response.status_code == 400
    assert records(app) == []


def test_duplicate_roll_number(client, app):
    login(client)
    add(client)
    response = add(client)
    assert response.status_code == 400
    assert b"already exists" in response.data
    assert len(records(app)) == 1


def test_edit_student(client, app):
    login(client)
    add(client)
    assert client.get("/students/1/edit").status_code == 200
    response = post(client, "/students/1/edit",
                    {"name": "Updated Student", "roll_number": "NEW001", "course": "IT"})
    assert response.status_code == 200
    assert records(app) == [("Updated Student", "NEW001", "IT")]


def test_edit_duplicate_preserves_record(client, app):
    login(client)
    add(client, "R1", "First")
    add(client, "R2", "Second")
    response = post(client, "/students/2/edit",
                    {"name": "Changed", "roll_number": "R1", "course": "IT"})
    assert response.status_code == 400
    assert records(app)[1] == ("Second", "R2", "Engineering")


def test_delete_student(client, app):
    login(client)
    add(client)
    assert post(client, "/students/1/delete").status_code == 200
    assert records(app) == []


def test_search(client):
    login(client)
    add(client, "AL1", "Alice")
    add(client, "BO2", "Bob")
    response = client.get("/?q=alice")
    assert b"AL1" in response.data
    assert b"BO2" not in response.data
    assert b"BO2" in client.get("/?q=BO2").data


def test_logout(client):
    login(client)
    post(client, "/logout")
    assert client.get("/").status_code == 302


def test_missing_csrf_rejected(client, app):
    login(client)
    assert client.post("/students/new", data={"name": "A", "roll_number": "R1", "course": "CS"}).status_code == 400
    assert records(app) == []


def test_unauthenticated_write_rejected(client, app):
    response = add(client)
    assert b"Welcome back" in response.data
    assert records(app) == []


def test_persistence_after_restart(client, app):
    login(client)
    add(client)
    restarted = create_app(dict(TESTING=True, SECRET_KEY="another-test-key", DATABASE=app.config["DATABASE"]))
    new_client = restarted.test_client()
    assert b"TEST001" in login(new_client).data


def test_student_html_is_escaped(client):
    login(client)
    response = add(client, name="<script>alert(1)</script>")
    assert b"<script>alert(1)</script>" not in response.data
    assert b"&lt;script&gt;" in response.data


def test_unknown_student(client):
    login(client)
    assert client.get("/students/999/edit").status_code == 404
    assert post(client, "/students/999/delete").status_code == 404


def test_long_field_rejected(client, app):
    login(client)
    assert add(client, name="A" * 101).status_code == 400
    assert records(app) == []


def test_stylesheet(client):
    response = client.get("/static/style.css")
    assert response.status_code == 200
    assert b".card" in response.data
