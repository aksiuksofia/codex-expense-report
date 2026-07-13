import pandas as pd


def prepare_expenses(rows):
    expenses = pd.DataFrame(rows).copy()
    expenses["amount"] = pd.to_numeric(expenses["amount"])
    expenses["date"] = pd.to_datetime(expenses["date"])
    expenses["month"] = expenses["date"].dt.strftime("%Y-%m")
    return expenses


def calculate_summary(expenses):
    total_amount = expenses["amount"].sum()
    average_expense = expenses["amount"].mean()
    biggest_expense = expenses.loc[expenses["amount"].idxmax()]
    return total_amount, average_expense, biggest_expense


def calculate_category_totals(expenses):
    return (
        expenses.groupby("category", as_index=False)["amount"]
        .sum()
        .sort_values("category")
    )


def calculate_month_totals(expenses):
    return (
        expenses.groupby("month", as_index=False)["amount"]
        .sum()
        .sort_values("month")
    )


def calculate_month_category_totals(expenses):
    return expenses.pivot_table(
        index="month",
        columns="category",
        values="amount",
        aggfunc="sum",
        fill_value=0,
    ).sort_index()


def filter_expenses(
    expenses,
    start_date=None,
    end_date=None,
    categories=None,
    import_ids=None,
    description_text="",
):
    filtered = expenses.copy()
    filtered["date"] = pd.to_datetime(filtered["date"])

    if start_date is not None:
        filtered = filtered[filtered["date"] >= pd.Timestamp(start_date)]
    if end_date is not None:
        filtered = filtered[filtered["date"] <= pd.Timestamp(end_date)]
    if categories:
        filtered = filtered[filtered["category"].isin(categories)]
    if import_ids:
        filtered = filtered[filtered["import_id"].isin(import_ids)]
    if description_text.strip():
        filtered = filtered[
            filtered["description"].str.contains(
                description_text.strip(),
                case=False,
                na=False,
                regex=False,
            )
        ]

    filtered["month"] = filtered["date"].dt.strftime("%Y-%m")
    return filtered


def build_analysis_tables(expenses):
    return (
        calculate_category_totals(expenses),
        calculate_month_totals(expenses),
        calculate_month_category_totals(expenses),
    )
