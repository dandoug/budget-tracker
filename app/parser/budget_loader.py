"""Budget YAML file loader with validation."""

import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, validator


class SubCategory(BaseModel):
    """Subcategory definition."""
    category: str
    amount: Optional[float] = None  # None for INHERITED

    @validator('amount', pre=True)
    def parse_inherited(cls, v):
        if isinstance(v, str) and v.upper() == 'INHERITED':
            return None
        return v


class ExpenseCategory(BaseModel):
    """Expense category definition."""
    category: str
    amount: float
    subcategories: Optional[List[SubCategory]] = None


class IncomeSource(BaseModel):
    """Income source definition."""
    source: str
    amount: float


class Budget(BaseModel):
    """Complete budget definition."""
    income: List[IncomeSource]
    expenses: List[ExpenseCategory]

    def get_total_income(self) -> float:
        """Calculate total budgeted income."""
        return sum(source.amount for source in self.income)

    def get_total_expenses(self) -> float:
        """Calculate total budgeted expenses."""
        return sum(expense.amount for expense in self.expenses)

    def get_net_budget(self) -> float:
        """Calculate net budget (income - expenses)."""
        return self.get_total_income() - self.get_total_expenses()


class BudgetLoader:
    """Loads and validates budget YAML files."""

    @staticmethod
    def load_budget(file_path: Path) -> Budget:
        """Load budget from YAML file."""
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file)

        return Budget(**data)

    @staticmethod
    def validate_budget_file(file_path: Path) -> bool:
        """Validate budget file format."""
        try:
            BudgetLoader.load_budget(file_path)
            return True
        except Exception:
            return False
