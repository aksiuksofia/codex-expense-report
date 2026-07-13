import pandas as pd
import streamlit as st

from database import delete_import, get_expenses_by_import, get_imports
from logging_config import write_deletion_log


IMPORT_COLUMNS = [
    "import_id",
    "imported_at",
    "source_name",
    "row_count",
    "skipped_duplicates",
    "total_amount",
]


def get_selected_import(imports, import_id):
    return next(item for item in imports if item["import_id"] == import_id)


def get_expense_total(expenses):
    return sum(expense["amount"] for expense in expenses)


def get_source_files(expenses):
    return sorted(
        {
            expense["source_file"]
            for expense in expenses
            if expense.get("source_file")
        }
    )


def render_import_details(selected_import, expenses):
    st.subheader("Selected import")
    st.dataframe(
        pd.DataFrame([selected_import])[IMPORT_COLUMNS],
        use_container_width=True,
        hide_index=True,
    )

    total_amount = get_expense_total(expenses)
    col1, col2 = st.columns(2)
    col1.metric("Saved expenses", len(expenses))
    col2.metric("Expense total", f"{total_amount:.2f}")

    st.write("Source files")
    source_files = get_source_files(expenses)
    if source_files:
        for source_file in source_files:
            st.write(f"- {source_file}")
    else:
        st.info("Source file names are not available for this import.")

    st.write("First saved expenses")
    if expenses:
        preview_columns = [
            "date",
            "category",
            "description",
            "amount",
            "source_file",
        ]
        st.dataframe(
            pd.DataFrame(expenses)[preview_columns].head(),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("This import has no saved expenses. They may all have been duplicates.")


def render_delete_import(selected_import, expenses):
    st.subheader("Delete selected import")
    st.warning(
        "This will permanently delete the selected import and its saved expenses. "
        "This action cannot be undone."
    )
    confirmed = st.checkbox(
        "I understand that this import and its expenses will be deleted.",
        key=f"confirm_delete_{selected_import['import_id']}",
    )
    if st.button(
        "Delete selected import",
        disabled=not confirmed,
        type="secondary",
    ):
        deleted_expenses = len(expenses)
        deleted_count = delete_import(selected_import["import_id"])
        if deleted_count:
            write_deletion_log(
                selected_import["import_id"],
                selected_import["source_name"],
                deleted_expenses,
            )
            st.success("The import and its related expenses were deleted.")
            st.rerun()
        else:
            st.error("The selected import was not found.")


def render_history_section():
    st.title("History")
    imports = get_imports()
    if not imports:
        st.info("No imports have been saved to the database yet.")
        return

    st.subheader("Saved imports")
    st.dataframe(
        pd.DataFrame(imports)[IMPORT_COLUMNS],
        use_container_width=True,
        hide_index=True,
    )

    import_ids = [item["import_id"] for item in imports]
    selected_import_id = st.selectbox(
        "Choose an import",
        import_ids,
        format_func=lambda import_id: (
            f"Import {import_id} - "
            f"{get_selected_import(imports, import_id)['source_name']}"
        ),
    )
    selected_import = get_selected_import(imports, selected_import_id)
    expenses = get_expenses_by_import(selected_import_id)

    render_import_details(selected_import, expenses)
    render_delete_import(selected_import, expenses)
