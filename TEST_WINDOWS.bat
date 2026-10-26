@echo off
setlocal
cd /d "%~dp0"
if not exist "venv\Scripts\python.exe" goto missing
"venv\Scripts\python.exe" -m pytest -v --junitxml=test-results.xml
if errorlevel 1 goto failed
"venv\Scripts\python.exe" -m build
if errorlevel 1 goto failed
"venv\Scripts\python.exe" scripts\check_wheel.py
if errorlevel 1 goto failed
echo Tests and build succeeded. Packages are in dist.
pause
exit /b 0
:missing
echo Run START_WINDOWS.bat first to install dependencies.
pause
exit /b 1
:failed
echo A check failed. Please read the error above.
pause
exit /b 1
