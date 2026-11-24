@echo off
cd /d "%~dp0"
py -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
if not exist .env copy .env.example .env
echo.
echo Setup complete.
echo 1. Open the .env file in Notepad.
echo 2. Paste your N2YO API key after N2YO_API_KEY=
echo 3. Save the file.
echo 4. Double-click run_windows_after_setup.bat to start the dashboard.
pause
