"""Version command - display CLI version."""

import typer

from ui_cli import __version__

app = typer.Typer(help="Display CLI version")


@app.callback(invoke_without_command=True)
def version() -> None:
    """Display the CLI version."""
    typer.echo(f"ui-cli version {__version__}")
