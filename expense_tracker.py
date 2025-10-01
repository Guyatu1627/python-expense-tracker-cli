#!/usr/bin/env python3
"""
expense_tracker.py
Simple CLI expense tracker that stores entries in expenses.csv.

Features:
- Add expense
- Delete expense by id
- List expenses (recent first)
- Summarize expenses (total and by category; optionally filter by YYYY-MM)

This file is commented heavily so each line's purpose is clear while you learn.
"""

# --- IMPORTS: modules we need and why ---
import csv                       # read/write CSV files
import os                        # check file existence
from decimal import Decimal, InvalidOperation  # exact decimal arithmetic for money
from datetime import datetime, date          # parse and format dates

# --- CONSTANTS: central config you can change later ---
CSV_FILE = "expenses.csv"        # filename where expenses are stored
FIELDNAMES = ["id", "date", "category", "amount", "currency", "description"]
# FIELDNAMES defines CSV columns and order. Keep consistent to read/write correctly.

# --- Helper: ensure CSV file exists and has header ---
def ensure_file():
    """
    If CSV_FILE does not exist, create it and write the header row.
    This avoids errors when reading later.
    """
    if not os.path.exists(CSV_FILE):
        # open in write mode and create the file with header row
        with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()  # write header row

# --- Load expenses from CSV into Python structures ---
def load_expenses():
    """
    Read CSV_FILE and return a list of expense dicts.
    We convert types:
      - id -> int
      - date -> datetime.date (or None if parse fail)
      - amount -> Decimal
    """
    ensure_file()  # make sure file exists first
    expenses = []  # will hold parsed expense dicts
    with open(CSV_FILE, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # skip empty rows (defensive)
            if not row or not row.get("id"):
                continue
            # parse id (int)
            try:
                eid = int(row["id"])
            except (ValueError, TypeError):
                # if id is invalid, skip this row
                continue
            # parse date (YYYY-MM-DD), fallback to None
            d_str = row.get("date", "").strip()
            if d_str:
                try:
                    d = datetime.strptime(d_str, "%Y-%m-%d").date()
                except ValueError:
                    d = None
            else:
                d = None
            # parse amount into Decimal for money arithmetic
            amt_str = row.get("amount", "").strip()
            try:
                amount = Decimal(amt_str) if amt_str else Decimal("0")
            except InvalidOperation:
                amount = Decimal("0")
            # build normalized dict
            expense = {
                "id": eid,
                "date": d,
                "category": row.get("category", "").strip() or "uncategorized",
                "amount": amount,
                "currency": row.get("currency", "").strip() or "USD",
                "description": row.get("description", "").strip() or ""
            }
            expenses.append(expense)
    return expenses

# --- Save a list of expense dicts back to the CSV ---
def save_expenses(expenses):
    """
    Write the list of expense dicts to CSV_FILE.
    Convert date and Decimal back to string so CSV contains readable text.
    """
    with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for e in expenses:
            # convert Python types into CSV-serializable strings
            row = {
                "id": str(e["id"]),
                "date": e["date"].isoformat() if e.get("date") else "",
                "category": e.get("category", ""),
                "amount": str(e.get("amount", "0")),
                "currency": e.get("currency", ""),
                "description": e.get("description", "")
            }
            writer.writerow(row)

# --- Utility: compute next id from existing expenses ---
def next_id(expenses):
    """Return next integer id (1-based)."""
    if not expenses:
        return 1
    return max(e["id"] for e in expenses) + 1

# --- Feature: add a new expense interactively ---
def add_expense():
    """
    Prompt the user to enter expense fields, validate them,
    append to CSV and confirm.
    """
    expenses = load_expenses()            # load current list
    eid = next_id(expenses)               # determine new id
    today = date.today()                  # default date if user presses Enter

    # Input: date (optional default)
    date_input = input(f"Date (YYYY-MM-DD) [default {today.isoformat()}]: ").strip()
    if not date_input:
        date_input = today.isoformat()
    try:
        dt = datetime.strptime(date_input, "%Y-%m-%d").date()
    except ValueError:
        print("Invalid date format. Use YYYY-MM-DD. Expense not added.")
        return

    # Input: category with default
    category = input("Category (e.g., food, transport, rent) [default: uncategorized]: ").strip()
    if not category:
        category = "uncategorized"

    # Input: amount, convert to Decimal and validate
    amt_raw = input("Amount (numbers only, e.g. 12.50): ").strip()
    try:
        amount = Decimal(amt_raw)
    except (InvalidOperation, ValueError):
        print("Invalid amount. Use numbers like 12.50. Expense not added.")
        return

    # Input: currency, default USD
    currency = input("Currency [default USD]: ").strip() or "USD"

    # Input: optional description
    description = input("Description (optional): ").strip()

    # Build expense dict and save
    new_expense = {
        "id": eid,
        "date": dt,
        "category": category,
        "amount": amount,
        "currency": currency,
        "description": description
    }
    expenses.append(new_expense)
    save_expenses(expenses)
    print(f"Added expense id={eid}: {amount} {currency} on {dt.isoformat()} ({category})")

# --- Feature: delete an expense by id ---
def delete_expense():
    """
    Show recent expenses, ask for an id to delete, then remove it and save.
    """
    expenses = load_expenses()
    if not expenses:
        print("No expenses to delete.")
        return

    list_expenses(expenses, limit=50)  # show up to 50 so user sees ids

    try:
        eid = int(input("Enter expense id to delete: ").strip())
    except (ValueError, TypeError):
        print("Invalid id. Cancelled.")
        return

    # Filter out the chosen id
    new_expenses = [e for e in expenses if e["id"] != eid]
    if len(new_expenses) == len(expenses):
        print("No expense with that id. Nothing deleted.")
        return

    save_expenses(new_expenses)
    print(f"Deleted expense id={eid}.")

# --- Feature: list expenses (recent first) ---
def list_expenses(expenses=None, limit=20):
    """
    Print a table of expenses to the console. If expenses is None, load from file.
    limit: maximum rows to show (most recent first).
    """
    if expenses is None:
        expenses = load_expenses()
    if not expenses:
        print("No expenses found.")
        return

    # Sort by date descending; if date is None, place at earliest
    expenses_sorted = sorted(expenses, key=lambda x: (x["date"] or date.min), reverse=True)

    # Header
    print(f"{'id':<4} {'date':<10} {'category':<15} {'amount':>10} {'currency':<8} {'description'}")
    # Rows
    for e in expenses_sorted[:limit]:
        date_str = e["date"].isoformat() if e.get("date") else ""
        print(f"{e['id']:<4} {date_str:<10} {e['category']:<15} {str(e['amount']):>10} {e['currency']:<8} {e['description']}")

# --- Feature: summarize expenses (total + by category, optional month filter) ---
def summarize_expenses(month: str = None):
    """
    Summarize expenses.
    - If month is None: summarize all-time.
    - If month is 'YYYY-MM', summarize that month only.
    Shows total and breakdown by category.
    """
    expenses = load_expenses()
    if not expenses:
        print("No expenses to summarize.")
        return

    # Optionally filter by month
    filtered = []
    title = "Summary (all time)"
    if month:
        try:
            parts = month.split("-")
            year = int(parts[0])
            mon = int(parts[1])
        except Exception:
            print("Invalid month format. Use YYYY-MM (e.g., 2025-10).")
            return
        for e in expenses:
            if e.get("date") and e["date"].year == year and e["date"].month == mon:
                filtered.append(e)
        title = f"Summary for {year}-{mon:02d}"
    else:
        filtered = expenses

    if not filtered:
        print(f"No expenses for {title}.")
        return

    # Total (Decimal)
    total = sum(e["amount"] for e in filtered)

    # Breakdown by category
    by_cat = {}
    for e in filtered:
        cat = e.get("category", "uncategorized")
        by_cat.setdefault(cat, Decimal("0"))
        by_cat[cat] += e["amount"]

    # Print
    print(title)
    print(f"Total: {total} {filtered[0].get('currency', 'USD')}")
    print("By category:")
    for cat, amt in sorted(by_cat.items(), key=lambda x: x[1], reverse=True):
        print(f" - {cat}: {amt}")

# --- Main interactive loop ---
def main():
    """
    Run the CLI loop. The user chooses actions from a short menu.
    """
    ensure_file()  # create file if missing
    print("Simple Expense Tracker — enter a choice. (type 'help' to see options)")
    while True:
        print("\nOptions: [A]dd  [D]elete  [L]ist  [S]ummarize  [Q]uit")
        choice = input("Choose: ").strip().lower()
        if not choice:
            continue
        if choice in ("a", "add"):
            add_expense()
        elif choice in ("d", "delete"):
            delete_expense()
        elif choice in ("l", "list"):
            list_expenses()
        elif choice in ("s", "summarize"):
            month = input("Enter month (YYYY-MM) or press Enter for all: ").strip()
            summarize_expenses(month or None)
        elif choice in ("q", "quit", "exit"):
            print("Goodbye — your expenses are saved in", CSV_FILE)
            break
        elif choice in ("help", "h", "?"):
            print("Commands: add, delete, list, summarize, quit")
        else:
            print("Unknown option. Type 'help' for commands.")

# Standard Python entry point guard
if __name__ == "__main__":
    main()
