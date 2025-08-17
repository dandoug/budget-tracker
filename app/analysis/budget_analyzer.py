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
        self.start_month: Optional[Tuple[str,int]] = None # format is (columname, columindex)
        self.end_month: Optional[Tuple[str,int]] = None
        self.overspend_threshold: Optional[float] = 10.0
        self.only_overspend: Optional[bool] = False

    def set_actual_data(self, data: pd.DataFrame) -> None:
        """Set actual spending data."""
        self.actual_data = data
        # Initialize category matcher with budget categories
        budget_categories = [exp.category for exp in self.budget.get_expense_categories()]
        self.matcher = CategoryMatcher(budget_categories)
        
    def set_analysis_date_range(self, start_month: tuple[str,int], end_month: tuple[str,int]) -> None:
        """Set date range for analysis."""
        if self.actual_data is None:
            raise ValueError("No actual data set. Call set_actual_data() first.")
        self.start_month = start_month
        self.end_month = end_month

    def set_overspend_threshold(self, threshold: float) -> None:
        """Set overspend threshold."""
        self.overspend_threshold = threshold

    def set_only_overspend(self, only_overspend: bool) -> None:
        """Set only overspend."""
        self.only_overspend = only_overspend

    def calculate_variances(self) -> pd.DataFrame:
        """Calculate budget vs actual variances."""
        if self.actual_data is None:
            raise ValueError("No actual data set. Call set_actual_data() first.")

        variances = []

        # actual_data contains data for several months.  Calculate the total number of
        # months by finding the difference between the start and end months indexes
        num_of_months = self.end_month[1] - self.start_month[1] + 1

        actual_spending = self.summarize_totals_by_budget_category()

        # Limit series to just expenses
        all_budget_expense_cats = [exp.category for exp in self.budget.get_expense_categories()]
        actual_spending = actual_spending.reindex(all_budget_expense_cats, fill_value=0.0)

        for expense in self.budget.get_expense_categories():
            # Find matching actual spending using matched categories
            actual = actual_spending.get(expense.category, 0.0)
            budget_amount = expense.amount * num_of_months

            variance = budget_amount + actual # actual spend is negative
            variance_pct = (variance / budget_amount) * -100 if budget_amount != 0 else 0.0

            # Limit to overspend categories if that option is selected
            if self.only_overspend and variance_pct <= self.overspend_threshold:
                continue

            variance_data = {
                'category': expense.category,
                'budgeted': budget_amount,
                'actual': -actual,
                'variance': -variance,  # spending less than budget is negative variance
                'variance_percent': variance_pct
            }
            variances.append(variance_data)

        return pd.DataFrame(variances)

    def summarize_totals_by_budget_category(self) -> pd.Series:
        """Calculate totals by budget category."""
        # Create a copy of actual data that includes the category column and only
        # the data columns from the start_month to end_month
        columns_to_include = list(self.actual_data.columns[self.start_month[1]:self.end_month[1] + 1])
        actual_data_subset = self.actual_data[columns_to_include].copy()

        # Sum across all months to get total
        actual_data_subset['Total'] = actual_data_subset.iloc[:, 1:].sum(axis=1)

        # Create a simplified view of actual data grouped by matched categories
        actual_spending = actual_data_subset[['Total']].copy()
        actual_spending['Budget_Category'] = actual_spending.index.map(
            lambda x: self.budget.get_budget_category(x).category if self.budget.get_budget_category(x) else None
        )
        actual_spending = actual_spending[actual_spending['Budget_Category'].notna()]
        actual_spending = actual_spending.groupby('Budget_Category')['Total'].sum()
        return actual_spending

    def get_spending_trends(self, category: Optional[str] = None) -> pd.DataFrame:
        """Get spending trends over time."""
        if self.actual_data is None:
            raise ValueError("No actual data set.")

        # TODO: Implement trend analysis
        return pd.DataFrame()

    def identify_overspending(self, threshold_percent: float = 10.0) -> List[str]:
        """Identify categories with significant overspending."""
        variances = self.calculate_variances()
        if variances.empty:
            return []
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

        actual_inc_and_expenses_by_category = self.summarize_totals_by_budget_category()
        income_categories = [cat.category for cat in self.budget.get_income_categories()]
        expense_categories = [cat.category for cat in self.budget.get_expense_categories()]
        all_categories = income_categories + expense_categories
        # Ensure all the categories have some entry, so the .sum() operations below work
        actual_inc_and_expenses_by_category = actual_inc_and_expenses_by_category.reindex(
            all_categories, fill_value=0.0)
        
        actual_income = actual_inc_and_expenses_by_category[income_categories].sum()
        actual_expenses = actual_inc_and_expenses_by_category[expense_categories].sum()

        num_of_months = self.end_month[1] - self.start_month[1] + 1

        return {
            'total_budgeted_income': self.budget.get_total_income()*num_of_months,
            'total_budgeted_expenses': self.budget.get_total_expenses()*num_of_months,
            'budgeted_net': self.budget.get_net_budget()*num_of_months,
            'total_actual_income': actual_income,
            'total_actual_expenses': actual_expenses,
            'actual_net': actual_income + actual_expenses  # expenses are negative
        }
