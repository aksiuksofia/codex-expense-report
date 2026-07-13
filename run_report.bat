@echo off
cd /d "%~dp0"

echo Installing dependencies...
python -m pip install -r requirements.txt

echo.
echo Creating Excel report...
python src\analyze_expenses.py

echo.
echo Done. Check output\expense_report.xlsx
echo.
echo Last log lines:
if exist output\run_log.txt type output\run_log.txt
pause
