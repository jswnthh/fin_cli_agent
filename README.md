# FinAgent

Financial Expenditure Awareness Agent - Track and reflect on your spending habits.

## Installation

```bash
pip install finagent
```

Or for development:
```bash
git clone https://github.com/yourusername/finagent.git
cd finagent
pip install -e .
```

## Usage

### Create a user
```bash
finagent users create "YourName"
```

### Log expenses
```bash
finagent logs add YourName
```
Choose from interactive prompts or use `--manual` for text input.

### View summaries
```bash
finagent summary show YourName
```

### Daily reflection
```bash
finagent reflect debrief YourName
```

## Features

- Interactive logging with dropdowns for categories
- Manual text input option
- Rich summaries and tables
- Daily reflection prompts
- JSONL-based storage for performance

## Development

- Built with Typer, Rich, and Questionary
- CLI app with subcommands
- Python 3.8+

## License

MIT