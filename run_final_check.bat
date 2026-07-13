@echo off
cd /d "%~dp0"

echo Installing dependencies...
python -m pip install -r requirements.txt

echo.
echo 1) Default report run
python src\analyze_expenses.py

echo.
echo 2) Good CSV with custom output
python src\analyze_expenses.py --input data\expenses.csv --output output\report_good.xlsx

echo.
echo 3) Bad CSV should show errors and should not create a valid report
if exist output\report_bad.xlsx del output\report_bad.xlsx
python src\analyze_expenses.py --input data\expenses_bad.csv --output output\report_bad.xlsx

echo.
echo 4) Running tests
python -m pytest

echo.
echo Output folder:
dir output

echo.
echo Run log:
if exist output\run_log.txt type output\run_log.txt

echo.
pause
