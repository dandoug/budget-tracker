# Data Directory

This directory contains private data files that should not be checked into version control.

Required files:
- `budget.yaml`: Budget definition file in YAML format
- Simplifi export file for "income and expense" report (P&L) (Excel format)

Example budget.yaml format:

```yaml
# Budget for 2025
income:
  - source: Salary
    amount: 5000

expenses:
  - category: Housing
    amount: 1500
    subcategories:
      - category: Rent
        amount: 1400
      - category: Renter's Insurance
        amount: INHERITED
  - category: Food
    amount: 600
    subcategories:
      - category: Groceries
        amount: 450
      - category: Restaurants
        amount: INHERITED
```
