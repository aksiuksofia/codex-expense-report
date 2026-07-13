import streamlit as st

from app_config import is_cloud_mode
from analytics import build_analysis_tables, filter_expenses, prepare_expenses
from database import get_expenses, get_imports
from report import build_filtered_excel_report
from session_data import get_current_session_expenses


def render_filters(expenses, imports):
    st.subheader("Filters")
    minimum_date = expenses["date"].min().date()
    maximum_date = expenses["date"].max().date()
    first_column, second_column = st.columns(2)
    start_date = first_column.date_input(
        "Start date",
        value=minimum_date,
        min_value=minimum_date,
        max_value=maximum_date,
    )
    end_date = second_column.date_input(
        "End date",
        value=maximum_date,
        min_value=minimum_date,
        max_value=maximum_date,
    )
    categories = st.multiselect(
        "Categories",
        options=sorted(expenses["category"].unique()),
        placeholder="All categories",
    )
    import_ids = []
    if "import_id" in expenses.columns:
        import_labels = {
            item["import_id"]: f"{item['import_id']}: {item['source_name']}"
            for item in imports
        }
        import_ids = st.multiselect(
            "Imports",
            options=sorted(expenses["import_id"].unique()),
            format_func=lambda import_id: import_labels.get(
                import_id,
                f"Import {import_id}",
            ),
            placeholder="All imports",
        )
    description_text = st.text_input("Search in description")
    return start_date, end_date, categories, import_ids, description_text


def render_summary(expenses):
    st.subheader("Summary")
    maximum = expenses.loc[expenses["amount"].idxmax(), "amount"]
    minimum = expenses.loc[expenses["amount"].idxmin(), "amount"]
    values = [
        ("Total expenses", f"{expenses['amount'].sum():.2f}"),
        ("Average expense", f"{expenses['amount'].mean():.2f}"),
        ("Maximum expense", f"{maximum:.2f}"),
        ("Minimum expense", f"{minimum:.2f}"),
        ("Expenses", len(expenses)),
        ("Categories", expenses["category"].nunique()),
        ("Months", expenses["month"].nunique()),
    ]
    columns = st.columns(4)
    for index, (label, value) in enumerate(values):
        columns[index % 4].metric(label, value)


def render_analysis_results(expenses):
    render_summary(expenses)
    category_totals, month_totals, month_category_totals = build_analysis_tables(expenses)

    st.subheader("By Category")
    st.dataframe(category_totals, use_container_width=True, hide_index=True)
    st.bar_chart(category_totals.set_index("category")["amount"])

    st.subheader("By Month")
    st.dataframe(month_totals, use_container_width=True, hide_index=True)
    st.line_chart(month_totals.set_index("month")["amount"])

    st.subheader("Month x Category")
    st.dataframe(month_category_totals, use_container_width=True)

    st.subheader("Filtered expense rows")
    display_expenses = expenses.copy()
    display_expenses["date"] = display_expenses["date"].dt.strftime("%Y-%m-%d")
    st.dataframe(display_expenses, use_container_width=True, hide_index=True)


def show_filtered_report_download(expenses, filters):
    report_bytes = build_filtered_excel_report(expenses, filters)
    st.download_button(
        label="Download filtered Excel report",
        data=report_bytes,
        file_name="filtered_expense_report.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
    )


def render_analysis_section():
    st.title("Analysis")
    if is_cloud_mode():
        expenses = get_current_session_expenses()
        imports = []
        if expenses is None or expenses.empty:
            st.info("Upload CSV files or load demo data in Import first.")
            return
        expenses = prepare_expenses(expenses)
        st.warning(
            "Cloud demo mode analyzes only the data loaded in the current session."
        )
    else:
        rows = get_expenses()
        if not rows:
            st.info("No expenses have been saved to the database yet.")
            return
        expenses = prepare_expenses(rows)
        imports = get_imports()

    start_date, end_date, categories, import_ids, description_text = render_filters(
        expenses,
        imports,
    )
    if start_date > end_date:
        st.warning("Start date must be earlier than or equal to end date.")
        return

    filtered_expenses = filter_expenses(
        expenses,
        start_date=start_date,
        end_date=end_date,
        categories=categories,
        import_ids=import_ids,
        description_text=description_text,
    )
    if filtered_expenses.empty:
        st.info("No expenses match the selected filters. Try changing the filters.")
        return

    report_filters = {
        "date_range": f"{start_date} to {end_date}",
        "categories": ", ".join(categories) if categories else "All categories",
        "imports": ", ".join(map(str, import_ids)) if import_ids else (
            "Current session" if is_cloud_mode() else "All imports"
        ),
        "description_text": description_text or "No text filter",
    }
    show_filtered_report_download(filtered_expenses, report_filters)
    render_analysis_results(filtered_expenses)
