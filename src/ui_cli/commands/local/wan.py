"""WAN configuration commands for local controller."""

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

app = typer.Typer(name="wan", help="WAN configuration (upstream DNS, type)", no_args_is_help=True)


def _is_wan(network: dict[str, Any]) -> bool:
    return network.get("purpose") in ("wan", "wan2")


def _pref(network: dict[str, Any]) -> str:
    return network.get("wan_dns_preference") or "auto"


@app.command("list")
def list_wans(
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
) -> None:
    """List WAN uplinks with their DNS settings."""
    from ui_cli.commands.local.utils import run_with_spinner

    async def _list():
        client = UniFiLocalClient()
        nets = await client.get_networks()
        return [n for n in nets if _is_wan(n)]

    try:
        wans = run_with_spinner(_list(), "Fetching WAN networks...")
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if not wans:
        console.print("[dim]No WAN networks found[/dim]")
        return

    if output == OutputFormat.JSON:
        output_json(wans)
        return

    if output == OutputFormat.CSV:
        columns = [
            ("_id", "ID"),
            ("name", "Name"),
            ("purpose", "Purpose"),
            ("wan_type", "Type"),
            ("wan_dns_preference", "DNS Pref"),
            ("wan_dns1", "DNS1"),
            ("wan_dns2", "DNS2"),
        ]
        output_csv(wans, columns)
        return

    from rich.table import Table

    table = Table(title="WAN Uplinks", show_header=True, header_style="bold cyan")
    table.add_column("ID", style="dim")
    table.add_column("Name")
    table.add_column("Purpose")
    table.add_column("Type")
    table.add_column("DNS Pref")
    table.add_column("DNS1")
    table.add_column("DNS2")

    for n in wans:
        table.add_row(
            n.get("_id", ""),
            n.get("name", ""),
            n.get("purpose", ""),
            n.get("wan_type", "-"),
            _pref(n),
            n.get("wan_dns1", "") or "-",
            n.get("wan_dns2", "") or "-",
        )

    console.print(table)
    console.print(f"\n[dim]{len(wans)} WAN(s)[/dim]")


@app.command("get")
def get_wan(
    wan_id: Annotated[str, typer.Argument(help="WAN ID or name")],
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
) -> None:
    """Show WAN details (DNS, IPv6 DNS, gateway, type)."""
    from ui_cli.commands.local.utils import run_with_spinner

    async def _get():
        client = UniFiLocalClient()
        nets = await client.get_networks()
        wans = [n for n in nets if _is_wan(n)]
        for n in wans:
            if n.get("_id") == wan_id or n.get("name", "").lower() == wan_id.lower():
                return n
        for n in wans:
            if wan_id.lower() in n.get("name", "").lower():
                return n
        return None

    try:
        wan = run_with_spinner(_get(), "Finding WAN...")
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if not wan:
        print_error(f"WAN '{wan_id}' not found")
        raise typer.Exit(1)

    if output == OutputFormat.JSON:
        output_json(wan)
        return

    from rich.table import Table

    console.print()
    console.print(f"[bold cyan]WAN: {wan.get('name', 'Unknown')}[/bold cyan]")
    console.print("─" * 40)
    console.print()

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="dim")
    table.add_column("Value")

    table.add_row("ID:", wan.get("_id", ""))
    table.add_row("Purpose:", wan.get("purpose", ""))
    table.add_row("Type:", wan.get("wan_type", "-"))
    table.add_row("", "")
    table.add_row("DNS Preference:", _pref(wan))
    table.add_row("DNS1:", wan.get("wan_dns1", "") or "-")
    table.add_row("DNS2:", wan.get("wan_dns2", "") or "-")
    table.add_row("", "")
    table.add_row("IPv6 DNS Preference:", wan.get("wan_ipv6_dns_preference", "auto"))
    table.add_row("IPv6 DNS1:", wan.get("wan_ipv6_dns1", "") or "-")
    table.add_row("IPv6 DNS2:", wan.get("wan_ipv6_dns2", "") or "-")

    console.print(table)
    console.print()


@app.command("update")
def update_wan(
    wan_ids: Annotated[
        list[str],
        typer.Argument(help="WAN ID(s) or name(s) — pass multiple to update in one call"),
    ],
    dns1: Annotated[
        str | None,
        typer.Option("--dns1", help="Primary upstream DNS server (wan_dns1)"),
    ] = None,
    dns2: Annotated[
        str | None,
        typer.Option("--dns2", help="Secondary upstream DNS server (wan_dns2)"),
    ] = None,
    dns6_1: Annotated[
        str | None,
        typer.Option("--dns6-1", help="Primary IPv6 upstream DNS server (wan_ipv6_dns1)"),
    ] = None,
    dns6_2: Annotated[
        str | None,
        typer.Option("--dns6-2", help="Secondary IPv6 upstream DNS server (wan_ipv6_dns2)"),
    ] = None,
    auto: Annotated[
        bool,
        typer.Option(
            "--auto",
            help="Switch DNS preference back to auto (ISP-provided); clears dns1/dns2",
        ),
    ] = False,
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
) -> None:
    """Update WAN DNS settings.

    Setting --dns1 or --dns2 implies wan_dns_preference=manual. --auto reverts
    to ISP-provided DNS and clears the manual DNS entries.
    """
    from ui_cli.commands.local.utils import run_with_spinner
    from ui_cli.output import print_success

    v4_requested = dns1 is not None or dns2 is not None
    v6_requested = dns6_1 is not None or dns6_2 is not None

    if not v4_requested and not v6_requested and not auto:
        print_error("At least one option required (--dns1, --dns2, --dns6-1, --dns6-2, --auto)")
        raise typer.Exit(1)

    if auto and (v4_requested or v6_requested):
        print_error("--auto cannot be combined with --dns1/--dns2/--dns6-1/--dns6-2")
        raise typer.Exit(1)

    def _resolve(wans: list[dict[str, Any]], needle: str) -> dict[str, Any] | None:
        for n in wans:
            if n.get("_id") == needle or n.get("name", "").lower() == needle.lower():
                return n
        for n in wans:
            if needle.lower() in n.get("name", "").lower():
                return n
        return None

    async def _update_one(
        client: UniFiLocalClient,
        wans: list[dict[str, Any]],
        needle: str,
    ) -> tuple[dict[str, Any] | None, str | None]:
        wan = _resolve(wans, needle)
        if not wan:
            return None, f"WAN '{needle}' not found"

        net_id = wan["_id"]
        payload: dict[str, Any] = {"_id": net_id}

        if auto:
            payload["wan_dns_preference"] = "auto"
            payload["wan_dns1"] = ""
            payload["wan_dns2"] = ""
        elif v4_requested:
            payload["wan_dns_preference"] = "manual"
            if dns1 is not None:
                payload["wan_dns1"] = dns1
            if dns2 is not None:
                payload["wan_dns2"] = dns2

        if v6_requested:
            payload["wan_ipv6_dns_preference"] = "manual"
            if dns6_1 is not None:
                payload["wan_ipv6_dns1"] = dns6_1
            if dns6_2 is not None:
                payload["wan_ipv6_dns2"] = dns6_2

        updated = await client.update_network(net_id, payload)
        return updated, None

    async def _update_all():
        client = UniFiLocalClient()
        nets = await client.get_networks()
        wans = [n for n in nets if _is_wan(n)]
        results: list[tuple[str, dict[str, Any] | None, str | None]] = []
        for needle in wan_ids:
            result, err = await _update_one(client, wans, needle)
            results.append((needle, result, err))
        return results

    try:
        results = run_with_spinner(_update_all(), "Updating WAN(s)...")
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if output == OutputFormat.JSON:
        output_json([
            {"wan": needle, "error": err, "result": result}
            for needle, result, err in results
        ])
        raise typer.Exit(1 if any(err for _, _, err in results) else 0)

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
        print_success(f"Updated WAN '{name}'")
        console.print(f"  DNS Pref: {result.get('wan_dns_preference', 'auto')}")
        if result.get("wan_dns1") or result.get("wan_dns2"):
            console.print(
                f"  DNS: {result.get('wan_dns1', '') or '-'}, {result.get('wan_dns2', '') or '-'}"
            )
        if result.get("wan_ipv6_dns1") or result.get("wan_ipv6_dns2"):
            console.print(
                f"  IPv6 DNS: {result.get('wan_ipv6_dns1', '') or '-'}, "
                f"{result.get('wan_ipv6_dns2', '') or '-'}"
            )

    if exit_code:
        raise typer.Exit(exit_code)
