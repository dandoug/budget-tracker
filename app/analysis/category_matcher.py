"""Category matching between budget and actual expenses."""

from typing import Dict, List, Tuple, Optional
from fuzzywuzzy import fuzz
import pandas as pd


class CategoryMatcher:
    """Matches actual expense categories to budget categories."""

    def __init__(self, budget_categories: List[str]):
        self.budget_categories = budget_categories
        self.custom_mappings: Dict[str, str] = {}

    def add_custom_mapping(self, actual_category: str, budget_category: str) -> None:
        """Add custom mapping between actual and budget categories."""
        self.custom_mappings[actual_category] = budget_category

    def find_best_match(self, actual_category: str, threshold: int = 80) -> Optional[str]:
        """Find best matching budget category for an actual category."""
        # Check custom mappings first
        if actual_category in self.custom_mappings:
            return self.custom_mappings[actual_category]

        best_match = None
        best_score = 0

        for budget_cat in self.budget_categories:
            score = fuzz.partial_ratio(actual_category.lower(), budget_cat.lower())
            if score > best_score and score >= threshold:
                best_score = score
                best_match = budget_cat

        return best_match

    def match_all_categories(self, actual_categories: List[str]) -> Dict[str, Optional[str]]:
        """Match all actual categories to budget categories."""
        matches = {}
        for category in actual_categories:
            matches[category] = self.find_best_match(category)
        return matches

    def get_unmatched_categories(self, actual_categories: List[str]) -> List[str]:
        """Get list of actual categories that couldn't be matched."""
        unmatched = []
        for category in actual_categories:
            if self.find_best_match(category) is None:
                unmatched.append(category)
        return unmatched

    def export_mappings(self) -> Dict[str, str]:
        """Export current category mappings."""
        return self.custom_mappings.copy()

    def import_mappings(self, mappings: Dict[str, str]) -> None:
        """Import category mappings."""
        self.custom_mappings.update(mappings)
