import argparse
from pathlib import Path

try:
    import pandas as pd  # noqa: F401
except ModuleNotFoundError:
    print("Missing library: pandas")
    print("Install project dependencies with this command:")
    print("pip install -r requirements.txt")
    raise SystemExit(1)

from analytics import (
    calculate_category_totals,
    calculate_month_category_totals,
    calculate_month_totals,
    calculate_summary,
)
from importer import count_csv_rows, read_expenses
from logging_config import LOG_FILE, write_log
from report import create_excel_report
from validate_data import print_validation_errors, validate_csv


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_INPUT_FILE = BASE_DIR / "data" / "expenses.csv"
DEFAULT_OUTPUT_FILE = BASE_DIR / "output" / "expense_report.xlsx"


def wait_before_close():
    try:
        input("\nPress Enter to close...")
    except EOFError:
        pass


def parse_args():
    parser = argparse.ArgumentParser(description="Create an Excel expense report.")
    parser.add_argument("--input", default=DEFAULT_INPUT_FILE, help="Path to the input CSV file.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_FILE, help="Path to the output Excel file.")
    return parser.parse_args()


def print_report(total_amount, average_expense, biggest_expense, category_totals, output_file):
    print("Expense analysis")
    print("================")
    print(f"Total amount: {total_amount:.2f}")
    print(f"Average expense: {average_expense:.2f}")
    print()
    print("Amount by category:")
    for _, row in category_totals.iterrows():
        print(f"- {row['category']}: {row['amount']:.2f}")
    print()
    print("Biggest expense:")
    print(f"Date: {biggest_expense['date']}")
    print(f"Category: {biggest_expense['category']}")
    print(f"Description: {biggest_expense['description']}")
    print(f"Amount: {biggest_expense['amount']:.2f}")
    print()
    print(f"Excel report saved to: {output_file}")
    print("Excel report file check: OK")


def main():
    exit_code = 0
    input_file = DEFAULT_INPUT_FILE
    output_file = DEFAULT_OUTPUT_FILE
    try:
        args = parse_args()
        input_file = Path(args.input)
        output_file = Path(args.output)
        row_count = count_csv_rows(input_file)
        validation_errors = validate_csv(input_file)
        if validation_errors:
            print_validation_errors(validation_errors)
            write_log(input_file, output_file, row_count, "ERROR", error_text="; ".join(validation_errors))
            exit_code = 1
        else:
            expenses = read_expenses(input_file)
            report_data = create_excel_report(expenses, output_file)
            print_report(*report_data, output_file)
            write_log(input_file, output_file, len(expenses), "SUCCESS", total_amount=report_data[0])
    except ImportError as error:
        library_name = getattr(error, "name", None) or "pandas/openpyxl"
        print(f"Missing library: {library_name}")
        print("Install project dependencies with this command:")
        print("pip install -r requirements.txt")
        write_log(input_file, output_file, "unknown", "ERROR", error_text=f"Missing library: {library_name}")
        exit_code = 1
    except Exception as error:
        print(f"Error: {error}")
        write_log(input_file, output_file, count_csv_rows(input_file), "ERROR", error_text=str(error))
        exit_code = 1
    finally:
        wait_before_close()
    if exit_code:
        raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
