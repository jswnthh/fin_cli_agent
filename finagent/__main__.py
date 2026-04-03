import typer

from finagent.commands import logs, reflect, summary, users

app = typer.Typer()

# Register sub-commands
app.add_typer(users.app, name="users")
app.add_typer(logs.app, name="logs")
app.add_typer(summary.app, name="summary")
app.add_typer(reflect.app, name="reflect")


if __name__ == "__main__":
    app()
