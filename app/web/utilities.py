import streamlit as st

def rerun():
    """Small compatibility shim for Streamlit rerun API changes"""
    # Prefer new API
    if hasattr(st, "rerun"):
        st.rerun()
    # Backward compatibility (older Streamlit versions)
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()
    # Last resort: nudge a re-render
    else:
        st.session_state["_force_rerender"] = st.session_state.get("_force_rerender", 0) + 1
