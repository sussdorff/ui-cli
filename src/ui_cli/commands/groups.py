"""Client groups management commands."""

import typer
from rich.console import Console

from ui_cli.groups import GroupManager, AutoGroupRules
from ui_cli.output import output_table, output_json, output_csv

app = typer.Typer(
    name="groups",
    help="Manage client groups for bulk actions",
    no_args_is_help=True,
)

console = Console()

# Column definitions for output
GROUP_COLUMNS = [
    ("name", "Name"),
    ("type", "Type"),
    ("member_count", "Members"),
    ("description", "Description"),
]

MEMBER_COLUMNS = [
    ("alias", "Alias"),
    ("mac", "MAC"),
]


# -----------------------------------------------------------------------------
# Group CRUD Commands
# -----------------------------------------------------------------------------


@app.command("list")
def list_groups(
    output: str = typer.Option("table", "-o", "--output", help="Output format"),
) -> None:
    """List all groups."""
    gm = GroupManager()
    groups = gm.list_groups()

    data = []
    for slug, group in groups:
        member_count: str | int = len(group.members) if group.members else 0
        if group.type == "auto":
            member_count = "(auto)"
        data.append({
            "slug": slug,
            "name": group.name,
            "type": group.type,
            "member_count": member_count,
            "description": group.description or "",
        })

    if output == "json":
        output_json(data)
    elif output == "csv":
        output_csv(data, GROUP_COLUMNS)
    else:
        if not data:
            console.print("[dim]No groups defined. Create one with:[/dim]")
            console.print("  ./ui groups create \"My Group\"")
            return
        output_table(data, GROUP_COLUMNS)


# Alias for list
@app.command("ls", hidden=True)
def list_groups_alias(
    output: str = typer.Option("table", "-o", "--output"),
) -> None:
    """List all groups (alias for list)."""
    list_groups(output=output)


@app.command("create")
def create_group(
    name: str = typer.Argument(..., help="Group name"),
    description: str = typer.Option(None, "-d", "--description", help="Description"),
) -> None:
    """Create a static group."""
    gm = GroupManager()
    try:
        slug, group = gm.create_group(name, description)
        console.print(f"[green]Created group:[/green] {group.name} [dim]({slug})[/dim]")
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("show")
def show_group(
    name: str = typer.Argument(..., help="Group name or slug"),
    output: str = typer.Option("table", "-o", "--output", help="Output format"),
) -> None:
    """Show group details and members."""
    gm = GroupManager()
    result = gm.get_group(name)

    if not result:
        console.print(f"[red]Error:[/red] Group '{name}' not found")
        raise typer.Exit(1)

    slug, group = result

    if output == "json":
        output_json({"slug": slug, **group.model_dump()})
        return

    # Header info
    console.print(f"\n[bold]Group:[/bold] {group.name}")
    console.print(f"[bold]Type:[/bold] {group.type}")
    if group.description:
        console.print(f"[bold]Description:[/bold] {group.description}")

    if group.type == "auto" and group.rules:
        console.print("\n[bold]Rules:[/bold]")
        rules = group.rules.model_dump(exclude_none=True)
        for key, values in rules.items():
            console.print(f"  {key}: {', '.join(values)}")
        console.print("\n[dim]Use './ui lo clients list -g {slug}' to see matching clients[/dim]")

    if group.type == "static":
        console.print(f"[bold]Members:[/bold] {len(group.members or [])}")
        console.print(f"[bold]Created:[/bold] {group.created_at:%Y-%m-%d %H:%M}")
        console.print(f"[bold]Updated:[/bold] {group.updated_at:%Y-%m-%d %H:%M}")

        if group.members:
            console.print()
            member_data = [
                {"alias": m.alias or "-", "mac": m.mac}
                for m in group.members
            ]
            output_table(member_data, MEMBER_COLUMNS)
        else:
            console.print("\n[dim]No members. Add with:[/dim]")
            console.print(f"  ./ui groups add {slug} <mac-address>")


@app.command("delete")
def delete_group(
    name: str = typer.Argument(..., help="Group name or slug"),
    yes: bool = typer.Option(False, "-y", "--yes", help="Skip confirmation"),
) -> None:
    """Delete a group."""
    gm = GroupManager()
    result = gm.get_group(name)

    if not result:
        console.print(f"[red]Error:[/red] Group '{name}' not found")
        raise typer.Exit(1)

    slug, group = result

    if not yes:
        confirm = typer.confirm(f"Delete group '{group.name}'?")
        if not confirm:
            raise typer.Abort()

    gm.delete_group(slug)
    console.print(f"[green]Deleted group:[/green] {group.name}")


# Alias for delete
@app.command("rm", hidden=True)
def delete_group_alias(
    name: str = typer.Argument(..., help="Group name or slug"),
    yes: bool = typer.Option(False, "-y", "--yes"),
) -> None:
    """Delete a group (alias for delete)."""
    delete_group(name=name, yes=yes)


# -----------------------------------------------------------------------------
# Group Edit Command
# -----------------------------------------------------------------------------


@app.command("edit")
def edit_group(
    name: str = typer.Argument(..., help="Group name or slug"),
    new_name: str = typer.Option(None, "-n", "--name", help="New name"),
    description: str = typer.Option(None, "-d", "--description", help="New description"),
) -> None:
    """Edit group name or description."""
    gm = GroupManager()

    if not new_name and description is None:
        console.print("[red]Error:[/red] Specify --name or --description")
        raise typer.Exit(1)

    try:
        slug, group = gm.update_group(
            name,
            new_name=new_name,
            description=description if description is not None else ...,
        )
        console.print(f"[green]Updated group:[/green] {group.name} [dim]({slug})[/dim]")
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


# -----------------------------------------------------------------------------
# Member CRUD Commands
# -----------------------------------------------------------------------------


@app.command("add")
def add_members(
    group: str = typer.Argument(..., help="Group name or slug"),
    clients: list[str] = typer.Argument(..., help="Client MAC addresses"),
    alias: str = typer.Option(None, "-a", "--alias", help="Alias (single client only)"),
) -> None:
    """Add member(s) to a static group."""
    gm = GroupManager()
    result = gm.get_group(group)

    if not result:
        console.print(f"[red]Error:[/red] Group '{group}' not found")
        raise typer.Exit(1)

    _, grp = result
    if grp.type != "static":
        console.print("[red]Error:[/red] Cannot add members to auto groups")
        console.print("[dim]Auto groups use rules to match clients dynamically[/dim]")
        raise typer.Exit(1)

    if alias and len(clients) > 1:
        console.print("[red]Error:[/red] --alias can only be used with a single client")
        raise typer.Exit(1)

    for client in clients:
        try:
            mac = GroupManager.normalize_mac(client)
            client_alias = alias if len(clients) == 1 else None
            gm.add_member(group, mac, client_alias)
            display = client_alias or mac
            console.print(f"[green]Added:[/green] {display}")
        except ValueError as e:
            console.print(f"[red]Error:[/red] {e}")


@app.command("remove")
def remove_members(
    group: str = typer.Argument(..., help="Group name or slug"),
    clients: list[str] = typer.Argument(..., help="Client MACs or aliases"),
) -> None:
    """Remove member(s) from a static group."""
    gm = GroupManager()

    result = gm.get_group(group)
    if not result:
        console.print(f"[red]Error:[/red] Group '{group}' not found")
        raise typer.Exit(1)

    for client in clients:
        try:
            if gm.remove_member(group, client):
                console.print(f"[green]Removed:[/green] {client}")
            else:
                console.print(f"[yellow]Not found:[/yellow] {client}")
        except ValueError as e:
            console.print(f"[red]Error:[/red] {e}")


@app.command("alias")
def set_alias(
    group: str = typer.Argument(..., help="Group name or slug"),
    client: str = typer.Argument(..., help="Client MAC or current alias"),
    alias: str = typer.Argument(None, help="New alias (omit to clear)"),
    clear: bool = typer.Option(False, "--clear", help="Clear the alias"),
) -> None:
    """Set or clear a member's alias."""
    gm = GroupManager()

    new_alias = None if clear else alias

    try:
        if gm.update_member(group, client, alias=new_alias):
            if new_alias:
                console.print(f"[green]Set alias:[/green] {new_alias}")
            else:
                console.print(f"[green]Cleared alias for:[/green] {client}")
        else:
            console.print(f"[red]Error:[/red] Member not found: {client}")
            raise typer.Exit(1)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("members")
def list_members(
    group: str = typer.Argument(..., help="Group name or slug"),
    output: str = typer.Option("table", "-o", "--output", help="Output format"),
) -> None:
    """List group members."""
    gm = GroupManager()

    result = gm.get_group(group)
    if not result:
        console.print(f"[red]Error:[/red] Group '{group}' not found")
        raise typer.Exit(1)

    _, grp = result

    if grp.type != "static":
        console.print("[yellow]Auto groups have dynamic membership based on rules[/yellow]")
        console.print(f"Use: ./ui lo clients list -g {group}")
        return

    try:
        members = gm.list_members(group)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    data = [{"alias": m.alias or "-", "mac": m.mac} for m in members]

    if output == "json":
        output_json(data)
    elif output == "csv":
        output_csv(data, MEMBER_COLUMNS)
    else:
        if not data:
            console.print("[dim]No members in group[/dim]")
            return
        output_table(data, MEMBER_COLUMNS)


@app.command("clear")
def clear_members(
    group: str = typer.Argument(..., help="Group name or slug"),
    yes: bool = typer.Option(False, "-y", "--yes", help="Skip confirmation"),
) -> None:
    """Remove all members from a static group."""
    gm = GroupManager()

    result = gm.get_group(group)
    if not result:
        console.print(f"[red]Error:[/red] Group '{group}' not found")
        raise typer.Exit(1)

    _, grp = result
    member_count = len(grp.members or [])

    if member_count == 0:
        console.print("[dim]Group has no members[/dim]")
        return

    if not yes:
        confirm = typer.confirm(f"Remove all {member_count} members from '{grp.name}'?")
        if not confirm:
            raise typer.Abort()

    try:
        gm.clear_members(group)
        console.print(f"[green]Cleared {member_count} members[/green]")
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


# -----------------------------------------------------------------------------
# Auto Group Command
# -----------------------------------------------------------------------------


@app.command("auto")
def create_auto_group(
    name: str = typer.Argument(..., help="Group name"),
    vendor: list[str] = typer.Option(None, "--vendor", help="Vendor/OUI patterns"),
    name_pattern: list[str] = typer.Option(None, "--name", help="Client name patterns"),
    hostname: list[str] = typer.Option(None, "--hostname", help="Hostname patterns"),
    network: list[str] = typer.Option(None, "--network", help="Network/SSID names"),
    ip: list[str] = typer.Option(None, "--ip", help="IP patterns/ranges"),
    mac: list[str] = typer.Option(None, "--mac", help="MAC prefix patterns"),
    conn_type: list[str] = typer.Option(None, "--type", help="Connection type: wired, wireless"),
    description: str = typer.Option(None, "-d", "--description", help="Description"),
    dry_run: bool = typer.Option(False, "--dry-run", "--preview", help="Preview without creating"),
) -> None:
    """Create an auto group with pattern rules.

    Auto groups dynamically match clients based on rules.
    Multiple rules of the same type use OR logic.
    Different rule types use AND logic.

    Pattern syntax:
      - Exact: "Apple"
      - Wildcard: "*phone*", "iPhone*"
      - Regex: "~^iPhone-[0-9]+"
      - Multiple: "Apple,Samsung" (comma-separated)

    Examples:
      ./ui groups auto "Apple Devices" --vendor "Apple"
      ./ui groups auto "IoT" --vendor "Philips,LIFX,Ring"
      ./ui groups auto "Cameras" --name "*camera*,*cam*"
      ./ui groups auto "Guest WiFi" --network "Guest"
      ./ui groups auto "Servers" --ip "192.168.1.100-200"
    """
    # Build rules
    rules = AutoGroupRules(
        vendor=vendor,
        name=name_pattern,
        hostname=hostname,
        network=network,
        ip=ip,
        mac=mac,
        conn_type=conn_type,
    )

    # Check at least one rule specified
    if not any([vendor, name_pattern, hostname, network, ip, mac, conn_type]):
        console.print("[red]Error:[/red] Specify at least one rule")
        console.print("[dim]Available: --vendor, --name, --hostname, --network, --ip, --mac, --type[/dim]")
        raise typer.Exit(1)

    gm = GroupManager()

    # Show rules
    rules_dict = rules.model_dump(exclude_none=True)

    if dry_run:
        console.print(f"\n[bold]Preview:[/bold] Auto group '{name}'")
        if description:
            console.print(f"[bold]Description:[/bold] {description}")
        console.print("\n[bold]Rules:[/bold]")
        for key, val in rules_dict.items():
            console.print(f"  {key}: {', '.join(val)}")
        console.print("\n[yellow]Dry run - group not created[/yellow]")
        console.print("Run without --dry-run to create")
        return

    try:
        slug, group = gm.create_group(name, description, "auto", rules)
        console.print(f"[green]Created auto group:[/green] {group.name} [dim]({slug})[/dim]")
        console.print("\n[bold]Rules:[/bold]")
        for key, val in rules_dict.items():
            console.print(f"  {key}: {', '.join(val)}")
        console.print(f"\n[dim]View matches: ./ui lo clients list -g {slug}[/dim]")
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


# -----------------------------------------------------------------------------
# Import/Export Commands
# -----------------------------------------------------------------------------


@app.command("export")
def export_groups(
    output_file: str = typer.Option(None, "-o", "--output", help="Output file path"),
) -> None:
    """Export all groups to JSON."""
    gm = GroupManager()
    data = gm.export_groups()

    if output_file:
        from pathlib import Path
        Path(output_file).write_text(
            __import__("json").dumps(data, indent=2, default=str)
        )
        console.print(f"[green]Exported to:[/green] {output_file}")
    else:
        output_json(data)


@app.command("import")
def import_groups(
    input_file: str = typer.Argument(..., help="JSON file to import"),
    replace: bool = typer.Option(False, "--replace", help="Replace all existing groups"),
    yes: bool = typer.Option(False, "-y", "--yes", help="Skip confirmation"),
) -> None:
    """Import groups from JSON file."""
    from pathlib import Path
    import json

    path = Path(input_file)
    if not path.exists():
        console.print(f"[red]Error:[/red] File not found: {input_file}")
        raise typer.Exit(1)

    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        console.print(f"[red]Error:[/red] Invalid JSON: {e}")
        raise typer.Exit(1)

    group_count = len(data.get("groups", {}))

    if replace and not yes:
        confirm = typer.confirm(f"Replace all groups with {group_count} from file?")
        if not confirm:
            raise typer.Abort()

    gm = GroupManager()
    imported = gm.import_groups(data, replace=replace)
    action = "Replaced with" if replace else "Imported"
    console.print(f"[green]{action} {imported} groups[/green]")
