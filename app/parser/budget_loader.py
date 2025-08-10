"""Budget YAML file loader with validation."""

import yaml
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, model_validator
import jsonschema


class Category(BaseModel):
    """Category definition for both income and expenses."""
    category: str
    amount: Optional[float] = None  # None for INHERITED
    subcategories: Optional[List['Category']] = None

    @classmethod
    def parse_inherited_recursive(cls, data):
        if isinstance(data, dict):
            # Process amount field
            if 'amount' in data and isinstance(data['amount'], str) and data['amount'].upper() == 'INHERITED':
                data = data.copy()  # Don't mutate original
                data['amount'] = None

            # Recursively process subcategories
            if 'subcategories' in data and isinstance(data['subcategories'], list):
                data = data.copy()  # Don't mutate original
                data['subcategories'] = [cls.parse_inherited_recursive(sub) for sub in data['subcategories']]

        return data

    def get_total_amount(self) -> float:
        """Calculate the total amount including subcategories."""
        if self.amount is not None:
            return self.amount

        # If amount is None (INHERITED), sum subcategories
        if self.subcategories:
            return sum(sub.get_total_amount() for sub in self.subcategories)

        return 0.0


# Enable forward reference resolution
Category.model_rebuild()


class Budget(BaseModel):
    """Complete budget definition."""
    income: List[Category]
    expenses: List[Category]

    @model_validator(mode='before')
    @classmethod
    def preprocess_inherited(cls, data):
        """Recursively convert INHERITED strings to None throughout the data structure."""

        def process_category(cat_data):
            if isinstance(cat_data, dict):
                cat_data = cat_data.copy()
                # Process amount field
                if 'amount' in cat_data and isinstance(cat_data['amount'], str) and cat_data['amount'].upper() == 'INHERITED':
                    cat_data['amount'] = None
                # Recursively process subcategories
                if 'subcategories' in cat_data and isinstance(cat_data['subcategories'], list):
                    cat_data['subcategories'] = [process_category(sub) for sub in cat_data['subcategories']]
            return cat_data

        if isinstance(data, dict):
            data = data.copy()
            # Process income categories
            if 'income' in data and isinstance(data['income'], list):
                data['income'] = [process_category(cat) for cat in data['income']]
            # Process expense categories
            if 'expenses' in data and isinstance(data['expenses'], list):
                data['expenses'] = [process_category(cat) for cat in data['expenses']]

        return data

    def _iter_categories_with_amount(self, categories: List[Category]):
        """Yield categories (including subcategories) that have a non-None amount."""
        for cat in categories:
            if cat.amount is not None:
                yield cat
            if cat.subcategories:
                yield from self._iter_categories_with_amount(cat.subcategories)

    def get_income_categories(self) -> List[Category]:
        """Return all income categories (including subcategories) with a defined amount."""
        return list(self._iter_categories_with_amount(self.income))

    def get_expense_categories(self) -> List[Category]:
        """Return all expense categories (including subcategories) with a defined amount."""
        return list(self._iter_categories_with_amount(self.expenses))

    def get_total_income(self) -> float:
        """Calculate total budgeted income."""
        return sum(category.get_total_amount() for category in self.income)

    def get_total_expenses(self) -> float:
        """Calculate total budgeted expenses."""
        return sum(category.get_total_amount() for category in self.expenses)

    def get_net_budget(self) -> float:
        """Calculate net budget (income - expenses)."""
        return self.get_total_income() - self.get_total_expenses()


class BudgetLoader:
    """Loads and validates budget YAML files."""

    @staticmethod
    def _load_schema() -> Dict[str, Any]:
        """Load the JSON schema for budget validation."""
        schema_path = Path(__file__).parent.parent.parent / "data" / "budget_schema.json"
        with open(schema_path, 'r') as file:
            return json.load(file)

    @staticmethod
    def load_budget(file_path: Path) -> Budget:
        """Load budget from YAML file."""
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file)

        # Validate against JSON schema first
        schema = BudgetLoader._load_schema()
        jsonschema.validate(data, schema)

        return Budget(**data)

    @staticmethod
    def validate_budget_file(file_path: Path) -> bool:
        """Validate budget file format."""
        try:
            BudgetLoader.load_budget(file_path)
            return True
        except Exception:
            return False
