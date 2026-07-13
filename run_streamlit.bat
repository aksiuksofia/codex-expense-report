@echo off
cd /d "%~dp0"

echo Installing dependencies...
python -m pip install -r requirements.txt

echo.
echo Starting Streamlit app...
echo If the browser does not open automatically, use this address:
echo http://localhost:8501
echo.
python -m streamlit run src\app.py

pause
