import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import typer
from rich import box
from rich.console import Console
from rich.table import Table

from finagent.commands.logs import rewrite_log_with_summary

app = typer.Typer()
console = Console()

JSON_DIR = Path("json_files")
SETTINGS_DIR = Path("db")
SETTINGS_DIR.mkdir(exist_ok=True)

CURRENCY = "₹"


# Helpers


def fmt(amount: float) -> str:
    return f"{CURRENCY}{amount:,.2f}"


def parse_date(entry: dict) -> Optional[datetime]:
    try:
        return datetime.strptime(entry.get("date", ""), "%d/%m/%Y")
    except ValueError:
        return None


def is_summary_record(entry: dict) -> bool:
    return isinstance(entry, dict) and entry.get("__summary__") is True


def filter_today(entries: list[dict]) -> list[dict]:
    today = datetime.today().date()
    return [e for e in entries if (d := parse_date(e)) and d.date() == today]


def filter_by_date(entries: list[dict], date_str: str) -> list[dict]:
    try:
        target = datetime.strptime(date_str, "%d/%m/%Y").date()
    except ValueError:
        console.print("[red]Invalid date format. Use DD/MM/YYYY[/red]")
        raise typer.Exit(1)

    return [e for e in entries if (d := parse_date(e)) and d.date() == target]


def filter_last_days(entries: list[dict], days: int) -> list[dict]:
    today = datetime.today().date()
    cutoff = today - timedelta(days=days - 1)

    return [e for e in entries if (d := parse_date(e)) and cutoff <= d.date() <= today]


def load_entries(name: str) -> list[dict]:
    path = JSON_DIR / f"{name.lower()}_logs.json"
    if not path.exists():
        console.print(f"[red]No log file found for '{name}'[/red]")
        raise typer.Exit(1)

    text = path.read_text().strip()
    if not text:
        return []

    decoder = json.JSONDecoder()
    idx = 0
    entries: list[dict] = []

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
                entry
                for entry in item
                if isinstance(entry, dict) and not is_summary_record(entry)
            )

        idx = end
        while idx < len(text) and text[idx].isspace():
            idx += 1

    return entries


def load_summary_record(name: str) -> dict | None:
    path = JSON_DIR / f"{name.lower()}_logs.json"
    if not path.exists():
        return None

    text = path.read_text().strip()
    if not text:
        return None

    decoder = json.JSONDecoder()
    idx = 0
    last_summary = None

    while idx < len(text):
        try:
            item, end = decoder.raw_decode(text, idx)
        except json.JSONDecodeError:
            break

        if isinstance(item, dict) and item.get("__summary__") is True:
            last_summary = item

        idx = end
        while idx < len(text) and text[idx].isspace():
            idx += 1

    return last_summary


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
    except:
        return 0.0


def save_opening_balance(name: str, amount: float):
    path = settings_path(name)
    with path.open("w") as f:
        json.dump({"opening_balance": amount}, f, indent=2)


# Balance Helpers


def apply_entry_to_balance(balance: float, e: dict) -> float:
    """Apply a single entry's effect to a running balance and return the new balance."""
    amount = float(e.get("amount", 0))
    etype = e.get("type")
    category = e.get("category", "-")

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


def compute_balance_before(
    all_entries: list[dict], filtered_entries: list[dict], opening_balance: float
) -> float:
    """
    Compute the running balance just before the earliest entry in filtered_entries.
    This gives the correct starting balance for filtered views (today, --date, --last).
    """
    if not filtered_entries:
        return opening_balance

    all_entries_sorted = sorted(
        [e for e in all_entries if parse_date(e)],
        key=lambda e: parse_date(e),
    )

    filtered_dates = {parse_date(e) for e in filtered_entries if parse_date(e)}
    cutoff = min(filtered_dates)

    balance = opening_balance
    for e in all_entries_sorted:
        if parse_date(e) >= cutoff:
            break
        balance = apply_entry_to_balance(balance, e)

    return balance


# Core Passbook


def print_passbook(entries: list[dict], opening_balance: float, sort: str):
    if not entries:
        console.print("[yellow]No entries to display.[/yellow]")
        return

    today = datetime.today().date()

    entries.sort(key=lambda e: parse_date(e) or datetime.min)
    balance = opening_balance

    table = Table(title="Passbook", box=box.ROUNDED, show_lines=True)
    table.add_column("S.No", justify="right")
    table.add_column("Date")
    table.add_column("Type")
    table.add_column("Category")
    table.add_column("Amount", justify="right")
    table.add_column("Balance", justify="right")
    table.add_column("Remarks")

    rows = []
    for e in entries:
        amount = float(e.get("amount", 0))
        etype = e.get("type")
        category = e.get("category", "-")
        date = e.get("date", "-")
        remarks = e.get("memo", "")

        parsed = parse_date(e)
        is_today = parsed and parsed.date() == today

        if etype == "income":
            balance += amount
            amt_str = f"[green]+{fmt(amount)}[/green]"
        elif etype == "expense":
            balance -= amount
            amt_str = f"[red]-{fmt(amount)}[/red]"
        elif etype == "rotation":
            if category == "liability":
                balance += amount
                amt_str = (
                    f"[green]{fmt(amount)}[/green]"
                    if amount >= 0
                    else f"[red]{fmt(amount)}[/red]"
                )
            elif category == "receivable":
                balance -= amount
                amt_str = (
                    f"[red]{fmt(amount)}[/red]"
                    if amount >= 0
                    else f"[green]{fmt(amount)}[/green]"
                )
            else:
                amt_str = fmt(amount)
        else:
            amt_str = fmt(amount)

        bal_color = "green" if balance >= 0 else "red"

        # Highlight today's rows
        if is_today:
            date = f"[bold]{date}[/bold]"
            remarks = f"[bold]{remarks}[/bold]"

        rows.append(
            (
                date,
                etype,
                category,
                amt_str,
                f"[{bal_color}]{fmt(balance)}[/{bal_color}]",
                remarks,
            )
        )

    if sort.lower() != "asc":
        rows = list(reversed(rows))

    for i, (date, etype, category, amt_str, balance_str, remarks) in enumerate(rows, 1):
        table.add_row(
            str(i),
            date,
            etype,
            category,
            amt_str,
            balance_str,
            remarks,
        )

    final_color = "green" if balance >= 0 else "red"
    table.add_row(
        "",
        "",
        "",
        "",
        "[bold]Available balance[/bold]",
        f"[{final_color}]{fmt(balance)}[/{final_color}]",
        "",
    )

    console.print(table)


# ── Command ─────────────────────────────────────────


@app.command()
def passbook(
    name: str,
    sort: str = typer.Option(
        "desc",
        "--sort",
        "-s",
        help="Sort order for displaying entries. "
        "'asc' shows oldest entries first, 'desc' shows newest first (default).",
    ),
    opening_balance: Optional[float] = typer.Option(
        None,
        "--set-balance",
        "-b",
        help="Set or update the opening balance for this account. "
        "If provided, this overwrites the stored opening balance.",
    ),
    full: bool = typer.Option(
        False,
        "--full",
        "-f",
        help="Show the complete passbook history. "
        "By default, only today's entries are displayed.",
    ),
    date: Optional[str] = typer.Option(
        None,
        "--date",
        "-d",
        help="Filter passbook entries for a specific date. "
        "Provide date in DD/MM/YYYY format. "
        "Overrides default today-only view.",
    ),
    last: Optional[int] = typer.Option(
        None,
        "--last",
        "-l",
        help="Show entries for the last N days (including today). "
        "Overrides default today-only view.",
    ),
):

    all_entries = load_entries(name)

    if opening_balance is not None:
        save_opening_balance(name, opening_balance)
        console.print(f"[green]Opening balance set to {fmt(opening_balance)}[/green]")
        rewrite_log_with_summary(name, JSON_DIR / f"{name.lower()}_logs.json")

    opening_balance = load_opening_balance(name)

    # Filtering priority
    if full:
        filtered = all_entries
    elif date:
        filtered = filter_by_date(all_entries, date)
    elif last:
        filtered = filter_last_days(all_entries, last)
    else:
        filtered = filter_today(all_entries)

    # Compute the correct starting balance for the filtered window.
    # For --full, this is just the opening_balance (no entries precede the window).
    # For all other filters, we accumulate all transactions before the window first.
    starting_balance = compute_balance_before(all_entries, filtered, opening_balance)

    print_passbook(filtered, starting_balance, sort)


if __name__ == "__main__":
    app()
