"""UI-CLI MCP Server v2.

FastMCP server that exposes UniFi management tools via CLI subprocess calls.
"""

import json

from mcp.server.fastmcp import FastMCP

from ui_mcp.cli_runner import run_cli, format_result

# Initialize FastMCP server
server = FastMCP(
    "ui-cli",
    instructions="Manage UniFi network infrastructure - check status, manage clients and devices",
)


# =============================================================================
# Status & Health Tools
# =============================================================================


@server.tool()
async def network_status() -> str:
    """Check UniFi API connection status.

    Returns connection status for both Cloud API and Local Controller.
    """
    result = run_cli(["status"])
    if "error" in result:
        return format_result(result)
    return format_result(result, "Network API status retrieved.")


@server.tool()
async def network_health() -> str:
    """Get network health summary.

    Returns health status for WAN, LAN, WLAN, and VPN subsystems.
    """
    result = run_cli(["lo", "health"])
    if "error" in result:
        return format_result(result)

    # Build summary from health data
    if isinstance(result, list):
        subsystems = []
        for h in result:
            name = h.get("subsystem", "unknown")
            status = h.get("status", "unknown")
            subsystems.append(f"{name}: {status}")
        summary = f"Health: {', '.join(subsystems)}"
    else:
        summary = "Health data retrieved."

    return format_result(result, summary)


@server.tool()
async def internet_speed() -> str:
    """Get the last speed test result.

    Returns download/upload speeds and latency from the most recent test.
    """
    result = run_cli(["speedtest"])
    if "error" in result:
        return format_result(result)
    return format_result(result, "Speed test results retrieved.")


@server.tool()
async def run_speedtest() -> str:
    """Run a new internet speed test.

    Initiates a speed test on the gateway. Takes 30-60 seconds to complete.
    """
    result = run_cli(["speedtest", "-r"], timeout=90)
    if "error" in result:
        return format_result(result)
    return format_result(result, "Speed test completed.")


@server.tool()
async def isp_performance(hours: int = 168) -> str:
    """Get ISP performance metrics over time.

    Args:
        hours: Hours of data to retrieve (default: 168 = 7 days)

    Returns latency, download/upload speeds, and uptime statistics.
    """
    result = run_cli(["isp", "metrics", "--hours", str(hours)])
    if "error" in result:
        return format_result(result)
    return format_result(result, f"ISP metrics for last {hours} hours.")


# =============================================================================
# Client Count & Summary Tools
# =============================================================================


@server.tool()
async def client_count(by: str = "type") -> str:
    """Count connected clients grouped by category.

    Args:
        by: Group by 'type' (wired/wireless), 'network', 'vendor', 'ap', or 'experience'

    Returns client counts without listing individual clients.
    """
    result = run_cli(["lo", "clients", "count", "--by", by])
    if "error" in result:
        return format_result(result)

    # Build summary
    counts = result.get("counts", {})
    total = result.get("total", sum(counts.values()))
    summary = f"Total: {total} clients. " + ", ".join(
        f"{k}: {v}" for k, v in counts.items()
    )
    return format_result(result, summary)


@server.tool()
async def device_list() -> str:
    """List UniFi network devices (APs, switches, gateways).

    Returns all managed UniFi devices with status and firmware info.
    """
    result = run_cli(["lo", "devices", "list"])
    if "error" in result:
        return format_result(result)

    # Build summary
    if isinstance(result, list):
        count = len(result)
        types = {}
        for d in result:
            t = d.get("type", "unknown")
            types[t] = types.get(t, 0) + 1
        type_str = ", ".join(f"{v} {k}" for k, v in types.items())
        summary = f"Found {count} devices: {type_str}"
    else:
        summary = "Device list retrieved."

    return format_result(result, summary)


@server.tool()
async def network_list() -> str:
    """List configured networks and VLANs.

    Returns all networks with VLAN IDs, subnets, and DHCP settings.
    """
    result = run_cli(["lo", "networks", "list"])
    if "error" in result:
        return format_result(result)

    # Build summary
    if isinstance(result, list):
        names = [n.get("name", "unnamed") for n in result]
        summary = f"Found {len(result)} networks: {', '.join(names)}"
    else:
        summary = "Network list retrieved."

    return format_result(result, summary)


# =============================================================================
# Lookup Tools
# =============================================================================


@server.tool()
async def find_client(name: str) -> str:
    """Find a specific client by name or MAC address.

    Args:
        name: Client name, hostname, or MAC address

    Returns detailed client info including IP, connection type, and status.
    """
    result = run_cli(["lo", "clients", "get", name])
    if "error" in result:
        return format_result(result)
    return format_result(result, f"Found client: {name}")


@server.tool()
async def find_device(name: str) -> str:
    """Find a specific UniFi device by name, MAC, or IP.

    Args:
        name: Device name, MAC address, or IP address

    Returns detailed device info including model, firmware, and status.
    """
    result = run_cli(["lo", "devices", "get", name])
    if "error" in result:
        return format_result(result)
    return format_result(result, f"Found device: {name}")


@server.tool()
async def client_status(name: str) -> str:
    """Check if a client is online and/or blocked.

    Args:
        name: Client name, hostname, or MAC address

    Returns connection status, block status, and network info.
    """
    result = run_cli(["lo", "clients", "status", name])
    if "error" in result:
        return format_result(result)

    # Build summary
    online = result.get("online", False)
    blocked = result.get("blocked", False)
    status_parts = []
    status_parts.append("online" if online else "offline")
    if blocked:
        status_parts.append("BLOCKED")
    summary = f"{name}: {', '.join(status_parts)}"

    return format_result(result, summary)


# =============================================================================
# Action Tools
# =============================================================================


@server.tool()
async def block_client(name: str) -> str:
    """Block a client from the network.

    Args:
        name: Client name, hostname, or MAC address to block

    The client will be disconnected and prevented from reconnecting.
    """
    result = run_cli(["lo", "clients", "block", name])
    if "error" in result:
        return format_result(result)

    success = result.get("success", False)
    if success:
        return format_result(result, f"Blocked client: {name}")
    else:
        return format_result(result, f"Failed to block: {name}")


@server.tool()
async def unblock_client(name: str) -> str:
    """Unblock a previously blocked client.

    Args:
        name: Client name, hostname, or MAC address to unblock

    The client will be able to reconnect to the network.
    """
    result = run_cli(["lo", "clients", "unblock", name])
    if "error" in result:
        return format_result(result)

    success = result.get("success", False)
    if success:
        return format_result(result, f"Unblocked client: {name}")
    else:
        return format_result(result, f"Failed to unblock: {name}")


@server.tool()
async def kick_client(name: str) -> str:
    """Disconnect a client from the network.

    Args:
        name: Client name, hostname, or MAC address to disconnect

    The client will be disconnected but can reconnect immediately.
    """
    result = run_cli(["lo", "clients", "kick", name])
    if "error" in result:
        return format_result(result)

    success = result.get("success", False)
    if success:
        return format_result(result, f"Kicked client: {name}")
    else:
        return format_result(result, f"Failed to kick: {name}")


@server.tool()
async def restart_device(name: str) -> str:
    """Restart a UniFi device.

    Args:
        name: Device name, MAC address, or IP address

    The device will reboot and be offline for 1-3 minutes.
    """
    result = run_cli(["lo", "devices", "restart", name])
    if "error" in result:
        return format_result(result)

    success = result.get("success", False)
    if success:
        return format_result(result, f"Restarting device: {name}")
    else:
        return format_result(result, f"Failed to restart: {name}")


@server.tool()
async def create_voucher(
    duration_hours: int = 24,
    count: int = 1,
) -> str:
    """Create guest WiFi voucher(s).

    Args:
        duration_hours: How long the voucher is valid (default: 24 hours)
        count: Number of vouchers to create (default: 1)

    Returns the voucher code(s) that guests can use to access WiFi.
    """
    duration_minutes = duration_hours * 60
    result = run_cli([
        "lo", "vouchers", "create",
        "--count", str(count),
        "--duration", str(duration_minutes),
    ])
    if "error" in result:
        return format_result(result)

    vouchers = result.get("vouchers", [])
    if vouchers:
        codes = [v.get("code", "") for v in vouchers]
        summary = f"Created {len(vouchers)} voucher(s): {', '.join(codes)}"
    else:
        summary = "Voucher creation response received."

    return format_result(result, summary)


# =============================================================================
# Client Groups Tools
# =============================================================================


@server.tool()
async def list_groups() -> str:
    """List all client groups.

    Returns all defined groups with member counts.
    Groups can be used for bulk actions like blocking/unblocking.
    """
    result = run_cli(["groups", "list"])
    if "error" in result:
        return format_result(result)

    if isinstance(result, list):
        count = len(result)
        summary = f"Found {count} group(s)"
    else:
        summary = "Groups retrieved."

    return format_result(result, summary)


@server.tool()
async def get_group(name: str) -> str:
    """Get details of a client group.

    Args:
        name: Group name or slug

    Returns group info including members and rules (for auto groups).
    """
    result = run_cli(["groups", "show", name])
    if "error" in result:
        return format_result(result)
    return format_result(result, f"Group details: {name}")


@server.tool()
async def block_group(name: str) -> str:
    """Block all clients in a group.

    Args:
        name: Group name or slug

    All clients in the group will be blocked from the network.
    Useful for parental controls (e.g., bedtime restrictions).
    """
    result = run_cli(["lo", "clients", "block", "-g", name, "-y"])
    if "error" in result:
        return format_result(result)

    summary = result.get("summary", {})
    blocked = summary.get("blocked", 0)
    already = summary.get("already", 0)
    failed = summary.get("failed", 0)
    return format_result(
        result,
        f"Blocked {blocked} clients (already blocked: {already}, failed: {failed})"
    )


@server.tool()
async def unblock_group(name: str) -> str:
    """Unblock all clients in a group.

    Args:
        name: Group name or slug

    All previously blocked clients in the group will be unblocked.
    """
    result = run_cli(["lo", "clients", "unblock", "-g", name, "-y"])
    if "error" in result:
        return format_result(result)

    summary = result.get("summary", {})
    unblocked = summary.get("unblocked", 0)
    not_blocked = summary.get("not_blocked", 0)
    failed = summary.get("failed", 0)
    return format_result(
        result,
        f"Unblocked {unblocked} clients (not blocked: {not_blocked}, failed: {failed})"
    )


@server.tool()
async def group_status(name: str) -> str:
    """Get live status of all clients in a group.

    Args:
        name: Group name or slug

    Returns online/offline status for each group member.
    """
    result = run_cli(["lo", "clients", "list", "-g", name])
    if "error" in result:
        return format_result(result)

    if isinstance(result, list):
        count = len(result)
        summary = f"Found {count} client(s) in group '{name}'"
    else:
        summary = f"Status for group: {name}"

    return format_result(result, summary)


# =============================================================================
# Entry Point
# =============================================================================


def main():
    """Run the MCP server."""
    server.run()


if __name__ == "__main__":
    main()
