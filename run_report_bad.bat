@echo off
cd /d "%~dp0"

echo Running report with bad test data...
python src\analyze_expenses.py --input data\expenses_bad.csv --output output\report_bad.xlsx

echo.
echo Expected result: validation errors should be shown, and report_bad.xlsx should not be created.
echo.
echo Last log lines:
if exist output\run_log.txt type output\run_log.txt
pause
