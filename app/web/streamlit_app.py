"""Main Streamlit application for budget tracking and reporting."""
import os
import sys
import tempfile
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional

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
            if st.session_state.budget is None or st.button("Reload Budget"):
                st.session_state.budget = load_budget_file(budget_file)
                if st.session_state.budget:
                    st.success("Budget loaded successfully!")
                    # Reset analyzer when budget changes
                    st.session_state.analyzer = None

        # Simplifi file upload
        st.subheader("Actual Spending Data")
        simplifi_file = st.file_uploader(
            "Upload Simplifi Export",
            type=['csv', 'xlsx'],
            help="Upload your Simplifi P&L export file"
        )

        if simplifi_file is not None:
            if st.session_state.actual_data is None or st.button("Reload Data"):
                st.session_state.actual_data = load_simplifi_file(simplifi_file)
                if st.session_state.actual_data is not None:
                    st.success("Simplifi data loaded successfully!")
                    # Reset analyzer when data changes
                    st.session_state.analyzer = None

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
            start_month = st.selectbox(
                "Start Month",
                options=month_options,
                format_func=lambda x: x[0],
                index=0
            )

            end_month = st.selectbox(
                "End Month",
                options=month_options,
                format_func=lambda x: x[0],
                index=len(month_options) - 1
            )

            # Category detail level
            st.subheader("Display Options")
            show_subcategories = st.checkbox("Show subcategories", value=False)
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
            st.metric("Total Income", f"${st.session_state.budget.get_total_income() * num_of_months:,.2f}")
        with col2:
            st.metric("Total Expenses", f"${st.session_state.budget.get_total_expenses() * num_of_months:,.2f}")
        with col3:
            net_budget = st.session_state.budget.get_net_budget()
            st.metric("Net Budget", f"${net_budget * num_of_months:,.2f}", delta=None)
    else:
        # Get the number of months between beginning and end months
        num_of_months = end_month[1] - start_month[1] + 1
        st.session_state.analyzer = BudgetAnalyzer(st.session_state.budget)
        st.session_state.analyzer.set_actual_data(st.session_state.actual_data)
        st.session_state.analyzer.set_analysis_date_range(start_month=start_month, end_month=end_month)

        # Get summary statistics
        summary_stats = st.session_state.analyzer.generate_summary_stats()
        with col1:
            st.metric("Total Income", f"${summary_stats['total_budgeted_income']:,.2f}")
        with col2:
            st.metric("Total Expenses", f"${summary_stats['total_budgeted_expenses']:,.2f}")
        with col3:
            net_budget = st.session_state.budget.get_net_budget()
            st.metric("Net Budget", f"${summary_stats['budgeted_net']:,.2f}", delta=None)




    if num_of_months > 1:
        st.write(f"**Note:** This analysis is based on {num_of_months} months of data.")
    else:
        st.write("**Note:** This analysis is based on a single month of data.")

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
        st.dataframe(pd.DataFrame(expense_data), use_container_width=True)

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
            st.metric("Actual Expenses", f"${summary_stats['total_actual_expenses']:,.2f}")
        with col3:
            st.metric("Actual Net", f"${summary_stats['actual_net']:,.2f}")
        with col4:
            variance = summary_stats['actual_net'] - summary_stats['budgeted_net']
            variance_pct = (variance / summary_stats['budgeted_net']) * 100
            st.metric("Net Variance", f"${variance:,.2f}", delta=f"{variance_pct:.2f}%")

        # Variance analysis
        st.subheader("Category Variance Analysis")
        variance_data = st.session_state.analyzer.calculate_variances()
        st.dataframe(variance_data, use_container_width=True)

        # Overspending alerts
        overspending = st.session_state.analyzer.identify_overspending()
        if overspending:
            st.warning(f"⚠️ Overspending detected in: {', '.join(overspending)}")

    with tab2:
        st.header("Visual Analysis")

        if not variance_data.empty:
            # Budget vs Actual chart
            fig1 = st.session_state.chart_generator.budget_vs_actual_bar(variance_data)
            st.plotly_chart(fig1, use_container_width=True)

            # Category pie chart
            fig2 = st.session_state.chart_generator.category_pie_chart(variance_data)
            st.plotly_chart(fig2, use_container_width=True)

            # Summary chart
            summary_stats = st.session_state.analyzer.generate_summary_stats()
            fig3 = st.session_state.chart_generator.income_vs_expenses_summary(summary_stats)
            st.plotly_chart(fig3, use_container_width=True)

    with tab3:
        st.header("Detailed Analysis")

        # Raw data preview
        st.subheader("Actual Spending Data Preview")
        st.dataframe(st.session_state.actual_data.head(10), use_container_width=True)

        # Category matching
        st.subheader("Category Matching")
        if st.button("Show Category Matching Analysis"):
            # This would show how actual categories map to budget categories
            st.info("Category matching analysis would be displayed here.")

    with tab4:
        st.header("Report Generation")

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
                        report_period="Current Analysis"
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
