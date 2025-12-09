"""WLAN management commands for local controller."""

from typing import Annotated, Any

import typer

from ui_cli.commands.local.utils import run_with_spinner
from ui_cli.local_client import LocalAPIError, UniFiLocalClient
from ui_cli.output import (
    OutputFormat,
    console,
    output_csv,
    output_json,
    print_error,
)

app = typer.Typer(name="wlans", help="WLAN management", no_args_is_help=True)


def get_security_type(wlan: dict[str, Any]) -> str:
    """Get human-readable security type for a WLAN."""
    security = wlan.get("security", "open")
    wpa_mode = wlan.get("wpa_mode", "")

    if security == "open":
        return "Open"
    elif security == "wpapsk":
        if wpa_mode == "wpa2":
            return "WPA2-Personal"
        elif wpa_mode == "wpa3":
            return "WPA3-Personal"
        return "WPA-Personal"
    elif security == "wpaeap":
        if wpa_mode == "wpa2":
            return "WPA2-Enterprise"
        elif wpa_mode == "wpa3":
            return "WPA3-Enterprise"
        return "WPA-Enterprise"
    return security


def find_wlan(wlans: list[dict[str, Any]], identifier: str) -> dict[str, Any] | None:
    """Find WLAN by ID or name."""
    identifier_lower = identifier.lower()

    # First try exact ID match
    for w in wlans:
        if w.get("_id") == identifier:
            return w

    # Try exact name match
    for w in wlans:
        name = w.get("name", "").lower()
        if name == identifier_lower:
            return w

    # Try partial name match
    for w in wlans:
        name = w.get("name", "").lower()
        if identifier_lower in name:
            return w

    return None


# ========== WLAN Commands ==========


@app.command("list")
def list_wlans(
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Show additional details"),
    ] = False,
) -> None:
    """List all WLANs (wireless networks)."""

    async def _list():
        client = UniFiLocalClient()
        return await client.get_wlans()

    try:
        wlans = run_with_spinner(_list(), "Fetching WLANs...")
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if not wlans:
        console.print("[dim]No WLANs found[/dim]")
        return

    if output == OutputFormat.JSON:
        output_json(wlans)
    elif output == OutputFormat.CSV:
        columns = [
            ("_id", "ID"),
            ("name", "Name"),
            ("security", "Security"),
            ("vlan", "VLAN"),
            ("enabled", "Enabled"),
        ]
        csv_data = []
        for w in wlans:
            csv_data.append({
                "_id": w.get("_id", ""),
                "name": w.get("name", ""),
                "security": get_security_type(w),
                "vlan": w.get("vlan", ""),
                "enabled": "Yes" if w.get("enabled", True) else "No",
            })
        output_csv(csv_data, columns)
    else:
        from rich.table import Table

        table = Table(title="WLANs", show_header=True, header_style="bold cyan")
        table.add_column("ID", style="dim")
        table.add_column("Name")
        table.add_column("Security")
        table.add_column("VLAN")
        table.add_column("Enabled")
        if verbose:
            table.add_column("Band")
            table.add_column("Hide SSID")
            table.add_column("PMF")

        for w in wlans:
            wlan_id = w.get("_id", "")
            name = w.get("name", "")
            security = get_security_type(w)
            vlan = str(w.get("vlan", "-")) if w.get("vlan") else "-"
            enabled = "[green]Yes[/green]" if w.get("enabled", True) else "[red]No[/red]"

            if verbose:
                # Band steering / radio settings
                wlan_band = w.get("wlan_band", "both")
                if wlan_band == "both":
                    band = "2.4/5 GHz"
                elif wlan_band == "5g":
                    band = "5 GHz"
                else:
                    band = "2.4 GHz"

                hide_ssid = "Yes" if w.get("hide_ssid", False) else "No"
                pmf = w.get("pmf_mode", "disabled")
                pmf_map = {"disabled": "Off", "optional": "Optional", "required": "Required"}
                pmf_display = pmf_map.get(pmf, pmf)

                table.add_row(
                    wlan_id, name, security, vlan, enabled, band, hide_ssid, pmf_display
                )
            else:
                table.add_row(wlan_id, name, security, vlan, enabled)

        console.print(table)
        console.print(f"\n[dim]{len(wlans)} WLAN(s)[/dim]")


@app.command("get")
def get_wlan(
    identifier: Annotated[str, typer.Argument(help="WLAN ID or name")],
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
) -> None:
    """Get detailed WLAN information."""

    async def _get():
        client = UniFiLocalClient()
        wlans = await client.get_wlans()
        return find_wlan(wlans, identifier)

    try:
        wlan = run_with_spinner(_get(), "Finding WLAN...")
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if not wlan:
        print_error(f"WLAN '{identifier}' not found")
        raise typer.Exit(1)

    if output == OutputFormat.JSON:
        output_json(wlan)
        return

    # Table output
    from rich.table import Table

    name = wlan.get("name", "Unknown")
    console.print()
    console.print(f"[bold cyan]WLAN: {name}[/bold cyan]")
    console.print("-" * 40)
    console.print()

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="dim")
    table.add_column("Value")

    table.add_row("ID:", wlan.get("_id", ""))
    table.add_row("Name:", name)
    table.add_row("Security:", get_security_type(wlan))
    enabled_display = "[green]Yes[/green]" if wlan.get("enabled", True) else "[red]No[/red]"
    table.add_row("Enabled:", enabled_display)
    table.add_row("", "")

    # VLAN
    vlan = wlan.get("vlan")
    if vlan:
        table.add_row("VLAN:", str(vlan))

    # Network group
    network_id = wlan.get("networkconf_id")
    if network_id:
        table.add_row("Network ID:", network_id)

    table.add_row("", "")

    # Radio settings
    wlan_band = wlan.get("wlan_band", "both")
    if wlan_band == "both":
        table.add_row("Band:", "2.4 GHz & 5 GHz")
    elif wlan_band == "5g":
        table.add_row("Band:", "5 GHz only")
    else:
        table.add_row("Band:", "2.4 GHz only")

    # Visibility
    table.add_row("Hidden SSID:", "Yes" if wlan.get("hide_ssid", False) else "No")

    # PMF
    pmf = wlan.get("pmf_mode", "disabled")
    pmf_map = {"disabled": "Disabled", "optional": "Optional", "required": "Required"}
    pmf_display = pmf_map.get(pmf, pmf)
    table.add_row("PMF Mode:", pmf_display)

    # Fast roaming
    table.add_row("Fast Roaming:", "Yes" if wlan.get("fast_roaming_enabled", False) else "No")

    table.add_row("", "")

    # Guest settings
    if wlan.get("is_guest", False):
        table.add_row("Guest Network:", "[yellow]Yes[/yellow]")
        if wlan.get("guest_lan_isolation", False):
            table.add_row("Client Isolation:", "Yes")

    # Rate limiting
    if wlan.get("usergroup_id"):
        table.add_row("User Group:", wlan.get("usergroup_id", ""))

    console.print(table)
    console.print()
