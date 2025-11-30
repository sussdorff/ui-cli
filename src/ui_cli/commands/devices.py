"""Device management commands."""

import asyncio
from collections import Counter
from enum import Enum
from typing import Annotated

import typer

from ui_cli.client import APIError, UniFiClient
from ui_cli.output import (
    OutputFormat,
    output_count_table,
    output_csv,
    output_json,
    print_error,
    render_output,
)

app = typer.Typer(help="Manage UniFi devices")

# Column definitions for devices table
DEVICE_COLUMNS = [
    ("id", "ID"),
    ("name", "Name"),
    ("model", "Model"),
    ("ip", "IP Address"),
    ("mac", "MAC"),
    ("productLine", "Product Line"),
    ("status", "Status"),
    ("version", "Version"),
    ("hostName", "Host"),
]


class GroupBy(str, Enum):
    """Device grouping options."""

    HOST = "host"
    MODEL = "model"
    STATUS = "status"
    PRODUCT_LINE = "product-line"


@app.command("list")
def list_devices(
    host: Annotated[
        str | None,
        typer.Option(
            "--host",
            "-H",
            help="Filter devices by host ID",
        ),
    ] = None,
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
    """List all UniFi devices managed by your hosts."""

    async def _list() -> list:
        client = UniFiClient()
        host_ids = [host] if host else None
        return await client.list_devices(host_ids=host_ids)

    try:
        devices = asyncio.run(_list())

        if verbose:
            typer.echo(f"Found {len(devices)} device(s)")

        render_output(
            data=devices,
            output_format=output,
            columns=DEVICE_COLUMNS,
            title="UniFi Devices",
            verbose=verbose,
        )
    except APIError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("count")
def count_devices(
    by: Annotated[
        GroupBy | None,
        typer.Option(
            "--by",
            "-b",
            help="Group count by: host, model, status, or product-line",
        ),
    ] = None,
    host: Annotated[
        str | None,
        typer.Option(
            "--host",
            "-H",
            help="Filter devices by host ID",
        ),
    ] = None,
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
    """Count devices with optional grouping."""

    async def _list() -> list:
        client = UniFiClient()
        host_ids = [host] if host else None
        return await client.list_devices(host_ids=host_ids)

    try:
        devices = asyncio.run(_list())

        if by is None:
            # Simple total count
            count_data = {"total": len(devices)}

            if output == OutputFormat.JSON:
                output_json(count_data, verbose=verbose)
            elif output == OutputFormat.CSV:
                output_csv([count_data])
            else:
                typer.echo(f"Total devices: {len(devices)}")
            return

        # Group by specified field
        key_map = {
            GroupBy.HOST: ("hostName", "Host"),
            GroupBy.MODEL: ("model", "Model"),
            GroupBy.STATUS: ("status", "Status"),
            GroupBy.PRODUCT_LINE: ("productLine", "Product Line"),
        }

        field_key, header = key_map[by]
        counts: Counter = Counter()

        for device in devices:
            value = device.get(field_key, "Unknown") or "Unknown"
            counts[value] += 1

        if output == OutputFormat.JSON:
            output_json(dict(counts), verbose=verbose)
        elif output == OutputFormat.CSV:
            csv_data = [{header: k, "Count": v} for k, v in counts.items()]
            output_csv(csv_data)
        else:
            output_count_table(
                counts=dict(counts),
                group_header=header,
                count_header="Count",
                title=f"Device Count by {header}",
            )

        if verbose:
            typer.echo(f"Total: {sum(counts.values())} device(s)")

    except APIError as e:
        print_error(e.message)
        raise typer.Exit(1)
