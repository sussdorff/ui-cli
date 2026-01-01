"""Client commands for local controller."""

import asyncio
from typing import Annotated

import typer

from ui_cli.commands.local.utils import run_with_spinner
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
    ("oui", "Vendor"),
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


def is_mac_address(value: str) -> bool:
    """Check if a string looks like a MAC address."""
    # MAC formats: AA:BB:CC:DD:EE:FF or AA-BB-CC-DD-EE-FF or AABBCCDDEEFF
    import re
    mac_patterns = [
        r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$',  # AA:BB:CC:DD:EE:FF
        r'^([0-9A-Fa-f]{2}-){5}[0-9A-Fa-f]{2}$',  # AA-BB-CC-DD-EE-FF
        r'^[0-9A-Fa-f]{12}$',                       # AABBCCDDEEFF
    ]
    return any(re.match(pattern, value) for pattern in mac_patterns)


async def resolve_client_identifier(
    api_client: UniFiLocalClient,
    identifier: str,
) -> tuple[str | None, str | None]:
    """Resolve a client name or MAC to (mac, name).

    Returns (mac, name) if found, (None, None) if not found.
    If identifier is a MAC, returns it directly with the name if found.
    If identifier is a name, searches for matching client.
    """
    if is_mac_address(identifier):
        # It's a MAC address - try to get the client to find its name
        client_data = await api_client.get_client(identifier)
        if client_data:
            name = client_data.get("name") or client_data.get("hostname") or identifier
            return identifier.lower().replace("-", ":"), name
        return identifier.lower().replace("-", ":"), None

    # It's a name - search for it in all clients
    clients = await api_client.list_all_clients()
    identifier_lower = identifier.lower()

    for client in clients:
        name = client.get("name") or client.get("hostname") or ""
        if name.lower() == identifier_lower:
            return client.get("mac", "").lower(), name

    # Try partial match if exact match not found
    matches = []
    for client in clients:
        name = client.get("name") or client.get("hostname") or ""
        if identifier_lower in name.lower():
            matches.append((client.get("mac", "").lower(), name))

    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        console.print(f"[yellow]Multiple clients match '{identifier}':[/yellow]")
        for mac, name in matches:
            console.print(f"  - {name} ({mac.upper()})")
        return None, None

    return None, None


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
    group: Annotated[
        str | None,
        typer.Option("--group", "-g", help="Filter by client group"),
    ] = None,
) -> None:
    """List active (connected) clients."""
    async def _list():
        client = UniFiLocalClient()
        return await client.list_clients()

    try:
        clients = run_with_spinner(_list(), "Fetching clients...")
    except Exception as e:
        handle_error(e)
        return

    # Apply group filter
    if group:
        from ui_cli.groups import GroupManager
        gm = GroupManager()
        result = gm.get_group(group)
        if not result:
            console.print(f"[red]Error:[/red] Group '{group}' not found")
            raise typer.Exit(1)

        _, grp = result
        if grp.type == "static":
            member_macs = {m.mac.upper() for m in grp.members or []}
            clients = [c for c in clients if c.get("mac", "").upper() in member_macs]
        else:
            # Auto group - evaluate rules
            clients = gm.evaluate_auto_group(group, clients)

    # Apply other filters
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

    title = f"Clients in '{group}'" if group else "Connected Clients"

    if output == OutputFormat.JSON:
        output_json(formatted, verbose=verbose)
    elif output == OutputFormat.CSV:
        output_csv(formatted, columns)
    else:
        output_table(formatted, columns, title=title)


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
    async def _list():
        client = UniFiLocalClient()
        return await client.list_all_clients()

    try:
        clients = run_with_spinner(_list(), "Fetching all clients...")
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
    identifier: Annotated[
        str | None,
        typer.Argument(help="Client MAC address or name"),
    ] = None,
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
) -> None:
    """Get details for a specific client.

    Examples:
        ./ui lo clients get my-iPhone
        ./ui lo clients get AA:BB:CC:DD:EE:FF
    """
    if not identifier:
        console.print("[yellow]Usage:[/yellow] ./ui lo clients get <name or MAC>")
        console.print()
        console.print("Examples:")
        console.print("  ./ui lo clients get my-iPhone")
        console.print("  ./ui lo clients get AA:BB:CC:DD:EE:FF")
        raise typer.Exit(1)
    async def _get():
        api_client = UniFiLocalClient()
        mac, name = await resolve_client_identifier(api_client, identifier)
        if not mac:
            return None, None
        client_data = await api_client.get_client(mac)
        return client_data, name

    try:
        client_data, resolved_name = run_with_spinner(_get(), "Finding client...")
    except Exception as e:
        handle_error(e)
        return

    if not client_data:
        console.print(f"[yellow]Client not found:[/yellow] {identifier}")
        raise typer.Exit(1)

    if output == OutputFormat.JSON:
        output_json(client_data)
    else:
        # Display as key-value pairs
        formatted = format_client(client_data, verbose=True)
        display_name = resolved_name or formatted.get("name", identifier)
        console.print()
        console.print(f"[bold]Client Details: {display_name}[/bold]")
        console.print("─" * 40)
        for key, value in formatted.items():
            if value:
                console.print(f"  [dim]{key}:[/dim] {value}")
        console.print()


@app.command("set-ip")
def set_fixed_ip(
    identifier: Annotated[
        str,
        typer.Argument(help="Client MAC address or name"),
    ],
    ip: Annotated[
        str,
        typer.Argument(help="Fixed IP address to assign"),
    ],
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation prompt"),
    ] = False,
    no_kick: Annotated[
        bool,
        typer.Option("--no-kick", help="Don't kick client to force DHCP renewal"),
    ] = False,
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
) -> None:
    """Set a fixed IP address for a client (DHCP reservation).

    By default, kicks the client after setting the IP to force immediate
    DHCP renewal. Use --no-kick to skip this.

    Examples:
        ui lo clients set-ip "Shelly Keller" 192.168.30.21
        ui lo clients set-ip AA:BB:CC:DD:EE:FF 192.168.30.21 -y
        ui lo clients set-ip "Device" 192.168.1.100 --no-kick
    """
    import re

    # Validate IP address format
    ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if not re.match(ip_pattern, ip):
        console.print(f"[red]Invalid IP address:[/red] {ip}")
        raise typer.Exit(1)

    # Validate IP octets
    octets = [int(x) for x in ip.split('.')]
    if any(o < 0 or o > 255 for o in octets):
        console.print(f"[red]Invalid IP address:[/red] {ip}")
        raise typer.Exit(1)

    async def _resolve_and_get_id():
        api_client = UniFiLocalClient()
        mac, name = await resolve_client_identifier(api_client, identifier)
        if not mac:
            return None, None, None, api_client

        # Get user record to find the _id
        # Need to search all users for this MAC
        response = await api_client.get("/rest/user")
        users = response.get("data", [])
        user_id = None
        for user in users:
            if user.get("mac", "").lower() == mac.lower():
                user_id = user.get("_id")
                break

        return mac, name, user_id, api_client

    try:
        mac, name, user_id, api_client = run_with_spinner(
            _resolve_and_get_id(), "Finding client..."
        )
    except Exception as e:
        handle_error(e)
        return

    if not mac:
        console.print(f"[yellow]Client not found:[/yellow] {identifier}")
        raise typer.Exit(1)

    if not user_id:
        console.print(f"[red]Error:[/red] Could not find user record for {identifier}")
        console.print("[dim]The client may not have connected recently enough to have a user record.[/dim]")
        raise typer.Exit(1)

    display = f"{name} ({mac.upper()})" if name else mac.upper()

    # Confirm action
    if not yes:
        if not typer.confirm(f"Set fixed IP {ip} for {display}?"):
            console.print("[dim]Cancelled[/dim]")
            raise typer.Exit(0)

    # Execute action
    async def _set_ip():
        return await api_client.set_client_fixed_ip(user_id, fixed_ip=ip)

    try:
        success = run_with_spinner(_set_ip(), "Setting fixed IP...")
    except Exception as e:
        handle_error(e)
        return

    if not success:
        if output == OutputFormat.JSON:
            output_json({"success": False, "name": name, "mac": mac, "fixed_ip": ip, "error": "API call failed"})
        else:
            console.print(f"[red]Failed to set fixed IP for:[/red] {display}")
        raise typer.Exit(1)

    if output != OutputFormat.JSON:
        console.print(f"[green]Set fixed IP:[/green] {display} -> {ip}")

    # Kick client to force DHCP renewal (unless --no-kick)
    kicked = False
    if not no_kick:
        async def _kick():
            return await api_client.kick_client(mac)

        try:
            kicked = run_with_spinner(_kick(), "Kicking client for DHCP renewal...")
            if output != OutputFormat.JSON:
                if kicked:
                    console.print(f"[green]Kicked client:[/green] {display} (will reconnect with new IP)")
                else:
                    console.print(f"[yellow]Could not kick client[/yellow] - may need manual reconnect")
        except Exception:
            if output != OutputFormat.JSON:
                console.print(f"[yellow]Could not kick client[/yellow] - may need manual reconnect")

    if output == OutputFormat.JSON:
        output_json({"success": True, "name": name, "mac": mac, "fixed_ip": ip, "kicked": kicked})


def format_bytes(bytes_val: int) -> str:
    """Format bytes to human-readable string."""
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.1f} KB"
    elif bytes_val < 1024 * 1024 * 1024:
        return f"{bytes_val / (1024 * 1024):.1f} MB"
    else:
        return f"{bytes_val / (1024 * 1024 * 1024):.2f} GB"


def format_uptime(seconds: int) -> str:
    """Format uptime seconds to human-readable string."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}m"
    elif seconds < 86400:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"
    else:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        return f"{days}d {hours}h"


@app.command("status")
def client_status(
    identifier: Annotated[
        str | None,
        typer.Argument(help="Client MAC address or name"),
    ] = None,
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
) -> None:
    """Show client connection and block status.

    Examples:
        ./ui lo clients status my-iPhone
        ./ui lo clients status AA:BB:CC:DD:EE:FF
    """
    if not identifier:
        console.print("[yellow]Usage:[/yellow] ./ui lo clients status <name or MAC>")
        console.print()
        console.print("Examples:")
        console.print("  ./ui lo clients status my-iPhone")
        console.print("  ./ui lo clients status AA:BB:CC:DD:EE:FF")
        raise typer.Exit(1)

    async def _get_status():
        api_client = UniFiLocalClient()
        mac, name = await resolve_client_identifier(api_client, identifier)
        if not mac:
            return None, None, None, None
        # Get from all clients (includes offline) for block status
        all_clients = await api_client.list_all_clients()
        client_info = None
        for c in all_clients:
            if c.get("mac", "").lower() == mac.lower():
                client_info = c
                break
        # Also check active clients for online status and live data
        active_clients = await api_client.list_clients()
        active_info = None
        for c in active_clients:
            if c.get("mac", "").lower() == mac.lower():
                active_info = c
                break
        is_online = active_info is not None
        return client_info, active_info, name, is_online

    try:
        client_info, active_info, resolved_name, is_online = run_with_spinner(_get_status(), "Checking status...")
    except Exception as e:
        handle_error(e)
        return

    if not client_info:
        console.print(f"[yellow]Client not found:[/yellow] {identifier}")
        raise typer.Exit(1)

    # Build status info - use active_info for live data if online
    info = active_info if active_info else client_info

    name = resolved_name or info.get("name") or info.get("hostname") or "(unknown)"
    mac = info.get("mac", "").upper()
    is_blocked = client_info.get("blocked", False)
    is_guest = info.get("is_guest", False)
    ip = info.get("ip") or info.get("last_ip") or ""
    is_wired = info.get("is_wired", False)
    conn_type = "Wired" if is_wired else "Wireless"

    # Network and AP info
    network = info.get("network") or info.get("essid") or info.get("last_connection_network_name") or ""
    ap_name = info.get("last_uplink_name") or ""

    # Wireless-specific info
    signal = info.get("signal")  # dBm
    rssi = info.get("rssi")
    channel = info.get("channel")
    radio = info.get("radio_proto", "")  # e.g., "ac", "ax"

    # Connection quality
    satisfaction = info.get("satisfaction")

    # Connection speed
    tx_rate = info.get("tx_rate", 0)  # in kbps
    rx_rate = info.get("rx_rate", 0)

    # Data usage
    tx_bytes = info.get("tx_bytes", 0)
    rx_bytes = info.get("rx_bytes", 0)

    # Uptime
    uptime = info.get("uptime", 0)

    # Vendor
    vendor = info.get("oui", "")

    status_data = {
        "name": name,
        "mac": mac,
        "ip": ip,
        "online": is_online,
        "blocked": is_blocked,
        "guest": is_guest,
        "type": conn_type,
        "network": network,
        "ap": ap_name if not is_wired else None,
        "signal": signal,
        "rssi": rssi,
        "channel": channel,
        "radio": radio,
        "satisfaction": satisfaction,
        "tx_rate": tx_rate,
        "rx_rate": rx_rate,
        "tx_bytes": tx_bytes,
        "rx_bytes": rx_bytes,
        "uptime": uptime,
        "vendor": vendor,
    }

    if output == OutputFormat.JSON:
        output_json(status_data)
    else:
        console.print()
        console.print(f"[bold]Client Status: {name}[/bold]")
        console.print("─" * 40)
        console.print(f"  [dim]MAC:[/dim]       {mac}")
        if vendor:
            console.print(f"  [dim]Vendor:[/dim]    {vendor}")
        if ip:
            console.print(f"  [dim]IP:[/dim]        {ip}")
        console.print(f"  [dim]Type:[/dim]      {conn_type}")
        if network:
            console.print(f"  [dim]Network:[/dim]   {network}")
        if ap_name and not is_wired:
            console.print(f"  [dim]AP:[/dim]        {ap_name}")

        # Wireless info section
        if not is_wired and is_online:
            console.print()
            console.print("  [bold]WiFi Info[/bold]")
            if signal is not None:
                # Color code signal strength
                if signal >= -50:
                    sig_color = "green"
                elif signal >= -70:
                    sig_color = "yellow"
                else:
                    sig_color = "red"
                console.print(f"  [dim]Signal:[/dim]    [{sig_color}]{signal} dBm[/{sig_color}]")
            if channel:
                channel_info = f"Ch {channel}"
                if radio:
                    channel_info += f" ({radio.upper()})"
                console.print(f"  [dim]Channel:[/dim]   {channel_info}")
            if satisfaction is not None:
                # Color code experience
                if satisfaction >= 80:
                    exp_color = "green"
                elif satisfaction >= 50:
                    exp_color = "yellow"
                else:
                    exp_color = "red"
                console.print(f"  [dim]Experience:[/dim] [{exp_color}]{satisfaction}%[/{exp_color}]")

        # Connection info section (when online)
        if is_online:
            console.print()
            console.print("  [bold]Connection[/bold]")
            if uptime:
                console.print(f"  [dim]Uptime:[/dim]    {format_uptime(uptime)}")
            if tx_rate or rx_rate:
                tx_str = f"{tx_rate / 1000:.0f}" if tx_rate else "0"
                rx_str = f"{rx_rate / 1000:.0f}" if rx_rate else "0"
                console.print(f"  [dim]Speed:[/dim]     ↑{tx_str} / ↓{rx_str} Mbps")
            if tx_bytes or rx_bytes:
                console.print(f"  [dim]Data:[/dim]      ↑{format_bytes(tx_bytes)} / ↓{format_bytes(rx_bytes)}")

        # Status section
        console.print()
        console.print("  [bold]Status[/bold]")
        if is_online:
            console.print(f"  [dim]Online:[/dim]    [green]Yes[/green]")
        else:
            console.print(f"  [dim]Online:[/dim]    [dim]No[/dim]")

        if is_blocked:
            console.print(f"  [dim]Blocked:[/dim]   [red]Yes[/red]")
        else:
            console.print(f"  [dim]Blocked:[/dim]   [green]No[/green]")

        if is_guest:
            console.print(f"  [dim]Guest:[/dim]     Yes")

        console.print()


@app.command("block")
def block_client(
    identifier: Annotated[
        str | None,
        typer.Argument(help="Client MAC address or name"),
    ] = None,
    group: Annotated[
        str | None,
        typer.Option("--group", "-g", help="Block all clients in a group"),
    ] = None,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation prompt"),
    ] = False,
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
) -> None:
    """Block a client or all clients in a group.

    Examples:
        ./ui lo clients block my-iPhone
        ./ui lo clients block AA:BB:CC:DD:EE:FF -y
        ./ui lo clients block -g kids-devices
    """
    if group and identifier:
        console.print("[red]Error:[/red] Specify client OR --group, not both")
        raise typer.Exit(1)

    if not group and not identifier:
        console.print("[yellow]Usage:[/yellow] ./ui lo clients block <name or MAC>")
        console.print("       ./ui lo clients block --group <group-name>")
        console.print()
        console.print("Examples:")
        console.print("  ./ui lo clients block my-iPhone")
        console.print("  ./ui lo clients block -g kids-devices")
        raise typer.Exit(1)

    # Handle group blocking
    if group:
        _block_group(group, yes, output)
        return

    # Resolve identifier to MAC
    async def _resolve():
        api_client = UniFiLocalClient()
        return await resolve_client_identifier(api_client, identifier)

    try:
        mac, name = run_with_spinner(_resolve(), "Finding client...")
    except Exception as e:
        handle_error(e)
        return

    if not mac:
        console.print(f"[yellow]Client not found:[/yellow] {identifier}")
        raise typer.Exit(1)

    display = f"{name} ({mac.upper()})" if name else mac.upper()

    # Confirm action
    if not yes:
        if not typer.confirm(f"Block client {display}?"):
            console.print("[dim]Cancelled[/dim]")
            raise typer.Exit(0)

    # Execute action
    async def _block():
        api_client = UniFiLocalClient()
        return await api_client.block_client(mac)

    try:
        success = run_with_spinner(_block(), "Blocking client...")
    except Exception as e:
        handle_error(e)
        return

    if success:
        if output == OutputFormat.JSON:
            output_json({"success": True, "action": "blocked", "name": name, "mac": mac})
        else:
            console.print(f"[green]Blocked client:[/green] {display}")
    else:
        if output == OutputFormat.JSON:
            output_json({"success": False, "action": "blocked", "name": name, "mac": mac, "error": "API call failed"})
        else:
            console.print(f"[red]Failed to block client:[/red] {display}")
        raise typer.Exit(1)


def _block_group(group: str, yes: bool, output: OutputFormat) -> None:
    """Block all clients in a group."""
    from ui_cli.groups import GroupManager

    gm = GroupManager()
    result = gm.get_group(group)
    if not result:
        console.print(f"[red]Error:[/red] Group '{group}' not found")
        raise typer.Exit(1)

    _, grp = result

    async def _get_members():
        api_client = UniFiLocalClient()
        if grp.type == "static":
            members = []
            for m in grp.members or []:
                members.append({"mac": m.mac, "name": m.alias})
            return members, api_client
        else:
            # Auto group - evaluate rules
            clients = await api_client.list_all_clients()
            matching = gm.evaluate_auto_group(group, clients)
            members = [{"mac": c["mac"], "name": c.get("name") or c.get("hostname")} for c in matching]
            return members, api_client

    try:
        members, api_client = run_with_spinner(_get_members(), "Getting group members...")
    except Exception as e:
        handle_error(e)
        return

    if not members:
        console.print(f"[yellow]No members in group '{grp.name}'[/yellow]")
        return

    # Confirm action
    if not yes:
        if not typer.confirm(f"Block {len(members)} clients in group '{grp.name}'?"):
            console.print("[dim]Cancelled[/dim]")
            raise typer.Exit(0)

    console.print(f"\nBlocking {len(members)} clients in group \"{grp.name}\"...\n")

    # Block each client
    results = {"blocked": 0, "already": 0, "failed": 0}
    result_details = []

    async def _block_one(mac: str):
        return await api_client.block_client(mac)

    for member in members:
        mac = member["mac"]
        name = member["name"] or mac
        display = f"{name} ({mac.upper()})" if name != mac else mac.upper()

        try:
            # Check current status first
            async def _check():
                all_clients = await api_client.list_all_clients()
                for c in all_clients:
                    if c.get("mac", "").upper() == mac.upper():
                        return c.get("blocked", False)
                return False

            is_blocked = asyncio.run(_check())

            if is_blocked:
                console.print(f"[dim]- {display} - already blocked[/dim]")
                results["already"] += 1
                result_details.append({"mac": mac, "name": name, "status": "already_blocked"})
            else:
                success = asyncio.run(_block_one(mac))
                if success:
                    console.print(f"[green]✓[/green] {display} - blocked")
                    results["blocked"] += 1
                    result_details.append({"mac": mac, "name": name, "status": "blocked"})
                else:
                    console.print(f"[red]✗[/red] {display} - failed")
                    results["failed"] += 1
                    result_details.append({"mac": mac, "name": name, "status": "failed"})
        except Exception:
            console.print(f"[red]✗[/red] {display} - failed")
            results["failed"] += 1
            result_details.append({"mac": mac, "name": name, "status": "failed"})

    console.print(f"\nBlocked: {results['blocked']} | Already blocked: {results['already']} | Failed: {results['failed']}")

    if output == OutputFormat.JSON:
        output_json({"group": grp.name, "results": result_details, "summary": results})


@app.command("unblock")
def unblock_client(
    identifier: Annotated[
        str | None,
        typer.Argument(help="Client MAC address or name"),
    ] = None,
    group: Annotated[
        str | None,
        typer.Option("--group", "-g", help="Unblock all clients in a group"),
    ] = None,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation prompt"),
    ] = False,
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
) -> None:
    """Unblock a client or all clients in a group.

    Examples:
        ./ui lo clients unblock my-iPhone
        ./ui lo clients unblock AA:BB:CC:DD:EE:FF -y
        ./ui lo clients unblock -g kids-devices
    """
    if group and identifier:
        console.print("[red]Error:[/red] Specify client OR --group, not both")
        raise typer.Exit(1)

    if not group and not identifier:
        console.print("[yellow]Usage:[/yellow] ./ui lo clients unblock <name or MAC>")
        console.print("       ./ui lo clients unblock --group <group-name>")
        console.print()
        console.print("Examples:")
        console.print("  ./ui lo clients unblock my-iPhone")
        console.print("  ./ui lo clients unblock -g kids-devices")
        raise typer.Exit(1)

    # Handle group unblocking
    if group:
        _unblock_group(group, yes, output)
        return

    # Resolve identifier to MAC
    async def _resolve():
        api_client = UniFiLocalClient()
        return await resolve_client_identifier(api_client, identifier)

    try:
        mac, name = run_with_spinner(_resolve(), "Finding client...")
    except Exception as e:
        handle_error(e)
        return

    if not mac:
        console.print(f"[yellow]Client not found:[/yellow] {identifier}")
        raise typer.Exit(1)

    display = f"{name} ({mac.upper()})" if name else mac.upper()

    # Confirm action
    if not yes:
        if not typer.confirm(f"Unblock client {display}?"):
            console.print("[dim]Cancelled[/dim]")
            raise typer.Exit(0)

    # Execute action
    async def _unblock():
        api_client = UniFiLocalClient()
        return await api_client.unblock_client(mac)

    try:
        success = run_with_spinner(_unblock(), "Unblocking client...")
    except Exception as e:
        handle_error(e)
        return

    if success:
        if output == OutputFormat.JSON:
            output_json({"success": True, "action": "unblocked", "name": name, "mac": mac})
        else:
            console.print(f"[green]Unblocked client:[/green] {display}")
    else:
        if output == OutputFormat.JSON:
            output_json({"success": False, "action": "unblocked", "name": name, "mac": mac, "error": "API call failed"})
        else:
            console.print(f"[red]Failed to unblock client:[/red] {display}")
        raise typer.Exit(1)


def _unblock_group(group: str, yes: bool, output: OutputFormat) -> None:
    """Unblock all clients in a group."""
    from ui_cli.groups import GroupManager

    gm = GroupManager()
    result = gm.get_group(group)
    if not result:
        console.print(f"[red]Error:[/red] Group '{group}' not found")
        raise typer.Exit(1)

    _, grp = result

    async def _get_members():
        api_client = UniFiLocalClient()
        if grp.type == "static":
            members = []
            for m in grp.members or []:
                members.append({"mac": m.mac, "name": m.alias})
            return members, api_client
        else:
            clients = await api_client.list_all_clients()
            matching = gm.evaluate_auto_group(group, clients)
            members = [{"mac": c["mac"], "name": c.get("name") or c.get("hostname")} for c in matching]
            return members, api_client

    try:
        members, api_client = run_with_spinner(_get_members(), "Getting group members...")
    except Exception as e:
        handle_error(e)
        return

    if not members:
        console.print(f"[yellow]No members in group '{grp.name}'[/yellow]")
        return

    if not yes:
        if not typer.confirm(f"Unblock {len(members)} clients in group '{grp.name}'?"):
            console.print("[dim]Cancelled[/dim]")
            raise typer.Exit(0)

    console.print(f"\nUnblocking {len(members)} clients in group \"{grp.name}\"...\n")

    results = {"unblocked": 0, "not_blocked": 0, "failed": 0}
    result_details = []

    for member in members:
        mac = member["mac"]
        name = member["name"] or mac
        display = f"{name} ({mac.upper()})" if name != mac else mac.upper()

        try:
            async def _check():
                all_clients = await api_client.list_all_clients()
                for c in all_clients:
                    if c.get("mac", "").upper() == mac.upper():
                        return c.get("blocked", False)
                return False

            is_blocked = asyncio.run(_check())

            if not is_blocked:
                console.print(f"[dim]- {display} - not blocked[/dim]")
                results["not_blocked"] += 1
                result_details.append({"mac": mac, "name": name, "status": "not_blocked"})
            else:
                async def _unblock_one():
                    return await api_client.unblock_client(mac)

                success = asyncio.run(_unblock_one())
                if success:
                    console.print(f"[green]✓[/green] {display} - unblocked")
                    results["unblocked"] += 1
                    result_details.append({"mac": mac, "name": name, "status": "unblocked"})
                else:
                    console.print(f"[red]✗[/red] {display} - failed")
                    results["failed"] += 1
                    result_details.append({"mac": mac, "name": name, "status": "failed"})
        except Exception:
            console.print(f"[red]✗[/red] {display} - failed")
            results["failed"] += 1
            result_details.append({"mac": mac, "name": name, "status": "failed"})

    console.print(f"\nUnblocked: {results['unblocked']} | Not blocked: {results['not_blocked']} | Failed: {results['failed']}")

    if output == OutputFormat.JSON:
        output_json({"group": grp.name, "results": result_details, "summary": results})


@app.command("kick")
def kick_client(
    identifier: Annotated[
        str | None,
        typer.Argument(help="Client MAC address or name"),
    ] = None,
    group: Annotated[
        str | None,
        typer.Option("--group", "-g", help="Kick all clients in a group"),
    ] = None,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation prompt"),
    ] = False,
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
) -> None:
    """Kick (disconnect) a client or all clients in a group.

    Examples:
        ./ui lo clients kick my-iPhone
        ./ui lo clients kick AA:BB:CC:DD:EE:FF -y
        ./ui lo clients kick -g kids-devices
    """
    if group and identifier:
        console.print("[red]Error:[/red] Specify client OR --group, not both")
        raise typer.Exit(1)

    if not group and not identifier:
        console.print("[yellow]Usage:[/yellow] ./ui lo clients kick <name or MAC>")
        console.print("       ./ui lo clients kick --group <group-name>")
        console.print()
        console.print("Examples:")
        console.print("  ./ui lo clients kick my-iPhone")
        console.print("  ./ui lo clients kick -g kids-devices")
        raise typer.Exit(1)

    # Handle group kicking
    if group:
        _kick_group(group, yes, output)
        return

    # Resolve identifier to MAC
    async def _resolve():
        api_client = UniFiLocalClient()
        return await resolve_client_identifier(api_client, identifier)

    try:
        mac, name = run_with_spinner(_resolve(), "Finding client...")
    except Exception as e:
        handle_error(e)
        return

    if not mac:
        console.print(f"[yellow]Client not found:[/yellow] {identifier}")
        raise typer.Exit(1)

    display = f"{name} ({mac.upper()})" if name else mac.upper()

    # Confirm action
    if not yes:
        if not typer.confirm(f"Kick client {display}?"):
            console.print("[dim]Cancelled[/dim]")
            raise typer.Exit(0)

    # Execute action
    async def _kick():
        api_client = UniFiLocalClient()
        return await api_client.kick_client(mac)

    try:
        success = run_with_spinner(_kick(), "Kicking client...")
    except Exception as e:
        handle_error(e)
        return

    if success:
        if output == OutputFormat.JSON:
            output_json({"success": True, "action": "kicked", "name": name, "mac": mac})
        else:
            console.print(f"[green]Kicked client:[/green] {display}")
    else:
        if output == OutputFormat.JSON:
            output_json({"success": False, "action": "kicked", "name": name, "mac": mac, "error": "API call failed"})
        else:
            console.print(f"[red]Failed to kick client:[/red] {display}")
        raise typer.Exit(1)


def _kick_group(group: str, yes: bool, output: OutputFormat) -> None:
    """Kick all clients in a group."""
    from ui_cli.groups import GroupManager

    gm = GroupManager()
    result = gm.get_group(group)
    if not result:
        console.print(f"[red]Error:[/red] Group '{group}' not found")
        raise typer.Exit(1)

    _, grp = result

    async def _get_members():
        api_client = UniFiLocalClient()
        if grp.type == "static":
            members = []
            for m in grp.members or []:
                members.append({"mac": m.mac, "name": m.alias})
            return members, api_client
        else:
            clients = await api_client.list_clients()  # Only online clients
            matching = gm.evaluate_auto_group(group, clients)
            members = [{"mac": c["mac"], "name": c.get("name") or c.get("hostname")} for c in matching]
            return members, api_client

    try:
        members, api_client = run_with_spinner(_get_members(), "Getting group members...")
    except Exception as e:
        handle_error(e)
        return

    if not members:
        console.print(f"[yellow]No members in group '{grp.name}'[/yellow]")
        return

    if not yes:
        if not typer.confirm(f"Kick {len(members)} clients in group '{grp.name}'?"):
            console.print("[dim]Cancelled[/dim]")
            raise typer.Exit(0)

    console.print(f"\nKicking {len(members)} clients in group \"{grp.name}\"...\n")

    results = {"kicked": 0, "failed": 0}
    result_details = []

    for member in members:
        mac = member["mac"]
        name = member["name"] or mac
        display = f"{name} ({mac.upper()})" if name != mac else mac.upper()

        try:
            async def _kick_one():
                return await api_client.kick_client(mac)

            success = asyncio.run(_kick_one())
            if success:
                console.print(f"[green]✓[/green] {display} - kicked")
                results["kicked"] += 1
                result_details.append({"mac": mac, "name": name, "status": "kicked"})
            else:
                console.print(f"[red]✗[/red] {display} - failed")
                results["failed"] += 1
                result_details.append({"mac": mac, "name": name, "status": "failed"})
        except Exception:
            console.print(f"[red]✗[/red] {display} - failed")
            results["failed"] += 1
            result_details.append({"mac": mac, "name": name, "status": "failed"})

    console.print(f"\nKicked: {results['kicked']} | Failed: {results['failed']}")

    if output == OutputFormat.JSON:
        output_json({"group": grp.name, "results": result_details, "summary": results})


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
    async def _count():
        api_client = UniFiLocalClient()
        if include_offline:
            return await api_client.list_all_clients()
        else:
            return await api_client.list_clients()

    try:
        clients = run_with_spinner(_count(), "Counting clients...")
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


@app.command("rename")
def rename_client(
    identifier: Annotated[
        str,
        typer.Argument(help="Client MAC address or current name"),
    ],
    new_name: Annotated[
        str,
        typer.Argument(help="New name for the client"),
    ],
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation prompt"),
    ] = False,
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
) -> None:
    """Rename a client (set display name).

    Sets a custom name for a client that will be shown in the UniFi
    controller instead of the hostname or MAC address.

    Examples:
        ui lo clients rename 7A:3E:07:23:13:75 "AEG Dampfgarer"
        ui lo clients rename "old-name" "new-name" -y
    """
    async def _resolve_and_get_id():
        api_client = UniFiLocalClient()
        mac, current_name = await resolve_client_identifier(api_client, identifier)
        if not mac:
            return None, None, None, api_client

        # Get user record to find the _id
        response = await api_client.get("/rest/user")
        users = response.get("data", [])
        user_id = None
        for user in users:
            if user.get("mac", "").lower() == mac.lower():
                user_id = user.get("_id")
                break

        return mac, current_name, user_id, api_client

    try:
        mac, current_name, user_id, api_client = run_with_spinner(
            _resolve_and_get_id(), "Finding client..."
        )
    except Exception as e:
        handle_error(e)
        return

    if not mac:
        console.print(f"[yellow]Client not found:[/yellow] {identifier}")
        raise typer.Exit(1)

    if not user_id:
        console.print(f"[red]Error:[/red] Could not find user record for {identifier}")
        console.print("[dim]The client may not have connected recently enough to have a user record.[/dim]")
        raise typer.Exit(1)

    display = f"{current_name} ({mac.upper()})" if current_name else mac.upper()

    # Confirm action
    if not yes:
        if not typer.confirm(f"Rename {display} to \"{new_name}\"?"):
            console.print("[dim]Cancelled[/dim]")
            raise typer.Exit(0)

    # Execute action
    async def _rename():
        return await api_client.set_client_name(user_id, new_name)

    try:
        success = run_with_spinner(_rename(), "Renaming client...")
    except Exception as e:
        handle_error(e)
        return

    if success:
        if output == OutputFormat.JSON:
            output_json({
                "success": True,
                "mac": mac,
                "old_name": current_name,
                "new_name": new_name,
            })
        else:
            console.print(f"[green]Renamed:[/green] {mac.upper()} -> \"{new_name}\"")
    else:
        if output == OutputFormat.JSON:
            output_json({
                "success": False,
                "mac": mac,
                "old_name": current_name,
                "new_name": new_name,
                "error": "API call failed",
            })
        else:
            console.print(f"[red]Failed to rename client:[/red] {display}")
        raise typer.Exit(1)


@app.command("duplicates")
def find_duplicates(
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
) -> None:
    """Find clients with duplicate names.

    Searches all known clients (including offline) for duplicate names.
    This can indicate:
    - Same device with multiple NICs (WiFi + Ethernet)
    - Different devices that happen to share a name

    Shows connection type (wired/wireless) to help distinguish.
    """
    async def _list():
        api_client = UniFiLocalClient()
        return await api_client.list_all_clients()

    try:
        clients = run_with_spinner(_list(), "Finding duplicates...")
    except Exception as e:
        handle_error(e)
        return

    # Group clients by name
    by_name: dict[str, list[dict]] = {}
    for client in clients:
        name = client.get("name") or client.get("hostname") or ""
        if not name:
            continue
        name_lower = name.lower()
        if name_lower not in by_name:
            by_name[name_lower] = []
        by_name[name_lower].append(client)

    # Find duplicates (names with more than one client)
    duplicates = {name: clients for name, clients in by_name.items() if len(clients) > 1}

    if not duplicates:
        console.print("[green]No duplicate client names found.[/green]")
        return

    if output == OutputFormat.JSON:
        # Format for JSON output
        result = []
        for name, clients in sorted(duplicates.items()):
            # Determine if likely multi-NIC (has both wired and wireless)
            has_wired = any(c.get("is_wired", False) for c in clients)
            has_wireless = any(not c.get("is_wired", False) for c in clients)
            likely_multi_nic = has_wired and has_wireless

            for client in clients:
                is_wired = client.get("is_wired", False)
                result.append({
                    "name": client.get("name") or client.get("hostname"),
                    "mac": client.get("mac", "").upper(),
                    "ip": client.get("ip") or client.get("last_ip") or "",
                    "type": "wired" if is_wired else "wireless",
                    "vendor": client.get("oui", ""),
                    "likely_multi_nic": likely_multi_nic,
                })
        output_json(result)
    else:
        # Table output grouped by name
        console.print()
        console.print(f"[bold]Found {len(duplicates)} duplicate name(s):[/bold]")
        console.print()

        for name, clients in sorted(duplicates.items()):
            display_name = clients[0].get("name") or clients[0].get("hostname")

            # Check if likely multi-NIC device
            has_wired = any(c.get("is_wired", False) for c in clients)
            has_wireless = any(not c.get("is_wired", False) for c in clients)
            likely_multi_nic = has_wired and has_wireless

            if likely_multi_nic:
                console.print(f"[yellow]{display_name}[/yellow] ({len(clients)} NICs) [dim]← likely same device[/dim]")
            else:
                console.print(f"[yellow]{display_name}[/yellow] ({len(clients)} clients)")

            for client in clients:
                mac = client.get("mac", "").upper()
                ip = client.get("ip") or client.get("last_ip") or "no IP"
                is_wired = client.get("is_wired", False)
                conn_type = "[blue]wired[/blue]" if is_wired else "[cyan]wifi[/cyan]"
                vendor = client.get("oui", "")
                vendor_str = f" - {vendor}" if vendor else ""
                console.print(f"  • {mac} ({ip}) {conn_type}{vendor_str}")
            console.print()
