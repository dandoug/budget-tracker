from typing import List

import pandas as pd
import streamlit as st

from app.parser.budget_loader import Category, Budget

# python
def flatten_categories(categories: List[Category], is_income: bool) -> pd.DataFrame:
    rows = []
    def walk(nodes, parent_path=None, level=0):
        for node in nodes:
            path = f"{parent_path}/{node.category}" if parent_path else node.category
            is_top = level == 0
            inherited = (node.amount is None) and not is_top
            rows.append({
                "id": path,
                "parent_id": parent_path,
                "level": level,
                "is_income": is_income,
                "is_top_level": is_top,
                "category": node.category,
                "inherited": inherited,
                "amount": None if inherited else (node.amount if node.amount is not None else None),
            })
            if node.subcategories:
                walk(node.subcategories, path, level + 1)
    walk(categories, None, 0)
    return pd.DataFrame(rows)


# python
def render_editor_table(df, key: str) -> pd.DataFrame:
    """
    Render the budget editor table and return the edited DataFrame.

    Notes:
    - st.data_editor does not mutate the input df; it returns an edited copy.
    - Capture and use the returned DataFrame (or read st.session_state[key]) to persist changes.
    """
    # Create a visual indent for hierarchy
    df = df.copy()
    df["name"] = df.apply(lambda r: ("    " * r["level"]) + ("• " if r["level"] else "") + r["category"], axis=1)

    # Put category into the index so it stays in the data but can be hidden visually
    df = df.set_index("category", drop=False)

    edited_df = st.data_editor(
        df[["name", "inherited", "amount"]],
        column_config={
            "name": st.column_config.TextColumn("Category", disabled=True),
            "inherited": st.column_config.CheckboxColumn("Inherited"),
            "amount": st.column_config.NumberColumn("Amount", format="$%.2f", step=10.0, min_value=0.0),
        },
        hide_index=True,
        disabled=["name"],  # redundant with column_config disabled=True
        use_container_width=True,
        key=key,
    )
    return edited_df

# python
def category_to_yaml_dict(cat):
    data = {"category": cat["category"]}
    if cat["is_top_level"]:
        # Top-level: include amount if set, otherwise omit (or include explicitly None)
        data["amount"] = cat["amount"] if cat["amount"] is not None else None
    else:
        if cat["inherited"]:
            data["amount"] = "INHERITED"
        else:
            data["amount"] = cat["amount"]
    return data


def apply_changes_to_working_copy(edit_table_df: pd.DataFrame, working_budget: Budget) -> bool:
    """
    Apply any changes made by the user to the working budget
    :return: True if any changes were made
    """
    changes_made = False

    for idx, row in edit_table_df.iterrows():
        current_category = working_budget.get_category_from_name(idx)
        # Compute the desired new amount based on 'inherited' and user entry
        if bool(row.get("inherited", False)):
            if current_category.amount is not None:
                current_category.amount = None
                changes_made = True
        else:
            new_amount = row.get("amount", None)
            # Convert pandas NaN to None for reliable comparison
            if pd.isna(new_amount):
                new_amount = None
            if current_category.amount != new_amount:
                current_category.amount = new_amount
                changes_made = True

    if changes_made:
        working_budget.model_post_init(None)

    return changes_made
