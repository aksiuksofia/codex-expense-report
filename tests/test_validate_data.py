from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from validate_data import validate_csv


def write_csv(path, content):
    path.write_text(content, encoding="utf-8")


def test_good_file_passes_validation(tmp_path):
    csv_file = tmp_path / "good.csv"
    write_csv(
        csv_file,
        "\n".join(
            [
                "date,category,description,amount",
                "2026-06-01,Food,Lunch,12.50",
                "2026-06-02,Transport,Bus,2.25",
            ]
        ),
    )

    assert validate_csv(csv_file) == []


def test_file_without_required_column_fails(tmp_path):
    csv_file = tmp_path / "missing_column.csv"
    write_csv(
        csv_file,
        "\n".join(
            [
                "date,category,description",
                "2026-06-01,Food,Lunch",
            ]
        ),
    )

    errors = validate_csv(csv_file)

    assert any("Missing required columns" in error for error in errors)
    assert any("amount" in error for error in errors)


def test_file_with_negative_amount_fails(tmp_path):
    csv_file = tmp_path / "negative_amount.csv"
    write_csv(
        csv_file,
        "\n".join(
            [
                "date,category,description,amount",
                "2026-06-01,Health,Medicine,-5.00",
            ]
        ),
    )

    errors = validate_csv(csv_file)

    assert any("Negative expenses" in error for error in errors)


def test_file_with_text_amount_fails(tmp_path):
    csv_file = tmp_path / "text_amount.csv"
    write_csv(
        csv_file,
        "\n".join(
            [
                "date,category,description,amount",
                "2026-06-01,Shopping,Shoes,not-a-number",
            ]
        ),
    )

    errors = validate_csv(csv_file)

    assert any("Non-numeric amount" in error for error in errors)
