"""Chart generation using Plotly."""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Optional, List, Dict, Any


class ChartGenerator:
    """Generates various charts for budget analysis."""

    def __init__(self):
        self.theme = 'plotly_white'

    def budget_vs_actual_bar(self, variance_data: pd.DataFrame) -> go.Figure:
        """Create budget vs actual comparison bar chart."""
        fig = go.Figure(data=[
            go.Bar(name='Budgeted', x=variance_data['category'], y=variance_data['budgeted']),
            go.Bar(name='Actual', x=variance_data['category'], y=variance_data['actual'])
        ])

        fig.update_layout(
            title='Budget vs Actual Spending by Category',
            xaxis_title='Category',
            yaxis_title='Amount ($)',
            barmode='group',
            template=self.theme
        )

        return fig

    def variance_waterfall(self, variance_data: pd.DataFrame) -> go.Figure:
        """Create variance waterfall chart."""
        fig = go.Figure(go.Waterfall(
            name="Variance Analysis",
            orientation="v",
            measure=["relative"] * len(variance_data),
            x=variance_data['category'],
            y=variance_data['variance'],
            connector={"line": {"color": "rgb(63, 63, 63)"}},
        ))

        fig.update_layout(
            title="Budget Variance Waterfall",
            template=self.theme
        )

        return fig

    def spending_trends(self, trend_data: pd.DataFrame, category: Optional[str] = None) -> go.Figure:
        """Create spending trends over time."""
        if category:
            title = f"Spending Trends - {category}"
            data = trend_data[trend_data['category'] == category] if 'category' in trend_data.columns else trend_data
        else:
            title = "Overall Spending Trends"
            data = trend_data

        fig = px.line(data, x='date', y='amount', title=title, template=self.theme)

        return fig

    def category_pie_chart(self, data: pd.DataFrame, value_col: str = 'actual', title: str = None) -> go.Figure:
        """Create pie chart of spending by category."""
        if title is None:
            title = f"Spending Distribution by Category"

        fig = px.pie(data, values=value_col, names='category', title=title, template=self.theme)

        return fig

    def income_vs_expenses_summary(self, summary_stats: Dict[str, float]) -> go.Figure:
        """Create summary chart of income vs expenses."""
        categories = ['Income', 'Expenses', 'Net']
        budgeted = [
            summary_stats['total_budgeted_income'],
            -summary_stats['total_budgeted_expenses'],  # Negative for expenses
            summary_stats['budgeted_net']
        ]
        actual = [
            summary_stats['total_actual_income'],
            -summary_stats['total_actual_expenses'],  # Negative for expenses
            summary_stats['actual_net']
        ]

        fig = go.Figure(data=[
            go.Bar(name='Budgeted', x=categories, y=budgeted),
            go.Bar(name='Actual', x=categories, y=actual)
        ])

        fig.update_layout(
            title='Income vs Expenses Summary',
            yaxis_title='Amount ($)',
            barmode='group',
            template=self.theme
        )

        return fig

    def monthly_trend_comparison(self, monthly_data: pd.DataFrame) -> go.Figure:
        """Create monthly budget vs actual trend comparison."""
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Income Trends', 'Expense Trends'),
            shared_xaxis=True
        )

        # TODO: Implement based on actual monthly data structure

        fig.update_layout(
            title='Monthly Budget vs Actual Trends',
            template=self.theme,
            height=600
        )

        return fig

    def set_theme(self, theme: str) -> None:
        """Set chart theme."""
        self.theme = theme
