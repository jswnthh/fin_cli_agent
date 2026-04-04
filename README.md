# FinAgent — Financial Expenditure Awareness Agent
<p align="center">
  <img src="https://github.com/user-attachments/assets/b627466f-dffe-423b-a6b8-4826b8ec7871" width="400" alt="FinAgent"/>
</p>

> *Most finance apps assume you're a rational human making intentional choices. FinAgent is built for the rest of us.*

FinAgent is a command-line tool for tracking daily expenses and reflecting on the emotional patterns behind your spending. No flashy UI, no hand-holding — just you, the terminal, and the courage to type.

---

## Why FinAgent?

Emotional spending is your brain saying *"I'm in pain and I cannot process this, but that jacket is 40% off"* and calling it a solution. The jacket knows. You know. Everyone knows. And yet.

It's not stupidity. It's not weakness. It's your psyche doing a terrible job at being a therapist — prescribing retail as medicine for boredom, stress, and every feeling you didn't want to sit with.

**Awareness is the first step.** FinAgent is built for exactly that.
<p align="centre">
<img width="1193" height="731" alt="image" src="https://github.com/user-attachments/assets/ca90aa68-584f-41ea-8d75-6828405a6e11" />
</p>

---

## Features

- **User Profiles** — Create separate log files per person
- **Expense Logging** — Interactive or manual mode with categories, amounts, and optional memos
- **Planned vs. Unplanned Tracking** — The single most important distinction you can make
- **Spending Summaries** — Category breakdowns, top expenses, income vs. expense balance
- **Nightly Debrief** — Context-aware reflection prompts based on your actual day's data

---

## Installation

**Requirements:** Python 3.8+

```bash
# Clone the repo
git clone https://github.com/jswnthh/fin_cli_agent
cd finagent

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install the package
pip install -e .
```

---

## Quick Start

```bash
# 1. Create your profile
fin users create "jaswanth"

# 2. Log today's expenses
fin logs add "jaswanth"

# 3. View your spending summary
fin summary show "jaswanth"

# 4. Do your nightly debrief
fin reflect debrief "jaswanth"
```

---

## Command Reference

### `fin users`

```bash
fin users create <name>          # Create a new user profile
```

### `fin logs`

```bash
fin logs add <name>              # Log expenses interactively (recommended)
fin logs add <name> --manual     # Log using text input
fin logs add --list              # List all existing log files

A summary metadata record is saved automatically after each logging session, so `fin summary passbook` can read totals from the file.
```

**Manual mode format:**
```
expense food 250 --unplanned -m 'stress eating after work'
income freelance 5000 --planned
```
Type `end` to finish a manual session.

### `fin summary`

```bash
fin summary passbook <name>                   # View the passbook with running balance
fin summary passbook <name> --sort asc        # Oldest entries first in passbook
fin summary passbook <name> --opening-balance 10000  # Override stored opening balance

The passbook reads precomputed income / expense / rotation totals from the log file when available.
```
### `fin reflect`

```bash
fin reflect debrief <name>       # Nightly debrief with reflection prompt
```

The debrief shows today's entries, a planned vs. unplanned breakdown, and a personalised reflection question based on your actual spending patterns — not a generic prompt.

---

## Spending Categories

| Category | Examples |
|---|---|
| `food` | Groceries, restaurants, meals |
| `clothing` | Apparel, accessories |
| `transport` | Fuel, public transit, rideshare |
| `entertainment` | Movies, games, hobbies |
| `utilities` | Electricity, water, internet |
| `health` | Medical, fitness, medications |
| `education` | Courses, books, learning |
| `shopping` | General retail |
| `travel` | Flights, hotels, vacations |
| `other` | Everything else |

Custom categories are also supported via the interactive prompt or manual mode.

---

## Data Storage

All logs are stored locally as newline-delimited JSON in the `json_files/` directory. Each user gets their own file: `json_files/<username>_logs.json`.

You can back up, inspect, or move these files freely — there's no database, no cloud sync, no account required.

---

## Example Workflow

```bash
$ fin users create "jaswanth"
Hello jaswanth.
You have been served with a JSON file json_files/ravi_logs.json.

$ fin logs add "jaswanth"
# → Interactive prompts: type, category, amount, planned?, memo

$ fin summary show "jaswanth" --month 4
# → Income / Expense / Balance table
# → Category breakdown

$ fin reflect debrief "jaswanth"
# → Today's entries table
# → Planned vs. unplanned breakdown
# → Personalised reflection prompt
# → Journal entry saved to log
```

---

## License

MIT — see [LICENSE](LICENSE) for details.

---

