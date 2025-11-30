"""Status command - check API connectivity and authentication."""

import asyncio
import time
from typing import Annotated

import httpx
import typer

from ui_cli import __version__
from ui_cli.config import settings
from ui_cli.output import OutputFormat, console, output_json


app = typer.Typer(help="Check API connectivity and authentication status")


def mask_api_key(key: str, show_full: bool = False) -> str:
    """Mask API key for display."""
    if not key:
        return "(not configured)"
    if show_full:
        return key
    if len(key) <= 8:
        return "****"
    return f"****...{key[-6:]}"


async def check_site_manager_api(verbose: bool = False) -> dict:
    """Check Site Manager API connectivity and auth."""
    result = {
        "name": "Site Manager API",
        "url": settings.api_url,
        "api_key_configured": bool(settings.api_key),
        "api_key_display": mask_api_key(settings.api_key, show_full=verbose),
        "connection": None,
        "connection_time_ms": None,
        "authentication": None,
        "error": None,
        "hosts_count": None,
        "sites_count": None,
        "devices_count": None,
    }

    if not settings.api_key:
        result["error"] = "Set UNIFI_API_KEY in .env file"
        return result

    headers = {
        "X-API-Key": settings.api_key,
        "Accept": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Test connection and auth with hosts endpoint
            start = time.perf_counter()
            response = await client.get(
                f"{settings.api_url}/hosts",
                headers=headers,
            )
            elapsed_ms = (time.perf_counter() - start) * 1000

            result["connection"] = "OK"
            result["connection_time_ms"] = round(elapsed_ms, 1)

            if response.status_code == 200:
                result["authentication"] = "Valid"
                data = response.json()
                hosts = data.get("data", [])
                result["hosts_count"] = len(hosts)

                # Get sites count
                sites_resp = await client.get(
                    f"{settings.api_url}/sites",
                    headers=headers,
                )
                if sites_resp.status_code == 200:
                    sites_data = sites_resp.json()
                    result["sites_count"] = len(sites_data.get("data", []))

                # Get devices count
                devices_resp = await client.get(
                    f"{settings.api_url}/devices",
                    headers=headers,
                )
                if devices_resp.status_code == 200:
                    devices_data = devices_resp.json()
                    # Flatten devices from host groups
                    total_devices = 0
                    for host_group in devices_data.get("data", []):
                        total_devices += len(host_group.get("devices", []))
                    result["devices_count"] = total_devices

            elif response.status_code == 401:
                result["authentication"] = "FAILED"
                result["error"] = "Invalid API key"
            elif response.status_code == 429:
                result["authentication"] = "Valid"
                result["error"] = "Rate limit exceeded"
            else:
                result["authentication"] = "FAILED"
                result["error"] = f"HTTP {response.status_code}"

    except httpx.ConnectError:
        result["connection"] = "FAILED"
        result["error"] = "Could not connect to api.ui.com"
    except httpx.TimeoutException:
        result["connection"] = "FAILED"
        result["error"] = "Connection timeout"
    except Exception as e:
        result["connection"] = "FAILED"
        result["error"] = str(e)

    return result


def print_status_table(status: dict) -> None:
    """Print status in formatted table."""
    from rich.panel import Panel
    from rich.table import Table

    console.print()
    console.print(f"[bold cyan]UniFi CLI v{__version__}[/bold cyan]")
    console.print("─" * 40)
    console.print()

    # Site Manager API section
    console.print("[bold]Site Manager API[/bold] (api.ui.com)")

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="dim")
    table.add_column("Value")

    table.add_row("URL:", status["url"])

    # API Key status
    if status["api_key_configured"]:
        table.add_row("API Key:", f"[green]{status['api_key_display']}[/green] (configured)")
    else:
        table.add_row("API Key:", f"[red]{status['api_key_display']}[/red]")

    # Connection status
    if status["connection"] == "OK":
        table.add_row(
            "Connection:",
            f"[green]OK[/green] ({status['connection_time_ms']}ms)"
        )
    elif status["connection"] == "FAILED":
        table.add_row("Connection:", f"[red]FAILED[/red]")
    else:
        table.add_row("Connection:", "[dim]-[/dim]")

    # Authentication status
    if status["authentication"] == "Valid":
        table.add_row("Authentication:", "[green]Valid[/green]")
    elif status["authentication"] == "FAILED":
        table.add_row("Authentication:", f"[red]FAILED[/red]")
    else:
        table.add_row("Authentication:", "[dim]-[/dim]")

    console.print(table)

    # Error message
    if status["error"]:
        console.print()
        console.print(f"  [red]Error:[/red] {status['error']}")

    # Account info (if authenticated)
    if status["authentication"] == "Valid" and status["hosts_count"] is not None:
        console.print()
        console.print("[bold]Account Summary:[/bold]")

        info_table = Table(show_header=False, box=None, padding=(0, 2))
        info_table.add_column("Key", style="dim")
        info_table.add_column("Value")

        info_table.add_row("Hosts:", str(status["hosts_count"]))
        info_table.add_row("Sites:", str(status["sites_count"]))
        info_table.add_row("Devices:", str(status["devices_count"]))

        console.print(info_table)

    console.print()


@app.callback(invoke_without_command=True)
def status(
    ctx: typer.Context,
    output: Annotated[
        OutputFormat,
        typer.Option(
            "--output",
            "-o",
            help="Output format: table or json",
        ),
    ] = OutputFormat.TABLE,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Show detailed information including full API key",
        ),
    ] = False,
) -> None:
    """Check API connectivity and authentication status."""

    # Run async check
    result = asyncio.run(check_site_manager_api(verbose=verbose))

    if output == OutputFormat.JSON:
        output_json(result, verbose=verbose)
    else:
        print_status_table(result)

    # Exit with error code if not authenticated
    if result["authentication"] != "Valid":
        raise typer.Exit(1)
