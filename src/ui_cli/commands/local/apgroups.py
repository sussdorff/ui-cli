"""AP Group (Broadcasting Group) management commands for local controller."""

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
    print_success,
)

app = typer.Typer(name="apgroups", help="AP Group (broadcasting) management", no_args_is_help=True)


def find_ap_group(
    groups: list[dict[str, Any]], identifier: str
) -> dict[str, Any] | None:
    """Find AP group by ID or name."""
    identifier_lower = identifier.lower()

    # First try exact ID match
    for g in groups:
        if g.get("_id") == identifier:
            return g

    # Try exact name match
    for g in groups:
        name = g.get("name", "").lower()
        if name == identifier_lower:
            return g

    # Try partial name match
    for g in groups:
        name = g.get("name", "").lower()
        if identifier_lower in name:
            return g

    return None


def find_device(
    devices: list[dict[str, Any]], identifier: str
) -> dict[str, Any] | None:
    """Find device by MAC, name, or IP."""
    identifier_lower = identifier.lower().replace("-", ":")

    for d in devices:
        # Match by MAC
        if d.get("mac", "").lower() == identifier_lower:
            return d
        # Match by name
        if d.get("name", "").lower() == identifier_lower:
            return d
        # Match by IP
        if d.get("ip", "") == identifier:
            return d

    # Partial name match
    for d in devices:
        if identifier_lower in d.get("name", "").lower():
            return d

    return None


@app.command("list")
def list_groups(
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
    all_groups: Annotated[
        bool,
        typer.Option("--all", "-a", help="Show all groups including system groups"),
    ] = False,
) -> None:
    """List all AP groups (broadcasting groups).

    AP groups determine which WLANs are broadcast on which Access Points.
    By default, system-managed groups (like 'All APs') are hidden.
    """

    async def _list():
        client = UniFiLocalClient()
        groups = await client.get_ap_groups()
        devices = await client.get_devices()
        return groups, devices

    try:
        groups, devices = run_with_spinner(_list(), "Fetching AP groups...")
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if not groups:
        console.print("[dim]No AP groups found[/dim]")
        return

    # Build device lookup
    device_lookup = {
        d.get("mac", "").lower(): d.get("name", d.get("mac", ""))
        for d in devices
        if d.get("type") == "uap"
    }

    # Filter out system groups unless --all
    if not all_groups:
        groups = [
            g for g in groups
            if not g.get("attr_hidden_id") and not g.get("for_wlanconf")
        ]

    if output == OutputFormat.JSON:
        output_json(groups)
    elif output == OutputFormat.CSV:
        columns = [
            ("_id", "ID"),
            ("name", "Name"),
            ("device_count", "Devices"),
        ]
        csv_data = []
        for g in groups:
            csv_data.append({
                "_id": g.get("_id", ""),
                "name": g.get("name", ""),
                "device_count": len(g.get("device_macs", [])),
            })
        output_csv(csv_data, columns)
    else:
        from rich.table import Table

        table = Table(title="AP Groups", show_header=True, header_style="bold cyan")
        table.add_column("Name")
        table.add_column("Devices", justify="right")
        table.add_column("Access Points")

        for g in groups:
            name = g.get("name", "")
            device_macs = g.get("device_macs", [])
            device_count = str(len(device_macs))

            # Resolve device names
            ap_names = []
            for mac in device_macs[:5]:  # Show max 5
                ap_name = device_lookup.get(mac.lower(), mac)
                ap_names.append(ap_name)
            if len(device_macs) > 5:
                ap_names.append(f"... +{len(device_macs) - 5} more")

            table.add_row(name, device_count, ", ".join(ap_names) if ap_names else "-")

        console.print(table)
        console.print(f"\n[dim]{len(groups)} group(s)[/dim]")


@app.command("get")
def get_group(
    identifier: Annotated[str, typer.Argument(help="AP group ID or name")],
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
) -> None:
    """Get detailed AP group information."""

    async def _get():
        client = UniFiLocalClient()
        groups = await client.get_ap_groups()
        devices = await client.get_devices()
        return find_ap_group(groups, identifier), devices

    try:
        group, devices = run_with_spinner(_get(), "Finding AP group...")
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if not group:
        print_error(f"AP group '{identifier}' not found")
        raise typer.Exit(1)

    if output == OutputFormat.JSON:
        output_json(group)
        return

    # Build device lookup
    device_lookup = {
        d.get("mac", "").lower(): d
        for d in devices
        if d.get("type") == "uap"
    }

    # Table output
    from rich.table import Table

    name = group.get("name", "Unknown")
    console.print()
    console.print(f"[bold cyan]AP Group: {name}[/bold cyan]")
    console.print("-" * 40)
    console.print()

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="dim")
    table.add_column("Value")

    table.add_row("ID:", group.get("_id", ""))
    table.add_row("Name:", name)

    device_macs = group.get("device_macs", [])
    table.add_row("Device Count:", str(len(device_macs)))

    console.print(table)

    if device_macs:
        console.print()
        console.print("[bold]Access Points:[/bold]")

        ap_table = Table(show_header=True, header_style="bold")
        ap_table.add_column("Name")
        ap_table.add_column("MAC")
        ap_table.add_column("Model")
        ap_table.add_column("IP")

        for mac in device_macs:
            device = device_lookup.get(mac.lower())
            if device:
                ap_table.add_row(
                    device.get("name", "-"),
                    mac,
                    device.get("model", "-"),
                    device.get("ip", "-"),
                )
            else:
                ap_table.add_row("-", mac, "-", "-")

        console.print(ap_table)

    console.print()


@app.command("create")
def create_group(
    name: Annotated[str, typer.Argument(help="Name for the new AP group")],
    devices: Annotated[
        list[str] | None,
        typer.Option("--device", "-d", help="Device MAC, name, or IP to add (can be repeated)"),
    ] = None,
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
) -> None:
    """Create a new AP group."""

    async def _create():
        client = UniFiLocalClient()

        # Resolve device identifiers to MACs
        device_macs = []
        if devices:
            all_devices = await client.get_devices()
            aps = [d for d in all_devices if d.get("type") == "uap"]

            for dev_id in devices:
                device = find_device(aps, dev_id)
                if not device:
                    raise LocalAPIError(f"Device '{dev_id}' not found")
                device_macs.append(device.get("mac", "").lower())

        return await client.create_ap_group(name, device_macs)

    try:
        group = run_with_spinner(_create(), "Creating AP group...")
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if output == OutputFormat.JSON:
        output_json(group)
    else:
        print_success(f"Created AP group '{name}'")
        if devices:
            console.print(f"  [dim]Devices:[/dim] {len(devices)}")


@app.command("delete")
def delete_group(
    identifier: Annotated[str, typer.Argument(help="AP group ID or name")],
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation"),
    ] = False,
) -> None:
    """Delete an AP group."""

    async def _get_group():
        client = UniFiLocalClient()
        groups = await client.get_ap_groups()
        return find_ap_group(groups, identifier)

    try:
        group = run_with_spinner(_get_group(), "Finding AP group...")
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if not group:
        print_error(f"AP group '{identifier}' not found")
        raise typer.Exit(1)

    name = group.get("name", identifier)
    group_id = group.get("_id", "")

    # Check if group can be deleted
    if group.get("attr_no_delete"):
        print_error(f"AP group '{name}' cannot be deleted (system group)")
        raise typer.Exit(1)

    if not yes:
        confirm = typer.confirm(f"Delete AP group '{name}'?")
        if not confirm:
            console.print("[dim]Cancelled[/dim]")
            raise typer.Exit(0)

    async def _delete():
        client = UniFiLocalClient()
        return await client.delete_ap_group(group_id)

    try:
        success = run_with_spinner(_delete(), "Deleting AP group...")
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if success:
        print_success(f"Deleted AP group '{name}'")
    else:
        print_error(f"Failed to delete AP group '{name}'")
        raise typer.Exit(1)


@app.command("add-device")
def add_device(
    group: Annotated[str, typer.Argument(help="AP group ID or name")],
    device: Annotated[str, typer.Argument(help="Device MAC, name, or IP to add")],
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
) -> None:
    """Add a device to an AP group."""

    async def _add():
        client = UniFiLocalClient()
        groups = await client.get_ap_groups()
        devices = await client.get_devices()

        ap_group = find_ap_group(groups, group)
        if not ap_group:
            raise LocalAPIError(f"AP group '{group}' not found")

        aps = [d for d in devices if d.get("type") == "uap"]
        ap = find_device(aps, device)
        if not ap:
            raise LocalAPIError(f"Device '{device}' not found")

        device_mac = ap.get("mac", "").lower()
        current_macs = [m.lower() for m in ap_group.get("device_macs", [])]

        if device_mac in current_macs:
            raise LocalAPIError(f"Device '{ap.get('name', device)}' is already in group")

        new_macs = current_macs + [device_mac]
        return await client.update_ap_group(
            ap_group.get("_id", ""),
            ap_group.get("name", ""),
            new_macs,
        ), ap.get("name", device)

    try:
        updated, device_name = run_with_spinner(_add(), "Adding device to group...")
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if output == OutputFormat.JSON:
        output_json(updated)
    else:
        print_success(f"Added '{device_name}' to AP group '{updated.get('name', group)}'")


@app.command("remove-device")
def remove_device(
    group: Annotated[str, typer.Argument(help="AP group ID or name")],
    device: Annotated[str, typer.Argument(help="Device MAC, name, or IP to remove")],
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
) -> None:
    """Remove a device from an AP group."""

    async def _remove():
        client = UniFiLocalClient()
        groups = await client.get_ap_groups()
        devices = await client.get_devices()

        ap_group = find_ap_group(groups, group)
        if not ap_group:
            raise LocalAPIError(f"AP group '{group}' not found")

        aps = [d for d in devices if d.get("type") == "uap"]
        ap = find_device(aps, device)
        if not ap:
            raise LocalAPIError(f"Device '{device}' not found")

        device_mac = ap.get("mac", "").lower()
        current_macs = [m.lower() for m in ap_group.get("device_macs", [])]

        if device_mac not in current_macs:
            raise LocalAPIError(f"Device '{ap.get('name', device)}' is not in group")

        new_macs = [m for m in current_macs if m != device_mac]
        return await client.update_ap_group(
            ap_group.get("_id", ""),
            ap_group.get("name", ""),
            new_macs,
        ), ap.get("name", device)

    try:
        updated, device_name = run_with_spinner(_remove(), "Removing device from group...")
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if output == OutputFormat.JSON:
        output_json(updated)
    else:
        print_success(f"Removed '{device_name}' from AP group '{updated.get('name', group)}'")
