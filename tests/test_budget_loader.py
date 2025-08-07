"""Tests for budget loader functionality."""

import pytest
from pathlib import Path
import tempfile
import yaml

from app.parser.budget_loader import BudgetLoader, Budget


class TestBudgetLoader:
    """Test budget loader functionality."""

    def test_load_valid_budget(self):
        """Test loading a valid budget file."""
        budget_data = {
            'income': [
                {'source': 'Salary', 'amount': 5000}
            ],
            'expenses': [
                {'category': 'Housing', 'amount': 1500}
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(budget_data, f)
            temp_path = Path(f.name)

        try:
            budget = BudgetLoader.load_budget(temp_path)
            assert isinstance(budget, Budget)
            assert budget.get_total_income() == 5000
            assert budget.get_total_expenses() == 1500
        finally:
            temp_path.unlink()

    def test_budget_with_subcategories(self):
        """Test budget with subcategories."""
        # TODO: Implement test
        pass

    def test_inherited_amounts(self):
        """Test handling of INHERITED amounts."""
        # TODO: Implement test
        pass
