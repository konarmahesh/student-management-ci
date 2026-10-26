@echo off
setlocal
cd /d "%~dp0"
if exist "venv\Scripts\python.exe" goto install
python --version >nul 2>&1
if errorlevel 1 goto no_python
python -m venv venv
if errorlevel 1 goto failed
:install
"venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
echo.
echo First launch: choose your username and password when asked.
echo Password typing is hidden. This is normal.
echo Once the server starts, open http://127.0.0.1:5000 in Chrome.
echo Keep this window open. Press Ctrl+C to stop.
echo.
"venv\Scripts\python.exe" app.py
pause
exit /b
:no_python
echo Python was not found. Install Python 3.12 and enable Add Python to PATH.
pause
exit /b 1
:failed
echo Setup failed. Please send the error shown above for help.
pause
exit /b 1
