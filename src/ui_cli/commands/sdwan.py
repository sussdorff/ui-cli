"""SD-WAN configuration commands."""

import asyncio
from typing import Annotated

import typer

from ui_cli.client import APIError, UniFiClient
from ui_cli.output import OutputFormat, print_error, render_output

app = typer.Typer(help="Manage SD-WAN configurations")

# Column definitions for SD-WAN configs table
SDWAN_COLUMNS = [
    ("id", "ID"),
    ("name", "Name"),
    ("type", "Type"),
    ("variant", "Variant"),
]

# Column definitions for SD-WAN status table
SDWAN_STATUS_COLUMNS = [
    ("fingerprint", "Fingerprint"),
    ("status", "Status"),
    ("progress", "Progress"),
    ("updatedAt", "Updated At"),
]


@app.command("list")
def list_configs(
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
    """List all SD-WAN configurations."""

    async def _list() -> list:
        client = UniFiClient()
        return await client.list_sdwan_configs()

    try:
        configs = asyncio.run(_list())

        if verbose:
            typer.echo(f"Found {len(configs)} SD-WAN configuration(s)")

        render_output(
            data=configs,
            output_format=output,
            columns=SDWAN_COLUMNS,
            title="SD-WAN Configurations",
            verbose=verbose,
        )
    except APIError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("get")
def get_config(
    config_id: Annotated[
        str,
        typer.Argument(help="The unique identifier of the SD-WAN config"),
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
    """Get detailed information about a specific SD-WAN configuration."""

    async def _get() -> dict:
        client = UniFiClient()
        return await client.get_sdwan_config(config_id)

    try:
        config = asyncio.run(_get())

        if not config:
            print_error(f"SD-WAN config '{config_id}' not found")
            raise typer.Exit(1)

        render_output(
            data=config,
            output_format=output,
            columns=SDWAN_COLUMNS,
            title=f"SD-WAN Config: {config_id}",
            verbose=verbose,
            is_single=True,
        )
    except APIError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("status")
def get_status(
    config_id: Annotated[
        str,
        typer.Argument(help="The unique identifier of the SD-WAN config"),
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
    """Get deployment status of a specific SD-WAN configuration."""

    async def _get() -> dict:
        client = UniFiClient()
        return await client.get_sdwan_status(config_id)

    try:
        status = asyncio.run(_get())

        if not status:
            print_error(f"Status for SD-WAN config '{config_id}' not found")
            raise typer.Exit(1)

        render_output(
            data=status,
            output_format=output,
            columns=SDWAN_STATUS_COLUMNS,
            title=f"SD-WAN Status: {config_id}",
            verbose=verbose,
            is_single=True,
        )
    except APIError as e:
        print_error(e.message)
        raise typer.Exit(1)
