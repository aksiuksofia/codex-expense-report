import streamlit as st

from app_config import get_mode_label, is_cloud_mode


def render_about_section():
    st.title("About")
    st.write(
        "Expense Report Generator validates CSV expense data, creates Excel "
        "reports and provides simple analysis by category and month."
    )
    st.write("Required CSV columns: date, category, description and amount.")
    st.write("The command-line version remains available in analyze_expenses.py.")
    st.write(f"Current app mode: {get_mode_label()}.")
    if is_cloud_mode():
        st.warning(
            "Cloud demo mode does not promise persistent SQLite storage after "
            "the app restarts."
        )
