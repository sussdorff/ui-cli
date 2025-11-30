"""Site management commands."""

import asyncio
from typing import Annotated

import typer

from ui_cli.client import APIError, UniFiClient
from ui_cli.output import OutputFormat, print_error, render_output

app = typer.Typer(help="Manage UniFi sites")

# Column definitions for sites table
SITE_COLUMNS = [
    ("siteId", "Site ID"),
    ("meta.name", "Name"),
    ("meta.desc", "Description"),
    ("hostId", "Host ID"),
    ("meta.timezone", "Timezone"),
    ("permission", "Permission"),
    ("isOwner", "Owner"),
]


@app.command("list")
def list_sites(
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
    """List all sites from hosts running UniFi Network application."""

    async def _list() -> list:
        client = UniFiClient()
        return await client.list_sites()

    try:
        sites = asyncio.run(_list())

        if verbose:
            typer.echo(f"Found {len(sites)} site(s)")

        render_output(
            data=sites,
            output_format=output,
            columns=SITE_COLUMNS,
            title="UniFi Sites",
            verbose=verbose,
        )
    except APIError as e:
        print_error(e.message)
        raise typer.Exit(1)
