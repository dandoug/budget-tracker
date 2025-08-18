"""Programmatic navigation entrypoint for the Budget app."""

import streamlit as st

# Global page config for the app (applies to all pages)
st.set_page_config(
    page_title="Budget Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Define pages using paths relative to this file's folder (app/web)
home = st.Page("streamlit_app.py", title="Home", icon="💰")
edit_budget = st.Page("pages/edit_budget.py", title="Edit Budget", icon="✏️")

# Optional: group pages under sections to organize the sidebar menu
nav = st.navigation({
    "Budget Tracker": [home, edit_budget],
})

# Render the selected page
nav.run()
