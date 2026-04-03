import json
import os

import typer

app = typer.Typer()


@app.command()
def create(name: str):
    print(f"Hello {name}.")

    # Directory
    folder = "json_files"

    # Create folder if it doesn't exist
    if not os.path.exists(folder):
        os.makedirs(folder)

    # Clean name (optional but recommended)
    safe_name = name.lower().replace(" ", "_")

    # File path
    file_path = os.path.join(folder, f"{safe_name}_logs.json")

    # Check if file already exists
    if os.path.exists(file_path):
        print(f"File already exists: {file_path}")
        return

    # Create empty JSON file
    with open(file_path, "w") as f:
        json.dump([], f, indent=4)

    print(f"You have been served with a JSON file {file_path}.")
    print("This sheet + daily logs will help you identify spending patterns.")
