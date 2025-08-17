"""Tests for budget loader functionality."""

from pathlib import Path
import tempfile
import yaml

from app.parser.budget_loader import BudgetLoader, Budget, Category

DATA_DIR = Path(__file__).parent.parent / "data"


def test_load_valid_budget():
    """Test loading a valid budget file."""
    budget_data = {
        'income': [
            {'category': 'Salary', 'amount': 5000}
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

def test_sample_budget():
    """Test budget with subcategories."""
    budget = BudgetLoader.load_budget(DATA_DIR / "sample_budget.yaml")
    assert isinstance(budget, Budget)
    assert budget.get_total_income() == 6000
    assert budget.get_total_expenses() == 3900

    housing_category = budget.get_expense_category('Housing')
    assert isinstance(housing_category, Category)
    assert housing_category.amount == 1500
    assert housing_category.category == 'Housing'
    assert len(housing_category.subcategories) == 2
    ri = housing_category.get_subcategory("Renter's Insurance")
    assert isinstance(ri, Category)
    assert ri.amount is None

    salary_category = budget.get_income_category('Salary')
    assert isinstance(salary_category, Category)
    assert salary_category.category == 'Salary'



