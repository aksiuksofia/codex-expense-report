from pathlib import Path

from flask import Flask, redirect, render_template_string, request, send_file, url_for
from werkzeug.utils import secure_filename

from analyze_expenses import (
    count_csv_rows,
    create_excel_report,
    read_expenses,
    write_log,
)
from validate_data import validate_csv


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"
UPLOAD_DIR = OUTPUT_DIR / "uploads"
WEB_REPORT_FILE = OUTPUT_DIR / "web_expense_report.xlsx"

app = Flask(__name__)


PAGE_TEMPLATE = """
<!doctype html>
<html lang="ru">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Expense Report</title>
    <style>
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #f4f6f8;
            color: #1f2933;
        }
        main {
            max-width: 960px;
            margin: 0 auto;
            padding: 32px 20px;
        }
        h1 {
            margin: 0 0 8px;
            font-size: 28px;
        }
        p {
            line-height: 1.5;
        }
        .panel {
            background: #ffffff;
            border: 1px solid #d8dee6;
            border-radius: 8px;
            padding: 20px;
            margin-top: 20px;
        }
        label {
            display: block;
            font-weight: 700;
            margin-bottom: 8px;
        }
        input[type="file"] {
            display: block;
            margin-bottom: 16px;
        }
        button,
        .button {
            display: inline-block;
            border: 0;
            border-radius: 6px;
            background: #2563eb;
            color: #ffffff;
            padding: 10px 14px;
            font-weight: 700;
            text-decoration: none;
            cursor: pointer;
        }
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 12px;
        }
        .metric {
            border: 1px solid #d8dee6;
            border-radius: 6px;
            padding: 12px;
            background: #fafbfc;
        }
        .metric strong {
            display: block;
            margin-bottom: 6px;
            font-size: 13px;
            color: #52606d;
        }
        ul {
            margin-bottom: 0;
        }
        .error {
            border-color: #f5b7b1;
            background: #fff5f5;
        }
        .success {
            border-color: #a7d7c5;
            background: #f3fbf7;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 12px;
        }
        th,
        td {
            border-bottom: 1px solid #e1e7ef;
            padding: 8px;
            text-align: left;
        }
    </style>
</head>
<body>
    <main>
        <h1>Анализ расходов</h1>
        <p>Загрузите CSV-файл с колонками <code>date</code>, <code>category</code>, <code>description</code>, <code>amount</code>.</p>

        <section class="panel">
            <form method="post" enctype="multipart/form-data">
                <label for="csv_file">CSV-файл</label>
                <input id="csv_file" name="csv_file" type="file" accept=".csv" required>
                <button type="submit">Создать отчет</button>
            </form>
        </section>

        {% if errors %}
            <section class="panel error">
                <h2>CSV-файл не прошел проверку</h2>
                <ul>
                    {% for error in errors %}
                        <li>{{ error }}</li>
                    {% endfor %}
                </ul>
            </section>
        {% endif %}

        {% if summary %}
            <section class="panel success">
                <h2>Краткая сводка</h2>
                <div class="summary">
                    <div class="metric">
                        <strong>Строк в CSV</strong>
                        {{ summary.row_count }}
                    </div>
                    <div class="metric">
                        <strong>Общая сумма</strong>
                        {{ "%.2f"|format(summary.total_amount) }}
                    </div>
                    <div class="metric">
                        <strong>Средний расход</strong>
                        {{ "%.2f"|format(summary.average_expense) }}
                    </div>
                    <div class="metric">
                        <strong>Самый большой расход</strong>
                        {{ summary.biggest_description }} — {{ "%.2f"|format(summary.biggest_amount) }}
                    </div>
                </div>

                <h3>По категориям</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Категория</th>
                            <th>Сумма</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for row in category_rows %}
                            <tr>
                                <td>{{ row.category }}</td>
                                <td>{{ "%.2f"|format(row.amount) }}</td>
                            </tr>
                        {% endfor %}
                    </tbody>
                </table>

                <p>
                    <a class="button" href="{{ url_for('download_report') }}">Скачать Excel-отчет</a>
                </p>
            </section>
        {% endif %}
    </main>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    errors = []
    summary = None
    category_rows = []

    if request.method == "POST":
        uploaded_file = request.files.get("csv_file")

        if uploaded_file is None or uploaded_file.filename == "":
            errors = ["Choose a CSV file before creating a report."]
        else:
            filename = secure_filename(uploaded_file.filename)
            UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            input_file = UPLOAD_DIR / filename
            uploaded_file.save(input_file)

            errors = validate_csv(input_file)
            row_count = count_csv_rows(input_file)

            if errors:
                write_log(
                    input_file=input_file,
                    output_file=WEB_REPORT_FILE,
                    row_count=row_count,
                    status="ERROR",
                    error_text="; ".join(errors),
                )
            else:
                expenses = read_expenses(input_file)
                report_data = create_excel_report(expenses, WEB_REPORT_FILE)
                total_amount, average_expense, biggest_expense, category_totals = report_data

                if not WEB_REPORT_FILE.exists():
                    errors = [f"Excel report was not created: {WEB_REPORT_FILE}"]
                else:
                    write_log(
                        input_file=input_file,
                        output_file=WEB_REPORT_FILE,
                        row_count=len(expenses),
                        status="SUCCESS",
                        total_amount=total_amount,
                    )

                    summary = {
                        "row_count": len(expenses),
                        "total_amount": total_amount,
                        "average_expense": average_expense,
                        "biggest_description": biggest_expense["description"],
                        "biggest_amount": biggest_expense["amount"],
                    }
                    category_rows = category_totals.to_dict("records")

    return render_template_string(
        PAGE_TEMPLATE,
        errors=errors,
        summary=summary,
        category_rows=category_rows,
    )


@app.route("/download")
def download_report():
    if not WEB_REPORT_FILE.exists():
        return redirect(url_for("index"))

    return send_file(WEB_REPORT_FILE, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
