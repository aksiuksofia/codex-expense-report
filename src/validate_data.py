import argparse
from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = {"date", "category", "description", "amount"}


def wait_before_close():
    try:
        input("\nPress Enter to close...")
    except EOFError:
        pass


def validate_csv(input_file):
    input_path = Path(input_file)
    errors = []

    if not input_path.exists():
        return [f"Input file does not exist: {input_path}"]

    try:
        data = pd.read_csv(input_path)
    except Exception as error:
        return [f"Could not read CSV file: {error}"]

    missing_columns = REQUIRED_COLUMNS - set(data.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        errors.append(f"Missing required columns: {missing}")

    if errors:
        return errors

    empty_dates = data["date"].isna() | (data["date"].astype(str).str.strip() == "")
    if empty_dates.any():
        rows = ", ".join(str(index + 2) for index in data.index[empty_dates])
        errors.append(f"Empty dates found in rows: {rows}")

    empty_categories = data["category"].isna() | (
        data["category"].astype(str).str.strip() == ""
    )
    if empty_categories.any():
        rows = ", ".join(str(index + 2) for index in data.index[empty_categories])
        errors.append(f"Empty categories found in rows: {rows}")

    amounts = pd.to_numeric(data["amount"], errors="coerce")
    bad_amounts = amounts.isna()
    if bad_amounts.any():
        rows = ", ".join(str(index + 2) for index in data.index[bad_amounts])
        errors.append(f"Non-numeric amount values found in rows: {rows}")

    negative_amounts = amounts < 0
    if negative_amounts.any():
        rows = ", ".join(str(index + 2) for index in data.index[negative_amounts])
        errors.append(f"Negative expenses found in rows: {rows}")

    dates = pd.to_datetime(data["date"], errors="coerce")
    bad_dates = dates.isna()
    if bad_dates.any():
        rows = ", ".join(str(index + 2) for index in data.index[bad_dates])
        errors.append(f"Invalid date values found in rows: {rows}")

    return errors


def print_validation_errors(errors):
    print("Data validation failed.")
    print("Excel report was not created.")
    print()
    print("Problems found:")

    for error in errors:
        print(f"- {error}")


def parse_args():
    parser = argparse.ArgumentParser(description="Validate an expense CSV file.")
    parser.add_argument(
        "--input",
        default=Path(__file__).resolve().parent.parent / "data" / "expenses.csv",
        help="Path to the CSV file.",
    )
    return parser.parse_args()


def main():
    exit_code = 0

    try:
        args = parse_args()
        errors = validate_csv(args.input)

        if errors:
            print_validation_errors(errors)
            exit_code = 1
        else:
            print("Data validation passed.")
            print(f"CSV file is OK: {args.input}")
    except Exception as error:
        print(f"Error: {error}")
        exit_code = 1
    finally:
        wait_before_close()

    if exit_code:
        raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
