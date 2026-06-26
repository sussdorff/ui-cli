"""Firewall commands for local controller."""

import ipaddress
from typing import Annotated, Any

import typer

from ui_cli.local_client import LocalAPIError, UniFiLocalClient
from ui_cli.output import (
    OutputFormat,
    console,
    output_csv,
    output_json,
    print_error,
    print_success,
)

app = typer.Typer(name="firewall", help="Firewall rules and groups", no_args_is_help=True)


# Ruleset display names
RULESET_NAMES = {
    "WAN_IN": "WAN In",
    "WAN_OUT": "WAN Out",
    "WAN_LOCAL": "WAN Local",
    "LAN_IN": "LAN In",
    "LAN_OUT": "LAN Out",
    "LAN_LOCAL": "LAN Local",
    "GUEST_IN": "Guest In",
    "GUEST_OUT": "Guest Out",
    "GUEST_LOCAL": "Guest Local",
}

VALID_ACTIONS = {"accept", "drop", "reject"}
VALID_PROTOCOLS = {"all", "tcp", "udp", "tcp_udp", "icmp"}


def format_action(action: str) -> tuple[str, str]:
    """Format action with color."""
    action_lower = action.lower()
    if action_lower == "accept":
        return "accept", "green"
    elif action_lower == "drop":
        return "drop", "red"
    elif action_lower == "reject":
        return "reject", "yellow"
    return action, "white"


def format_protocol(rule: dict[str, Any]) -> str:
    """Format protocol for display."""
    protocol = rule.get("protocol", "all")
    if protocol == "all":
        return "any"
    return protocol.upper()


def format_address(rule: dict[str, Any], prefix: str) -> str:
    """Format source or destination address."""
    # Check for network type
    net_type = rule.get(f"{prefix}_network_type", "")
    if net_type == "ADDRv4":
        addr = rule.get(f"{prefix}_address", "")
        return addr if addr else "any"

    # Check for firewall group
    group = rule.get(f"{prefix}_firewallgroup_ids", [])
    if group:
        return f"group:{len(group)}"

    # Check for specific network
    network = rule.get(f"{prefix}_network", "")
    if network:
        return network

    return "any"


def format_port(rule: dict[str, Any], prefix: str) -> str:
    """Format port information."""
    port = rule.get(f"{prefix}_port", "")
    if port:
        return str(port)
    return "*"


def get_ruleset_order(ruleset: str) -> int:
    """Get sort order for rulesets."""
    order = [
        "WAN_IN",
        "WAN_OUT",
        "WAN_LOCAL",
        "LAN_IN",
        "LAN_OUT",
        "LAN_LOCAL",
        "GUEST_IN",
        "GUEST_OUT",
        "GUEST_LOCAL",
    ]
    try:
        return order.index(ruleset)
    except ValueError:
        return 100


def normalize_ruleset(ruleset: str) -> str:
    """Normalize and validate a classic firewall ruleset name."""
    normalized = ruleset.upper().replace("-", "_")
    if normalized not in RULESET_NAMES:
        valid = ", ".join(RULESET_NAMES)
        raise ValueError(f"Unsupported ruleset '{ruleset}'. Valid rulesets: {valid}")
    return normalized


def normalize_action(action: str) -> str:
    """Normalize and validate a firewall action."""
    normalized = action.lower()
    if normalized not in VALID_ACTIONS:
        valid = ", ".join(sorted(VALID_ACTIONS))
        raise ValueError(f"Unsupported action '{action}'. Valid actions: {valid}")
    return normalized


def normalize_protocol(protocol: str) -> str:
    """Normalize and validate a firewall protocol."""
    normalized = protocol.lower().replace("-", "_")
    if normalized in ("any", "*"):
        normalized = "all"
    elif normalized == "both":
        normalized = "tcp_udp"
    if normalized not in VALID_PROTOCOLS:
        valid = ", ".join(sorted(VALID_PROTOCOLS))
        raise ValueError(f"Unsupported protocol '{protocol}'. Valid protocols: {valid}")
    return normalized


def normalize_address(value: str | None, label: str) -> str | None:
    """Normalize an IPv4 host or CIDR address for UniFi firewall payloads."""
    if value is None or value.lower() in ("", "any", "*"):
        return None

    try:
        network = ipaddress.ip_network(value, strict=False)
    except ValueError as exc:
        raise ValueError(f"Invalid {label} address '{value}'") from exc

    if network.version != 4:
        raise ValueError(f"Invalid {label} address '{value}': only IPv4 is supported")
    return str(network)


def normalize_port(value: str | None, label: str) -> str | None:
    """Normalize a port list/range string."""
    if value is None or value.lower() in ("", "any", "*"):
        return None

    parts = [part.strip() for part in value.split(",") if part.strip()]
    if not parts:
        return None

    for part in parts:
        if "-" in part:
            start, end = part.split("-", 1)
            if not start.isdigit() or not end.isdigit():
                raise ValueError(f"Invalid {label} port range '{part}'")
            start_int = int(start)
            end_int = int(end)
            if start_int < 1 or end_int > 65535 or start_int > end_int:
                raise ValueError(f"Invalid {label} port range '{part}'")
        else:
            if not part.isdigit():
                raise ValueError(f"Invalid {label} port '{part}'")
            port_int = int(part)
            if port_int < 1 or port_int > 65535:
                raise ValueError(f"Invalid {label} port '{part}'")

    return ",".join(parts)


def build_firewall_rule_payload(
    *,
    name: str,
    ruleset: str,
    action: str,
    protocol: str,
    src: str | None,
    dst: str | None,
    src_port: str | None,
    dst_port: str | None,
    logging: bool,
    enabled: bool,
    rule_index: int | None,
) -> dict[str, Any]:
    """Build a classic UniFi firewall rule payload."""
    if not name.strip():
        raise ValueError("Rule name cannot be empty")

    normalized_ruleset = normalize_ruleset(ruleset)
    normalized_action = normalize_action(action)
    normalized_protocol = normalize_protocol(protocol)
    normalized_src = normalize_address(src, "source")
    normalized_dst = normalize_address(dst, "destination")
    normalized_src_port = normalize_port(src_port, "source")
    normalized_dst_port = normalize_port(dst_port, "destination")

    if normalized_protocol in ("all", "icmp") and (
        normalized_src_port or normalized_dst_port
    ):
        raise ValueError("Port filters require protocol tcp, udp, or tcp_udp")

    payload: dict[str, Any] = {
        "name": name.strip(),
        "enabled": enabled,
        "ruleset": normalized_ruleset,
        "action": normalized_action,
        "protocol": normalized_protocol,
        "logging": logging,
    }

    if normalized_src:
        payload["src_network_type"] = "ADDRv4"
        payload["src_address"] = normalized_src
    if normalized_dst:
        payload["dst_network_type"] = "ADDRv4"
        payload["dst_address"] = normalized_dst
    if normalized_src_port:
        payload["src_port"] = normalized_src_port
    if normalized_dst_port:
        payload["dst_port"] = normalized_dst_port
    if rule_index is not None:
        payload["rule_index"] = rule_index

    return payload


def resolve_rule_reference(
    rules: list[dict[str, Any]],
    identifier: str,
    ruleset: str,
) -> dict[str, Any]:
    """Resolve a firewall rule by ID, exact name, or unique name substring."""
    ruleset_rules = [
        rule for rule in rules if rule.get("ruleset", "").upper() == ruleset
    ]
    identifier_lower = identifier.lower()

    exact_matches = [
        rule
        for rule in ruleset_rules
        if rule.get("_id") == identifier
        or rule.get("name", "").lower() == identifier_lower
    ]
    if len(exact_matches) == 1:
        return exact_matches[0]
    if len(exact_matches) > 1:
        raise ValueError(f"Multiple rules match '{identifier}'")

    partial_matches = [
        rule
        for rule in ruleset_rules
        if identifier_lower in rule.get("name", "").lower()
    ]
    if len(partial_matches) == 1:
        return partial_matches[0]
    if len(partial_matches) > 1:
        raise ValueError(f"Multiple rules match '{identifier}'")

    raise ValueError(f"No {ruleset} rule matches '{identifier}'")


def compute_relative_rule_index(
    rules: list[dict[str, Any]],
    *,
    ruleset: str,
    before: str | None,
    after: str | None,
) -> int:
    """Compute a rule index before or after an existing rule."""
    if before and after:
        raise ValueError("--before and --after cannot be used together")
    if not before and not after:
        raise ValueError("Either --before or --after is required")

    sorted_rules = sorted(
        [rule for rule in rules if rule.get("ruleset", "").upper() == ruleset],
        key=lambda rule: int(rule.get("rule_index", 0)),
    )
    target = resolve_rule_reference(rules, before or after or "", ruleset)
    position = sorted_rules.index(target)
    target_index = int(target.get("rule_index", 0))

    if before:
        lower_index = (
            int(sorted_rules[position - 1].get("rule_index", 0))
            if position > 0
            else target_index - 1000
        )
        gap = target_index - lower_index
        if gap > 1:
            return lower_index + gap // 2
        return max(1, target_index - 1)

    upper_index = (
        int(sorted_rules[position + 1].get("rule_index", target_index + 1000))
        if position < len(sorted_rules) - 1
        else target_index + 1000
    )
    gap = upper_index - target_index
    if gap > 1:
        return target_index + gap // 2
    return target_index + 1


def print_rule_summary(rule: dict[str, Any], *, created: bool = True) -> None:
    """Print a concise created-rule summary."""
    from rich.table import Table

    title = "Firewall Rule" if created else "Firewall Rule Payload"
    table = Table(title=title, show_header=False, box=None, padding=(0, 2))
    table.add_column("Field", style="dim")
    table.add_column("Value")
    if created:
        table.add_row("ID:", rule.get("_id", ""))
    table.add_row("Name:", rule.get("name", ""))
    table.add_row("Ruleset:", rule.get("ruleset", ""))
    table.add_row("Action:", rule.get("action", ""))
    table.add_row("Protocol:", format_protocol(rule))
    table.add_row("Source:", format_address(rule, "src"))
    table.add_row("Destination:", format_address(rule, "dst"))
    table.add_row("Destination Port:", format_port(rule, "dst"))
    if "rule_index" in rule:
        table.add_row("Rule Index:", str(rule.get("rule_index", "")))
    table.add_row("Logging:", "Yes" if rule.get("logging", False) else "No")
    table.add_row("Enabled:", "Yes" if rule.get("enabled", True) else "No")

    if created:
        print_success(f"Created firewall rule '{rule.get('name', '')}'")
    console.print(table)


@app.command("add")
def add_rule(
    name: Annotated[str, typer.Argument(help="Name for the new firewall rule")],
    ruleset: Annotated[
        str,
        typer.Option("--ruleset", "-r", help="Ruleset, for example LAN_IN"),
    ] = "LAN_IN",
    action: Annotated[
        str,
        typer.Option("--action", "-a", help="Action: accept, drop, reject"),
    ] = "accept",
    protocol: Annotated[
        str,
        typer.Option("--protocol", "-p", help="Protocol: all, tcp, udp, tcp_udp, icmp"),
    ] = "all",
    src: Annotated[
        str | None,
        typer.Option("--src", help="Source IPv4 address/CIDR, or any"),
    ] = None,
    dst: Annotated[
        str | None,
        typer.Option("--dst", help="Destination IPv4 address/CIDR, or any"),
    ] = None,
    src_port: Annotated[
        str | None,
        typer.Option("--src-port", help="Source port, list, or range"),
    ] = None,
    dst_port: Annotated[
        str | None,
        typer.Option("--dst-port", help="Destination port, list, or range"),
    ] = None,
    rule_index: Annotated[
        int | None,
        typer.Option("--rule-index", help="Explicit UniFi rule_index value"),
    ] = None,
    before: Annotated[
        str | None,
        typer.Option("--before", help="Place before rule ID/name in the same ruleset"),
    ] = None,
    after: Annotated[
        str | None,
        typer.Option("--after", help="Place after rule ID/name in the same ruleset"),
    ] = None,
    logging: Annotated[
        bool,
        typer.Option("--logging/--no-logging", help="Enable controller logging"),
    ] = False,
    enabled: Annotated[
        bool,
        typer.Option("--enabled/--disabled", help="Create rule enabled or disabled"),
    ] = True,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Print the payload without creating the rule"),
    ] = False,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation prompt"),
    ] = False,
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
) -> None:
    """Create a classic UniFi firewall rule."""
    from ui_cli.commands.local.utils import run_with_spinner

    try:
        if rule_index is not None and (before or after):
            raise ValueError("--rule-index cannot be combined with --before or --after")

        payload = build_firewall_rule_payload(
            name=name,
            ruleset=ruleset,
            action=action,
            protocol=protocol,
            src=src,
            dst=dst,
            src_port=src_port,
            dst_port=dst_port,
            logging=logging,
            enabled=enabled,
            rule_index=rule_index,
        )

        client: UniFiLocalClient | None = None
        if before or after:
            client = UniFiLocalClient()
            rules = run_with_spinner(
                client.get_firewall_rules(),
                "Fetching firewall rules...",
            )
            payload["rule_index"] = compute_relative_rule_index(
                rules,
                ruleset=payload["ruleset"],
                before=before,
                after=after,
            )
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if dry_run:
        if output == OutputFormat.JSON:
            output_json(payload)
        elif output == OutputFormat.CSV:
            output_csv([payload])
        else:
            print_rule_summary(payload, created=False)
        return

    if not yes:
        confirmed = typer.confirm(
            f"Create firewall rule '{payload['name']}' in {payload['ruleset']}?"
        )
        if not confirmed:
            raise typer.Exit(0)

    async def _create():
        active_client = client if client is not None else UniFiLocalClient()
        return await active_client.create_firewall_rule(payload)

    try:
        created = run_with_spinner(_create(), "Creating firewall rule...")
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if output == OutputFormat.JSON:
        output_json(created)
    elif output == OutputFormat.CSV:
        output_csv([created])
    else:
        print_rule_summary(created)


@app.command("list")
def list_rules(
    ruleset: Annotated[
        str | None,
        typer.Option("--ruleset", "-r", help="Filter by ruleset (e.g., WAN_IN, LAN_IN)"),
    ] = None,
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Show additional details"),
    ] = False,
) -> None:
    """List firewall rules."""
    from ui_cli.commands.local.utils import run_with_spinner

    async def _list():
        client = UniFiLocalClient()
        return await client.get_firewall_rules()

    try:
        rules = run_with_spinner(_list(), "Fetching firewall rules...")
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if not rules:
        console.print("[dim]No firewall rules found[/dim]")
        return

    # Filter by ruleset if specified
    if ruleset:
        ruleset_upper = ruleset.upper()
        rules = [r for r in rules if r.get("ruleset", "").upper() == ruleset_upper]
        if not rules:
            console.print(f"[dim]No rules found for ruleset '{ruleset}'[/dim]")
            return

    # Sort by ruleset then by rule index
    rules.sort(key=lambda r: (get_ruleset_order(r.get("ruleset", "")), r.get("rule_index", 0)))

    if output == OutputFormat.JSON:
        output_json(rules)
    elif output == OutputFormat.CSV:
        columns = [
            ("name", "Name"),
            ("ruleset", "Ruleset"),
            ("action", "Action"),
            ("protocol", "Protocol"),
            ("src_address", "Source"),
            ("dst_address", "Destination"),
            ("enabled", "Enabled"),
        ]
        csv_data = []
        for r in rules:
            csv_data.append({
                "name": r.get("name", ""),
                "ruleset": r.get("ruleset", ""),
                "action": r.get("action", ""),
                "protocol": format_protocol(r),
                "src_address": format_address(r, "src"),
                "dst_address": format_address(r, "dst"),
                "enabled": "Yes" if r.get("enabled", True) else "No",
            })
        output_csv(csv_data, columns)
    else:
        from rich.table import Table

        table = Table(title="Firewall Rules", show_header=True, header_style="bold cyan")
        table.add_column("Name")
        table.add_column("Ruleset")
        table.add_column("Action")
        table.add_column("Protocol")
        table.add_column("Source")
        table.add_column("Destination")
        if verbose:
            table.add_column("Src Port")
            table.add_column("Dst Port")
        table.add_column("Enabled")

        for r in rules:
            name = r.get("name", "(unnamed)")
            ruleset_name = RULESET_NAMES.get(r.get("ruleset", ""), r.get("ruleset", ""))
            action, action_style = format_action(r.get("action", ""))
            protocol = format_protocol(r)
            src = format_address(r, "src")
            dst = format_address(r, "dst")
            enabled = "[green]✓[/green]" if r.get("enabled", True) else "[dim]✗[/dim]"

            if verbose:
                src_port = format_port(r, "src")
                dst_port = format_port(r, "dst")
                table.add_row(
                    name,
                    ruleset_name,
                    f"[{action_style}]{action}[/{action_style}]",
                    protocol,
                    src,
                    dst,
                    src_port,
                    dst_port,
                    enabled,
                )
            else:
                table.add_row(
                    name,
                    ruleset_name,
                    f"[{action_style}]{action}[/{action_style}]",
                    protocol,
                    src,
                    dst,
                    enabled,
                )

        console.print(table)
        console.print(f"\n[dim]{len(rules)} rule(s)[/dim]")


@app.command("groups")
def list_groups(
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
) -> None:
    """List firewall groups (address and port groups)."""
    from ui_cli.commands.local.utils import run_with_spinner

    async def _list():
        client = UniFiLocalClient()
        return await client.get_firewall_groups()

    try:
        groups = run_with_spinner(_list(), "Fetching firewall groups...")
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if not groups:
        console.print("[dim]No firewall groups found[/dim]")
        return

    # Sort by type then name
    groups.sort(key=lambda g: (g.get("group_type", ""), g.get("name", "")))

    if output == OutputFormat.JSON:
        output_json(groups)
    elif output == OutputFormat.CSV:
        columns = [
            ("_id", "ID"),
            ("name", "Name"),
            ("group_type", "Type"),
            ("members", "Members"),
        ]
        csv_data = []
        for g in groups:
            members = g.get("group_members", [])
            csv_data.append({
                "_id": g.get("_id", ""),
                "name": g.get("name", ""),
                "group_type": g.get("group_type", ""),
                "members": ", ".join(members) if members else "",
            })
        output_csv(csv_data, columns)
    else:
        from rich.table import Table

        table = Table(title="Firewall Groups", show_header=True, header_style="bold cyan")
        table.add_column("ID", style="dim")
        table.add_column("Name")
        table.add_column("Type")
        table.add_column("Members")

        for g in groups:
            group_id = g.get("_id", "")
            name = g.get("name", "")
            group_type = g.get("group_type", "")

            # Format type for display
            type_display = group_type.replace("-", " ").title()

            # Format members
            members = g.get("group_members", [])
            if len(members) <= 3:
                members_str = ", ".join(members) if members else "[dim]-[/dim]"
            else:
                members_str = f"{', '.join(members[:3])}... (+{len(members) - 3})"

            table.add_row(group_id, name, type_display, members_str)

        console.print(table)
        console.print(f"\n[dim]{len(groups)} group(s)[/dim]")
