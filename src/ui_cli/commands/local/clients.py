"""Client commands for local controller."""

import asyncio
from typing import Annotated

import typer

from ui_cli.local_client import (
    LocalAPIError,
    LocalAuthenticationError,
    LocalConnectionError,
    UniFiLocalClient,
)
from ui_cli.output import OutputFormat, console, output_count_table, output_csv, output_json, output_table

app = typer.Typer(help="Manage connected clients")


# Column definitions for client output: (key, header)
CLIENT_COLUMNS = [
    ("name", "Name"),
    ("mac", "MAC"),
    ("ip", "IP"),
    ("network", "Network"),
    ("type", "Type"),
    ("signal", "Signal"),
    ("satisfaction", "Experience"),
]

CLIENT_COLUMNS_VERBOSE = [
    ("name", "Name"),
    ("mac", "MAC"),
    ("ip", "IP"),
    ("network", "Network"),
    ("type", "Type"),
    ("oui", "Vendor"),
    ("signal", "Signal"),
    ("satisfaction", "Experience"),
    ("tx_rate", "TX Rate"),
    ("rx_rate", "RX Rate"),
    ("uptime", "Uptime"),
]


def format_client(client: dict, verbose: bool = False) -> dict:
    """Format raw client data for display."""
    # Determine connection type
    is_wired = client.get("is_wired", False)
    conn_type = "Wired" if is_wired else "Wireless"

    # Get network name
    network = client.get("network", client.get("essid", ""))

    # Format signal strength (wireless only)
    signal = ""
    if not is_wired:
        rssi = client.get("rssi")
        if rssi is not None:
            signal = f"{rssi} dBm"

    # Format experience/satisfaction score
    satisfaction = client.get("satisfaction")
    if satisfaction is not None:
        satisfaction = f"{satisfaction}%"
    else:
        satisfaction = ""

    # Format uptime
    uptime_seconds = client.get("uptime", 0)
    if uptime_seconds:
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        uptime = f"{int(hours)}h {int(minutes)}m"
    else:
        uptime = ""

    # Format rates (in Mbps)
    tx_rate = client.get("tx_rate", 0)
    rx_rate = client.get("rx_rate", 0)
    tx_rate_str = f"{tx_rate / 1000:.0f} Mbps" if tx_rate else ""
    rx_rate_str = f"{rx_rate / 1000:.0f} Mbps" if rx_rate else ""

    result = {
        "name": client.get("name") or client.get("hostname") or "(unknown)",
        "mac": client.get("mac", "").upper(),
        "ip": client.get("ip", ""),
        "network": network,
        "type": conn_type,
        "oui": client.get("oui", ""),
        "signal": signal,
        "satisfaction": satisfaction,
        "tx_rate": tx_rate_str,
        "rx_rate": rx_rate_str,
        "uptime": uptime,
    }

    return result


def handle_error(e: Exception) -> None:
    """Handle and display API errors."""
    if isinstance(e, LocalAuthenticationError):
        console.print(f"[red]Authentication error:[/red] {e.message}")
    elif isinstance(e, LocalConnectionError):
        console.print(f"[red]Connection error:[/red] {e.message}")
    elif isinstance(e, LocalAPIError):
        console.print(f"[red]API error:[/red] {e.message}")
    else:
        console.print(f"[red]Error:[/red] {e}")
    raise typer.Exit(1)


@app.command("list")
def list_clients(
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
    network: Annotated[
        str | None,
        typer.Option("--network", "-n", help="Filter by network/SSID"),
    ] = None,
    wired: Annotated[
        bool,
        typer.Option("--wired", "-w", help="Show only wired clients"),
    ] = False,
    wireless: Annotated[
        bool,
        typer.Option("--wireless", "-W", help="Show only wireless clients"),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Show additional details"),
    ] = False,
) -> None:
    """List active (connected) clients."""
    try:
        client = UniFiLocalClient()
        clients = asyncio.run(client.list_clients())
    except Exception as e:
        handle_error(e)
        return

    # Apply filters
    if wired:
        clients = [c for c in clients if c.get("is_wired", False)]
    elif wireless:
        clients = [c for c in clients if not c.get("is_wired", False)]

    if network:
        network_lower = network.lower()
        clients = [
            c
            for c in clients
            if network_lower in (c.get("network", "") or c.get("essid", "")).lower()
        ]

    # Format for output
    formatted = [format_client(c, verbose=verbose) for c in clients]

    columns = CLIENT_COLUMNS_VERBOSE if verbose else CLIENT_COLUMNS

    if output == OutputFormat.JSON:
        output_json(formatted, verbose=verbose)
    elif output == OutputFormat.CSV:
        output_csv(formatted, columns)
    else:
        output_table(formatted, columns, title="Connected Clients")


@app.command("all")
def list_all_clients(
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Show additional details"),
    ] = False,
) -> None:
    """List all known clients (including offline)."""
    try:
        client = UniFiLocalClient()
        clients = asyncio.run(client.list_all_clients())
    except Exception as e:
        handle_error(e)
        return

    # Format for output
    formatted = [format_client(c, verbose=verbose) for c in clients]

    columns = CLIENT_COLUMNS_VERBOSE if verbose else CLIENT_COLUMNS

    if output == OutputFormat.JSON:
        output_json(formatted, verbose=verbose)
    elif output == OutputFormat.CSV:
        output_csv(formatted, columns)
    else:
        output_table(formatted, columns, title="All Known Clients")


@app.command("get")
def get_client(
    mac: Annotated[str, typer.Argument(help="Client MAC address")],
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
) -> None:
    """Get details for a specific client."""
    try:
        api_client = UniFiLocalClient()
        client_data = asyncio.run(api_client.get_client(mac))
    except Exception as e:
        handle_error(e)
        return

    if not client_data:
        console.print(f"[yellow]Client not found:[/yellow] {mac}")
        raise typer.Exit(1)

    if output == OutputFormat.JSON:
        output_json(client_data)
    else:
        # Display as key-value pairs
        formatted = format_client(client_data, verbose=True)
        console.print()
        console.print(f"[bold]Client Details: {mac.upper()}[/bold]")
        console.print("─" * 40)
        for key, value in formatted.items():
            if value:
                console.print(f"  [dim]{key}:[/dim] {value}")
        console.print()


@app.command("block")
def block_client(
    mac: Annotated[str, typer.Argument(help="Client MAC address to block")],
) -> None:
    """Block a client from connecting."""
    try:
        client = UniFiLocalClient()
        success = asyncio.run(client.block_client(mac))
    except Exception as e:
        handle_error(e)
        return

    if success:
        console.print(f"[green]Blocked client:[/green] {mac.upper()}")
    else:
        console.print(f"[red]Failed to block client:[/red] {mac.upper()}")
        raise typer.Exit(1)


@app.command("unblock")
def unblock_client(
    mac: Annotated[str, typer.Argument(help="Client MAC address to unblock")],
) -> None:
    """Unblock a previously blocked client."""
    try:
        client = UniFiLocalClient()
        success = asyncio.run(client.unblock_client(mac))
    except Exception as e:
        handle_error(e)
        return

    if success:
        console.print(f"[green]Unblocked client:[/green] {mac.upper()}")
    else:
        console.print(f"[red]Failed to unblock client:[/red] {mac.upper()}")
        raise typer.Exit(1)


@app.command("kick")
def kick_client(
    mac: Annotated[str, typer.Argument(help="Client MAC address to kick")],
) -> None:
    """Kick (disconnect) a client, forcing reconnection."""
    try:
        client = UniFiLocalClient()
        success = asyncio.run(client.kick_client(mac))
    except Exception as e:
        handle_error(e)
        return

    if success:
        console.print(f"[green]Kicked client:[/green] {mac.upper()}")
    else:
        console.print(f"[red]Failed to kick client:[/red] {mac.upper()}")
        raise typer.Exit(1)


class CountBy(str, typer.Typer):
    """Grouping options for count command."""

    TYPE = "type"
    NETWORK = "network"
    VENDOR = "vendor"
    AP = "ap"
    EXPERIENCE = "experience"


def get_experience_category(satisfaction: int | None) -> str:
    """Categorize experience score."""
    if satisfaction is None:
        return "Unknown"
    if satisfaction >= 80:
        return "Good (80%+)"
    if satisfaction >= 50:
        return "Fair (50-79%)"
    return "Poor (<50%)"


@app.command("count")
def count_clients(
    by: Annotated[
        str,
        typer.Option(
            "--by",
            "-b",
            help="Group by: type, network, vendor, ap, experience",
        ),
    ] = "type",
    include_offline: Annotated[
        bool,
        typer.Option(
            "--include-offline",
            "-a",
            help="Include offline clients in count",
        ),
    ] = False,
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
) -> None:
    """Count clients grouped by category (online only by default)."""
    try:
        api_client = UniFiLocalClient()
        if include_offline:
            clients = asyncio.run(api_client.list_all_clients())
        else:
            clients = asyncio.run(api_client.list_clients())
    except Exception as e:
        handle_error(e)
        return

    # Count by the specified grouping
    counts: dict[str, int] = {}
    by_lower = by.lower()

    for client in clients:
        if by_lower == "type":
            key = "Wired" if client.get("is_wired", False) else "Wireless"
        elif by_lower == "network":
            key = client.get("network") or client.get("essid") or "(none)"
        elif by_lower == "vendor":
            key = client.get("oui") or "(unknown)"
        elif by_lower == "ap":
            # Get AP name - wireless clients have ap_mac and last_uplink_name
            if client.get("is_wired", False):
                key = "(wired)"
            else:
                key = client.get("last_uplink_name") or client.get("ap_mac", "(unknown)")
        elif by_lower == "experience":
            satisfaction = client.get("satisfaction")
            key = get_experience_category(satisfaction)
        else:
            console.print(f"[red]Invalid grouping:[/red] {by}")
            console.print("Valid options: type, network, vendor, ap, experience")
            raise typer.Exit(1)

        counts[key] = counts.get(key, 0) + 1

    # Determine title and headers based on grouping
    titles = {
        "type": ("Client Count by Type", "Type"),
        "network": ("Client Count by Network", "Network"),
        "vendor": ("Client Count by Vendor", "Vendor"),
        "ap": ("Client Count by Access Point", "Access Point"),
        "experience": ("Client Count by Experience", "Experience"),
    }
    title, group_header = titles.get(by_lower, ("Client Count", "Group"))

    if output == OutputFormat.JSON:
        output_json({"counts": counts, "total": sum(counts.values())})
    elif output == OutputFormat.CSV:
        # Output as CSV
        rows = [{"group": k, "count": v} for k, v in sorted(counts.items())]
        rows.append({"group": "Total", "count": sum(counts.values())})
        output_csv(rows, [("group", group_header), ("count", "Count")])
    else:
        output_count_table(counts, group_header=group_header, title=title)
