import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import questionary
import typer

app = typer.Typer()

JSON_DIR = Path("json_files")
JSON_DIR.mkdir(exist_ok=True)
SETTINGS_DIR = Path("db")
SETTINGS_DIR.mkdir(exist_ok=True)
CURRENCY = "₹"


def fmt(amount: float) -> str:
    return f"{CURRENCY}{amount:,.2f}"


def settings_path(name: str) -> Path:
    return SETTINGS_DIR / f"{name.lower()}_settings.json"


def load_opening_balance(name: str) -> float:
    path = settings_path(name)
    if not path.exists():
        return 0.0

    try:
        with path.open() as f:
            data = json.load(f)
            return float(data.get("opening_balance", 0.0))
    except Exception:
        return 0.0


def save_opening_balance(name: str, amount: float):
    path = settings_path(name)
    with path.open("w") as f:
        json.dump({"opening_balance": amount}, f, indent=2)


def is_summary_record(entry: dict) -> bool:
    return isinstance(entry, dict) and entry.get("__summary__") is True


def parse_log_entries(path: Path) -> list[dict]:
    if not path.exists():
        return []

    text = path.read_text().strip()
    if not text:
        return []

    try:
        data = json.loads(text)
        if isinstance(data, list):
            return [
                entry
                for entry in data
                if isinstance(entry, dict) and not is_summary_record(entry)
            ]
    except json.JSONDecodeError:
        pass

    entries: list[dict] = []
    decoder = json.JSONDecoder()
    idx = 0
    while idx < len(text):
        try:
            item, end = decoder.raw_decode(text, idx)
        except json.JSONDecodeError:
            break

        if isinstance(item, dict):
            if not is_summary_record(item):
                entries.append(item)
        elif isinstance(item, list):
            entries.extend(
                [
                    entry
                    for entry in item
                    if isinstance(entry, dict) and not is_summary_record(entry)
                ]
            )

        idx = end
        while idx < len(text) and text[idx].isspace():
            idx += 1

    return entries


def compute_aggregates(name: str, entries: list[dict]) -> dict:
    total_income = 0.0
    total_expense = 0.0
    total_liability = 0.0
    total_receivable = 0.0

    for entry in entries:
        amount = float(entry.get("amount", 0))
        etype = entry.get("type")
        category = entry.get("category", "")

        if etype == "income":
            total_income += amount
        elif etype == "expense":
            total_expense += amount
        elif etype == "rotation":
            if category == "liability":
                total_liability += amount
            elif category == "receivable":
                total_receivable += amount

    opening_balance = load_opening_balance(name)
    available_balance = (
        opening_balance
        + total_income
        - total_expense
        + total_liability
        - total_receivable
    )

    return {
        "__summary__": True,
        "opening_balance": opening_balance,
        "total_income": total_income,
        "total_expense": total_expense,
        "total_liability": total_liability,
        "total_receivable": total_receivable,
        "available_balance": available_balance,
    }


def write_log_file(entries: list[dict], summary: dict, path: Path) -> None:
    with path.open("w") as f:
        for entry in entries:
            json.dump(entry, f)
            f.write("\n")
        json.dump(summary, f)
        f.write("\n")


def rewrite_log_with_summary(name: str, file_path: Path) -> float:
    entries = parse_log_entries(file_path)
    summary = compute_aggregates(name, entries)
    write_log_file(entries, summary, file_path)
    return summary["available_balance"]


def parse_date(entry: dict) -> Optional[datetime]:
    try:
        return datetime.strptime(entry.get("date", ""), "%d/%m/%Y")
    except ValueError:
        return None


def compute_balance(name: str, file_path: Path) -> float:
    balance = load_opening_balance(name)
    entries = parse_log_entries(file_path)
    entries.sort(key=lambda e: parse_date(e) or datetime.min)

    for e in entries:
        amount = float(e.get("amount", 0) or 0)
        etype = e.get("type")
        category = e.get("category", "")

        if etype == "income":
            balance += amount
        elif etype == "expense":
            balance -= amount
        elif etype == "rotation":
            if category == "liability":
                balance += amount
            elif category == "receivable":
                balance -= amount

    return balance


def format_balance(balance: float) -> str:
    return f"Available balance: {fmt(balance)}"


def strip_amount(amount):
    amount_list = amount.split("+")
    for i in range(len(amount_list)):
        amount_list[i] = float(amount_list[i])
    amount = sum(amount_list)
    print("Entered amount is: ", amount)
    return amount


# -------------------------
# Categories
# -------------------------
INCOME_CATEGORIES = [
    "salary",
    "bonus",
    "interest",
    "freelance",
    "gift",
    "reimbursement",
    "other",
]

EXPENSE_CATEGORIES = [
    "food",
    "clothing",
    "transport",
    "entertainment",
    "utilities",
    "health",
    "education",
    "shopping",
    "travel",
    "other",
]

ROTATION_CATEGORIES = [
    "liability",  # you owe someone
    "receivable",  # someone owes you
]


# -------------------------
# CLI Command
# -------------------------
@app.command()
def add(
    name: str = typer.Argument(None),
    list_files: bool = typer.Option(False, "--list", help="List all log files"),
    manual: bool = typer.Option(False, "--manual", help="Use manual text input"),
    date: str = typer.Option(
        None, "--date", help="Set a custom date (format: DD/MM/YYYY)"
    ),
):
    """
    Start logging for a user OR list available log files
    """

    # -------------------------
    # List files
    # -------------------------
    if list_files:
        files = list(JSON_DIR.glob("*_logs.json"))
        if not files:
            print("No log files found.")
            return

        print("Available log files:")
        for f in files:
            print(f"- {f.name}")
        return

    # -------------------------
    # Validate name
    # -------------------------
    if not name:
        print("Please provide a username or use --list")
        return

    file_path = JSON_DIR / f"{name.lower()}_logs.json"

    if not file_path.exists():
        print(f"File not found: {file_path}")
        return

    # -------------------------
    # Parse session date
    # -------------------------
    def parse_date(input_date):
        if input_date:
            try:
                dt = datetime.strptime(input_date, "%d/%m/%Y")
                return dt.strftime("%d/%m/%Y"), dt.isoformat()
            except ValueError:
                print("Invalid date format. Use DD/MM/YYYY. Using today instead.")
        now = datetime.now()
        return now.strftime("%d/%m/%Y"), now.isoformat()

    session_date, session_meta = parse_date(date)
    current_balance = compute_balance(name, file_path)

    # -------------------------
    # Manual mode
    # -------------------------
    if manual:
        print(f"Logging started for {name} (manual mode)")
        print(f"All entries will use date: {session_date}")
        print(format_balance(current_balance))
        print("Type 'end' to stop.\n")
        print("Format: type category amount [-m 'note']")
        print("Example: rotation liability 5000 -m 'borrowed from John'\n")

        saved_any = False

        while True:
            user_input = input(">> ").strip()
            if user_input.lower() == "end":
                break

            memo = None

            if "-m" in user_input:
                parts_m = user_input.split("-m", 1)
                user_input = parts_m[0].strip()
                memo = parts_m[1].strip().strip("'\"")

            parts = user_input.split()
            if len(parts) != 3:
                print("Invalid format. Use: type category amount [-m 'note']")
                continue

            entry_type, category, amount = parts

            if entry_type not in ("income", "expense", "rotation"):
                print("Type must be 'income', 'expense', or 'rotation'")
                continue

            # Validate category
            if entry_type == "income" and category not in INCOME_CATEGORIES:
                print("Invalid income category")
                continue
            elif entry_type == "expense" and category not in EXPENSE_CATEGORIES:
                print("Invalid expense category")
                continue
            elif entry_type == "rotation" and category not in ROTATION_CATEGORIES:
                print("Category must be 'liability' or 'receivable'")
                continue

            try:
                amount = float(amount)
            except ValueError:
                print("Amount must be a number")
                continue

            entry = {
                "type": entry_type,
                "category": category,
                "amount": amount,
                "date": session_date,
                "meta": session_meta,
            }

            if memo:
                entry["memo"] = memo

            print(
                f"  ✓ logged {entry_type} {category} {amount}"
                f"{f' — {memo}' if memo else ''} on {session_date}"
            )

            with open(file_path, "a") as f:
                json.dump(entry, f)
                f.write("\n")

            saved_any = True
            if entry_type == "income":
                current_balance += amount
            elif entry_type == "expense":
                current_balance -= amount
            elif entry_type == "rotation":
                if category == "liability":
                    current_balance += amount
                elif category == "receivable":
                    current_balance -= amount

            print(format_balance(current_balance))

        if saved_any:
            rewrite_log_with_summary(name, file_path)
        print("Data saved.")

    # -------------------------
    # Interactive mode
    # -------------------------
    else:
        print(f"Logging started for {name}")
        print(f"All entries will use date: {session_date}\n")
        print(format_balance(current_balance))

        saved_any = False
        while True:
            add_more = questionary.confirm("Add a new entry?").ask()
            if not add_more:
                break

            # Select type
            entry_type = questionary.select(
                "Select type:", choices=["income", "expense", "rotation"]
            ).ask()

            # Category selection
            if entry_type == "income":
                category_choice = questionary.select(
                    "Select income category:",
                    choices=INCOME_CATEGORIES + ["custom"],
                ).ask()

            elif entry_type == "expense":
                category_choice = questionary.select(
                    "Select expense category:",
                    choices=EXPENSE_CATEGORIES + ["custom"],
                ).ask()

            else:  # rotation
                category_choice = questionary.select(
                    "Select rotation type:",
                    choices=ROTATION_CATEGORIES,
                ).ask()

            category = (
                questionary.text("Enter custom category:").ask()
                if category_choice == "custom"
                else category_choice
            )

            # Amount
            amount_str = questionary.text(
                "Enter amount (use negative to settle):"
            ).ask()

            try:
                amount = strip_amount(amount_str)
            except ValueError:
                print("Invalid amount, skipping entry.")
                continue

            # Planned (only expense)
            planned = None
            if entry_type == "expense":
                planned_choice = questionary.select(
                    "Was this planned?", choices=["yes", "no", "unsure"]
                ).ask()
                if planned_choice == "yes":
                    planned = True
                elif planned_choice == "no":
                    planned = False

            # Memo
            memo = questionary.text("Add a note (optional):").ask()
            memo = memo if memo.strip() else None

            entry = {
                "type": entry_type,
                "category": category,
                "amount": amount,
                "date": session_date,
                "meta": session_meta,
            }

            if planned is not None:
                entry["planned"] = planned
            if memo:
                entry["memo"] = memo

            print(
                f"logged {entry_type} {category} {amount}"
                f"{' [planned]' if planned else ' [unplanned]' if planned is False else ''}"
                f"{f' — {memo}' if memo else ''} on {session_date}"
            )

            with open(file_path, "a") as f:
                json.dump(entry, f)
                f.write("\n")

            saved_any = True
            if entry_type == "income":
                current_balance += amount
            elif entry_type == "expense":
                current_balance -= amount
            elif entry_type == "rotation":
                if category == "liability":
                    current_balance += amount
                elif category == "receivable":
                    current_balance -= amount

            print(format_balance(current_balance))

        if saved_any:
            rewrite_log_with_summary(name, file_path)
        print("Logging complete.")


if __name__ == "__main__":
    app()
