"""Local controller commands - ./ui local or ./ui lo."""

from typing import Annotated

import typer

from ui_cli.commands.local.utils import QUICK_TIMEOUT, get_timeout, run_with_spinner, set_timeout_override, spinner

# Re-export for convenience
__all__ = ["app", "get_timeout", "run_with_spinner", "spinner", "QUICK_TIMEOUT"]


app = typer.Typer(
    name="local",
    help="Local UniFi Controller commands (UDM, Cloud Key, self-hosted)",
    no_args_is_help=True,
)


@app.callback()
def local_callback(
    quick: Annotated[
        bool,
        typer.Option(
            "--quick",
            "-q",
            help="Use short timeout (5s) for quick connectivity checks",
        ),
    ] = False,
    timeout: Annotated[
        int | None,
        typer.Option(
            "--timeout",
            "-t",
            help="Request timeout in seconds (default: 15)",
        ),
    ] = None,
) -> None:
    """Local controller commands with optional timeout override."""
    if quick:
        set_timeout_override(QUICK_TIMEOUT)
    elif timeout is not None:
        set_timeout_override(timeout)


# Import subcommands after app is defined to avoid circular imports
from ui_cli.commands.local import apgroups, clients, config, devices, dpi, events, firewall, health, networks, portfwd, stats, vouchers, wlans

# Register subcommands
app.add_typer(apgroups.app, name="apgroups")
app.add_typer(clients.app, name="clients")
app.add_typer(config.app, name="config")
app.add_typer(devices.app, name="devices")
app.add_typer(dpi.app, name="dpi")
app.add_typer(events.app, name="events")
app.add_typer(firewall.app, name="firewall")
app.add_typer(health.app, name="health")
app.add_typer(networks.app, name="networks")
app.add_typer(portfwd.app, name="portfwd")
app.add_typer(stats.app, name="stats")
app.add_typer(vouchers.app, name="vouchers")
app.add_typer(wlans.app, name="wlans")
