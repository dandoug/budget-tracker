"""Budget analysis and comparison functionality."""

import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime, date
import numpy as np

from app.parser.budget_loader import Budget
from app.analysis.category_matcher import CategoryMatcher


class BudgetAnalyzer:
    """Analyzes budget vs actual spending."""

    def __init__(self, budget: Budget):
        self.budget = budget
        self.actual_data: Optional[pd.DataFrame] = None
        self.matcher: Optional[CategoryMatcher] = None

    def set_actual_data(self, data: pd.DataFrame) -> None:
        """Set actual spending data."""
        self.actual_data = data
        # Initialize category matcher with budget categories
        budget_categories = [exp.category for exp in self.budget.expenses]
        self.matcher = CategoryMatcher(budget_categories)

    def calculate_variances(self, month: Optional[str] = None) -> pd.DataFrame:
        """Calculate budget vs actual variances."""
        if self.actual_data is None:
            raise ValueError("No actual data set. Call set_actual_data() first.")

        # TODO: Implement variance calculation logic
        variances = []

        for expense in self.budget.expenses:
            variance_data = {
                'category': expense.category,
                'budgeted': expense.amount,
                'actual': 0.0,  # TODO: Calculate from actual data
                'variance': 0.0,  # actual - budgeted
                'variance_percent': 0.0  # (variance / budgeted) * 100
            }
            variances.append(variance_data)

        return pd.DataFrame(variances)

    def get_spending_trends(self, category: Optional[str] = None) -> pd.DataFrame:
        """Get spending trends over time."""
        if self.actual_data is None:
            raise ValueError("No actual data set.")

        # TODO: Implement trend analysis
        return pd.DataFrame()

    def identify_overspending(self, threshold_percent: float = 10.0) -> List[str]:
        """Identify categories with significant overspending."""
        variances = self.calculate_variances()
        overspending = variances[
            variances['variance_percent'] > threshold_percent
        ]
        return overspending['category'].tolist()

    def get_savings_opportunities(self) -> List[Dict[str, float]]:
        """Identify potential savings opportunities."""
        variances = self.calculate_variances()
        opportunities = []

        # Categories spending less than budget
        under_budget = variances[variances['variance'] < 0]
        for _, row in under_budget.iterrows():
            opportunities.append({
                'category': row['category'],
                'potential_savings': abs(row['variance']),
                'current_spending': row['actual']
            })

        return opportunities

    def generate_summary_stats(self) -> Dict[str, float]:
        """Generate summary statistics."""
        if self.actual_data is None:
            return {
                'total_budgeted_income': self.budget.get_total_income(),
                'total_budgeted_expenses': self.budget.get_total_expenses(),
                'budgeted_net': self.budget.get_net_budget(),
                'total_actual_income': 0.0,
                'total_actual_expenses': 0.0,
                'actual_net': 0.0
            }

        # TODO: Calculate actual totals from data
        return {
            'total_budgeted_income': self.budget.get_total_income(),
            'total_budgeted_expenses': self.budget.get_total_expenses(),
            'budgeted_net': self.budget.get_net_budget(),
            'total_actual_income': 0.0,  # TODO: Calculate from actual data
            'total_actual_expenses': 0.0,  # TODO: Calculate from actual data
            'actual_net': 0.0  # TODO: Calculate from actual data
        }
