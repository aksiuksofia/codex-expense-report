import streamlit as st

from app_config import get_app_mode, get_mode_label, is_cloud_mode
from sections.about_section import render_about_section
from sections.analysis_section import render_analysis_section
from sections.compare_periods_section import render_compare_periods_section
from sections.history_section import render_history_section
from sections.import_section import render_import_section


LOCAL_SECTIONS = {
    "Import": render_import_section,
    "History": render_history_section,
    "Analysis": render_analysis_section,
    "Compare periods": render_compare_periods_section,
    "About": render_about_section,
}

CLOUD_SECTIONS = {
    "Import": render_import_section,
    "Analysis": render_analysis_section,
    "Compare periods": render_compare_periods_section,
    "About": render_about_section,
}


def get_sections():
    if is_cloud_mode():
        return CLOUD_SECTIONS
    return LOCAL_SECTIONS


def main():
    st.set_page_config(page_title="Expense Report Generator", layout="wide")

    st.sidebar.title("Expense Report")
    st.sidebar.caption(get_mode_label())
    if is_cloud_mode():
        st.sidebar.warning(
            "Cloud demo data may not be saved after the app restarts."
        )

    sections = get_sections()
    selected_section = st.sidebar.radio(
        "Navigation",
        options=list(sections),
    )

    sections[selected_section]()


if __name__ == "__main__":
    main()
