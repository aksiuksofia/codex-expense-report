@echo off
cd /d "%~dp0"

echo Installing dependencies...
python -m pip install -r requirements.txt

echo.
echo Starting web interface...
echo Open this address in your browser:
echo http://127.0.0.1:5000
echo.
python src\web_app.py

pause
