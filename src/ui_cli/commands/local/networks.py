"""Network configuration commands for local controller."""

import asyncio
from typing import Annotated, Any

import typer

from ui_cli.local_client import LocalAPIError, UniFiLocalClient
from ui_cli.output import (
    OutputFormat,
    console,
    output_csv,
    output_json,
    print_error,
)

app = typer.Typer(name="networks", help="Network configuration", no_args_is_help=True)


def format_dhcp_range(network: dict[str, Any]) -> str:
    """Format DHCP range for display."""
    if not network.get("dhcpd_enabled", False):
        return "Disabled"

    start = network.get("dhcpd_start", "")
    stop = network.get("dhcpd_stop", "")

    if start and stop:
        # Extract last octet for compact display
        start_last = start.split(".")[-1] if "." in start else start
        stop_last = stop.split(".")[-1] if "." in stop else stop
        return f".{start_last} - .{stop_last}"

    return "Enabled"


def format_subnet(network: dict[str, Any]) -> str:
    """Format subnet for display."""
    subnet = network.get("ip_subnet", "")
    if subnet:
        return subnet
    return "-"


def get_network_purpose(network: dict[str, Any]) -> str:
    """Get network purpose/type."""
    purpose = network.get("purpose", "")
    if purpose:
        return purpose
    # Fallback to network type
    return network.get("networkgroup", "LAN")


@app.command("list")
def list_networks(
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Show additional details"),
    ] = False,
) -> None:
    """List all networks."""
    from ui_cli.commands.local.utils import run_with_spinner

    async def _list():
        client = UniFiLocalClient()
        return await client.get_networks()

    try:
        networks = run_with_spinner(_list(), "Fetching networks...")
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if not networks:
        console.print("[dim]No networks found[/dim]")
        return

    if output == OutputFormat.JSON:
        output_json(networks)
    elif output == OutputFormat.CSV:
        columns = [
            ("_id", "ID"),
            ("name", "Name"),
            ("vlan", "VLAN"),
            ("ip_subnet", "Subnet"),
            ("purpose", "Purpose"),
            ("dhcpd_enabled", "DHCP"),
        ]
        csv_data = []
        for n in networks:
            csv_data.append({
                "_id": n.get("_id", ""),
                "name": n.get("name", ""),
                "vlan": n.get("vlan", "1"),
                "ip_subnet": n.get("ip_subnet", ""),
                "purpose": get_network_purpose(n),
                "dhcpd_enabled": "Yes" if n.get("dhcpd_enabled") else "No",
            })
        output_csv(csv_data, columns)
    else:
        from rich.table import Table

        table = Table(title="Networks", show_header=True, header_style="bold cyan")
        table.add_column("ID", style="dim")
        table.add_column("Name")
        table.add_column("VLAN")
        table.add_column("Subnet")
        table.add_column("DHCP")
        table.add_column("Purpose")
        if verbose:
            table.add_column("Gateway")
            table.add_column("Domain")

        for n in networks:
            network_id = n.get("_id", "")
            name = n.get("name", "")
            vlan = str(n.get("vlan", "1"))
            subnet = format_subnet(n)
            dhcp = format_dhcp_range(n)
            purpose = get_network_purpose(n)

            if verbose:
                gateway = n.get("dhcpd_gateway", n.get("ip_subnet", "").split("/")[0] if n.get("ip_subnet") else "")
                domain = n.get("domain_name", "-")
                table.add_row(network_id, name, vlan, subnet, dhcp, purpose, gateway, domain)
            else:
                table.add_row(network_id, name, vlan, subnet, dhcp, purpose)

        console.print(table)
        console.print(f"\n[dim]{len(networks)} network(s)[/dim]")


@app.command("get")
def get_network(
    network_id: Annotated[str, typer.Argument(help="Network ID or name")],
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
) -> None:
    """Get network details."""
    from ui_cli.commands.local.utils import run_with_spinner

    async def _get():
        client = UniFiLocalClient()
        networks = await client.get_networks()

        # Find by ID or name
        for n in networks:
            if n.get("_id") == network_id or n.get("name", "").lower() == network_id.lower():
                return n

        # Partial name match
        for n in networks:
            if network_id.lower() in n.get("name", "").lower():
                return n

        return None

    try:
        network = run_with_spinner(_get(), "Finding network...")
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if not network:
        print_error(f"Network '{network_id}' not found")
        raise typer.Exit(1)

    if output == OutputFormat.JSON:
        output_json(network)
        return

    # Table output
    from rich.table import Table

    name = network.get("name", "Unknown")
    console.print()
    console.print(f"[bold cyan]Network: {name}[/bold cyan]")
    console.print("─" * 40)
    console.print()

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="dim")
    table.add_column("Value")

    table.add_row("ID:", network.get("_id", ""))
    table.add_row("VLAN:", str(network.get("vlan", "1")))
    table.add_row("Purpose:", get_network_purpose(network))
    table.add_row("", "")

    # Subnet info
    subnet = network.get("ip_subnet", "")
    if subnet:
        table.add_row("Subnet:", subnet)
        gateway = subnet.split("/")[0] if "/" in subnet else ""
        if gateway:
            # Replace last octet with .1 for gateway
            parts = gateway.rsplit(".", 1)
            if len(parts) == 2:
                gateway = f"{parts[0]}.1"
            table.add_row("Gateway:", network.get("dhcpd_gateway", gateway))

    table.add_row("", "")

    # DHCP info
    if network.get("dhcpd_enabled"):
        table.add_row("DHCP:", "[green]Enabled[/green]")
        start = network.get("dhcpd_start", "")
        stop = network.get("dhcpd_stop", "")
        if start and stop:
            table.add_row("Range:", f"{start} - {stop}")
        lease = network.get("dhcpd_leasetime", 86400)
        table.add_row("Lease:", f"{lease // 3600}h")

        # DNS (dhcpd_dns_{1..4}, gated by dhcpd_dns_enabled)
        if network.get("dhcpd_dns_enabled"):
            dns_parts = [
                network.get(f"dhcpd_dns_{i}", "") for i in (1, 2, 3, 4)
            ]
            dns_parts = [d for d in dns_parts if d]
            if dns_parts:
                table.add_row("DNS:", ", ".join(dns_parts))
            else:
                table.add_row("DNS:", "[dim]custom enabled, no servers set[/dim]")
        else:
            table.add_row("DNS:", "[dim]auto (gateway)[/dim]")
    else:
        table.add_row("DHCP:", "[dim]Disabled[/dim]")

    table.add_row("", "")

    # Additional settings
    if network.get("igmp_snooping"):
        table.add_row("IGMP Snooping:", "Yes")

    if network.get("dhcpguard_enabled"):
        table.add_row("DHCP Guard:", "Yes")

    domain = network.get("domain_name")
    if domain:
        table.add_row("Domain:", domain)

    # Network isolation
    if network.get("purpose") == "guest":
        table.add_row("Guest Network:", "Yes")
        if network.get("networkgroup") == "LAN":
            table.add_row("Internet Only:", "Yes")

    console.print(table)
    console.print()


@app.command("update")
def update_network(
    network_ids: Annotated[
        list[str],
        typer.Argument(help="Network ID(s) or name(s) — pass multiple to update in one call"),
    ],
    dhcp_start: Annotated[
        str | None,
        typer.Option("--dhcp-start", help="DHCP range start (last octet or full IP)"),
    ] = None,
    dhcp_stop: Annotated[
        str | None,
        typer.Option("--dhcp-stop", help="DHCP range stop (last octet or full IP)"),
    ] = None,
    dns1: Annotated[
        str | None,
        typer.Option("--dns1", help="Primary DHCP DNS server (dhcpd_dns_1)"),
    ] = None,
    dns2: Annotated[
        str | None,
        typer.Option("--dns2", help="Secondary DHCP DNS server (dhcpd_dns_2)"),
    ] = None,
    dns3: Annotated[
        str | None,
        typer.Option("--dns3", help="Tertiary DHCP DNS server (dhcpd_dns_3)"),
    ] = None,
    dns4: Annotated[
        str | None,
        typer.Option("--dns4", help="Quaternary DHCP DNS server (dhcpd_dns_4)"),
    ] = None,
    no_dns: Annotated[
        bool,
        typer.Option("--no-dns", help="Disable custom DHCP DNS (fall back to auto/gateway)"),
    ] = False,
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
) -> None:
    """Update network settings (DHCP range, DHCP DNS servers)."""
    from ui_cli.commands.local.utils import run_with_spinner
    from ui_cli.output import print_success

    dns_requested = any(v is not None for v in (dns1, dns2, dns3, dns4)) or no_dns
    dhcp_requested = dhcp_start is not None or dhcp_stop is not None

    if not dhcp_requested and not dns_requested:
        print_error(
            "At least one option required (--dhcp-start, --dhcp-stop, --dns1..--dns4, --no-dns)"
        )
        raise typer.Exit(1)

    if no_dns and any(v is not None for v in (dns1, dns2, dns3, dns4)):
        print_error("--no-dns cannot be combined with --dns1/--dns2/--dns3/--dns4")
        raise typer.Exit(1)

    def _resolve(networks: list[dict[str, Any]], needle: str) -> dict[str, Any] | None:
        for n in networks:
            if n.get("_id") == needle or n.get("name", "").lower() == needle.lower():
                return n
        for n in networks:
            if needle.lower() in n.get("name", "").lower():
                return n
        return None

    async def _update_one(
        client: UniFiLocalClient,
        networks: list[dict[str, Any]],
        needle: str,
    ) -> tuple[dict[str, Any] | None, str | None]:
        network = _resolve(networks, needle)
        if not network:
            return None, f"Network '{needle}' not found"

        net_id = network["_id"]
        subnet = network.get("ip_subnet", "")
        payload: dict[str, Any] = {"_id": net_id}

        if dhcp_requested:
            if not network.get("dhcpd_enabled"):
                return None, f"Network '{network.get('name')}' has DHCP disabled"
            if not subnet:
                return None, f"Network '{network.get('name')}' has no subnet configured"
            prefix = ".".join(subnet.split("/")[0].split(".")[:3])

            if dhcp_start is not None:
                payload["dhcpd_start"] = (
                    f"{prefix}.{dhcp_start}" if "." not in dhcp_start else dhcp_start
                )
            if dhcp_stop is not None:
                payload["dhcpd_stop"] = (
                    f"{prefix}.{dhcp_stop}" if "." not in dhcp_stop else dhcp_stop
                )

        if dns_requested:
            if no_dns:
                payload["dhcpd_dns_enabled"] = False
                payload.update({
                    "dhcpd_dns_1": "",
                    "dhcpd_dns_2": "",
                    "dhcpd_dns_3": "",
                    "dhcpd_dns_4": "",
                })
            else:
                payload["dhcpd_dns_enabled"] = True
                if dns1 is not None:
                    payload["dhcpd_dns_1"] = dns1
                if dns2 is not None:
                    payload["dhcpd_dns_2"] = dns2
                if dns3 is not None:
                    payload["dhcpd_dns_3"] = dns3
                if dns4 is not None:
                    payload["dhcpd_dns_4"] = dns4

        updated = await client.update_network(net_id, payload)
        return updated, None

    async def _update_all():
        client = UniFiLocalClient()
        networks = await client.get_networks()
        results: list[tuple[str, dict[str, Any] | None, str | None]] = []
        for needle in network_ids:
            result, err = await _update_one(client, networks, needle)
            results.append((needle, result, err))
        return results

    try:
        results = run_with_spinner(_update_all(), "Updating networks...")
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if output == OutputFormat.JSON:
        output_json([
            {"network": needle, "error": err, "result": result}
            for needle, result, err in results
        ])
        exit_code = 1 if any(err for _, _, err in results) else 0
        raise typer.Exit(exit_code)

    exit_code = 0
    for needle, result, err in results:
        if err:
            print_error(f"[{needle}] {err}")
            exit_code = 1
            continue
        if not result:
            print_error(f"[{needle}] Update failed - no response from controller")
            exit_code = 1
            continue

        name = result.get("name", needle)
        print_success(f"Updated network '{name}'")
        if dhcp_requested:
            console.print(
                f"  DHCP Range: {result.get('dhcpd_start', '')} - {result.get('dhcpd_stop', '')}"
            )
        if dns_requested:
            if result.get("dhcpd_dns_enabled"):
                dns_parts = [
                    result.get(f"dhcpd_dns_{i}", "") for i in (1, 2, 3, 4)
                ]
                dns_parts = [d for d in dns_parts if d]
                console.print(f"  DNS: {', '.join(dns_parts) if dns_parts else '(enabled, empty)'}")
            else:
                console.print("  DNS: auto (custom disabled)")

    if exit_code:
        raise typer.Exit(exit_code)
