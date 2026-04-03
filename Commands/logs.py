import json
from datetime import datetime
from pathlib import Path

import typer

app = typer.Typer()

JSON_DIR = Path("json_files")
JSON_DIR.mkdir(exist_ok=True)


@app.command()
def add(
    name: str = typer.Argument(None),
    list_files: bool = typer.Option(False, "--list", help="List all log files"),
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

    print(f"Logging started for {name}")
    print("Type 'end' to stop.\n")
    print("Format: expense food 250 [--planned | --unplanned] [-m 'note']")
    print("Example: expense food 250 --unplanned -m 'stress eating after work'\n")

    # -------------------------
    # Load existing data safely
    # -------------------------
    if file_path.stat().st_size == 0:
        data = []
    else:
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            print("Corrupted JSON. Resetting file.")
            data = []

    # -------------------------
    # Loop
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

        data.append(entry)
        print(
            f"  ✓ logged{' [unplanned]' if planned is False else ' [planned]' if planned is True else ''}{f'  — {memo}' if memo else ''}"
        )

    # -------------------------
    # Save after loop
    # -------------------------
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

    print("Data saved.")
