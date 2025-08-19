"""Edit Budget page"""
import streamlit as st
from app.editor.budget_editor import flatten_categories, render_editor_table

# Page configuration must be the first Streamlit command
st.set_page_config(page_title="Edit Budget", page_icon="✏️", layout="wide")

# edit_budget_helpers must be imported AFTER st.set_page_config
from app.web.pages.edit_budget_helpers import apply_edit_changes_update_flag, \
    initialize_editor_state, EXPENSE_CATEGORIES_EDIT_TABLE_KEY, \
    INCOME_CATEGORIES_EDIT_TABLE_KEY, toolbar, show_modals, INCOME_CATEGORIES_WIDGET_KEY, EXPENSE_CATEGORIES_WIDGET_KEY

st.title("✏️ Edit Budget")
st.caption("Adjust budgeted amounts. Category structure edits are not supported here.")

# Guard: require a loaded budget
if "budget" not in st.session_state or st.session_state.budget is None:
    st.info("Please load a budget on the main page before using the editor.")
    # Link back to main page
    st.page_link("streamlit_app.py", label="⬅️ Back to main page")
    st.stop()

initialize_editor_state()

# If user requested to open a modal, show it
show_modals()

# Toolbar
toolbar()

# Unsaved changes banner (placed near top for visibility)
notice = st.empty()

st.divider()

# Placeholder content for the editor UI (to be implemented)
st.header("Editor")

st.subheader("Income")
st.session_state[INCOME_CATEGORIES_EDIT_TABLE_KEY] = render_editor_table(flatten_categories(
    st.session_state.working_budget.income, is_income=True),
    key=INCOME_CATEGORIES_WIDGET_KEY)

st.subheader("Expenses")
st.session_state[EXPENSE_CATEGORIES_EDIT_TABLE_KEY] = render_editor_table(flatten_categories(
    st.session_state.working_budget.expenses, is_income=False),
    key=EXPENSE_CATEGORIES_WIDGET_KEY)

apply_edit_changes_update_flag()

if st.session_state.unsaved_changes:
    notice.warning("You have unsaved changes. Remember to Save or Cancel before leaving this page.")
else:
    notice.empty()



