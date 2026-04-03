import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich import box
from rich.console import Console
from rich.table import Table

app = typer.Typer()
console = Console()

JSON_DIR = Path("json_files")
CURRENCY = "₹"


# ── Helpers ────────────────────────────────────────────────────────────────────


def fmt(amount: float) -> str:
    return f"{CURRENCY}{amount:,.2f}"


def load_entries(name: str) -> list[dict]:
    path = JSON_DIR / f"{name.lower()}_logs.json"
    if not path.exists():
        console.print(f"[red]No log file found for '{name}'. Expected: {path}[/red]")
        raise typer.Exit(1)
    with path.open() as f:
        return json.load(f)


def parse_date(entry: dict) -> Optional[datetime]:
    raw = entry.get("date")
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%d/%m/%Y")
    except ValueError:
        return None


def filter_entries(
    data: list[dict],
    type_filter: Optional[str],
    category_filter: Optional[str],
    month: Optional[int],
    year: Optional[int],
) -> list[dict]:
    result = []
    for entry in data:
        if type_filter and entry.get("type") != type_filter:
            continue
        if (
            category_filter
            and entry.get("category", "uncategorized") != category_filter
        ):
            continue
        if month or year:
            dt = parse_date(entry)
            if dt is None:
                continue
            if month and dt.month != month:
                continue
            if year and dt.year != year:
                continue
        result.append(entry)
    return result


def compute_summary(
    data: list[dict],
) -> tuple[float, float, dict[str, float], list[dict]]:
    total_income = 0.0
    total_expense = 0.0
    category_totals: dict[str, float] = {}
    expense_entries: list[dict] = []

    for entry in data:
        amount = float(entry.get("amount", 0))
        if entry.get("type") == "income":
            total_income += amount
        elif entry.get("type") == "expense":
            total_expense += amount
            cat = entry.get("category", "uncategorized")
            category_totals[cat] = category_totals.get(cat, 0) + amount
            expense_entries.append(entry)

    return total_income, total_expense, category_totals, expense_entries


# ── Views ──────────────────────────────────────────────────────────────────────


def print_summary(total_income: float, total_expense: float) -> None:
    balance = total_income - total_expense
    color = "green" if balance >= 0 else "red"

    t = Table(title="Summary", box=box.ROUNDED, show_lines=True)
    t.add_column("", style="bold")
    t.add_column("Amount", justify="right")
    t.add_row("Income", f"[green]{fmt(total_income)}[/green]")
    t.add_row("Expense", f"[red]{fmt(total_expense)}[/red]")
    t.add_row("Balance", f"[{color} bold]{fmt(balance)}[/{color} bold]")
    console.print(t)


def print_top_expenses(
    expense_entries: list[dict], n: Optional[int], reverse: bool
) -> None:
    if not expense_entries:
        console.print("[yellow]No expense entries found.[/yellow]")
        return

    sorted_entries = sorted(
        expense_entries, key=lambda x: x.get("amount", 0), reverse=reverse
    )
    if n:
        sorted_entries = sorted_entries[:n]

    title = "Top Expenses" if reverse else "Bottom Expenses"
    t = Table(title=title, box=box.ROUNDED, show_lines=True)
    t.add_column("#", justify="right", style="dim")
    t.add_column("Amount", justify="right")
    t.add_column("Category")
    t.add_column("Date")

    for i, e in enumerate(sorted_entries, 1):
        t.add_row(
            str(i),
            f"[red]{fmt(e.get('amount', 0))}[/red]",
            e.get("category", "uncategorized"),
            e.get("date", "-"),
        )
    console.print(t)


def print_category_table(
    category_totals: dict[str, float],
    total_expense: float,
    n: Optional[int],
    reverse: bool,
    title: str = "Expenses by Category",
) -> None:
    if not category_totals:
        console.print("[yellow]No expense data found.[/yellow]")
        return

    sorted_cats = sorted(category_totals.items(), key=lambda x: x[1], reverse=reverse)
    if n:
        sorted_cats = sorted_cats[:n]

    t = Table(title=title, box=box.ROUNDED, show_lines=True)
    t.add_column("Category")
    t.add_column("Total", justify="right")
    t.add_column("Share", justify="right")

    for cat, total in sorted_cats:
        share = (total / total_expense * 100) if total_expense else 0
        t.add_row(cat, f"[red]{fmt(total)}[/red]", f"{share:.1f}%")

    console.print(t)


# ── Command ────────────────────────────────────────────────────────────────────


@app.command()
def show(
    name: str = typer.Argument(..., help="Username whose logs to display"),
    show_max: bool = typer.Option(
        False, "--max", help="Show top/bottom expense entries"
    ),
    max_cat: bool = typer.Option(False, "--max-cat", help="Show top/bottom categories"),
    n: Optional[int] = typer.Option(None, "-n", help="Limit number of results"),
    type_filter: Optional[str] = typer.Option(
        None, "--type", help="Filter by type: income | expense"
    ),
    category_filter: Optional[str] = typer.Option(
        None, "--category", help="Filter by category name"
    ),
    month: Optional[int] = typer.Option(
        None, "--month", min=1, max=12, help="Filter by month (1-12)"
    ),
    year: Optional[int] = typer.Option(None, "--year", help="Filter by year"),
    summary_only: bool = typer.Option(
        False, "--summary-only", help="Show only the summary table"
    ),
    category_only: bool = typer.Option(
        False, "--category-only", help="Show only category breakdown"
    ),
    sort: str = typer.Option("desc", "--sort", help="Sort order: asc | desc"),
):
    """Display financial logs for a user with optional filters and views."""
    reverse = sort.lower() != "asc"

    data = load_entries(name)
    data = filter_entries(data, type_filter, category_filter, month, year)

    if not data:
        console.print("[yellow]No entries match the given filters.[/yellow]")
        raise typer.Exit()

    total_income, total_expense, category_totals, expense_entries = compute_summary(
        data
    )

    if not category_only:
        print_summary(total_income, total_expense)
        if summary_only:
            return

    if show_max:
        print_top_expenses(expense_entries, n, reverse)
        return

    if max_cat:
        print_category_table(
            category_totals, total_expense, n, reverse, title="Top Categories"
        )
        return

    if not summary_only:
        print_category_table(category_totals, total_expense, n, reverse)
