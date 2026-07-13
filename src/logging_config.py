from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
LOG_FILE = BASE_DIR / "output" / "run_log.txt"


def write_log(
    input_file,
    output_file,
    row_count,
    status,
    total_amount=None,
    error_text=None,
):
    LOG_FILE.parent.mkdir(exist_ok=True)
    lines = [
        "Run",
        f"time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"input_csv: {input_file}",
        f"output_excel: {output_file}",
        f"csv_rows: {row_count}",
        f"status: {status}",
    ]
    if total_amount is not None:
        lines.append(f"total_amount: {total_amount:.2f}")
    if error_text:
        lines.append(f"error: {error_text}")
    lines.append("")

    with LOG_FILE.open("a", encoding="utf-8") as log_file:
        log_file.write("\n".join(lines))
        log_file.write("\n")


def write_deletion_log(import_id, source_name, deleted_expenses):
    LOG_FILE.parent.mkdir(exist_ok=True)
    lines = [
        "Database action",
        f"time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "action: DELETE_IMPORT",
        f"import_id: {import_id}",
        f"source_name: {source_name}",
        f"deleted_expenses: {deleted_expenses}",
        "status: SUCCESS",
        "",
    ]
    with LOG_FILE.open("a", encoding="utf-8") as log_file:
        log_file.write("\n".join(lines))
