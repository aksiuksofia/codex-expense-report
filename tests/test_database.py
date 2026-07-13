import sqlite3
import sys
from decimal import Decimal
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from database import (  # noqa: E402
    count_expenses,
    database_exists,
    delete_import,
    get_expenses,
    get_expenses_by_import,
    get_imports,
    initialize_database,
    make_row_hash,
    make_source_hash,
    normalize_expense_row,
    save_expenses,
    save_import,
)
from sections.import_section import save_import_to_database  # noqa: E402
from sections.history_section import (  # noqa: E402
    get_expense_total,
    get_selected_import,
    get_source_files,
)


def sample_expenses():
    return [
        {
            "date": "2026-01-05",
            "category": "Food",
            "description": "Groceries",
            "amount": 42.50,
        },
        {
            "date": "2026-01-06",
            "category": "Transport",
            "description": "Bus ticket",
            "amount": 3.25,
        },
    ]


def create_import(database_path, source_name="expenses.csv"):
    rows = sample_expenses()
    total_amount = sum(row["amount"] for row in rows)
    return save_import(
        source_name=source_name,
        row_count=len(rows),
        skipped_duplicates=0,
        total_amount=total_amount,
        source_hash=make_source_hash(source_name, len(rows), total_amount),
        database_path=database_path,
    )


def test_initialize_database_creates_file_and_tables(tmp_path):
    database_path = tmp_path / "expenses.db"

    initialize_database(database_path)

    assert database_exists(database_path)
    with sqlite3.connect(database_path) as connection:
        table_rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    table_names = {row[0] for row in table_rows}
    assert {"imports", "expenses"}.issubset(table_names)


def test_save_and_read_import_and_expenses(tmp_path):
    database_path = tmp_path / "expenses.db"
    import_id = create_import(database_path)

    result = save_expenses(
        import_id,
        sample_expenses(),
        source_file="expenses.csv",
        database_path=database_path,
    )

    assert result == {
        "rows_read": 2,
        "rows_saved": 2,
        "duplicates_skipped": 0,
        "import_id": import_id,
        "total_amount": 45.75,
    }
    assert count_expenses(database_path) == 2
    assert get_imports(database_path)[0]["import_id"] == import_id
    assert len(get_expenses(database_path)) == 2
    assert len(get_expenses_by_import(import_id, database_path)) == 2


def test_normalized_duplicate_expenses_are_skipped(tmp_path):
    database_path = tmp_path / "expenses.db"
    first_import_id = create_import(database_path, "first.csv")
    second_import_id = create_import(database_path, "second.csv")
    normalized_differently = [
        {
            "date": "2026/01/05",
            "category": "  Food  ",
            "description": " Groceries ",
            "amount": "42.500",
        },
        {
            "date": "2026-01-06 00:00:00",
            "category": "Transport ",
            "description": "Bus ticket",
            "amount": "3.2500",
        },
    ]

    save_expenses(first_import_id, sample_expenses(), "first.csv", database_path)
    result = save_expenses(
        second_import_id,
        normalized_differently,
        "second.csv",
        database_path,
    )

    assert result == {
        "rows_read": 2,
        "rows_saved": 0,
        "duplicates_skipped": 2,
        "import_id": second_import_id,
        "total_amount": 45.75,
    }
    assert count_expenses(database_path) == 2

    imports = {row["import_id"]: row for row in get_imports(database_path)}
    assert imports[second_import_id]["row_count"] == 0
    assert imports[second_import_id]["skipped_duplicates"] == 2


def test_repeated_import_of_the_same_rows_does_not_create_duplicates(tmp_path):
    database_path = tmp_path / "expenses.db"
    first_import_id = create_import(database_path, "first.csv")
    second_import_id = create_import(database_path, "second.csv")

    save_expenses(first_import_id, sample_expenses(), "first.csv", database_path)
    result = save_expenses(
        second_import_id,
        sample_expenses(),
        "second.csv",
        database_path,
    )

    assert result["rows_saved"] == 0
    assert result["duplicates_skipped"] == 2
    assert count_expenses(database_path) == 2


def test_row_hash_uses_normalized_date_text_amount_and_empty_description():
    original = {
        "date": "2026/01/05",
        "category": "  Food  ",
        "description": None,
        "amount": "42.500",
    }
    equivalent = {
        "date": "2026-01-05 00:00:00",
        "category": "Food",
        "description": "   ",
        "amount": 42.50,
    }

    normalized = normalize_expense_row(original, "first.csv")

    assert normalized == {
        "date": "2026-01-05",
        "category": "Food",
        "description": "",
        "amount": Decimal("42.50"),
        "source_file": "first.csv",
    }
    assert f"{normalized['amount']:.2f}" == "42.50"
    assert make_row_hash(original) == make_row_hash(equivalent)


def test_empty_description_is_normalized(tmp_path):
    database_path = tmp_path / "expenses.db"
    first_import_id = create_import(database_path, "first.csv")
    second_import_id = create_import(database_path, "second.csv")
    row_with_none = [
        {
            "date": "2026-02-01",
            "category": "Other",
            "description": None,
            "amount": 10,
        }
    ]
    row_with_spaces = [
        {
            "date": "2026-02-01",
            "category": "Other",
            "description": "   ",
            "amount": "10.00",
        }
    ]

    save_expenses(first_import_id, row_with_none, "first.csv", database_path)
    result = save_expenses(
        second_import_id,
        row_with_spaces,
        "second.csv",
        database_path,
    )

    assert result["duplicates_skipped"] == 1
    assert count_expenses(database_path) == 1


def test_delete_import_deletes_related_expenses(tmp_path):
    database_path = tmp_path / "expenses.db"
    import_id = create_import(database_path)
    save_expenses(import_id, sample_expenses(), "expenses.csv", database_path)

    deleted_count = delete_import(import_id, database_path)

    assert deleted_count == 1
    assert get_expenses_by_import(import_id, database_path) == []
    assert count_expenses(database_path) == 0
    assert get_imports(database_path) == []


def test_import_section_saves_valid_rows_to_database(tmp_path):
    database_path = tmp_path / "expenses.db"
    source_file = tmp_path / "expenses.csv"
    source_file.write_text("date,category,description,amount\n", encoding="utf-8")

    result = save_import_to_database(
        expenses=sample_expenses(),
        saved_files=[source_file],
        total_amount=45.75,
        database_path=database_path,
    )

    assert result["rows_read"] == 2
    assert result["rows_saved"] == 2
    assert result["duplicates_skipped"] == 0
    assert result["total_amount"] == 45.75
    assert count_expenses(database_path) == 2


def test_history_helpers_show_selected_import_total_and_source_files(tmp_path):
    database_path = tmp_path / "expenses.db"
    import_id = create_import(database_path)
    save_expenses(import_id, sample_expenses(), "expenses.csv", database_path)

    imports = get_imports(database_path)
    expenses = get_expenses_by_import(import_id, database_path)

    assert get_selected_import(imports, import_id)["source_name"] == "expenses.csv"
    assert get_expense_total(expenses) == 45.75
    assert get_source_files(expenses) == ["expenses.csv"]
