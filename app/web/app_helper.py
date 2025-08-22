import hashlib
import tempfile
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st

from app.analysis.budget_analyzer import BudgetAnalyzer
from app.output.charts import ChartGenerator
from app.parser.budget_loader import Budget, BudgetLoader
from app.parser.simplifi_parser import SimplifiParser


def initialize_session_state():
    global st
    if 'budget' not in st.session_state:
        st.session_state.budget = None
    if 'actual_data' not in st.session_state:
        st.session_state.actual_data = None
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = None
    if 'chart_generator' not in st.session_state:
        st.session_state.chart_generator = ChartGenerator()
    # Persist uploaded filenames across page navigation
    if 'budget_filename' not in st.session_state:
        st.session_state.budget_filename = None
    if 'simplifi_filename' not in st.session_state:
        st.session_state.simplifi_filename = None
    # Track last uploaded Simplifi file content to auto-reload on change
    if 'simplifi_file_digest' not in st.session_state:
        st.session_state.simplifi_file_digest = None
    # Persist month range selections across navigation
    if 'start_month_label' not in st.session_state:
        st.session_state.start_month_label = None
    if 'end_month_label' not in st.session_state:
        st.session_state.end_month_label = None
    # Persist threshold and overspend filter selections across navigation
    if 'threshold' not in st.session_state:
        st.session_state.threshold = 10.0
    if 'only_show_overspend_categories' not in st.session_state:
        st.session_state.only_show_overspend_categories = False
    # Track budget reloads to keep editor working copy in sync
    if 'budget_version' not in st.session_state:
        st.session_state.budget_version = 0
    # Track last uploaded budget file content to auto-reload on change
    if 'budget_file_digest' not in st.session_state:
        st.session_state.budget_file_digest = None
    # ["plotly_white", "plotly_dark", "ggplot2", "seaborn"],
    if 'chart_theme' not in st.session_state:
        st.session_state.chart_theme = "plotly_dark"
    st.session_state.chart_generator.set_theme(st.session_state.chart_theme)


def _load_budget_file(uploaded_file) -> Optional[Budget]:
    """Load budget from uploaded file."""
    tmp_path = None
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.yaml') as tmp_file:
            tmp_path = Path(tmp_file.name)
        tmp_path.write_bytes(uploaded_file.getvalue())

        # Load budget
        budget = BudgetLoader.load_budget(tmp_path)
        return budget
    except Exception as e:
        st.error(f"Error loading budget file: {str(e)}")
        return None
    finally:
        if tmp_path:
            try:
                tmp_path.unlink(missing_ok=True)
            except Exception:
                # Best effort cleanup; avoid breaking UI on delete issues
                pass


def _load_simplifi_file(uploaded_file) -> Optional[pd.DataFrame]:
    """Load Simplifi data from uploaded file."""
    tmp_path = None
    try:
        # Save uploaded file temporarily
        suffix = '.csv' if uploaded_file.name.endswith('.csv') else '.xlsx'
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_path = Path(tmp_file.name)
        tmp_path.write_bytes(uploaded_file.getvalue())

        # Load data
        parser = SimplifiParser()
        data = parser.load_file(tmp_path)
        return data
    except Exception as e:
        st.error(f"Error loading Simplifi file: {str(e)}")
        return None
    finally:
        if tmp_path:
            try:
                tmp_path.unlink(missing_ok=True)
            except Exception:
                pass


def load_budget_file(budget_file):
    # Auto-reload when the uploaded file content changes
    _budget_bytes = budget_file.getvalue()
    _new_digest = hashlib.sha256(_budget_bytes).hexdigest()
    _changed_file = st.session_state.get("budget_file_digest") != _new_digest
    if st.session_state.budget is None or _changed_file or st.button("Reload Budget"):
        st.session_state.budget = _load_budget_file(budget_file)
        if st.session_state.budget:
            st.success("Budget loaded successfully!")
            st.session_state.budget_filename = budget_file.name
            st.session_state.budget_file_digest = _new_digest
            # Bump budget version and reset editor working copy state so the editor reflects the new file
            st.session_state.budget_version = st.session_state.get("budget_version", 0) + 1
            # Reset analyzer when budget changes
            st.session_state.analyzer = None


def load_simplifi_file(simplifi_file):
    # Auto-reload when the uploaded file content changes
    _simp_bytes = simplifi_file.getvalue()
    _simp_digest = hashlib.sha256(_simp_bytes).hexdigest()
    _changed_simplifi = st.session_state.get("simplifi_file_digest") != _simp_digest
    if st.session_state.actual_data is None or _changed_simplifi or st.button("Reload Data"):
        st.session_state.actual_data = _load_simplifi_file(simplifi_file)
        if st.session_state.actual_data is not None:
            st.success("Simplifi data loaded successfully!")
            st.session_state.simplifi_filename = simplifi_file.name
            st.session_state.simplifi_file_digest = _simp_digest
            # Reset analyzer when data changes
            st.session_state.analyzer = None


def build_analyzer(start_month: tuple[str,int], end_month: tuple[str,int]):
    st.session_state.analyzer = BudgetAnalyzer(st.session_state.budget)
    st.session_state.analyzer.set_actual_data(st.session_state.actual_data)
    st.session_state.analyzer.set_analysis_date_range(start_month=start_month, end_month=end_month)
    st.session_state.analyzer.set_only_overspend(st.session_state.only_show_overspend_categories)
    st.session_state.analyzer.set_overspend_threshold(st.session_state.threshold)
