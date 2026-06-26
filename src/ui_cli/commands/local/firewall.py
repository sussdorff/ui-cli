"""Firewall commands for local controller.

Modern UniFi controllers (UniFi OS / Network 9+) use a zone-based firewall:
policies describe traffic *from one zone to another* and are served from the
v2 ``/firewall-policies`` API. The classic ``/rest/firewallrule`` ruleset model
(LAN_IN, WAN_OUT, ...) is deprecated on these controllers -- GET still answers
with an empty list, but creates are rejected with ``api.err.InvalidValue``.

The ``add`` and ``list`` commands therefore operate on zone-based policies.
Source/destination zones are resolved automatically from the given host IPs
(via the network each IP belongs to), with ``--src-zone`` / ``--dst-zone`` as
explicit overrides.
"""

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


# Map user-facing actions to the zone-policy action enum.
ACTION_MAP = {
    "accept": "ALLOW",
    "allow": "ALLOW",
    "drop": "BLOCK",
    "block": "BLOCK",
    "reject": "REJECT",
}

VALID_PROTOCOLS = {"all", "tcp", "udp", "tcp_udp", "icmp", "icmpv6"}

# Default ordering hint for new user policies. The controller re-assigns the
# effective index within the zone pair, so this is only a starting point.
DEFAULT_POLICY_INDEX = 10000


def format_policy_action(action: str) -> tuple[str, str]:
    """Format a policy action with a display color."""
    normalized = (action or "").upper()
    if normalized == "ALLOW":
        return "ALLOW", "green"
    if normalized == "BLOCK":
        return "BLOCK", "red"
    if normalized == "REJECT":
        return "REJECT", "yellow"
    return normalized or "?", "white"


def normalize_action(action: str) -> str:
    """Normalize and validate a firewall action into the policy enum."""
    normalized = ACTION_MAP.get(action.lower())
    if normalized is None:
        valid = ", ".join(sorted(set(ACTION_MAP)))
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


def normalize_policy_ip(value: str | None, label: str) -> str | None:
    """Normalize a single IPv4/IPv6 host address for a zone policy.

    Returns ``None`` for an "any" match. Subnets are rejected because
    zone-based policies created by this CLI match single host IPs; use a
    network/zone match in the UI for whole subnets.
    """
    if value is None or value.strip().lower() in ("", "any", "*"):
        return None

    text = value.strip()
    try:
        network = ipaddress.ip_network(text, strict=False)
    except ValueError as exc:
        raise ValueError(f"Invalid {label} address '{value}'") from exc

    if network.prefixlen != network.max_prefixlen:
        raise ValueError(
            f"{label.capitalize()} '{value}' is a subnet. Zone-based policies "
            f"created by this CLI match single host IPs - pass a host address "
            f"(e.g. 192.168.2.120) or use --{label}-zone for a whole zone."
        )
    return str(network.network_address)


def normalize_port(value: str | None, label: str) -> str | None:
    """Normalize a port, list, or range string."""
    if value is None or value.strip().lower() in ("", "any", "*"):
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


def derive_ip_version(src_ip: str | None, dst_ip: str | None) -> str:
    """Derive the policy ip_version from the supplied host IPs."""
    versions = {
        ipaddress.ip_address(ip).version for ip in (src_ip, dst_ip) if ip
    }
    if versions == {4}:
        return "IPV4"
    if versions == {6}:
        return "IPV6"
    return "BOTH"


def find_zone(identifier: str, zones: list[dict[str, Any]]) -> dict[str, Any]:
    """Find a zone by display name or zone key (case-insensitive)."""
    ident = identifier.strip().lower()
    for zone in zones:
        if (
            zone.get("name", "").lower() == ident
            or zone.get("zone_key", "").lower() == ident
        ):
            return zone

    matches = [z for z in zones if ident in z.get("name", "").lower()]
    if len(matches) == 1:
        return matches[0]

    available = ", ".join(sorted(z.get("name", "") for z in zones)) or "(none)"
    raise ValueError(
        f"Unknown firewall zone '{identifier}'. Available zones: {available}"
    )


def resolve_zone_for_ip(
    ip: str,
    networks: list[dict[str, Any]],
    zones: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Resolve the firewall zone that owns the network containing ``ip``."""
    net_to_zone: dict[str, dict[str, Any]] = {}
    for zone in zones:
        for network_id in zone.get("network_ids") or []:
            net_to_zone[network_id] = zone

    address = ipaddress.ip_address(ip)
    for network in networks:
        for subnet_field in ("ip_subnet", "ipv6_subnet"):
            subnet = network.get(subnet_field)
            if not subnet:
                continue
            try:
                if address in ipaddress.ip_network(subnet, strict=False):
                    return net_to_zone.get(network.get("_id"))
            except ValueError:
                continue
    return None


def resolve_endpoint_zone(
    zone_option: str | None,
    ip: str | None,
    zones: list[dict[str, Any]],
    networks: list[dict[str, Any]],
    label: str,
) -> dict[str, Any]:
    """Resolve the zone for one endpoint from an override or its host IP."""
    if zone_option:
        return find_zone(zone_option, zones)
    if ip:
        zone = resolve_zone_for_ip(ip, networks, zones)
        if zone is not None:
            return zone
        raise ValueError(
            f"Could not map {label} IP {ip} to a firewall zone. "
            f"Pass --{label}-zone explicitly."
        )
    raise ValueError(
        f"{label.capitalize()} zone is required for zone-based policies. "
        f"Pass --{label}-zone (or a --{label} host IP that maps to a zone)."
    )


def build_policy_endpoint(
    ip: str | None,
    port: str | None,
    zone_id: str,
) -> dict[str, Any]:
    """Build a source/destination sub-object for a zone policy."""
    endpoint: dict[str, Any] = {
        "zone_id": zone_id,
        "matching_target": "IP" if ip else "ANY",
        "port_matching_type": "SPECIFIC" if port else "ANY",
        "match_opposite_ports": False,
    }
    if ip:
        endpoint["matching_target_type"] = "SPECIFIC"
        endpoint["ips"] = [ip]
        endpoint["match_opposite_ips"] = False
    if port:
        endpoint["port"] = port
    return endpoint


def build_firewall_policy_payload(
    *,
    name: str,
    action: str,
    protocol: str,
    src_ip: str | None,
    dst_ip: str | None,
    src_port: str | None,
    dst_port: str | None,
    src_zone_id: str,
    dst_zone_id: str,
    logging: bool,
    enabled: bool,
    index: int,
    ip_version: str,
) -> dict[str, Any]:
    """Build a zone-based UniFi firewall policy payload."""
    if not name.strip():
        raise ValueError("Rule name cannot be empty")

    if protocol in ("all", "icmp", "icmpv6") and (src_port or dst_port):
        raise ValueError("Port filters require protocol tcp, udp, or tcp_udp")

    return {
        "name": name.strip(),
        "action": action,
        "enabled": enabled,
        "protocol": protocol,
        "logging": logging,
        "ip_version": ip_version,
        "connection_state_type": "ALL",
        "connection_states": [],
        "create_allow_respond": action == "ALLOW",
        "icmp_typename": "ANY",
        "icmp_v6_typename": "ANY",
        "match_ip_sec": False,
        "match_opposite_protocol": False,
        "index": index,
        "schedule": {"mode": "ALWAYS", "repeat_on_days": [], "time_all_day": False},
        "source": build_policy_endpoint(src_ip, src_port, src_zone_id),
        "destination": build_policy_endpoint(dst_ip, dst_port, dst_zone_id),
    }


def format_policy_protocol(policy: dict[str, Any]) -> str:
    """Format a policy protocol for display."""
    protocol = policy.get("protocol", "all")
    if protocol == "all":
        return "any"
    return protocol.upper()


def format_policy_endpoint(
    endpoint: dict[str, Any],
    zone_names: dict[str, str],
) -> str:
    """Render a source/destination endpoint as ``zone[:ips][:port]``."""
    zone = zone_names.get(endpoint.get("zone_id", ""), endpoint.get("zone_id", "?"))
    parts = [zone]

    if endpoint.get("matching_target") == "IP" and endpoint.get("ips"):
        parts.append(",".join(endpoint["ips"]))
    elif endpoint.get("matching_target") == "NETWORK":
        parts.append("network")
    elif endpoint.get("matching_target") and endpoint["matching_target"] != "ANY":
        parts.append(str(endpoint["matching_target"]).lower())

    if endpoint.get("port_matching_type") == "SPECIFIC" and endpoint.get("port"):
        parts.append(f"port {endpoint['port']}")

    return ":".join(parts)


def print_policy_summary(
    policy: dict[str, Any],
    zone_names: dict[str, str],
    *,
    created: bool = True,
) -> None:
    """Print a concise created-policy summary."""
    from rich.table import Table

    title = "Firewall Policy" if created else "Firewall Policy Payload"
    table = Table(title=title, show_header=False, box=None, padding=(0, 2))
    table.add_column("Field", style="dim")
    table.add_column("Value")
    if created:
        table.add_row("ID:", policy.get("_id", ""))
    table.add_row("Name:", policy.get("name", ""))
    action, action_style = format_policy_action(policy.get("action", ""))
    table.add_row("Action:", f"[{action_style}]{action}[/{action_style}]")
    table.add_row("Protocol:", format_policy_protocol(policy))
    table.add_row("Source:", format_policy_endpoint(policy.get("source", {}), zone_names))
    table.add_row(
        "Destination:",
        format_policy_endpoint(policy.get("destination", {}), zone_names),
    )
    table.add_row("Logging:", "Yes" if policy.get("logging", False) else "No")
    table.add_row("Enabled:", "Yes" if policy.get("enabled", True) else "No")

    if created:
        print_success(f"Created firewall policy '{policy.get('name', '')}'")
    console.print(table)


@app.command("add")
def add_rule(
    name: Annotated[str, typer.Argument(help="Name for the new firewall policy")],
    action: Annotated[
        str,
        typer.Option("--action", "-a", help="Action: accept/allow, drop/block, reject"),
    ] = "accept",
    protocol: Annotated[
        str,
        typer.Option("--protocol", "-p", help="Protocol: all, tcp, udp, tcp_udp, icmp"),
    ] = "all",
    src: Annotated[
        str | None,
        typer.Option("--src", help="Source host IPv4/IPv6 address, or any"),
    ] = None,
    dst: Annotated[
        str | None,
        typer.Option("--dst", help="Destination host IPv4/IPv6 address, or any"),
    ] = None,
    src_port: Annotated[
        str | None,
        typer.Option("--src-port", help="Source port, list, or range"),
    ] = None,
    dst_port: Annotated[
        str | None,
        typer.Option("--dst-port", help="Destination port, list, or range"),
    ] = None,
    src_zone: Annotated[
        str | None,
        typer.Option("--src-zone", help="Source zone (overrides auto-resolution)"),
    ] = None,
    dst_zone: Annotated[
        str | None,
        typer.Option("--dst-zone", help="Destination zone (overrides auto-resolution)"),
    ] = None,
    rule_index: Annotated[
        int | None,
        typer.Option(
            "--rule-index",
            "--index",
            help="Ordering hint; the controller re-assigns the effective index",
        ),
    ] = None,
    ruleset: Annotated[
        str | None,
        typer.Option(
            "--ruleset",
            "-r",
            help="Deprecated/ignored on zone-based controllers (zones are resolved)",
        ),
    ] = None,
    logging: Annotated[
        bool,
        typer.Option("--logging/--no-logging", help="Enable controller logging"),
    ] = False,
    enabled: Annotated[
        bool,
        typer.Option("--enabled/--disabled", help="Create policy enabled or disabled"),
    ] = True,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Print the payload without creating the policy"),
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
    """Create a zone-based UniFi firewall policy."""
    from ui_cli.commands.local.utils import run_with_spinner

    try:
        normalized_action = normalize_action(action)
        normalized_protocol = normalize_protocol(protocol)
        normalized_src = normalize_policy_ip(src, "src")
        normalized_dst = normalize_policy_ip(dst, "dst")
        normalized_src_port = normalize_port(src_port, "source")
        normalized_dst_port = normalize_port(dst_port, "destination")

        if normalized_protocol in ("all", "icmp", "icmpv6") and (
            normalized_src_port or normalized_dst_port
        ):
            raise ValueError("Port filters require protocol tcp, udp, or tcp_udp")
        if not name.strip():
            raise ValueError("Rule name cannot be empty")

        client = UniFiLocalClient()
        zones = run_with_spinner(
            client.get_firewall_zones(), "Fetching firewall zones..."
        )
        if not zones:
            raise ValueError(
                "Controller returned no firewall zones. This controller may not "
                "use the zone-based firewall."
            )

        need_networks = (not src_zone and normalized_src) or (
            not dst_zone and normalized_dst
        )
        networks = (
            run_with_spinner(client.get_networks(), "Fetching networks...")
            if need_networks
            else []
        )

        src_zone_obj = resolve_endpoint_zone(
            src_zone, normalized_src, zones, networks, "src"
        )
        dst_zone_obj = resolve_endpoint_zone(
            dst_zone, normalized_dst, zones, networks, "dst"
        )

        payload = build_firewall_policy_payload(
            name=name,
            action=normalized_action,
            protocol=normalized_protocol,
            src_ip=normalized_src,
            dst_ip=normalized_dst,
            src_port=normalized_src_port,
            dst_port=normalized_dst_port,
            src_zone_id=src_zone_obj["_id"],
            dst_zone_id=dst_zone_obj["_id"],
            logging=logging,
            enabled=enabled,
            index=rule_index if rule_index is not None else DEFAULT_POLICY_INDEX,
            ip_version=derive_ip_version(normalized_src, normalized_dst),
        )
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    zone_names = {z.get("_id", ""): z.get("name", "") for z in zones}

    # Only surface advisory notes in human (table) output so JSON/CSV stay clean.
    if ruleset and output == OutputFormat.TABLE:
        console.print(
            f"[dim]Note: --ruleset '{ruleset}' is ignored on zone-based "
            f"controllers; resolved zones "
            f"{zone_names.get(src_zone_obj['_id'])} -> "
            f"{zone_names.get(dst_zone_obj['_id'])}.[/dim]"
        )

    if dry_run:
        if output == OutputFormat.JSON:
            output_json(payload)
        elif output == OutputFormat.CSV:
            output_csv([payload])
        else:
            print_policy_summary(payload, zone_names, created=False)
        return

    if not yes:
        confirmed = typer.confirm(
            f"Create firewall policy '{payload['name']}' "
            f"({zone_names.get(src_zone_obj['_id'])} -> "
            f"{zone_names.get(dst_zone_obj['_id'])})?"
        )
        if not confirmed:
            raise typer.Exit(0)

    async def _create():
        return await client.create_firewall_policy(payload)

    try:
        created = run_with_spinner(_create(), "Creating firewall policy...")
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if output == OutputFormat.JSON:
        output_json(created)
    elif output == OutputFormat.CSV:
        output_csv([created])
    else:
        print_policy_summary(created, zone_names)


@app.command("list")
def list_rules(
    zone: Annotated[
        str | None,
        typer.Option("--zone", "-z", help="Filter by zone name on either side"),
    ] = None,
    show_all: Annotated[
        bool,
        typer.Option("--all", help="Include predefined policies"),
    ] = False,
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Show additional details"),
    ] = False,
) -> None:
    """List zone-based firewall policies."""
    from ui_cli.commands.local.utils import run_with_spinner

    async def _list() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        client = UniFiLocalClient()
        policies = await client.get_firewall_policies()
        zones = await client.get_firewall_zones()
        return policies, zones

    try:
        policies, zones = run_with_spinner(_list(), "Fetching firewall policies...")
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    zone_names = {z.get("_id", ""): z.get("name", "") for z in zones}

    if not show_all:
        policies = [p for p in policies if not p.get("predefined")]

    if zone:
        zone_lower = zone.lower()

        def matches_zone(policy: dict[str, Any]) -> bool:
            for side in ("source", "destination"):
                zid = policy.get(side, {}).get("zone_id", "")
                if zone_lower in zone_names.get(zid, "").lower():
                    return True
            return False

        policies = [p for p in policies if matches_zone(p)]

    if not policies:
        console.print("[dim]No firewall policies found[/dim]")
        return

    policies.sort(key=lambda p: (p.get("index", 0), p.get("name", "")))

    if output == OutputFormat.JSON:
        output_json(policies)
    elif output == OutputFormat.CSV:
        columns = [
            ("name", "Name"),
            ("action", "Action"),
            ("protocol", "Protocol"),
            ("source", "Source"),
            ("destination", "Destination"),
            ("enabled", "Enabled"),
        ]
        csv_data = []
        for p in policies:
            csv_data.append({
                "name": p.get("name", ""),
                "action": p.get("action", ""),
                "protocol": format_policy_protocol(p),
                "source": format_policy_endpoint(p.get("source", {}), zone_names),
                "destination": format_policy_endpoint(
                    p.get("destination", {}), zone_names
                ),
                "enabled": "Yes" if p.get("enabled", True) else "No",
            })
        output_csv(csv_data, columns)
    else:
        from rich.table import Table

        table = Table(title="Firewall Policies", show_header=True, header_style="bold cyan")
        table.add_column("Name")
        table.add_column("Action")
        table.add_column("Protocol")
        table.add_column("Source")
        table.add_column("Destination")
        if verbose:
            table.add_column("Index")
        table.add_column("Enabled")

        for p in policies:
            name = p.get("name", "(unnamed)")
            action, action_style = format_policy_action(p.get("action", ""))
            protocol = format_policy_protocol(p)
            source = format_policy_endpoint(p.get("source", {}), zone_names)
            destination = format_policy_endpoint(p.get("destination", {}), zone_names)
            enabled = "[green]✓[/green]" if p.get("enabled", True) else "[dim]✗[/dim]"

            row = [
                name,
                f"[{action_style}]{action}[/{action_style}]",
                protocol,
                source,
                destination,
            ]
            if verbose:
                row.append(str(p.get("index", "")))
            row.append(enabled)
            table.add_row(*row)

        console.print(table)
        console.print(f"\n[dim]{len(policies)} policy/policies[/dim]")


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
