import json
from datetime import datetime
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


# ── Helpers ─────────────────────────────────────────


def fmt(amount: float) -> str:
    return f"{CURRENCY}{amount:,.2f}"


def load_entries(name: str) -> list[dict]:
    path = JSON_DIR / f"{name.lower()}_logs.json"
    if not path.exists():
        console.print(f"[red]No log file found for '{name}'[/red]")
        raise typer.Exit(1)

    with path.open() as f:
        text = f.read().strip()

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


def load_summary_record(name: str) -> Optional[dict]:
    path = JSON_DIR / f"{name.lower()}_logs.json"
    if not path.exists():
        return None

    text = path.read_text().strip()
    if not text:
        return None

    try:
        data = json.loads(text)
        if isinstance(data, list):
            summary_records = [
                entry
                for entry in data
                if isinstance(entry, dict) and entry.get("__summary__") is True
            ]
            return summary_records[-1] if summary_records else None
    except json.JSONDecodeError:
        pass

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
        elif isinstance(item, list):
            for entry in item:
                if isinstance(entry, dict) and entry.get("__summary__") is True:
                    last_summary = entry

        idx = end
        while idx < len(text) and text[idx].isspace():
            idx += 1

    return last_summary


"""
def print_summary_record(summary: dict):
    if not summary:
        return

    table = Table(title="Summary metadata", box=box.SIMPLE, show_lines=False)
    table.add_column("Metric")
    table.add_column("Value", justify="right")

    table.add_row("Opening balance", fmt(float(summary.get("opening_balance", 0.0))))
    table.add_row("Total income", fmt(float(summary.get("total_income", 0.0))))
    table.add_row("Total expense", fmt(float(summary.get("total_expense", 0.0))))
    table.add_row("Total liability rotations", fmt(float(summary.get("total_liability", 0.0))))
    table.add_row("Total receivable rotations", fmt(float(summary.get("total_receivable", 0.0))))
    table.add_row("Available balance", fmt(float(summary.get("available_balance", 0.0))))
    console.print(table)
"""


def parse_date(entry: dict) -> Optional[datetime]:
    try:
        return datetime.strptime(entry.get("date", ""), "%d/%m/%Y")
    except ValueError:
        return None


def is_summary_record(entry: dict) -> bool:
    return isinstance(entry, dict) and entry.get("__summary__") is True


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


# ── Core Passbook ───────────────────────────────────


def print_passbook(entries: list[dict], opening_balance: float, sort: str):
    if not entries:
        console.print("[yellow]No entries to display.[/yellow]")
        return

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
        "desc", "--sort", "-s", help="Use asc for oldest entries first"
    ),
    opening_balance: Optional[float] = typer.Option(None, "--set-balance", "-b"),
):
    entries = load_entries(name)

    if opening_balance is not None:
        save_opening_balance(name, opening_balance)
        console.print(f"[green]Opening balance set to {fmt(opening_balance)}[/green]")
        rewrite_log_with_summary(name, JSON_DIR / f"{name.lower()}_logs.json")

    opening_balance = load_opening_balance(name)

    summary_record = load_summary_record(name)
    """
    if summary_record:
          print_summary_record(summary_record)
    """
    print_passbook(entries, opening_balance, sort)


if __name__ == "__main__":
    app()

