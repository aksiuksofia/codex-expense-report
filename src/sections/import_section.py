import streamlit as st

from analysis_widgets import render_expense_analysis
from app_config import is_cloud_mode
from database import make_source_hash, save_expenses, save_import
from importer import (
    DEMO_EXPENSES,
    STREAMLIT_REPORT,
    combine_valid_expense_files,
    get_demo_file,
    save_uploaded_file,
    validate_expense_files,
)
from logging_config import write_log
from report import create_excel_report
from session_data import clear_current_session_expenses, save_current_session_expenses


def show_file_validation_results(saved_files, all_errors):
    errors_by_file = {filename: errors for filename, errors in all_errors}

    st.subheader("Validation results")
    for input_file in saved_files:
        errors = errors_by_file.get(input_file.name)
        if not errors:
            st.success(f"{input_file.name}: OK")
            continue

        st.error(f"{input_file.name}: ERROR")
        for error in errors:
            st.write(f"- {error}")


def show_validation_errors(all_errors):
    if STREAMLIT_REPORT.exists():
        STREAMLIT_REPORT.unlink()

    st.error("Some CSV files have validation errors.")
    st.warning("Fix the CSV files and upload them again. Excel report was not created.")
    for filename, validation_errors in all_errors:
        st.markdown(f"**File: {filename}**")
        for error in validation_errors:
            st.write(f"- {error}")


def show_download_button():
    if not STREAMLIT_REPORT.exists():
        st.error("Excel report was not created.")
        return

    with STREAMLIT_REPORT.open("rb") as file:
        st.download_button(
            label="Download Excel report",
            data=file,
            file_name="expense_report.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
        )


def save_import_to_database(expenses, saved_files, total_amount, database_path=None):
    source_name = ", ".join(input_file.name for input_file in saved_files)
    source_hash = make_source_hash(source_name, len(expenses), total_amount)
    save_import_kwargs = {}
    save_expenses_kwargs = {}
    if database_path is not None:
        save_import_kwargs["database_path"] = database_path
        save_expenses_kwargs["database_path"] = database_path

    import_id = save_import(
        source_name=source_name,
        row_count=0,
        skipped_duplicates=0,
        total_amount=0,
        source_hash=source_hash,
        **save_import_kwargs,
    )

    return save_expenses(
        import_id=import_id,
        expenses=expenses,
        source_file=source_name,
        **save_expenses_kwargs,
    )


def show_database_save_result(result):
    st.success("Data was saved to the database.")
    st.write(f"import_id: {result['import_id']}")
    st.write(f"rows_read: {result['rows_read']}")
    st.write(f"rows_saved: {result['rows_saved']}")
    st.write(f"duplicates_skipped: {result['duplicates_skipped']}")
    st.write(f"total_amount: {result['total_amount']:.2f}")


def show_pre_save_summary(expenses, total_amount):
    st.subheader("Summary before saving")
    first_column, second_column, third_column = st.columns(3)
    first_column.metric("Total expenses", f"{total_amount:.2f}")
    second_column.metric("Rows", len(expenses))
    third_column.metric("Categories", expenses["category"].nunique())


def show_save_to_database_button(expenses, saved_files, total_amount):
    if is_cloud_mode():
        st.info(
            "Cloud demo mode does not promise persistent SQLite storage. "
            "You can analyze the data and download the Excel report."
        )
        return

    st.subheader("Save data")
    if st.button("Save to database", type="primary"):
        result = save_import_to_database(expenses, saved_files, total_amount)
        show_database_save_result(result)


def process_uploaded_files(uploaded_files):
    saved_files = [save_uploaded_file(file) for file in uploaded_files]
    process_expense_files(saved_files)


def process_expense_files(saved_files):
    st.subheader("Uploaded files")
    for input_file in saved_files:
        st.write(f"- {input_file.name}")

    all_errors = validate_expense_files(saved_files)
    show_file_validation_results(saved_files, all_errors)
    if all_errors:
        clear_current_session_expenses()
        show_validation_errors(all_errors)
        write_log(
            input_file=", ".join(str(file) for file in saved_files),
            output_file=STREAMLIT_REPORT,
            row_count="unknown",
            status="ERROR",
            error_text="; ".join(
                f"{filename}: {', '.join(errors)}"
                for filename, errors in all_errors
            ),
        )
        return

    expenses = combine_valid_expense_files(saved_files)
    save_current_session_expenses(expenses)
    st.subheader("Combined preview")
    st.dataframe(expenses.head(), use_container_width=True)

    report_data = create_excel_report(expenses, STREAMLIT_REPORT)
    total_amount = report_data[0]
    st.success("CSV files are valid. Excel report was created.")
    show_pre_save_summary(expenses, total_amount)
    show_save_to_database_button(expenses, saved_files, total_amount)
    render_expense_analysis(expenses)

    write_log(
        input_file=", ".join(str(file) for file in saved_files),
        output_file=STREAMLIT_REPORT,
        row_count=len(expenses),
        status="SUCCESS",
        total_amount=total_amount,
    )
    show_download_button()


def process_demo_file():
    demo_file = get_demo_file()
    st.info(f"Using demo data: {DEMO_EXPENSES.name}")
    process_expense_files([demo_file])


def render_import_section():
    st.title("Import")
    if is_cloud_mode():
        st.warning(
            "Cloud demo mode can analyze files during this session, but data "
            "may not be saved after the app restarts."
        )

    st.write(
        "Upload one or more CSV files, or load safe demo data, "
        "and generate an Excel report."
    )

    if st.button("Load demo data"):
        st.session_state["use_demo_data"] = True

    uploaded_files = st.file_uploader(
        "Upload CSV files",
        type=["csv"],
        accept_multiple_files=True,
    )

    if uploaded_files:
        st.session_state["use_demo_data"] = False
    elif not st.session_state.get("use_demo_data"):
        return

    try:
        if st.session_state.get("use_demo_data"):
            process_demo_file()
        else:
            process_uploaded_files(uploaded_files)
    except Exception as error:
        st.error(f"Error: {error}")
        write_log(
            input_file=(
                str(DEMO_EXPENSES)
                if st.session_state.get("use_demo_data")
                else ", ".join(file.name for file in uploaded_files)
            ),
            output_file=STREAMLIT_REPORT,
            row_count="unknown",
            status="ERROR",
            error_text=str(error),
        )
