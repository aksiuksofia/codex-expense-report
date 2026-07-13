import pandas as pd
import streamlit as st

from app_config import is_cloud_mode
from database import get_expenses
from analytics import filter_expenses, prepare_expenses
from session_data import get_current_session_expenses


def calculate_period_summary(expenses):
    if expenses.empty:
        return None

    return {
        "total_amount": expenses["amount"].sum(),
        "average_expense": expenses["amount"].mean(),
        "maximum_expense": expenses["amount"].max(),
        "expense_count": len(expenses),
        "category_count": expenses["category"].nunique(),
    }


def build_category_comparison(period_a, period_b):
    category_a = (
        period_a.groupby("category", as_index=False)["amount"]
        .sum()
        .rename(columns={"amount": "Period A"})
    )
    category_b = (
        period_b.groupby("category", as_index=False)["amount"]
        .sum()
        .rename(columns={"amount": "Period B"})
    )
    comparison = category_a.merge(category_b, on="category", how="outer").fillna(0)
    comparison["Difference (B - A)"] = (
        comparison["Period B"] - comparison["Period A"]
    )
    return comparison.sort_values("category").reset_index(drop=True)


def get_comparison_values(summary_a, summary_b):
    total_a = summary_a["total_amount"] if summary_a else 0
    total_b = summary_b["total_amount"] if summary_b else 0
    average_a = summary_a["average_expense"] if summary_a else 0
    average_b = summary_b["average_expense"] if summary_b else 0
    count_a = summary_a["expense_count"] if summary_a else 0
    count_b = summary_b["expense_count"] if summary_b else 0

    return {
        "total_difference": abs(total_b - total_a),
        "percentage_change": None if total_a == 0 else (total_b - total_a) / total_a * 100,
        "average_difference": average_b - average_a,
        "expense_count_difference": count_b - count_a,
    }


def render_period_inputs(expenses):
    minimum_date = expenses["date"].min().date()
    maximum_date = expenses["date"].max().date()
    period_a_column, period_b_column = st.columns(2)

    with period_a_column:
        st.subheader("Period A")
        period_a_start = st.date_input(
            "Start date A",
            value=minimum_date,
            min_value=minimum_date,
            max_value=maximum_date,
        )
        period_a_end = st.date_input(
            "End date A",
            value=maximum_date,
            min_value=minimum_date,
            max_value=maximum_date,
        )
    with period_b_column:
        st.subheader("Period B")
        period_b_start = st.date_input(
            "Start date B",
            value=minimum_date,
            min_value=minimum_date,
            max_value=maximum_date,
        )
        period_b_end = st.date_input(
            "End date B",
            value=maximum_date,
            min_value=minimum_date,
            max_value=maximum_date,
        )

    return period_a_start, period_a_end, period_b_start, period_b_end


def render_period_summary(name, summary):
    st.subheader(name)
    if summary is None:
        st.info(f"{name} has no expenses for the selected dates.")
        return

    columns = st.columns(5)
    columns[0].metric("Total amount", f"{summary['total_amount']:.2f}")
    columns[1].metric("Average expense", f"{summary['average_expense']:.2f}")
    columns[2].metric("Maximum expense", f"{summary['maximum_expense']:.2f}")
    columns[3].metric("Expenses", summary["expense_count"])
    columns[4].metric("Categories", summary["category_count"])


def render_comparison(summary_a, summary_b, category_comparison):
    st.subheader("Comparison")
    values = get_comparison_values(summary_a, summary_b)
    first_column, second_column, third_column = st.columns(3)
    first_column.metric("Absolute total difference", f"{values['total_difference']:.2f}")
    third_column.metric(
        "Average expense difference (B - A)",
        f"{values['average_difference']:.2f}",
    )
    second_column.metric(
        "Expense count difference (B - A)",
        values["expense_count_difference"],
    )

    if values["percentage_change"] is None:
        st.info(
            "Percentage change cannot be calculated because Period A total is zero."
        )
    else:
        st.metric("Percentage change (B compared with A)", f"{values['percentage_change']:.2f}%")

    st.subheader("Category comparison")
    if category_comparison.empty:
        st.info("There are no category values to compare for these periods.")
        return

    st.dataframe(category_comparison, use_container_width=True, hide_index=True)
    st.bar_chart(category_comparison.set_index("category")[["Period A", "Period B"]])


def render_compare_periods_section():
    st.title("Compare periods")
    if is_cloud_mode():
        expenses = get_current_session_expenses()
        if expenses is None or expenses.empty:
            st.info("Upload CSV files or load demo data in Import first.")
            return
        expenses = prepare_expenses(expenses)
        st.warning(
            "Cloud demo mode compares only the data loaded in the current session."
        )
    else:
        rows = get_expenses()
        if not rows:
            st.info("No expenses have been saved to the database yet.")
            return
        expenses = prepare_expenses(rows)

    period_a_start, period_a_end, period_b_start, period_b_end = render_period_inputs(
        expenses
    )
    if period_a_start > period_a_end or period_b_start > period_b_end:
        st.warning("Each start date must be earlier than or equal to its end date.")
        return

    period_a = filter_expenses(
        expenses,
        start_date=period_a_start,
        end_date=period_a_end,
    )
    period_b = filter_expenses(
        expenses,
        start_date=period_b_start,
        end_date=period_b_end,
    )
    summary_a = calculate_period_summary(period_a)
    summary_b = calculate_period_summary(period_b)

    render_period_summary("Period A results", summary_a)
    render_period_summary("Period B results", summary_b)
    render_comparison(
        summary_a,
        summary_b,
        build_category_comparison(period_a, period_b),
    )
