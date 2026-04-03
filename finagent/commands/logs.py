import json
from datetime import datetime
from pathlib import Path

import questionary
import typer

app = typer.Typer()

JSON_DIR = Path("json_files")
JSON_DIR.mkdir(exist_ok=True)

# Common categories
COMMON_CATEGORIES = [
    "food",
    "clothing",
    "transport",
    "entertainment",
    "utilities",
    "health",
    "education",
    "shopping",
    "travel",
    "other"
]


@app.command()
def add(
    name: str = typer.Argument(None),
    list_files: bool = typer.Option(False, "--list", help="List all log files"),
    manual: bool = typer.Option(False, "--manual", help="Use manual text input instead of interactive prompts"),
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

    if manual:
        print(f"Logging started for {name} (manual mode)")
        print("Type 'end' to stop.\n")
        print("Format: expense food 250 [--planned | --unplanned] [-m 'note']")
        print("Example: expense food 250 --unplanned -m 'stress eating after work'\n")

        # -------------------------
        # Manual loop
        # -------------------------
        while True:
            user_input = input(">> ").strip()

            if user_input.lower() == "end":
                break

            # -------------------------
            # Parse flags inline
            # -------------------------
            planned = None
            memo = None

            if "--planned" in user_input:
                planned = True
                user_input = user_input.replace("--planned", "").strip()
            elif "--unplanned" in user_input:
                planned = False
                user_input = user_input.replace("--unplanned", "").strip()

            if "-m" in user_input:
                parts_m = user_input.split("-m", 1)
                user_input = parts_m[0].strip()
                memo = parts_m[1].strip().strip("'\"")

            parts = user_input.split()

            if len(parts) != 3:
                print(
                    "Invalid format. Use: expense food 250 [--planned | --unplanned] [-m 'note']"
                )
                continue

            entry_type, category, amount = parts

            if entry_type not in ("income", "expense"):
                print("Type must be 'income' or 'expense'")
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
                "date": datetime.now().strftime("%d/%m/%Y"),
                "meta": datetime.now().isoformat(),
            }

            if planned is not None:
                entry["planned"] = planned

            if memo:
                entry["memo"] = memo

            print(
                f"  ✓ logged{' [unplanned]' if planned is False else ' [planned]' if planned is True else ''}{f'  — {memo}' if memo else ''}"
            )

            # Append to file immediately
            with open(file_path, "a") as f:
                json.dump(entry, f)
                f.write("\n")

        print("Data saved.")
    else:
        print(f"Logging started for {name}")
        print("Use the interactive prompts to log your entries.\n")

        # -------------------------
        # Interactive loop
        # -------------------------
        while True:
            # Ask if user wants to add another entry
            add_more = questionary.confirm("Add a new entry?").ask()
            if not add_more:
                break

            # Select type
            entry_type = questionary.select(
                "Select type:",
                choices=["expense", "income"]
            ).ask()

            # Select or enter category
            category_choice = questionary.select(
                "Select category:",
                choices=COMMON_CATEGORIES + ["custom"]
            ).ask()
            
            if category_choice == "custom":
                category = questionary.text("Enter custom category:").ask()
            else:
                category = category_choice

            # Enter amount
            amount_str = questionary.text("Enter amount:").ask()
            try:
                amount = float(amount_str)
            except ValueError:
                print("Invalid amount, skipping entry.")
                continue

            # Planned? (only for expense)
            planned = None
            if entry_type == "expense":
                planned_choice = questionary.select(
                    "Was this planned?",
                    choices=["yes", "no", "unsure"]
                ).ask()
                if planned_choice == "yes":
                    planned = True
                elif planned_choice == "no":
                    planned = False
                # unsure leaves as None

            # Memo
            memo = questionary.text("Add a note (optional):").ask()
            if not memo.strip():
                memo = None

            # Create entry
            entry = {
                "type": entry_type,
                "category": category,
                "amount": amount,
                "date": datetime.now().strftime("%d/%m/%Y"),
                "meta": datetime.now().isoformat(),
            }

            if planned is not None:
                entry["planned"] = planned

            if memo:
                entry["memo"] = memo

            print(
                f"  ✓ logged {entry_type} {category} {amount}{' [planned]' if planned is True else ' [unplanned]' if planned is False else ''}{f' — {memo}' if memo else ''}"
            )

            # Append to file immediately
            with open(file_path, "a") as f:
                json.dump(entry, f)
                f.write("\n")

        print("Logging complete.")
