@echo off
cd /d "%~dp0"

echo Installing dependencies...
python -m pip install -r requirements.txt

echo.
echo Creating Excel report with custom input and output...
python src\analyze_expenses.py --input data\expenses.csv --output output\report_good.xlsx

echo.
echo Done. Check output\report_good.xlsx
echo.
echo Last log lines:
if exist output\run_log.txt type output\run_log.txt
pause
