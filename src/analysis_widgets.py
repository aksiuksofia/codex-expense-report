import streamlit as st

from analytics import (
    calculate_category_totals,
    calculate_month_category_totals,
    calculate_month_totals,
    calculate_summary,
)


def render_expense_analysis(expenses):
    total_amount, average_expense, biggest_expense = calculate_summary(expenses)
    category_totals = calculate_category_totals(expenses)
    month_totals = calculate_month_totals(expenses)
    month_category_totals = calculate_month_category_totals(expenses)

    st.subheader("Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total expenses", f"{total_amount:.2f}")
    col2.metric("Average expense", f"{average_expense:.2f}")
    col3.metric("Biggest expense", f"{biggest_expense['amount']:.2f}")

    col4, col5, col6 = st.columns(3)
    col4.metric("Rows", len(expenses))
    col5.metric("Months", expenses["month"].nunique())
    col6.metric("Categories", expenses["category"].nunique())

    st.write(
        "Biggest expense:",
        f"{biggest_expense['date']} - "
        f"{biggest_expense['category']} - "
        f"{biggest_expense['description']}",
    )

    st.subheader("By Category")
    st.dataframe(category_totals, use_container_width=True)
    st.bar_chart(category_totals.set_index("category")["amount"])

    st.subheader("By Month")
    st.dataframe(month_totals, use_container_width=True)
    st.line_chart(month_totals.set_index("month")["amount"])

    st.subheader("Month x Category")
    st.dataframe(month_category_totals, use_container_width=True)
    st.bar_chart(month_category_totals)

    return total_amount, average_expense, biggest_expense, category_totals
