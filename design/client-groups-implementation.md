# Client Groups Implementation Plan

## Summary

| Phase | Description | Files | Complexity |
|-------|-------------|-------|------------|
| 1 | Core Infrastructure | `groups.py` (new) | Medium |
| 2 | Basic Commands | `commands/groups.py` (new), `main.py` | Simple |
| 3 | Member Management | `commands/groups.py` | Medium |
| 4 | Group Editing | `commands/groups.py` | Simple |
| 5 | Auto Groups | `groups.py`, `commands/groups.py` | Complex |
| 6 | Bulk Actions | `commands/local/clients.py` | Medium |
| 7 | MCP Integration | `ui_mcp/server.py` | Simple |

---

## Phase 1: Core Infrastructure

**Goal**: Create GroupManager class and storage layer

### New File: `src/ui_cli/groups.py`

```python
from pathlib import Path
from datetime import datetime, timezone
from typing import Literal
import json
import re
import fnmatch
from pydantic import BaseModel


class GroupMember(BaseModel):
    mac: str
    alias: str | None = None


class AutoGroupRules(BaseModel):
    vendor: list[str] | None = None
    name: list[str] | None = None
    hostname: list[str] | None = None
    network: list[str] | None = None
    ip: list[str] | None = None
    mac: list[str] | None = None
    conn_type: list[str] | None = None  # "wired" or "wireless"


class Group(BaseModel):
    name: str
    description: str | None = None
    type: Literal["static", "auto"] = "static"
    members: list[GroupMember] | None = None  # For static groups
    rules: AutoGroupRules | None = None       # For auto groups
    created_at: datetime
    updated_at: datetime


class GroupsFile(BaseModel):
    version: int = 1
    groups: dict[str, Group] = {}


class GroupManager:
    """Manages client groups stored in ~/.config/ui-cli/groups.json"""

    def __init__(self):
        self._path = Path.home() / ".config" / "ui-cli" / "groups.json"
        self._data: GroupsFile | None = None

    @property
    def data(self) -> GroupsFile:
        if self._data is None:
            self._load()
        return self._data

    def _load(self) -> None:
        """Load groups from disk."""
        if self._path.exists():
            raw = json.loads(self._path.read_text())
            self._data = GroupsFile(**raw)
        else:
            self._data = GroupsFile()

    def _save(self) -> None:
        """Save groups to disk."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(self.data.model_dump(), indent=2, default=str)
        )

    @staticmethod
    def slugify(name: str) -> str:
        """Convert display name to slug: 'Kids Devices' -> 'kids-devices'"""
        slug = name.lower().strip()
        slug = re.sub(r"[^a-z0-9]+", "-", slug)
        return slug.strip("-")

    @staticmethod
    def normalize_mac(mac: str) -> str:
        """Normalize MAC address to uppercase with colons."""
        mac = mac.upper().replace("-", ":").replace(".", ":")
        # Handle formats like AABBCCDDEEFF
        if ":" not in mac and len(mac) == 12:
            mac = ":".join(mac[i:i+2] for i in range(0, 12, 2))
        return mac

    def _resolve_group(self, name_or_slug: str) -> str | None:
        """Resolve name or slug to slug, return None if not found."""
        slug = self.slugify(name_or_slug)
        if slug in self.data.groups:
            return slug
        # Try exact name match
        for s, g in self.data.groups.items():
            if g.name.lower() == name_or_slug.lower():
                return s
        return None

    # --- Group CRUD ---

    def list_groups(self) -> list[tuple[str, Group]]:
        """List all groups as (slug, Group) tuples."""
        return list(self.data.groups.items())

    def get_group(self, name_or_slug: str) -> tuple[str, Group] | None:
        """Get group by name or slug. Returns (slug, Group) or None."""
        slug = self._resolve_group(name_or_slug)
        if slug:
            return (slug, self.data.groups[slug])
        return None

    def create_group(
        self,
        name: str,
        description: str | None = None,
        group_type: Literal["static", "auto"] = "static",
        rules: AutoGroupRules | None = None,
    ) -> tuple[str, Group]:
        """Create a new group. Returns (slug, Group)."""
        slug = self.slugify(name)
        if slug in self.data.groups:
            raise ValueError(f"Group '{name}' already exists")

        now = datetime.now(timezone.utc)
        group = Group(
            name=name,
            description=description,
            type=group_type,
            members=[] if group_type == "static" else None,
            rules=rules if group_type == "auto" else None,
            created_at=now,
            updated_at=now,
        )
        self.data.groups[slug] = group
        self._save()
        return (slug, group)

    def delete_group(self, name_or_slug: str) -> bool:
        """Delete a group. Returns True if deleted."""
        slug = self._resolve_group(name_or_slug)
        if not slug:
            return False
        del self.data.groups[slug]
        self._save()
        return True

    def update_group(
        self,
        name_or_slug: str,
        new_name: str | None = None,
        description: str | None = ...,  # Use ... to distinguish from None
    ) -> tuple[str, Group]:
        """Update group name/description. Returns (slug, Group)."""
        slug = self._resolve_group(name_or_slug)
        if not slug:
            raise ValueError(f"Group '{name_or_slug}' not found")

        group = self.data.groups[slug]

        if new_name:
            group.name = new_name
            new_slug = self.slugify(new_name)
            if new_slug != slug:
                self.data.groups[new_slug] = group
                del self.data.groups[slug]
                slug = new_slug

        if description is not ...:
            group.description = description

        group.updated_at = datetime.now(timezone.utc)
        self._save()
        return (slug, group)

    # --- Member CRUD Operations (Static Groups) ---

    def add_member(
        self,
        name_or_slug: str,
        mac: str,
        alias: str | None = None,
    ) -> Group:
        """Add a member to a static group."""
        slug = self._resolve_group(name_or_slug)
        if not slug:
            raise ValueError(f"Group '{name_or_slug}' not found")

        group = self.data.groups[slug]
        if group.type != "static":
            raise ValueError("Cannot add members to auto groups")

        mac = self.normalize_mac(mac)

        # Check if already exists - update alias if so
        if group.members:
            for member in group.members:
                if member.mac == mac:
                    if alias:
                        member.alias = alias
                    self._save()
                    return group

        if group.members is None:
            group.members = []
        group.members.append(GroupMember(mac=mac, alias=alias))
        group.updated_at = datetime.now(timezone.utc)
        self._save()
        return group

    def get_member(self, name_or_slug: str, identifier: str) -> GroupMember | None:
        """Get a member by MAC or alias."""
        slug = self._resolve_group(name_or_slug)
        if not slug:
            raise ValueError(f"Group '{name_or_slug}' not found")

        group = self.data.groups[slug]
        if group.type != "static" or not group.members:
            return None

        identifier_mac = self.normalize_mac(identifier)
        for member in group.members:
            if member.mac == identifier_mac or member.alias == identifier:
                return member
        return None

    def update_member(
        self,
        name_or_slug: str,
        identifier: str,
        alias: str | None = ...,
    ) -> bool:
        """Update a member's alias. Returns True if updated."""
        slug = self._resolve_group(name_or_slug)
        if not slug:
            raise ValueError(f"Group '{name_or_slug}' not found")

        group = self.data.groups[slug]
        if group.type != "static" or not group.members:
            return False

        identifier_mac = self.normalize_mac(identifier)
        for member in group.members:
            if member.mac == identifier_mac or member.alias == identifier:
                if alias is not ...:
                    member.alias = alias
                group.updated_at = datetime.now(timezone.utc)
                self._save()
                return True
        return False

    def remove_member(self, name_or_slug: str, identifier: str) -> bool:
        """Remove a member by MAC or alias. Returns True if removed."""
        slug = self._resolve_group(name_or_slug)
        if not slug:
            raise ValueError(f"Group '{name_or_slug}' not found")

        group = self.data.groups[slug]
        if group.type != "static" or not group.members:
            return False

        identifier_mac = self.normalize_mac(identifier)
        for i, member in enumerate(group.members):
            if member.mac == identifier_mac or member.alias == identifier:
                group.members.pop(i)
                group.updated_at = datetime.now(timezone.utc)
                self._save()
                return True
        return False

    def list_members(self, name_or_slug: str) -> list[GroupMember]:
        """List all members in a static group."""
        slug = self._resolve_group(name_or_slug)
        if not slug:
            raise ValueError(f"Group '{name_or_slug}' not found")

        group = self.data.groups[slug]
        if group.type != "static":
            raise ValueError("Auto groups have dynamic membership")
        return group.members or []

    def clear_members(self, name_or_slug: str) -> bool:
        """Clear all members from a static group."""
        slug = self._resolve_group(name_or_slug)
        if not slug:
            raise ValueError(f"Group '{name_or_slug}' not found")

        group = self.data.groups[slug]
        if group.type != "static":
            raise ValueError("Cannot clear members from auto groups")

        group.members = []
        group.updated_at = datetime.now(timezone.utc)
        self._save()
        return True

    def get_member_macs(self, name_or_slug: str) -> list[str]:
        """Get list of MAC addresses in a static group."""
        result = self.get_group(name_or_slug)
        if not result:
            raise ValueError(f"Group '{name_or_slug}' not found")
        _, group = result
        if group.type != "static" or not group.members:
            return []
        return [m.mac for m in group.members]

    # --- Auto Group Operations ---

    def set_rules(self, name_or_slug: str, rules: AutoGroupRules) -> Group:
        """Set rules for an auto group."""
        slug = self._resolve_group(name_or_slug)
        if not slug:
            raise ValueError(f"Group '{name_or_slug}' not found")

        group = self.data.groups[slug]
        if group.type != "auto":
            raise ValueError("Cannot set rules on static groups")

        group.rules = rules
        group.updated_at = datetime.now(timezone.utc)
        self._save()
        return group

    @staticmethod
    def pattern_matches(pattern: str, value: str | None) -> bool:
        """Check if value matches pattern.

        Pattern syntax:
        - Exact: "Apple"
        - Wildcard: "*phone*" (uses fnmatch)
        - Regex: "~^iPhone-[0-9]+" (prefix with ~)
        - Multiple: "Apple,Samsung" (comma-separated, OR logic)
        """
        if not pattern or not value:
            return False

        # Handle multiple patterns (OR logic)
        if "," in pattern and not pattern.startswith("~"):
            patterns = [p.strip() for p in pattern.split(",")]
            return any(GroupManager.pattern_matches(p, value) for p in patterns)

        # Regex pattern (prefix with ~)
        if pattern.startswith("~"):
            try:
                return bool(re.search(pattern[1:], value, re.IGNORECASE))
            except re.error:
                return False

        # Wildcard pattern
        if "*" in pattern or "?" in pattern:
            return fnmatch.fnmatch(value.lower(), pattern.lower())

        # Exact match (case-insensitive)
        return value.lower() == pattern.lower()

    @staticmethod
    def ip_matches(pattern: str, ip: str | None) -> bool:
        """Check if IP matches pattern (CIDR, range, or wildcard)."""
        if not pattern or not ip:
            return False

        import ipaddress

        # CIDR notation: 192.168.1.0/24
        if "/" in pattern:
            try:
                network = ipaddress.ip_network(pattern, strict=False)
                return ipaddress.ip_address(ip) in network
            except ValueError:
                return False

        # Range: 192.168.1.100-200
        if "-" in pattern and not pattern.startswith("-"):
            try:
                base, end = pattern.rsplit("-", 1)
                if "." in end:
                    # Full IP range: 192.168.1.100-192.168.1.200
                    start_ip = ipaddress.ip_address(base)
                    end_ip = ipaddress.ip_address(end)
                else:
                    # Partial range: 192.168.1.100-200
                    start_ip = ipaddress.ip_address(base)
                    base_parts = base.rsplit(".", 1)
                    end_ip = ipaddress.ip_address(f"{base_parts[0]}.{end}")
                target = ipaddress.ip_address(ip)
                return start_ip <= target <= end_ip
            except ValueError:
                return False

        # Wildcard: 192.168.1.*
        return GroupManager.pattern_matches(pattern, ip)

    def evaluate_auto_group(
        self,
        name_or_slug: str,
        clients: list[dict],
    ) -> list[dict]:
        """Evaluate auto group rules against client list."""
        result = self.get_group(name_or_slug)
        if not result:
            raise ValueError(f"Group '{name_or_slug}' not found")

        _, group = result
        if group.type != "auto" or not group.rules:
            return []

        matching = []
        for client in clients:
            if self._client_matches_rules(client, group.rules):
                matching.append(client)
        return matching

    def _client_matches_rules(self, client: dict, rules: AutoGroupRules) -> bool:
        """Check if client matches all rules (AND logic between rule types)."""
        # Vendor (OUI)
        if rules.vendor:
            oui = client.get("oui", "")
            if not any(self.pattern_matches(p, oui) for p in rules.vendor):
                return False

        # Client name
        if rules.name:
            name = client.get("name") or client.get("hostname") or ""
            if not any(self.pattern_matches(p, name) for p in rules.name):
                return False

        # Hostname
        if rules.hostname:
            hostname = client.get("hostname", "")
            if not any(self.pattern_matches(p, hostname) for p in rules.hostname):
                return False

        # Network/SSID
        if rules.network:
            network = client.get("essid") or client.get("network", "")
            if not any(self.pattern_matches(p, network) for p in rules.network):
                return False

        # IP address
        if rules.ip:
            ip = client.get("ip", "")
            if not any(self.ip_matches(p, ip) for p in rules.ip):
                return False

        # MAC prefix
        if rules.mac:
            mac = client.get("mac", "")
            if not any(mac.upper().startswith(p.upper()) for p in rules.mac):
                return False

        # Connection type
        if rules.conn_type:
            is_wired = client.get("is_wired", False)
            client_type = "wired" if is_wired else "wireless"
            if client_type not in [t.lower() for t in rules.conn_type]:
                return False

        return True

    # --- Import/Export ---

    def export_groups(self) -> dict:
        """Export all groups as dict."""
        return self.data.model_dump()

    def import_groups(self, data: dict, replace: bool = False) -> int:
        """Import groups from dict. Returns count of imported groups."""
        imported = GroupsFile(**data)
        if replace:
            self._data = imported
        else:
            for slug, group in imported.groups.items():
                self.data.groups[slug] = group
        self._save()
        return len(imported.groups)
```

### Complexity: Medium

---

## Phase 2: Basic Group Commands

**Goal**: Implement create, list, show, delete

### New File: `src/ui_cli/commands/groups.py`

```python
import typer
from rich.console import Console
from ui_cli.groups import GroupManager
from ui_cli.output import output_table, output_json, output_csv

app = typer.Typer(
    name="groups",
    help="Manage client groups for bulk actions",
    no_args_is_help=True,
)
console = Console()

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


@app.command("list")
@app.command("ls", hidden=True)
def list_groups(
    output: str = typer.Option("table", "-o", "--output"),
) -> None:
    """List all groups."""
    gm = GroupManager()
    groups = gm.list_groups()

    data = []
    for slug, group in groups:
        member_count = len(group.members) if group.members else 0
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


@app.command("create")
def create_group(
    name: str = typer.Argument(..., help="Group name"),
    description: str = typer.Option(None, "-d", "--description"),
) -> None:
    """Create a static group."""
    gm = GroupManager()
    try:
        slug, group = gm.create_group(name, description)
        console.print(f"[green]Created group:[/green] {group.name} ({slug})")
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("show")
def show_group(
    name: str = typer.Argument(..., help="Group name or slug"),
    output: str = typer.Option("table", "-o", "--output"),
) -> None:
    """Show group details and members."""
    gm = GroupManager()
    result = gm.get_group(name)

    if not result:
        console.print(f"[red]Error:[/red] Group '{name}' not found")
        raise typer.Exit(1)

    slug, group = result

    if output == "json":
        output_json(group.model_dump())
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


@app.command("delete")
@app.command("rm", hidden=True)
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
```

### Modify: `src/ui_cli/main.py`

Add registration:

```python
from ui_cli.commands import groups

app.add_typer(groups.app, name="groups")
```

### Complexity: Simple

---

## Phase 3: Member Management (CRUD)

**Goal**: Add, remove, update, list members

### Add to `src/ui_cli/commands/groups.py`:

```python
@app.command("add")
def add_members(
    group: str = typer.Argument(..., help="Group name or slug"),
    clients: list[str] = typer.Argument(..., help="Client names or MACs"),
    alias: str = typer.Option(None, "--alias", "-a", help="Alias (single client only)"),
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
        raise typer.Exit(1)

    if alias and len(clients) > 1:
        console.print("[red]Error:[/red] --alias can only be used with single client")
        raise typer.Exit(1)

    for client in clients:
        mac = GroupManager.normalize_mac(client)
        client_alias = alias if len(clients) == 1 else None
        gm.add_member(group, mac, client_alias)
        display = client_alias or mac
        console.print(f"[green]Added:[/green] {display}")


@app.command("remove")
def remove_members(
    group: str = typer.Argument(..., help="Group name or slug"),
    clients: list[str] = typer.Argument(..., help="Client MACs or aliases"),
) -> None:
    """Remove member(s) from a static group."""
    gm = GroupManager()

    for client in clients:
        if gm.remove_member(group, client):
            console.print(f"[green]Removed:[/green] {client}")
        else:
            console.print(f"[yellow]Not found:[/yellow] {client}")


@app.command("alias")
def set_alias(
    group: str = typer.Argument(..., help="Group name or slug"),
    client: str = typer.Argument(..., help="Client MAC or current alias"),
    alias: str = typer.Argument(None, help="New alias (omit to clear)"),
    clear: bool = typer.Option(False, "--clear", help="Clear alias"),
) -> None:
    """Set or clear a member's alias."""
    gm = GroupManager()
    new_alias = None if clear else alias

    if gm.update_member(group, client, alias=new_alias):
        if new_alias:
            console.print(f"[green]Set alias:[/green] {new_alias}")
        else:
            console.print(f"[green]Cleared alias for:[/green] {client}")
    else:
        console.print(f"[red]Error:[/red] Member not found: {client}")
        raise typer.Exit(1)


@app.command("members")
def list_members(
    group: str = typer.Argument(..., help="Group name or slug"),
    output: str = typer.Option("table", "-o", "--output"),
) -> None:
    """List group members."""
    gm = GroupManager()

    try:
        members = gm.list_members(group)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    data = [{"alias": m.alias or "-", "mac": m.mac} for m in members]

    if output == "json":
        output_json(data)
    else:
        if not data:
            console.print("[dim]No members in group[/dim]")
            return
        output_table(data, MEMBER_COLUMNS)


@app.command("clear")
def clear_members(
    group: str = typer.Argument(..., help="Group name or slug"),
    yes: bool = typer.Option(False, "-y", "--yes"),
) -> None:
    """Remove all members from a static group."""
    gm = GroupManager()

    if not yes:
        confirm = typer.confirm(f"Clear all members from '{group}'?")
        if not confirm:
            raise typer.Abort()

    try:
        gm.clear_members(group)
        console.print("[green]Cleared all members[/green]")
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
```

### Complexity: Medium

---

## Phase 4: Group Editing

### Add to `src/ui_cli/commands/groups.py`:

```python
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
        console.print(f"[green]Updated group:[/green] {group.name}")
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
```

### Complexity: Simple

---

## Phase 5: Auto Groups

### Add to `src/ui_cli/commands/groups.py`:

```python
@app.command("auto")
def create_auto_group(
    name: str = typer.Argument(..., help="Group name"),
    vendor: list[str] = typer.Option(None, "--vendor", help="Vendor patterns"),
    name_pattern: list[str] = typer.Option(None, "--name", help="Name patterns"),
    hostname: list[str] = typer.Option(None, "--hostname", help="Hostname patterns"),
    network: list[str] = typer.Option(None, "--network", help="Network/SSID"),
    ip: list[str] = typer.Option(None, "--ip", help="IP patterns/ranges"),
    mac: list[str] = typer.Option(None, "--mac", help="MAC prefixes"),
    conn_type: list[str] = typer.Option(None, "--type", help="wired or wireless"),
    description: str = typer.Option(None, "-d", "--description"),
    dry_run: bool = typer.Option(False, "--dry-run", "--preview"),
) -> None:
    """Create an auto group with pattern rules."""
    from ui_cli.groups import AutoGroupRules

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
        raise typer.Exit(1)

    gm = GroupManager()

    if dry_run:
        console.print(f"[bold]Preview:[/bold] Auto group '{name}'")
        console.print("[dim]Rules:[/dim]")
        for key, val in rules.model_dump(exclude_none=True).items():
            console.print(f"  {key}: {', '.join(val)}")
        console.print("\n[yellow]Dry run - group not created[/yellow]")
        return

    try:
        slug, group = gm.create_group(name, description, "auto", rules)
        console.print(f"[green]Created auto group:[/green] {group.name}")
        console.print("[dim]Rules:[/dim]")
        for key, val in rules.model_dump(exclude_none=True).items():
            console.print(f"  {key}: {', '.join(val)}")
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
```

### Complexity: Complex

---

## Phase 6: Bulk Actions Integration

### Modify: `src/ui_cli/commands/local/clients.py`

Add `--group` / `-g` option to: `list`, `block`, `unblock`, `kick`, `status`

```python
# Add to list_clients command
group: str = typer.Option(None, "-g", "--group", help="Filter by group"),

# Inside async function:
if group:
    from ui_cli.groups import GroupManager
    gm = GroupManager()
    result = gm.get_group(group)
    if not result:
        raise ValueError(f"Group not found: {group}")
    _, grp = result
    if grp.type == "static":
        member_macs = {m.mac.upper() for m in grp.members or []}
        clients = [c for c in clients if c.get("mac", "").upper() in member_macs]
    else:
        clients = gm.evaluate_auto_group(group, clients)
```

### Complexity: Medium

---

## Phase 7: MCP Integration

### Modify: `src/ui_mcp/server.py`

```python
@mcp.tool()
async def list_groups() -> str:
    """List all client groups."""
    return await run_cli("groups", "list", "-o", "json")

@mcp.tool()
async def get_group(name: str) -> str:
    """Get details of a client group."""
    return await run_cli("groups", "show", name, "-o", "json")

@mcp.tool()
async def block_group(name: str) -> str:
    """Block all clients in a group."""
    return await run_cli("lo", "clients", "block", "-g", name, "-y")

@mcp.tool()
async def unblock_group(name: str) -> str:
    """Unblock all clients in a group."""
    return await run_cli("lo", "clients", "unblock", "-g", name, "-y")
```

### Complexity: Simple

---

## Member CRUD Summary

| Operation | Command | Example |
|-----------|---------|---------|
| **Create** | `groups add` | `./ui groups add kids AA:BB:CC:DD:EE:FF --alias "Emma"` |
| **Read** | `groups members` | `./ui groups members kids` |
| **Read One** | `groups show` | `./ui groups show kids` (shows all members) |
| **Update** | `groups alias` | `./ui groups alias kids AA:BB:CC "New Name"` |
| **Delete** | `groups remove` | `./ui groups remove kids AA:BB:CC` |
| **Delete All** | `groups clear` | `./ui groups clear kids` |

---

## File Summary

| Phase | New Files | Modified Files |
|-------|-----------|----------------|
| 1 | `src/ui_cli/groups.py` | - |
| 2 | `src/ui_cli/commands/groups.py` | `src/ui_cli/main.py` |
| 3 | - | `src/ui_cli/commands/groups.py` |
| 4 | - | `src/ui_cli/commands/groups.py` |
| 5 | - | `src/ui_cli/commands/groups.py` |
| 6 | - | `src/ui_cli/commands/local/clients.py` |
| 7 | - | `src/ui_mcp/server.py` |

---

## Recommended Build Order

1. **Phase 1** - Core GroupManager
2. **Phase 2** - Basic commands (can test)
3. **Phase 3** - Member CRUD
4. **Phase 4** - Group editing
5. **Phase 6** - Bulk actions (static groups)
6. **Phase 5** - Auto groups
7. **Phase 7** - MCP integration

This order delivers usable features incrementally.
