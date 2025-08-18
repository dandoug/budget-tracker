"""Edit Budget page scaffold."""

from typing import Optional

import streamlit as st

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
if "working_budget" not in st.session_state or st.session_state.working_budget is None:
    # Deep copy if available (pydantic v2: model_copy), else keep reference
    base_budget = st.session_state.budget
    st.session_state.working_budget = (
        base_budget.model_copy(deep=True) if hasattr(base_budget, "model_copy") else base_budget
    )

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
                st.session_state.unsaved_changes = False
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
                st.experimental_rerun()

    @st.dialog("Discard changes?")
    def _confirm_discard_modal():
        st.write("You have unsaved changes. Do you want to discard them?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Discard changes", type="primary"):
                # Reset working copy from live budget
                base_budget = st.session_state.budget
                st.session_state.working_budget = (
                    base_budget.model_copy(deep=True) if hasattr(base_budget, "model_copy") else base_budget
                )
                st.session_state.unsaved_changes = False
                st.session_state.show_discard_modal = False
                st.success("All unsaved changes have been discarded.")
                st.experimental_rerun()
        with c2:
            if st.button("Keep editing"):
                st.session_state.show_discard_modal = False
                st.experimental_rerun()

# If user requested to open a modal, show it
if hasattr(st, "dialog"):
    if st.session_state.get("show_leave_modal"):
        _confirm_leave_modal()
    if st.session_state.get("show_discard_modal"):
        _confirm_discard_modal()

# Toolbar
tcol1, tcol2, tcol3 = st.columns([1, 1, 1])
with tcol1:
    if st.button("Save Changes", type="primary", use_container_width=True):
        # Persist working copy as the live budget
        st.session_state.budget = st.session_state.working_budget
        st.session_state.unsaved_changes = False
        st.success("Changes saved.")
with tcol2:
    if st.button("Cancel Changes", use_container_width=True):
        if st.session_state.unsaved_changes and hasattr(st, "dialog"):
            # Prompt before discarding changes
            st.session_state.show_discard_modal = True
            st.experimental_rerun()
        else:
            # Reset working copy from live budget immediately
            base_budget = st.session_state.budget
            st.session_state.working_budget = (
                base_budget.model_copy(deep=True) if hasattr(base_budget, "model_copy") else base_budget
            )
            st.session_state.unsaved_changes = False
            st.info("All unsaved changes have been discarded.")
with tcol3:
    if st.button("⬅️ Back to main page", use_container_width=True):
        if st.session_state.unsaved_changes and hasattr(st, "dialog"):
            # Prompt before leaving
            st.session_state.show_leave_modal = True
            st.experimental_rerun()
        else:
            if hasattr(st, "switch_page"):
                st.switch_page("streamlit_app.py")
            else:
                # Fallback: show a link if programmatic navigation isn't available
                st.info("Use the link below to return to the main page.")
                if hasattr(st, "page_link"):
                    st.page_link("streamlit_app.py", label="⬅️ Back to main page")

st.divider()

# Unsaved changes banner
if st.session_state.unsaved_changes:
    st.warning("You have unsaved changes. Remember to Save or Cancel before leaving this page.")

# Placeholder content for the editor UI (to be implemented)
st.subheader("Editor")
st.write("This is a scaffold for the budget editor. The editable tree/table UI will be added here.")
st.caption("Tip: Any edits in this section should flip an 'unsaved changes' flag in session_state.")
