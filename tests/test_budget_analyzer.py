import math
from pathlib import Path

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from app.analysis.budget_analyzer import BudgetAnalyzer
from app.parser.budget_loader import BudgetLoader
from app.parser.simplifi_parser import SimplifiParser


@pytest.fixture(scope="module")
def project_root() -> Path:
    # tests/.. -> project root
    return Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def budget(project_root):
    budget_path = project_root / "data" / "sample_budget.yaml"
    return BudgetLoader.load_budget(budget_path)


@pytest.fixture(scope="module")
def actual_df(project_root):
    xlsx_path = project_root / "data" / "sample_Simplifi-profit-loss.xlsx"
    parser = SimplifiParser()
    df = parser.load_file(xlsx_path)
    # Ensure expected structure: index is categories, columns include month columns and 'HierarchyLevel'
    assert "HierarchyLevel" in df.columns
    assert df.index.name == "Category"
    # At least one numeric month column should exist
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    assert len(numeric_cols) > 0
    return df


def _find_month_bounds(df: pd.DataFrame):
    # Consider numeric columns except the helper column 'HierarchyLevel'
    month_cols = [c for c in df.columns if c != "HierarchyLevel" and pd.api.types.is_numeric_dtype(df[c])]
    if not month_cols:
        raise AssertionError("No numeric month columns found in Simplifi data.")
    start_col = month_cols[0]
    end_col = month_cols[-1]
    start_idx = df.columns.get_loc(start_col)
    end_idx = df.columns.get_loc(end_col)
    return (start_col, start_idx), (end_col, end_idx)


@pytest.fixture(scope="module")
def analyzer(budget, actual_df):
    analyzer = BudgetAnalyzer(budget)
    analyzer.set_actual_data(actual_df)
    start_month, end_month = _find_month_bounds(actual_df)
    analyzer.set_analysis_date_range(start_month, end_month)
    return analyzer


def _compute_expected_variances(budget, df: pd.DataFrame, start_idx: int, end_idx: int) -> pd.DataFrame:
    # Sum totals per row across the selected months
    months = list(df.columns[start_idx:end_idx + 1])
    totals = df[months].sum(axis=1)

    # Map each row's category to its budget category name (if any)
    def to_budget_cat_name(cat_name: str):
        cat = budget.get_budget_category(cat_name)
        return cat.category if cat else None

    mapped = pd.Series(df.index, index=df.index).map(to_budget_cat_name)
    gdf = pd.DataFrame({"Total": totals, "Budget_Category": mapped}).dropna(subset=["Budget_Category"])

    actual_by_budget_cat = gdf.groupby("Budget_Category")["Total"].sum()

    # Reindex to include all expense categories present in the budget (fill missing with 0)
    expense_categories = [c.category for c in budget.get_expense_categories()]
    actual_by_budget_cat = actual_by_budget_cat.reindex(expense_categories, fill_value=0.0)

    num_months = end_idx - start_idx + 1
    rows = []
    for exp_cat in budget.get_expense_categories():
        budget_amount = (exp_cat.amount or 0.0) * num_months
        actual = actual_by_budget_cat.get(exp_cat.category, 0.0)
        variance = budget_amount + actual  # actual spend is negative
        variance_pct = (variance / budget_amount) * -100 if budget_amount != 0 else 0.0

        rows.append(
            {
                "category": exp_cat.category,
                "budgeted": float(budget_amount),
                "actual": float(-actual),
                "variance": float(-variance),
                "variance_percent": float(variance_pct),
            }
        )

    expected = pd.DataFrame(rows)
    return expected


def _compute_expected_summary(budget, df: pd.DataFrame, start_idx: int, end_idx: int) -> dict:
    months = list(df.columns[start_idx:end_idx + 1])
    totals = df[months].sum(axis=1)

    def to_budget_cat_name(cat_name: str):
        cat = budget.get_budget_category(cat_name)
        return cat.category if cat else None

    mapped = pd.Series(df.index, index=df.index).map(to_budget_cat_name)
    gdf = pd.DataFrame({"Total": totals, "Budget_Category": mapped}).dropna(subset=["Budget_Category"])
    actual_by_budget_cat = gdf.groupby("Budget_Category")["Total"].sum()

    income_categories = [c.category for c in budget.get_income_categories()]
    expense_categories = [c.category for c in budget.get_expense_categories()]
    all_cats = income_categories + expense_categories
    actual_by_budget_cat = actual_by_budget_cat.reindex(all_cats, fill_value=0.0)

    actual_income = float(actual_by_budget_cat[income_categories].sum()) if income_categories else 0.0
    actual_expenses = float(actual_by_budget_cat[expense_categories].sum()) if expense_categories else 0.0

    num_months = end_idx - start_idx + 1

    return {
        "total_budgeted_income": budget.get_total_income() * num_months,
        "total_budgeted_expenses": budget.get_total_expenses() * num_months,
        "budgeted_net": budget.get_net_budget() * num_months,
        "total_actual_income": actual_income,
        "total_actual_expenses": actual_expenses,
        "actual_net": actual_income + actual_expenses,
    }


def test_calculate_variances_matches_expected(budget, actual_df, analyzer):
    (start_name, start_idx), (end_name, end_idx) = _find_month_bounds(actual_df)

    expected = _compute_expected_variances(budget, actual_df, start_idx, end_idx)
    result = analyzer.calculate_variances()

    # Sort both consistently and align columns
    cols = ["category", "budgeted", "actual", "variance", "variance_percent"]
    expected_sorted = expected[cols].sort_values("category").reset_index(drop=True)
    result_sorted = result[cols].sort_values("category").reset_index(drop=True)

    # Round to mitigate tiny float differences
    numeric_cols = ["budgeted", "actual", "variance", "variance_percent"]
    expected_sorted[numeric_cols] = expected_sorted[numeric_cols].astype(float).round(6)
    result_sorted[numeric_cols] = result_sorted[numeric_cols].astype(float).round(6)

    assert_frame_equal(expected_sorted, result_sorted, check_dtype=False)


def test_generate_summary_stats_matches_expected(budget, actual_df, analyzer):
    (start_name, start_idx), (end_name, end_idx) = _find_month_bounds(actual_df)

    expected = _compute_expected_summary(budget, actual_df, start_idx, end_idx)
    result = analyzer.generate_summary_stats()

    # Compare each key approximately
    for key, expected_val in expected.items():
        assert key in result, f"Missing key in summary: {key}"
        assert result[key] == pytest.approx(expected_val, abs=1e-6), f"Mismatch for {key}"
