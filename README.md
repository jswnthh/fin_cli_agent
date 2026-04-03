# FinAgent - Financial Expenditure Awareness Agent

A command-line tool to help you track and reflect on your spending habits. FinAgent provides an interactive way to log expenses, view summaries, and gain insights into your financial patterns.

## Features

- 📝 **Log Expenses**: Easily record your daily spending with categories
- 👥 **User Management**: Create and manage multiple user profiles
- 📊 **Spending Summaries**: View categorized spending reports
- 🤔 **Reflection**: Analyze your spending patterns and get insights

## Installation

### Requirements
- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. Clone or download the project
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the package in editable mode:
   ```bash
   pip install -e .
   ```

## Quick Start

### 1. Create a User Profile
```bash
fin users create "Your Name"
```
This creates a JSON file to store your spending logs.

### 2. Add an Expense
```bash
fin logs add "Your Name"
```
Interactively log an expense. You'll be prompted to select:
- **Category**: food, clothing, transport, entertainment, utilities, health, education, shopping, travel, or other
- **Amount**: How much you spent
- **Description**: What was the purchase for
- **Date**: When the purchase occurred

### 3. View All Log Files
```bash
fin logs add --list
```
Lists all available user log files.

### 4. View Spending Summary
```bash
fin summary
```
Get an overview of your spending by category.

### 5. Reflect on Spending
```bash
fin reflect
```
Analyze your spending patterns and get insights.

## Command Reference

### Users Command
```bash
fin users create <name>
```
Creates a new user profile and generates a JSON file for tracking expenses.

### Logs Command
```bash
fin logs add <name>                    # Add expense interactively
fin logs add <name> --manual           # Use manual text input
fin logs add --list                    # List all available log files
fin logs add <name> --help             # Show detailed help
```

### Summary Command
```bash
fin summary
```
Displays a breakdown of your total spending by category.

### Reflect Command
```bash
fin reflect
```
Provides analysis and insights about your spending habits.

### Help
```bash
fin --help                             # Show main help
fin <command> --help                   # Show command-specific help
```

## Spending Categories

The following categories are available for logging expenses:
- **food** - Groceries, restaurants, meals
- **clothing** - Apparel and accessories
- **transport** - Gas, public transit, rideshare
- **entertainment** - Movies, games, hobbies
- **utilities** - Electricity, water, internet
- **health** - Medical visits, fitness, medications
- **education** - Courses, books, learning materials
- **shopping** - General shopping and retail
- **travel** - Vacation, flights, hotels
- **other** - Miscellaneous expenses

## Data Storage

All expense logs are stored as JSON files in the `json_files/` directory. Each user has their own file named `<username>_logs.json`. You can view or backup these files directly.

## Example Workflow

```bash
# 1. Set up your profile
fin users create "Alice"

# 2. Log today's expenses
fin logs add "Alice"
# → Select "food", amount "15.50", description "Lunch", date "today"
# → Select "transport", amount "5.00", description "Bus fare", date "today"

# 3. View your spending
fin summary

# 4. Get insights
fin reflect
```

## License

MIT License - See LICENSE file for details

## Support

For issues or suggestions, please check the project repository or contact the maintainers.
<p align="center">
  <img src="https://github.com/user-attachments/assets/b627466f-dffe-423b-a6b8-4826b8ec7871" width="500" height="500" alt="image"/>
</p>

Most finance apps are built with the quiet assumption that you are a rational human being making intentional choices and at the end of every month some money is left, it's actually ADORABLE!. 
FinAgent is built for the rest of us... the ones where "some bullshit happens" is a legitimate budget line item. We just call it Miscellaneous Expenses to feel better about ourselves.

So yeah, FinAgent is basically my gift to everyone who understands that sometimes money isn’t just money—it’s survival.
- That ₹30 snack at 2 AM? — Life-saving.
- Buying a random book at 3 PM because it “might change your life”? — literally literary therapy.
- Booking a last-minute weekend trip just to escape your own thoughts? — Necessary existential escape.

A boring little ledger? Yeah, it will never get it. It just sits there judging silently, while you’re out there spending for your soul. However, the School of Life has a whole theory about it: 
Emotional spending is basically your brain going "I am in pain and I cannot process this, but that jacket is 40% off" and calling it a solution. It is not a solution. The jacket knows. You know. Everyone knows. And yet. It's not stupidity. It's not even weakness. It's just your psyche doing a really terrible job at being a therapist — prescribing retail as medicine for boredom, stress, sadness, and every other feeling you didn't want to sit with.

The fix? NGL, it's not more shopping or eating. It's the deeply unfun work of asking yourself "what am I actually feeling right now" before you checkout... and then feeling it. Like an adult, ufffff... The good news: **awareness is the first step.**

I developed this app for the exact reason, to bring awareness. Oh, and just so you know, FinAgent isn’t some pretty app with buttons and colors. Nope. It lives in the command line. That’s right, the terminal—the place where you stare at text and confront your own terrible choices.

Using Python’s CLI, I can:

Type commands like a wizard summoning my own money demons.
Add expenses on the fly, list past disasters, or check summaries without any distractions.
Watch my “Miscellaneous Expenses” grow in real time while knowing the Oreos I bought aren’t hiding anywhere.

Python quietly does all the heavy lifting—reading and writing JSON files, summing up categories, and keeping track of the chaos I call a budget. No flashy charts, no GUI holding my hand. Just me, the terminal, and the courage to type something like:


