import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich import box
from rich.console import Console
from rich.rule import Rule
from rich.table import Table

app = typer.Typer()
console = Console()

JSON_DIR = Path("json_files")
CURRENCY = "₹"

REFLECTION_PROMPTS = [
    "What was the emotional state behind your unplanned spending today?",
    "Was there a moment today where you spent to avoid something?",
    "Which expense do you feel best about, and why?",
    "If you could redo today's spending, what would you change?",
    "What triggered the unplanned expenses — stress, boredom, social pressure?",
]


# ── Helpers ────────────────────────────────────────────────────────────────────


def fmt(amount: float) -> str:
    return f"{CURRENCY}{amount:,.2f}"


def today_str() -> str:
    return datetime.now().strftime("%d/%m/%Y")


def load_entries(name: str) -> list[dict]:
    path = JSON_DIR / f"{name.lower()}_logs.json"
    if not path.exists():
        console.print(f"[red]No log file found for '{name}'.[/red]")
        raise typer.Exit(1)
    if path.stat().st_size == 0:
        return []
    with path.open() as f:
        return json.load(f)


def save_entries(name: str, data: list[dict]) -> None:
    path = JSON_DIR / f"{name.lower()}_logs.json"
    with path.open("w") as f:
        json.dump(data, f, indent=4)


def get_todays_entries(data: list[dict]) -> list[dict]:
    today = today_str()
    return [e for e in data if e.get("date") == today and e.get("type") != "reflection"]


def pick_prompt(data: list[dict], today_entries: list[dict]) -> str:
    expenses = [e for e in today_entries if e.get("type") == "expense"]

    if not expenses:
        return "No expenses today. How did that feel?"

    total_expense = sum(e.get("amount", 0) for e in expenses)

    unplanned = [e for e in expenses if e.get("planned") is False]
    unplanned_amount = sum(e.get("amount", 0) for e in unplanned)
    unplanned_pct = (unplanned_amount / total_expense * 100) if total_expense else 0

    # ---- CATEGORY DISTRIBUTION ----
    category_totals = {}
    for e in expenses:
        cat = e.get("category", "uncategorized")
        category_totals[cat] = category_totals.get(cat, 0) + e.get("amount", 0)

    top_category = None
    top_category_pct = 0

    if category_totals:
        top_category, top_amount = max(category_totals.items(), key=lambda x: x[1])
        top_category_pct = top_amount / total_expense * 100

    # ---- LARGE SINGLE EXPENSE ----
    largest_expense = max(e.get("amount", 0) for e in expenses)

    # ---- ENTRY COUNT ----
    entry_count = len(expenses)

    # ---- TRIGGERS ----

    # 1. High unplanned %
    if unplanned_pct > 50:
        return "More than half your spending today was unplanned. What was going on emotionally?"

    # 2. All unplanned, no memos
    if unplanned and all(not e.get("memo") for e in unplanned):
        return "You didn't note a reason for any unplanned spend. Can you recall what you were feeling?"

    # 3. Single category dominates
    if top_category_pct > 60:
        return f"{top_category} took up most of today. Was that need, habit, or something else?"

    # 4. No unplanned
    if not unplanned:
        return "You stuck to your plan today. What made that easier?"

    # 5. Large single expense
    if largest_expense > total_expense * 0.5:
        return "You made one big purchase today. Was it thought through or impulsive?"

    # 6. Too many entries
    if entry_count >= 8:
        return "You spent in many places today. Does scattered spending reflect a scattered day?"

    # 7. No income + high expense
    income = [e for e in today_entries if e.get("type") == "income"]
    if not income and total_expense > 0:
        return "Heavy spend day with no income. How does that feel?"

    # 8. Unplanned spending late in the day (after 8pm meta timestamps)
    late_unplanned = [
        e
        for e in unplanned
        if e.get("meta") and datetime.fromisoformat(e["meta"]).hour >= 20
    ]
    if late_unplanned:
        return "You had unplanned spending late in the evening. Tiredness and low willpower often peak then — was that a factor?"

    """ 
    9. Every expense is unplanned (nothing was planned at all)
    if expenses and not planned:
        return "Nothing today was planned. Was today reactive — just responding to whatever came up?"
    """

    # 10. Memo on every unplanned entry (self-aware day)
    if unplanned and all(e.get("memo") for e in unplanned):
        return "You noted a reason for every unplanned spend today. You're building awareness — what pattern do you notice across those reasons?"

    # 11. Same category appears multiple times unplanned
    from collections import Counter

    unplanned_cats = Counter(e.get("category") for e in unplanned)
    repeat_cat = [cat for cat, count in unplanned_cats.items() if count >= 2]
    if repeat_cat:
        return f"You made multiple unplanned {repeat_cat[0]} purchases today. Is {repeat_cat[0]} a comfort category for you?"

    # 12. Lots of small unplanned expenses (death by a thousand cuts)
    small_unplanned = [e for e in unplanned if e.get("amount", 0) < 100]
    if len(small_unplanned) >= 3:
        return "Several small unplanned expenses today — each feels harmless but they add up. What's the common thread?"

    # 13. Unplanned spend early in the day (before 10am)
    early_unplanned = [
        e
        for e in unplanned
        if e.get("meta") and datetime.fromisoformat(e["meta"]).hour < 10
    ]
    if early_unplanned:
        return "You had unplanned spending before 10am. Morning decisions are often automatic — was this intentional?"

    # 14. Today is significantly worse than personal average
    avg_daily_expense = sum(
        e.get("amount", 0)
        for e in data
        if e.get("type") == "expense" and e.get("date") != today_str()
    ) / max(
        len(
            set(
                e["date"]
                for e in data
                if e.get("type") == "expense" and e.get("date") != today_str()
            )
        ),
        1,
    )

    if avg_daily_expense and total_expense > avg_daily_expense * 1.5:
        return f"You spent {fmt(total_expense)} today — about {int(total_expense / avg_daily_expense * 100 - 100)}% more than your daily average. What made today different?"

    # 15. Today is significantly better than average (positive reinforcement)
    if avg_daily_expense and total_expense < avg_daily_expense * 0.5:
        return f"You spent well below your usual today. What helped you hold back — was it intentional or circumstantial?"

    """
    # 16. Repeat category from yesterday
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y")
    yesterday_cats = set(
        e.get("category") for e in data
        if e.get("date") == yesterday and e.get("type") == "expense"
    )
    today_cats = set(e.get("category") for e in expenses)
    overlap = today_cats & yesterday_cats
    if overlap:
        overlap_str = ", ".join(overlap)
        return f"You spent on {overlap_str} yesterday too. Is this a pattern forming or just coincidence?"
    """

    # 17. No entries at all marked planned or unplanned (not using the flags)
    unmarked = [e for e in expenses if e.get("planned") is None]
    if len(unmarked) == len(expenses):
        return "You didn't mark anything as planned or unplanned today. Try it tomorrow — that distinction alone builds awareness."

    # ---- FALLBACK ----
    return REFLECTION_PROMPTS[len(data) % len(REFLECTION_PROMPTS)]


# ── Views ──────────────────────────────────────────────────────────────────────


def print_todays_entries(entries: list[dict]) -> None:
    t = Table(
        title=f"Today's Entries — {today_str()}", box=box.ROUNDED, show_lines=True
    )
    t.add_column("#", justify="right", style="dim")
    t.add_column("Type")
    t.add_column("Category")
    t.add_column("Amount", justify="right")
    t.add_column("Planned")
    t.add_column("Memo")

    for i, e in enumerate(entries, 1):
        is_expense = e.get("type") == "expense"
        amount_fmt = (
            f"[red]{fmt(e.get('amount', 0))}[/red]"
            if is_expense
            else f"[green]{fmt(e.get('amount', 0))}[/green]"
        )

        planned = e.get("planned")
        if planned is True:
            planned_fmt = "[green]planned[/green]"
        elif planned is False:
            planned_fmt = "[red]unplanned[/red]"
        else:
            planned_fmt = "[dim]—[/dim]"

        t.add_row(
            str(i),
            e.get("type", "-"),
            e.get("category", "-"),
            amount_fmt,
            planned_fmt,
            e.get("memo", "[dim]—[/dim]"),
        )

    console.print(t)


def print_unplanned_summary(entries: list[dict]) -> None:
    expenses = [e for e in entries if e.get("type") == "expense"]
    unplanned = [e for e in expenses if e.get("planned") is False]
    planned = [e for e in expenses if e.get("planned") is True]
    unmarked = [e for e in expenses if e.get("planned") is None]

    total_expense = sum(e.get("amount", 0) for e in expenses)
    total_unplanned = sum(e.get("amount", 0) for e in unplanned)
    total_planned = sum(e.get("amount", 0) for e in planned)
    pct = (total_unplanned / total_expense * 100) if total_expense else 0

    t = Table(title="Spending Breakdown", box=box.ROUNDED, show_lines=True)
    t.add_column("", style="bold")
    t.add_column("Amount", justify="right")
    t.add_column("Entries", justify="right")

    t.add_row("Planned", f"[green]{fmt(total_planned)}[/green]", str(len(planned)))
    t.add_row("Unplanned", f"[red]{fmt(total_unplanned)}[/red]", str(len(unplanned)))

    if unmarked:
        total_unmarked = sum(e.get("amount", 0) for e in unmarked)
        t.add_row(
            "Unmarked",
            f"[dim]{fmt(total_unmarked)}[/dim]",
            f"[dim]{len(unmarked)}[/dim]",
        )

    t.add_row("Total", fmt(total_expense), str(len(expenses)))

    console.print(t)

    if total_unplanned > 0:
        console.print(
            f"\n  [bold red]{pct:.1f}%[/bold red] of today's spending was unplanned.\n"
        )
    else:
        console.print("\n  [bold green]No unplanned spending today.[/bold green]\n")


# ── Command ────────────────────────────────────────────────────────────────────


@app.command()
def debrief(
    name: str = typer.Argument(..., help="Username to reflect on"),
):
    """
    Nightly debrief — review today's entries, unplanned spending, and journal your reflection.
    """

    data = load_entries(name)
    today_entries = get_todays_entries(data)

    # -------------------------
    # Nothing logged today
    # -------------------------
    if not today_entries:
        console.print(f"\n[yellow]No entries found for today ({today_str()}).[/yellow]")
        console.print(
            "Log your day first with: [bold]python main.py logs add {name}[/bold]\n"
        )
        raise typer.Exit()

    # -------------------------
    # Show today
    # -------------------------
    console.print()
    console.print(Rule("[bold]Nightly Debrief[/bold]"))
    console.print()

    print_todays_entries(today_entries)
    console.print()
    print_unplanned_summary(today_entries)

    # -------------------------
    # Reflection prompt
    # -------------------------
    prompt = pick_prompt(data, today_entries)
    console.print(f"\n  [bold italic]{prompt}[/bold italic]\n")
    console.print("  Write your reflection below. Press Enter twice when done.\n")

    lines = []
    while True:
        line = input("  > ")
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)

    reflection_text = "\n".join(lines).strip()

    if not reflection_text:
        console.print("\n[dim]No reflection saved.[/dim]\n")
        raise typer.Exit()

    # -------------------------
    # Save reflection entry
    # -------------------------
    reflection_entry = {
        "type": "reflection",
        "date": today_str(),
        "meta": datetime.now().isoformat(),
        "prompt": prompt,
        "note": reflection_text,
    }

    data.append(reflection_entry)
    save_entries(name, data)

    console.print()
    console.print(Rule())
    console.print("\n  [green]Reflection saved. Good night.[/green]\n")
