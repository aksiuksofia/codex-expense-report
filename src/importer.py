from pathlib import Path

import pandas as pd

from validate_data import validate_csv


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"
UPLOAD_DIR = OUTPUT_DIR / "uploads"
STREAMLIT_REPORT = OUTPUT_DIR / "streamlit_expense_report.xlsx"
DEMO_EXPENSES = BASE_DIR / "data" / "demo_expenses.csv"


def get_demo_file():
    if not DEMO_EXPENSES.exists():
        raise FileNotFoundError(f"Demo file was not found: {DEMO_EXPENSES}")
    return DEMO_EXPENSES


def read_expenses(input_file, include_source_file=False):
    expenses = pd.read_csv(input_file)
    expenses["amount"] = pd.to_numeric(expenses["amount"])
    expenses["date"] = pd.to_datetime(expenses["date"])
    expenses["month"] = expenses["date"].dt.strftime("%Y-%m")
    expenses["date"] = expenses["date"].dt.strftime("%Y-%m-%d")
    if include_source_file:
        expenses["source_file"] = Path(input_file).name
    return expenses


def count_csv_rows(input_file):
    try:
        return len(pd.read_csv(input_file))
    except Exception:
        return "unknown"


def save_uploaded_file(uploaded_file):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    input_file = UPLOAD_DIR / uploaded_file.name
    with input_file.open("wb") as file:
        file.write(uploaded_file.getbuffer())
    if not input_file.exists():
        raise FileNotFoundError(f"Uploaded file was not saved: {input_file}")
    return input_file


def read_valid_expenses(input_file):
    return read_expenses(input_file, include_source_file=True)


def validate_expense_files(input_files):
    if not input_files:
        raise ValueError("Please upload at least one CSV file.")

    all_errors = []
    for input_file in input_files:
        validation_errors = validate_csv(input_file)
        if validation_errors:
            all_errors.append((Path(input_file).name, validation_errors))
    return all_errors


def combine_valid_expense_files(input_files):
    all_errors = validate_expense_files(input_files)
    if all_errors:
        details = "; ".join(
            f"{filename}: {', '.join(errors)}"
            for filename, errors in all_errors
        )
        raise ValueError(f"CSV validation failed. {details}")

    tables = [read_valid_expenses(input_file) for input_file in input_files]
    return pd.concat(tables, ignore_index=True)
