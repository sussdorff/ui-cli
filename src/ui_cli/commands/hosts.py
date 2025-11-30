"""Host management commands."""

import asyncio
from typing import Annotated

import typer

from ui_cli.client import APIError, UniFiClient
from ui_cli.output import OutputFormat, print_error, render_output

app = typer.Typer(help="Manage UniFi hosts (consoles and controllers)")

# Column definitions for hosts table
HOST_COLUMNS = [
    ("id", "ID"),
    ("reportedState.hostname", "Hostname"),
    ("type", "Type"),
    ("ipAddress", "IP Address"),
    ("reportedState.version", "Version"),
    ("owner", "Owner"),
    ("isBlocked", "Blocked"),
]


@app.command("list")
def list_hosts(
    output: Annotated[
        OutputFormat,
        typer.Option(
            "--output",
            "-o",
            help="Output format: table, json, or csv",
        ),
    ] = OutputFormat.TABLE,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Show detailed request/response information",
        ),
    ] = False,
) -> None:
    """List all hosts (consoles/controllers) associated with your account."""

    async def _list() -> list:
        client = UniFiClient()
        return await client.list_hosts()

    try:
        hosts = asyncio.run(_list())

        if verbose:
            typer.echo(f"Found {len(hosts)} host(s)")

        render_output(
            data=hosts,
            output_format=output,
            columns=HOST_COLUMNS,
            title="UniFi Hosts",
            verbose=verbose,
        )
    except APIError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("get")
def get_host(
    host_id: Annotated[
        str,
        typer.Argument(help="The unique identifier of the host"),
    ],
    output: Annotated[
        OutputFormat,
        typer.Option(
            "--output",
            "-o",
            help="Output format: table, json, or csv",
        ),
    ] = OutputFormat.TABLE,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Show detailed request/response information",
        ),
    ] = False,
) -> None:
    """Get detailed information about a specific host."""

    async def _get() -> dict:
        client = UniFiClient()
        return await client.get_host(host_id)

    try:
        host = asyncio.run(_get())

        if not host:
            print_error(f"Host '{host_id}' not found")
            raise typer.Exit(1)

        render_output(
            data=host,
            output_format=output,
            columns=HOST_COLUMNS,
            title=f"Host: {host_id}",
            verbose=verbose,
            is_single=True,
        )
    except APIError as e:
        print_error(e.message)
        raise typer.Exit(1)
