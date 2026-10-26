# Student Management System — DevOps CI Project

A complete local Flask application with login, student add/view/edit/delete,
search, SQLite storage, pytest tests, and a GitHub Actions build workflow.

## Start here on Windows

1. Stop the old Flask application: in its VS Code terminal press Ctrl+C.
2. Right-click the downloaded ZIP and select **Extract All**.
3. Open the extracted **student-management-ci-complete** folder.
   You must be able to see app.py, requirements.txt and START_WINDOWS.bat.
   Do not merge this folder with your old project.
4. Double-click **START_WINDOWS.bat**. Internet is needed to install packages.
5. On the first launch, choose a username and password in the terminal.
   Password must have at least 8 characters. While typing it, nothing appears;
   this is normal. Press Enter, then type the same password again.
6. When it says the server is running, open http://127.0.0.1:5000 in Chrome.
7. Log in using the username and password you just chose.
8. Keep the terminal window open. Ctrl+C stops the application.

Python 3.12 must be installed and available as the python command.
Your Python 3.12.10 installation is suitable. A virtual environment is
created automatically; no activation or PowerShell policy change is needed.
If setup fails, the window stays open so you can copy its error.

## Run from VS Code instead

File → Open Folder → choose the extracted folder containing app.py.
Terminal → New Terminal. Run ONLY these commands, one at a time:

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe app.py
```

On subsequent starts, only the last command is needed.
Do not type the terminal address or its > symbol.
The username/password prompts appear only when no user exists.

## What to demonstrate in the website

1. Log in with your chosen account.
2. Click Add student. Enter Test Student, TEST001, Computer Engineering.
3. Save; the student appears in the records table.
4. Edit the student and change the course to Information Technology.
5. Search for TEST001; clear the search to show all records.
6. Add a second sample record, then delete that sample and confirm.
7. Try reusing TEST001: duplicate roll numbers are rejected.
8. Sign out. Visiting the records page now redirects to login.
9. Restart the application and log in: saved records remain.

## Where the data is stored

The database is **instance/students.db**, created automatically at first launch.
SQLite stores students and password hashes in this file on your computer.
It is not PostgreSQL and it is not a cloud database.
Do not delete this file if you want to keep your records.
The Git ignore rules exclude the database, virtual environment and credentials.
This fresh project does not automatically import your old students.db.

To reset a forgotten password, stop the server and run:

```powershell
.\venv\Scripts\python.exe app.py --setup
```

Enter the existing username and choose a new password. Other accounts are
unchanged. Use the same command to create another local account.

## Automated tests and build

After running the setup once, double-click **TEST_WINDOWS.bat**, or run:

```powershell
.\venv\Scripts\python.exe -m pytest -v --junitxml=test-results.xml
.\venv\Scripts\python.exe -m build
.\venv\Scripts\python.exe scripts/check_wheel.py
```

The suite has 23 tests including parameterized cases. It checks login,
access restrictions, add/view/edit/delete, duplicate rolls, empty fields,
length limits, search, logout, missing records, CSRF protection, escaped
HTML, persistence, and CSS delivery. Tests use temporary databases and
do not delete your local records.

These are automated application/request tests using Flask's test client;
they do not operate a real browser or claim Selenium coverage.

The build creates a real Python wheel (.whl) and source distribution
(.tar.gz) in dist/. The wheel contains the application package, templates
and stylesheet. The smoke check installs the wheel into a fresh temporary
environment and verifies it works outside the source folder. It needs
internet to install the wheel's dependencies.

## Upload to GitHub — the DevOps part

GitHub Actions does not run just by extracting this ZIP. Push the project
to your GitHub repository to execute the supplied workflow.

1. Sign in at https://github.com.
2. Create a new repository named **student-management-ci**.
3. Choose its visibility. Leave Add README, .gitignore and license
   unchecked because this folder already contains the project files.
4. Create the repository and copy its HTTPS repository URL.
5. In VS Code, open this extracted project and use its terminal.
6. Check Git:

```powershell
git --version
```

If Git is not recognised, install Git for Windows, then fully reopen VS Code.

7. Run these commands. Replace the quoted identity values with your name
   and your GitHub email (or the no-reply email from GitHub email settings):

```powershell
git init
git config user.name "Your Name"
git config user.email "your-email@example.com"
git add .
git status
```

Review the file list. It should include .github/workflows/ci.yml,
student_ci, tests, scripts and the top-level code/configuration.
It should not include venv or instance/students.db.

```powershell
git commit -m "Add student management app with CI tests and build"
git branch -M main
```

8. Replace YOUR_USERNAME in the next command with your actual GitHub name:

```powershell
git remote add origin https://github.com/YOUR_USERNAME/student-management-ci.git
git push -u origin main
```

Complete Git's browser sign-in if prompted. Do not paste your password
or any access token into chat.

9. Open the repository in your browser → **Actions** → **Student Management CI**.
10. Open the run, then **test-and-build**, to inspect each step.
11. A successful run should show green checks. Under the run's Artifacts,
    download **test-results** and **student-management-build**.

The workflow runs on pushes and pull requests and can also be started
manually through Actions → Student Management CI → Run workflow.
It uses a GitHub-hosted Ubuntu runner with Python 3.12. Steps:

| Step | Purpose |
|---|---|
| Checkout | Download the repository code to the runner |
| Set up Python | Select the interpreter |
| Install dependencies | Install the pinned requirements |
| Tests | Verify application behavior; produce JUnit XML |
| Build | Create wheel and source distribution |
| Wheel check | Verify packaged HTML/CSS and application imports |
| Upload artifacts | Preserve test results and successful builds |

If tests fail, normal subsequent build steps are skipped. Test-result
upload runs even after failure, if the XML report was produced.
This is continuous integration, not automatic online deployment.

## Show a failure and a fix to your examiner

Use a temporary branch so the main branch remains intact:

```powershell
git switch -c demo-ci-failure
```

Create a file **tests/test_demo_failure.py** in VS Code containing:

```python
def test_intentional_ci_failure():
    assert False, "Intentional demonstration: CI must catch this failure."
```

Save it and run:

```powershell
git add tests/test_demo_failure.py
git commit -m "Demonstrate CI detecting an intentional test failure"
git push -u origin demo-ci-failure
```

Open Actions and show the failed run. Then delete only that deliberately
created test file in VS Code, save the fix with the commands below:

```powershell
git add -u
git commit -m "Remove intentional failure and restore passing CI"
git push
```

Show the new successful run and its build artifact. Return to main:

```powershell
git switch main
```

## Project files

| File/folder | Role |
|---|---|
| app.py | Start server and create/reset local login |
| student_ci/__init__.py | Routes, authentication, validation, database |
| student_ci/templates/ | All HTML pages (already in correct location) |
| student_ci/static/style.css | Website styles |
| tests/test_app.py | Application test suite |
| scripts/check_wheel.py | Verify the installable build |
| .github/workflows/ci.yml | GitHub Actions pipeline |
| pyproject.toml | Python package/build metadata |
| requirements.txt | Pinned setup and testing dependencies |
| START_WINDOWS.bat | Windows setup and launch |
| TEST_WINDOWS.bat | Windows test/build/check launcher |
| instance/students.db | Runtime database; not included in ZIP or Git |

## Troubleshooting

- **TemplateNotFound:** extract the entire ZIP, not just app.py. Templates
  now belong under student_ci/templates; leave this structure as supplied.
- **Port 5000 already in use:** stop the old server with Ctrl+C.
  Alternatively run app.py --port 5001, then visit http://127.0.0.1:5001.
- **Password entry looks blank:** passwords are hidden while you type.
- **Form expired:** refresh the page, then try again. Restarting the server
  signs you out because a new session signing key is generated.
- **ModuleNotFoundError:** run START_WINDOWS.bat or reinstall requirements
  using the exact virtual-environment Python command above.
- **Python was not found:** check python --version in a fresh terminal.
- **No Actions run:** check that .github/workflows/ci.yml was committed and
  pushed, and that Actions is enabled for the repository.
- **Old records not visible:** this is a separate fresh project. Keep your
  original folder as a backup; this ZIP does not migrate it automatically.

## Scope and explanation for viva

"We use Git and GitHub for version control. When code changes are pushed,
GitHub Actions installs dependencies, runs automated tests, builds the
application package and saves artifacts. This detects regressions early
and makes our build repeatable."

The application runs locally; CI runs separately on GitHub. Test data is
temporary. The workflow does not upload your local database.
Passwords are hashed, forms use CSRF tokens, and SQL uses bound parameters.
This is an educational local application. Internet hosting would additionally
need production configuration, HTTPS, a production server, durable secrets,
backups and login rate limiting. No hosting setup is included.

## Reference documentation

- https://docs.github.com/en/actions/tutorials/build-and-test-code/python
- https://github.com/actions/upload-artifact

## Validation

See VALIDATION.txt for the checks performed when preparing this ZIP.
The actual GitHub-hosted run must still be performed in your own repository.
