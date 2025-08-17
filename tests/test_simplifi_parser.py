"""Tests for Simplifi parser functionality."""

from pathlib import Path

from pandas import DataFrame, Series

from app.parser.simplifi_parser import SimplifiParser

DATA_DIR = Path(__file__).parent.parent / 'data'

def test_load_excel_file():
    """Test loading Excel file."""
    parser = SimplifiParser()
    df = parser.load_file(DATA_DIR / 'sample_Simplifi-profit-loss.xlsx')
    assert isinstance(df, DataFrame)
    groceries = df.loc['Groceries']
    assert isinstance(groceries, Series)
    assert groceries.August == -549.73
    assert groceries.July == -2076.62
    assert groceries.June == -1449.23
    assert groceries.HierarchyLevel == 1

    assert df.loc['Fitness Fees and Passes'].August == 0
    assert df.loc['Total Fitness'].July == -538

