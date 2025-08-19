"""Edit Budget page scaffold."""
import streamlit as st

from app.editor.budget_editor import flatten_categories, render_editor_table, apply_changes_to_working_copy
from app.web.utilities import rerun

EXPENSE_CATEGORIES_EDIT_TABLE_KEY = "expense_categories_edit_table"
INCOME_CATEGORIES_EDIT_TABLE_KEY = "income_categories_edit_table"


def _clear_editor_state():
    st.session_state.unsaved_changes = False
    for _k in (INCOME_CATEGORIES_EDIT_TABLE_KEY, EXPENSE_CATEGORIES_EDIT_TABLE_KEY):
        if _k in st.session_state:
            del st.session_state[_k]


def _apply_edit_changes_update_flag():
    for _k in (INCOME_CATEGORIES_EDIT_TABLE_KEY, EXPENSE_CATEGORIES_EDIT_TABLE_KEY):
        if _k in st.session_state:
            try:
                st.session_state.unsaved_changes = (
                        apply_changes_to_working_copy(st.session_state[_k], st.session_state.working_budget)
                        or st.session_state.unsaved_changes
                )
            except Exception:
                # Don't let a malformed widget value break the page
                pass


# Page configuration must be the first Streamlit command
st.set_page_config(page_title="Edit Budget", page_icon="✏️", layout="wide")

st.title("✏️ Edit Budget")
st.caption("Adjust budgeted amounts. Category structure edits are not supported here.")

# Guard: require a loaded budget
if "budget" not in st.session_state or st.session_state.budget is None:
    st.info("Please load a budget on the main page before using the editor.")
    # Link back to main page
    if hasattr(st, "page_link"):
        st.page_link("streamlit_app.py", label="⬅️ Back to main page")
    else:
        st.write("Return to the main page to upload a budget.")
    st.stop()

# Initialize editor state
# Track budget content changes across pages
if "budget_version" not in st.session_state:
    st.session_state.budget_version = 0
if "working_budget_version" not in st.session_state:
    st.session_state.working_budget_version = -1


def _setup_working_budget_copy():
    global base_budget, st
    # Deep copy if available (pydantic v2: model_copy), else keep reference
    base_budget = st.session_state.budget
    st.session_state.working_budget = (
        base_budget.model_copy(deep=True) if hasattr(base_budget, "model_copy") else base_budget
    )
    st.session_state.working_budget_version = st.session_state.budget_version


# Initialize or refresh the working copy if it's missing or out of date
if ("working_budget" not in st.session_state or st.session_state.working_budget is None
        or st.session_state.working_budget_version != st.session_state.budget_version):
    _setup_working_budget_copy()
    # Reset editor flags and any stale widget state
    _clear_editor_state()

if "unsaved_changes" not in st.session_state:
    st.session_state.unsaved_changes = False

if "show_leave_modal" not in st.session_state:
    st.session_state.show_leave_modal = False
if "show_discard_modal" not in st.session_state:
    st.session_state.show_discard_modal = False

# Optional confirm-leave modal and programmatic navigation if Streamlit supports it
if hasattr(st, "dialog"):
    @st.dialog("Unsaved changes")
    def _confirm_leave_modal():
        st.write("You have unsaved changes. Are you sure you want to leave without saving?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Leave without saving", type="primary"):
                _clear_editor_state()
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
    def _confirm_discard_modal():
        st.write("You have unsaved changes. Do you want to discard them?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Discard changes", type="primary"):
                # Reset working copy from live budget
                _setup_working_budget_copy()
                # Clear editor widget state so tables refresh to the live budget
                _clear_editor_state()
                st.session_state.show_discard_modal = False
                st.success("All unsaved changes have been discarded.")
                rerun()
        with c2:
            if st.button("Keep editing"):
                st.session_state.show_discard_modal = False
                rerun()

# If user requested to open a modal, show it
if hasattr(st, "dialog"):
    if st.session_state.get("show_leave_modal"):
        _confirm_leave_modal()
    if st.session_state.get("show_discard_modal"):
        _confirm_discard_modal()


# Apply any pending edits from editor widgets early so toolbar/banner reflect current state
_apply_edit_changes_update_flag()

# Toolbar
tcol1, tcol2, tcol3 = st.columns([1, 1, 1])
with tcol1:
    if st.button("💾 Save Changes", use_container_width=True):

        # Persist working copy as the live budget (deep copy for safety)
        _wb = st.session_state.working_budget
        st.session_state.budget = (_wb.model_copy(deep=True) if hasattr(_wb, "model_copy") else _wb)
        try:
            st.session_state.budget.model_post_init(None)
        except Exception:
            pass

        # Bump version and refresh working copy so editor widgets reflect saved state
        st.session_state.budget_version = st.session_state.get("budget_version", 0) + 1
        st.session_state.working_budget_version = st.session_state.budget_version

        # Clear editor widget state to avoid stale diffs
        _clear_editor_state()
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
            _setup_working_budget_copy()
            # Clear editor widget state to reflect discarded values
            _clear_editor_state()
            st.info("All unsaved changes have been discarded.")
with tcol3:
    if st.button("⬅️ Back to main page", use_container_width=True):
        if st.session_state.unsaved_changes and hasattr(st, "dialog"):
            # Prompt before leaving
            st.session_state.show_leave_modal = True
            rerun()
        else:
            if hasattr(st, "switch_page"):
                st.switch_page("streamlit_app.py")
            else:
                # Fallback: show a link if programmatic navigation isn't available
                st.info("Use the link below to return to the main page.")
                if hasattr(st, "page_link"):
                    st.page_link("streamlit_app.py", label="⬅️ Back to main page")

# Unsaved changes banner (placed near top for visibility)
if st.session_state.unsaved_changes:
    st.warning("You have unsaved changes. Remember to Save or Cancel before leaving this page.")

st.divider()

# Placeholder content for the editor UI (to be implemented)
st.subheader("Editor")

st.write("**Income**")
render_editor_table(flatten_categories(
    st.session_state.working_budget.income, is_income=True),
    key=INCOME_CATEGORIES_EDIT_TABLE_KEY)

st.write("**Expenses**")
render_editor_table(flatten_categories(
    st.session_state.working_budget.expenses, is_income=False),
    key=EXPENSE_CATEGORIES_EDIT_TABLE_KEY)

_apply_edit_changes_update_flag()



