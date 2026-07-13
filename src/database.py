import hashlib
import math
import sqlite3
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATABASE_PATH = BASE_DIR / "data" / "expenses.db"


def database_exists(database_path=DEFAULT_DATABASE_PATH):
    return Path(database_path).exists()


def get_connection(database_path=DEFAULT_DATABASE_PATH):
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(database_path=DEFAULT_DATABASE_PATH):
    database_path = Path(database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)

    with get_connection(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS imports (
                import_id INTEGER PRIMARY KEY AUTOINCREMENT,
                imported_at TEXT NOT NULL,
                source_name TEXT NOT NULL,
                row_count INTEGER NOT NULL,
                skipped_duplicates INTEGER NOT NULL,
                total_amount REAL NOT NULL,
                source_hash TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
                import_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                source_file TEXT NOT NULL,
                row_hash TEXT NOT NULL UNIQUE,
                FOREIGN KEY (import_id)
                    REFERENCES imports (import_id)
                    ON DELETE CASCADE
            )
            """
        )

    if not database_path.exists():
        raise FileNotFoundError(f"Database was not created: {database_path}")

    return database_path


def make_source_hash(source_name, row_count, total_amount):
    text = f"{source_name}|{row_count}|{total_amount:.2f}"
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _is_missing(value):
    if value is None:
        return True
    if isinstance(value, float):
        return math.isnan(value)
    return False


def normalize_date(value):
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()

    text = str(value).strip()
    for date_format in ("%Y-%m-%d", "%Y/%m/%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(text[:10], date_format).date().isoformat()
        except ValueError:
            continue

    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date().isoformat()
    except ValueError as error:
        raise ValueError(f"Invalid date value: {value}") from error


def normalize_text(value, empty_if_missing=False):
    if _is_missing(value):
        return "" if empty_if_missing else ""
    return str(value).strip()


def normalize_amount(value):
    return Decimal(str(value).strip()).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def normalize_expense_row(row, source_file=""):
    return {
        "date": normalize_date(row["date"]),
        "category": normalize_text(row["category"]),
        "description": normalize_text(
            row.get("description"),
            empty_if_missing=True,
        ),
        "amount": normalize_amount(row["amount"]),
        "source_file": normalize_text(row.get("source_file") or source_file),
    }


def make_row_hash(row, source_file=None):
    normalized = normalize_expense_row(row, source_file or "")
    text = "|".join(
        [
            normalized["date"],
            normalized["category"],
            normalized["description"],
            f"{normalized['amount']:.2f}",
        ]
    )
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def save_import(
    source_name,
    row_count,
    skipped_duplicates,
    total_amount,
    source_hash,
    database_path=DEFAULT_DATABASE_PATH,
):
    initialize_database(database_path)

    with get_connection(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO imports (
                imported_at,
                source_name,
                row_count,
                skipped_duplicates,
                total_amount,
                source_hash
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                source_name,
                int(row_count),
                int(skipped_duplicates),
                float(total_amount),
                source_hash,
            ),
        )
        return cursor.lastrowid


def _records_from_expenses(expenses):
    if hasattr(expenses, "to_dict"):
        return expenses.to_dict("records")
    return list(expenses)


def save_expenses(
    import_id,
    expenses,
    source_file,
    database_path=DEFAULT_DATABASE_PATH,
):
    initialize_database(database_path)
    records = _records_from_expenses(expenses)
    saved_count = 0
    skipped_duplicates = 0
    total_amount = Decimal("0.00")

    with get_connection(database_path) as connection:
        for row in records:
            normalized = normalize_expense_row(row, source_file)
            row_hash = make_row_hash(normalized)
            total_amount += normalized["amount"]
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO expenses (
                    import_id,
                    date,
                    category,
                    description,
                    amount,
                    source_file,
                    row_hash
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    import_id,
                    normalized["date"],
                    normalized["category"],
                    normalized["description"],
                    float(normalized["amount"]),
                    normalized["source_file"],
                    row_hash,
                ),
            )

            if cursor.rowcount == 1:
                saved_count += 1
            else:
                skipped_duplicates += 1

        connection.execute(
            """
            UPDATE imports
            SET row_count = ?, skipped_duplicates = ?, total_amount = ?
            WHERE import_id = ?
            """,
            (
                saved_count,
                skipped_duplicates,
                float(total_amount),
                import_id,
            ),
        )

    return {
        "rows_read": len(records),
        "rows_saved": saved_count,
        "duplicates_skipped": skipped_duplicates,
        "import_id": import_id,
        "total_amount": float(total_amount),
    }


def _rows_to_dicts(rows):
    return [dict(row) for row in rows]


def get_imports(database_path=DEFAULT_DATABASE_PATH):
    initialize_database(database_path)

    with get_connection(database_path) as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM imports
            ORDER BY imported_at DESC, import_id DESC
            """
        ).fetchall()

    return _rows_to_dicts(rows)


def get_expenses(database_path=DEFAULT_DATABASE_PATH):
    initialize_database(database_path)

    with get_connection(database_path) as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM expenses
            ORDER BY date, expense_id
            """
        ).fetchall()

    return _rows_to_dicts(rows)


def get_expenses_by_import(import_id, database_path=DEFAULT_DATABASE_PATH):
    initialize_database(database_path)

    with get_connection(database_path) as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM expenses
            WHERE import_id = ?
            ORDER BY date, expense_id
            """,
            (import_id,),
        ).fetchall()

    return _rows_to_dicts(rows)


def delete_import(import_id, database_path=DEFAULT_DATABASE_PATH):
    initialize_database(database_path)

    with get_connection(database_path) as connection:
        cursor = connection.execute(
            """
            DELETE FROM imports
            WHERE import_id = ?
            """,
            (import_id,),
        )
        return cursor.rowcount


def count_expenses(database_path=DEFAULT_DATABASE_PATH):
    initialize_database(database_path)

    with get_connection(database_path) as connection:
        row = connection.execute("SELECT COUNT(*) AS count FROM expenses").fetchone()

    return row["count"]
