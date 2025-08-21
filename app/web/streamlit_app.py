"""Main Streamlit application for budget tracking and reporting."""
import os
import sys
import tempfile
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional

import hashlib
import pandas as pd
import streamlit as st
import yaml

# Ensure the project root (which contains the 'app' package) is on sys.path
# This makes `from app.* import ...` work when this file is run from app/web
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# Import our custom modules
from app.parser.budget_loader import BudgetLoader, Budget
from app.parser.simplifi_parser import SimplifiParser
from app.analysis.budget_analyzer import BudgetAnalyzer
from app.analysis.category_matcher import CategoryMatcher
from app.output.charts import ChartGenerator
from app.output.report_generator import ReportGenerator


# Page configuration
st.set_page_config(
    page_title="Budget Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
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


def load_budget_file(uploaded_file) -> Optional[Budget]:
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


def load_simplifi_file(uploaded_file) -> Optional[pd.DataFrame]:
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


def main():
    """Main application function."""
    st.title("💰 Budget Tracker & Analyzer")
    st.markdown("Upload your budget YAML file and Simplifi export to analyze your spending patterns.")

    # Sidebar for file uploads and controls
    with st.sidebar:
        st.header("📁 Data Upload")

        # Budget file upload
        st.subheader("Budget Configuration")
        budget_file = st.file_uploader(
            "Upload Budget YAML",
            type=['yaml', 'yml'],
            help="Upload your budget definition file"
        )

        if budget_file is not None:
            # Auto-reload when the uploaded file content changes
            _budget_bytes = budget_file.getvalue()
            _new_digest = hashlib.sha256(_budget_bytes).hexdigest()
            _changed_file = st.session_state.get("budget_file_digest") != _new_digest
            if st.session_state.budget is None or _changed_file or st.button("Reload Budget"):
                st.session_state.budget = load_budget_file(budget_file)
                if st.session_state.budget:
                    st.success("Budget loaded successfully!")
                    st.session_state.budget_filename = budget_file.name
                    st.session_state.budget_file_digest = _new_digest
                    # Bump budget version and reset editor working copy state so the editor reflects the new file
                    st.session_state.budget_version = st.session_state.get("budget_version", 0) + 1
                    # Reset analyzer when budget changes
                    st.session_state.analyzer = None

        # Show persisted budget filename even if uploader is empty
        if st.session_state.get('budget_filename'):
            st.caption(f"Loaded budget file: {st.session_state.budget_filename}")

        # Simplifi file upload
        st.subheader("Actual Spending Data")
        simplifi_file = st.file_uploader(
            "Upload Simplifi P&L Report Export (excel format)",
            type=['xlsx'],
            help="Upload your Simplifi P&L export file"
        )

        if simplifi_file is not None:
            # Auto-reload when the uploaded file content changes
            _simp_bytes = simplifi_file.getvalue()
            _simp_digest = hashlib.sha256(_simp_bytes).hexdigest()
            _changed_simplifi = st.session_state.get("simplifi_file_digest") != _simp_digest
            if st.session_state.actual_data is None or _changed_simplifi or st.button("Reload Data"):
                st.session_state.actual_data = load_simplifi_file(simplifi_file)
                if st.session_state.actual_data is not None:
                    st.success("Simplifi data loaded successfully!")
                    st.session_state.simplifi_filename = simplifi_file.name
                    st.session_state.simplifi_file_digest = _simp_digest
                    # Reset analyzer when data changes
                    st.session_state.analyzer = None

        # Show persisted Simplifi filename even if uploader is empty
        if st.session_state.get('simplifi_filename'):
            st.caption(f"Loaded Simplifi file: {st.session_state.simplifi_filename}")

        # Analysis controls
        if st.session_state.budget and st.session_state.actual_data is not None:
            st.header("📊 Analysis Controls")

            # Date month range selection
            # Get all column names from actual_data
            columns = list(st.session_state.actual_data.columns)

            # Remove Category, Total, and HierarchyLevel from options
            exclude_cols = ['Category', 'Total', 'HierarchyLevel']
            month_columns = [col for col in columns if col not in exclude_cols]

            # Create options list with (label, index) tuples
            month_options = [(col, idx) for idx, col in enumerate(columns) if col in month_columns]

            # Beginning month selection
            st.subheader("Select Month Range")

            # Determine default indices from previously selected labels (if any)
            _start_label = st.session_state.get("start_month_label")
            _end_label = st.session_state.get("end_month_label")
            default_start_idx = next((i for i, opt in enumerate(month_options) if opt[0] == _start_label), 0)
            default_end_idx = next((i for i, opt in enumerate(month_options) if opt[0] == _end_label),
                                   len(month_options) - 1 if month_options else 0)
            # Ensure start <= end
            if month_options and default_start_idx > default_end_idx:
                default_end_idx = default_start_idx

            start_month = st.selectbox(
                "Start Month",
                options=month_options,
                format_func=lambda x: x[0],
                index=default_start_idx
            )
            # Persist chosen start month label
            st.session_state.start_month_label = start_month[0]

            end_month = st.selectbox(
                "End Month",
                options=month_options,
                format_func=lambda x: x[0],
                index=default_end_idx
            )
            # Persist chosen end month label
            st.session_state.end_month_label = end_month[0]

            # Threshold percentage selection
            st.subheader("Threshold Settings")
            threshold_options = [(2.0, "2%"), (5.0, "5%"), (10.0, "10%"), (25.0, "25%"), (50.0, "50%")]
            # Restore previously selected threshold (fallback to 10%)
            default_threshold_idx = next(
                (i for i, opt in enumerate(threshold_options) if opt[0] == st.session_state.get("threshold", 10.0)),
                2
            )
            threshold = st.selectbox(
                "Variance Threshold",
                options=threshold_options,
                format_func=lambda x: x[1],
                index=default_threshold_idx,
                help="Threshold for highlighting significant variances"
            )
            st.session_state.threshold = threshold[0]

            # Restore and persist overspend-only filter
            st.session_state.only_show_overspend_categories = st.checkbox(
                "Only show overspend categories",
                value=st.session_state.get("only_show_overspend_categories", False),
                help="Show only categories where actual spending exceeds budget by threshold"
            )

            st.subheader("Chart Controls")
            chart_theme = st.selectbox(
                "Chart theme",
                ["plotly_white", "plotly_dark", "ggplot2", "seaborn"],
                help="Select chart theme"
            )

            # Update chart theme
            st.session_state.chart_generator.set_theme(chart_theme)

    # Main content area
    if st.session_state.budget is None:
        st.info("👈 Please upload a budget YAML file to get started.")

        # Show sample budget format
        sample_budget_path = _PROJECT_ROOT / "data" / "sample_budget.yaml"
        with open(sample_budget_path, "r") as f:
            sample_budget = f.read()
        with st.expander("📝 Sample Budget Format"):
            st.code(sample_budget, language="yaml")

        return

    # Display budget summary
    # First check to see if data is loaded and if so, compute the number of months
    # used for the analysis
    col1, col2, col3 = st.columns(3)

    if st.session_state.actual_data is None:
        num_of_months = 1
        with col1:
            st.metric("Total Budgeted Income", f"${st.session_state.budget.get_total_income() * num_of_months:,.2f}")
        with col2:
            st.metric("Total Budgeted Expenses", f"${st.session_state.budget.get_total_expenses() * num_of_months:,.2f}")
        with col3:
            net_budget = st.session_state.budget.get_net_budget()
            st.metric("Net Budget", f"${net_budget * num_of_months:,.2f}", delta=None)
    else:
        # Get the number of months between beginning and end months
        num_of_months = end_month[1] - start_month[1] + 1
        st.session_state.analyzer = BudgetAnalyzer(st.session_state.budget)
        st.session_state.analyzer.set_actual_data(st.session_state.actual_data)
        st.session_state.analyzer.set_analysis_date_range(start_month=start_month, end_month=end_month)
        st.session_state.analyzer.set_only_overspend(st.session_state.only_show_overspend_categories)
        st.session_state.analyzer.set_overspend_threshold(st.session_state.threshold)

        # Get summary statistics
        summary_stats = st.session_state.analyzer.generate_summary_stats()
        with col1:
            st.metric("Total Budgeted Income", f"${summary_stats['total_budgeted_income']:,.2f}")
        with col2:
            st.metric("Total Budgeted Expenses", f"${summary_stats['total_budgeted_expenses']:,.2f}")
        with col3:
            net_budget = st.session_state.budget.get_net_budget()
            st.metric("Net Budget", f"${summary_stats['budgeted_net']:,.2f}", delta=None)



    if num_of_months > 1:
        st.write(f"**Note:** These budget numbers are  based on a period of {num_of_months} months.")
    else:
        st.write("**Note:** These budget numbers are for a single month.")

    # If no actual data, show budget details only
    if st.session_state.actual_data is None:
        st.info("Upload Simplifi data to see budget vs actual analysis.")

        # Show budget breakdown
        st.subheader("📋 Monthly Budget Breakdown")

        # Income breakdown
        st.write("**Income Sources:**")
        income_data = [{"Source": inc.category, "Amount": f"${inc.amount:,.2f}"}
                       for inc in st.session_state.budget.get_income_categories()]
        st.dataframe(pd.DataFrame(income_data), use_container_width=True)

        # Expense breakdown
        st.write("**Expense Categories:**")
        expense_data = [{"Category": exp.category, "Amount": f"${exp.amount:,.2f}"}
                        for exp in st.session_state.budget.get_expense_categories()]
        budget_expense_df = pd.DataFrame(expense_data)
        st.dataframe(budget_expense_df, use_container_width=True)

        return



    # Analysis tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📈 Charts", "📋 Details", "📄 Reports"])

    with tab1:
        st.header("Budget vs Actual Overview")

        # Display summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Actual Income", f"${summary_stats['total_actual_income']:,.2f}")
        with col2:
            st.metric("Actual Expenses", f"${-1*summary_stats['total_actual_expenses']:,.2f}")
        with col3:
            st.metric("Actual Net", f"${summary_stats['actual_net']:,.2f}")
        with col4:
            variance = summary_stats['actual_net'] - summary_stats['budgeted_net']
            variance_pct = (variance / summary_stats['budgeted_net']) * 100
            st.metric("Net Variance", f"${variance:,.2f}", delta=f"{variance_pct:.2f}%")

        if num_of_months > 1:
            st.write(f"**Note:** This analysis is based on {num_of_months} months of data.")
        else:
            st.write("**Note:** This analysis is based on a single month of data.")

        # Variance analysis
        st.subheader("Category Variance Analysis")
        variance_data = st.session_state.analyzer.calculate_variances()
        if variance_data.empty:
            threshold_pct_str = f"{st.session_state.threshold}%"
            if st.session_state.only_show_overspend_categories:
                st.text(f"No overspending categories were found for a {threshold_pct_str} threshold.")
            else:
                st.text(f"No variance data is available.")
        else:
            st.dataframe(variance_data,
                         column_config={
                             "category": st.column_config.TextColumn("Category"),
                             "budgeted": st.column_config.NumberColumn("Budgeted",
                                                                       format="$%.2f",
                                                                       help="USD"),
                             "actual": st.column_config.NumberColumn("Actual",
                                                                     format="$%.2f",
                                                                     help="USD"),
                             "variance": st.column_config.NumberColumn("Variance",
                                                                       format="$%.2f",
                                                                       help="USD"),
                             "variance_percent": st.column_config.NumberColumn(
                                 "Variance %",
                                 format="%.1f%%"
                             ),
                         }
            )

        # Overspending alerts
        overspending = st.session_state.analyzer.identify_overspending(st.session_state.threshold)
        if overspending:
            st.warning(f"⚠️ Overspending detected in: {', '.join(overspending)}")

    with tab2:
        st.header("Visual Analysis")

        if not variance_data.empty:
            # Budget vs Actual chart
            fig1 = st.session_state.chart_generator.budget_vs_actual_bar(variance_data)
            st.plotly_chart(fig1, use_container_width=True)

            fig2 = st.session_state.chart_generator.expenses_waterfall(variance_data.dropna())
            st.plotly_chart(fig2, use_container_width=True)

            # Summary chart
            summary_stats = st.session_state.analyzer.generate_summary_stats()
            fig3 = st.session_state.chart_generator.income_vs_expenses_summary(summary_stats)
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.text(f"No variance data is available.")

    with tab3:
        st.header("Raw Data Loaded")

        st.dataframe(st.session_state.actual_data, use_container_width=True)

    with tab4:
        st.header("Report Generation")

        if variance_data.empty:
            st.text(f"No variance data is availableto generate reports.")
        else:
            col1, col2 = st.columns(2)

            with col1:
                if st.button("📊 Generate PDF Report"):
                    try:
                        report_generator = ReportGenerator()
                        variance_data = st.session_state.analyzer.calculate_variances()
                        summary_stats = st.session_state.analyzer.generate_summary_stats()

                        # Generate report
                        report_buffer = report_generator.generate_budget_report(
                            variance_data,
                            summary_stats,
                            report_period=f"{start_month[0]} to {end_month[0]}"
                        )

                        st.download_button(
                            label="📥 Download PDF Report",
                            data=report_buffer.getvalue(),
                            file_name=f"budget_report_{datetime.now().strftime('%Y%m%d')}.pdf",
                            mime="application/pdf"
                        )

                    except Exception as e:
                        st.error(f"Error generating report: {str(e)}")

            with col2:
                if st.button("📈 Export to Excel"):
                    try:
                        variance_data = st.session_state.analyzer.calculate_variances()

                        # Create Excel file in memory
                        output = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)

                        with pd.ExcelWriter(output.name, engine='openpyxl') as writer:
                            variance_data.to_excel(writer, sheet_name='Variance Analysis', index=False)
                            st.session_state.actual_data.to_excel(writer, sheet_name='Raw Data', index=False)

                        # Read the file for download
                        with open(output.name, 'rb') as f:
                            st.download_button(
                                label="📥 Download Excel File",
                                data=f.read(),
                                file_name=f"budget_analysis_{datetime.now().strftime('%Y%m%d')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )

                        # Clean up
                        os.unlink(output.name)

                    except Exception as e:
                        st.error(f"Error exporting to Excel: {str(e)}")


if __name__ == "__main__":
    main()
