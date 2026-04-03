import json
from pathlib import Path

DB_DIR = Path("db")
DB_DIR.mkdir(exist_ok=True)


def get_file(name: str) -> Path:
    return DB_DIR / f"{name}.json"


def load_data(name: str):
    file = get_file(name)
    if not file.exists():
        return []
    with open(file, "r") as f:
        return json.load(f)


def save_data(name: str, data):
    file = get_file(name)
    with open(file, "w") as f:
        json.dump(data, f, indent=4)
