"""Helper methods for edit_budget page"""
import streamlit as st

from app.editor.budget_editor import apply_changes_to_working_copy
from app.web.utilities import rerun

EXPENSE_CATEGORIES_EDIT_TABLE_KEY = "expense_categories_edit_table"
INCOME_CATEGORIES_EDIT_TABLE_KEY = "income_categories_edit_table"

def clear_editor_state():
    st.session_state.unsaved_changes = False
    for _k in (INCOME_CATEGORIES_EDIT_TABLE_KEY, EXPENSE_CATEGORIES_EDIT_TABLE_KEY):
        if _k in st.session_state:
            del st.session_state[_k]


def apply_edit_changes_update_flag():
    for _k in (INCOME_CATEGORIES_EDIT_TABLE_KEY, EXPENSE_CATEGORIES_EDIT_TABLE_KEY):
        if _k in st.session_state:
            st.session_state.unsaved_changes = (
                st.session_state.unsaved_changes or
                apply_changes_to_working_copy(st.session_state[_k], st.session_state.working_budget)
            )


def setup_working_budget_copy():
    # Deep copy if available (pydantic v2: model_copy), else keep reference
    st.session_state.working_budget = st.session_state.budget.model_copy(deep=True)
    st.session_state.working_budget.model_post_init(None)

    st.session_state.working_budget_version = st.session_state.budget_version


def initialize_editor_state():
    # Track budget content changes across pages
    if "budget_version" not in st.session_state:
        st.session_state.budget_version = 0
    if "working_budget_version" not in st.session_state:
        st.session_state.working_budget_version = -1
    if "unsaved_changes" not in st.session_state:
        st.session_state.unsaved_changes = False
    if "show_leave_modal" not in st.session_state:
        st.session_state.show_leave_modal = False
    if "show_discard_modal" not in st.session_state:
        st.session_state.show_discard_modal = False
    # Initialize or refresh the working copy if it's missing or out of date
    if ("working_budget" not in st.session_state or st.session_state.working_budget is None
            or st.session_state.working_budget_version != st.session_state.budget_version):
        setup_working_budget_copy()
        # Reset editor flags and any stale widget state
        clear_editor_state()


@st.dialog("Unsaved changes")
def confirm_leave_modal():
    st.write("You have unsaved changes. Are you sure you want to leave without saving?")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Leave without saving", type="primary"):
            # Reset working copy from live budget
            setup_working_budget_copy()
            clear_editor_state()
            st.session_state.show_leave_modal = False
            if hasattr(st, "switch_page"):
                st.switch_page("streamlit_app.py")
            else:
                # Fallback: provide a link the user can click
                st.success("Navigate back using the link below.")
                if hasattr(st, "page_link"):
                    st.page_link("streamlit_app.py", label="⬅️ Back to main page")
    with c2:
        if st.button("Stay on page"):
            st.session_state.show_leave_modal = False
            rerun()


@st.dialog("Discard changes?")
def confirm_discard_modal():
    st.write("You have unsaved changes. Do you want to discard them?")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Discard changes", type="primary"):
            # Reset working copy from live budget
            setup_working_budget_copy()
            # Clear editor widget state so tables refresh to the live budget
            clear_editor_state()
            st.session_state.show_discard_modal = False
            st.success("All unsaved changes have been discarded.")
            rerun()
    with c2:
        if st.button("Keep editing"):
            st.session_state.show_discard_modal = False
            rerun()


def toolbar():
    global st
    tcol1, tcol2, tcol3 = st.columns([1, 1, 1])
    with tcol1:
        if st.button("💾 Save Changes", use_container_width=True):
            # Persist working copy as the live budget (deep copy for safety)
            st.session_state.budget = st.session_state.working_budget.model_copy(deep=True)
            st.session_state.budget.model_post_init(None)

            # Bump version and refresh working copy so editor widgets reflect saved state
            st.session_state.budget_version = st.session_state.get("budget_version", 0) + 1
            st.session_state.working_budget_version = st.session_state.budget_version

            # Clear editor widget state to avoid stale diffs
            clear_editor_state()
            if "analyzer" in st.session_state:
                st.session_state.analyzer = None

            st.success("Changes saved.")
    with tcol2:
        if st.button("🗑️ Cancel Changes", use_container_width=True):
            if st.session_state.unsaved_changes and hasattr(st, "dialog"):
                # Prompt before discarding changes
                st.session_state.show_discard_modal = True
                rerun()
            else:
                # Reset working copy from live budget immediately
                setup_working_budget_copy()
                # Clear editor widget state to reflect discarded values
                clear_editor_state()
                st.info("All unsaved changes have been discarded.")
    with tcol3:
        if st.button("⬅️ Back to main page", use_container_width=True):
            if st.session_state.unsaved_changes:
                # Prompt before leaving
                st.session_state.show_leave_modal = True
                rerun()
            else:
                st.switch_page("streamlit_app.py")


def show_modals():
    if st.session_state.get("show_leave_modal"):
        confirm_leave_modal()
    if st.session_state.get("show_discard_modal"):
        confirm_discard_modal()
