"""Simplifi P&L report parser."""
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional
import logging


logger = logging.getLogger(__name__)


class SimplifiParser:
    """Parser for Simplifi P&L export files (CSV/XLSX)."""

    def __init__(self):
        self.data: Optional[pd.DataFrame] = None
        self.monthly_summary: Optional[pd.DataFrame] = None

    def load_file(self, file_path: Path) -> pd.DataFrame:
        """Load Simplifi export file."""
        try:
            if file_path.suffix.lower() == '.csv':
                df = pd.read_csv(file_path)

                # 1. Filter out the summary "Total" rows immediately
                df = df[~df['Category 1'].astype(str).str.contains('Total', na=False)]
                if 'Category 2' in df.columns:
                    df = df[~df['Category 2'].astype(str).str.contains('Total', na=False)]
                # Filter out rows where 'Income/Expense' column is not NaN
                if 'Income/Expense' in df.columns:
                    df = df[df['Income/Expense'].isna()]

                # 2. Read the exact category and level from the row's populated column
                def resolve_hierarchy(row):
                    c3 = row.get('Category 3')
                    c2 = row.get('Category 2')
                    c1 = row.get('Category 1')

                    # Scan right-to-left: check Category 3 first
                    if pd.notna(c3) and str(c3).strip():
                        val = str(c3).strip()
                        if val.endswith(" (Other)"):
                            return pd.Series([val.replace(" (Other)", ""), 1])
                        return pd.Series([val, 2])

                    # Then check Category 2
                    elif pd.notna(c2) and str(c2).strip():
                        val = str(c2).strip()
                        if val.endswith(" (Other)"):
                            return pd.Series([val.replace(" (Other)", ""), 0])
                        return pd.Series([val, 1])

                    # Fallback to Category 1
                    else:
                        val = str(c1).strip() if pd.notna(c1) else "Unknown"
                        return pd.Series([val, 0])

                df[['Category', 'HierarchyLevel']] = df.apply(resolve_hierarchy, axis=1)

                # 3. Drop the matrix category cols and the grand 'Total' column
                cat_cols = ['Category 1', 'Category 2', 'Category 3', 'Income/Expense']
                existing_cats = [c for c in cat_cols if c in df.columns]
                cols_to_drop = existing_cats + (['Total'] if 'Total' in df.columns else [])
                df = df.drop(columns=cols_to_drop, errors='ignore')

            elif file_path.suffix.lower() in ['.xlsx', '.xls']:
                raise ValueError(f"Switching to only csv, not supported: {file_path.suffix}")
                # # Load the workbook and select the active sheet to get outline level
                # workbook = openpyxl.load_workbook(file_path)
                # sheet = workbook.active
                # # Create an empty list to hold the levels
                # outline_levels = []
                #
                # # Loop ONLY through the rows that contain data to build outline level column
                # # Data starts on Excel row 2; after title, min_row=2 skips the title
                # # sheet.iter_rows() is efficient for this.
                # for row in sheet.iter_rows(min_row=2, max_row=sheet.max_row):
                #     # The first cell in the row tuple gives us access to its properties
                #     level = sheet.row_dimensions[row[0].row].outline_level
                #     outline_levels.append(level)
                #
                # # Read the dataframe grid
                # df = pd.read_excel(file_path)
                #
                # # Add the hierarchy level column
                # df['HierarchyLevel'] = outline_levels

            else:
                raise ValueError(f"Unsupported file format: {file_path.suffix}")

            self.data = self._clean_data(df).set_index('Category')

            return self.data

        except Exception as e:
            logger.error(f"Error loading Simplifi file: {e}")
            raise

    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize the imported data."""
        df_clean = df.copy()

        # 2) Normalize numeric-looking object columns:
        #    - remove leading "\'" or "'" artifacts
        #    - remove any thousands separators
        #    - convert (123.45) -> -123.45
        #    - coerce to numeric
        obj_cols = df_clean.select_dtypes(include=['object']).columns.tolist()

        def to_numeric_series(s: pd.Series) -> pd.Series:
            # Work on string view
            s_str = s.astype(str).str.strip()

            # Strip leading \" and ' characters that may prefix negatives, e.g., "\'-315.87"
            s_str = s_str.str.replace(r"^[\\']+", "", regex=True)

            # Remove common currency/spacing artifacts (keep digits, minus, dot, parentheses, comma)
            # First handle parentheses negatives
            s_str = s_str.str.replace(r"^\((.*)\)$", r"-\1", regex=True)

            # Drop commas and dollar signs
            s_str = s_str.str.replace(r"[$,]", "", regex=True)

            # Finally, to_numeric
            return pd.to_numeric(s_str, errors='coerce')

        for col in obj_cols:
            parsed = to_numeric_series(df_clean[col])
            # Only convert the column if a significant portion parsed as numbers
            # (tune threshold as needed)
            if parsed.notna().mean() >= 0.6:
                df_clean[col] = parsed

        # 2) Replace NaN with 0 only for numeric columns
        num_cols = df_clean.select_dtypes(include=['number']).columns
        df_clean[num_cols] = df_clean[num_cols].fillna(0)

        return df_clean

    def get_monthly_summary(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """Generate a monthly summary of income/expenses by category."""
        if self.data is None:
            raise ValueError("No data loaded. Call load_file() first.")

        # TODO: Implement monthly aggregation logic
        # This is a placeholder implementation
        summary = self.data.copy()

        if start_date or end_date:
            # Filter by date range if provided
            pass

        self.monthly_summary = summary
        return summary

    def get_category_breakdown(self) -> Dict[str, Dict[str, float]]:
        """Get breakdown of expenses by category and subcategory."""
        if self.data is None:
            raise ValueError("No data loaded. Call load_file() first.")

        # TODO: Implement category breakdown logic
        return {}

    def export_processed_data(self, output_path: Path) -> None:
        """Export processed data to CSV."""
        if self.data is None:
            raise ValueError("No data loaded. Call load_file() first.")

        self.data.to_csv(output_path, index=True)
