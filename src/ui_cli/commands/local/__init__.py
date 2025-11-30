"""Local controller commands - ./ui local or ./ui lo."""

import typer

from ui_cli.commands.local import clients

app = typer.Typer(
    name="local",
    help="Local UniFi Controller commands (UDM, Cloud Key, self-hosted)",
    no_args_is_help=True,
)

# Register subcommands
app.add_typer(clients.app, name="clients")
