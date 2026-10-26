"""Install the built wheel in a clean environment and verify packaged assets."""
import os
from pathlib import Path
import subprocess
import tempfile
import venv

root = Path(__file__).resolve().parents[1]
wheels = list((root / "dist").glob("*.whl"))
if len(wheels) != 1:
    raise SystemExit("Expected exactly one wheel in dist/.")
with tempfile.TemporaryDirectory() as temporary:
    target = Path(temporary)
    venv.create(target / "env", with_pip=True)
    python = target / "env" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    subprocess.run([str(python), "-m", "pip", "install", str(wheels[0])], check=True)
    code = """
from student_ci import create_app
app = create_app({"TESTING": True, "DATABASE": "smoke.db"})
client = app.test_client()
assert client.get("/login").status_code == 200
assert client.get("/static/style.css").status_code == 200
with client.session_transaction() as session:
    session["user"] = "packaging-check"
assert client.get("/").status_code == 200
assert client.get("/students/new").status_code == 200
print("Installed wheel: imports, templates, CSS and database all work.")
"""
    subprocess.run([str(python), "-c", code], cwd=target, check=True)
