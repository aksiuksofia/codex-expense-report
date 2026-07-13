import streamlit as st


SESSION_EXPENSES_KEY = "current_session_expenses"


def save_current_session_expenses(expenses):
    st.session_state[SESSION_EXPENSES_KEY] = expenses.copy()


def get_current_session_expenses():
    return st.session_state.get(SESSION_EXPENSES_KEY)


def clear_current_session_expenses():
    st.session_state.pop(SESSION_EXPENSES_KEY, None)
