"""UI-CLI MCP Server.

FastMCP server that exposes UniFi management tools to Claude Desktop.
"""

import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from mcp.server.fastmcp import FastMCP

from ui_cli.client import UniFiClient, AuthenticationError, APIError
from ui_cli.local_client import (
    UniFiLocalClient,
    LocalAuthenticationError,
    LocalAPIError,
    LocalConnectionError,
)

from ui_mcp.helpers import resolve_client_mac, resolve_device_mac

# Initialize FastMCP server
server = FastMCP(
    "ui-cli",
    instructions="Manage UniFi infrastructure - controllers, devices, clients, and networks",
)

# Lazy client initialization
_cloud_client: UniFiClient | None = None
_local_client: UniFiLocalClient | None = None


def get_cloud_client() -> UniFiClient:
    """Get or create Cloud API client."""
    global _cloud_client
    if _cloud_client is None:
        _cloud_client = UniFiClient()
    return _cloud_client


def get_local_client() -> UniFiLocalClient:
    """Get or create Local Controller client."""
    global _local_client
    if _local_client is None:
        _local_client = UniFiLocalClient()
    return _local_client


# =============================================================================
# Cloud API Tools
# =============================================================================


@server.tool()
async def unifi_status() -> dict:
    """Check UniFi Cloud API connection status.

    Returns connection status and account information.
    """
    try:
        client = get_cloud_client()
        hosts = await client.list_hosts()
        return {
            "status": "connected",
            "api": "cloud",
            "hosts_count": len(hosts),
            "message": f"Connected to UniFi Cloud API with {len(hosts)} controller(s)",
        }
    except AuthenticationError as e:
        return {"status": "error", "error": "authentication_failed", "message": str(e)}
    except APIError as e:
        return {"status": "error", "error": "api_error", "message": str(e)}
    except Exception as e:
        return {"status": "error", "error": "unknown", "message": str(e)}


@server.tool()
async def unifi_list_hosts() -> dict:
    """List all UniFi controllers (hosts) associated with the account.

    Returns a list of controllers with their IDs, names, and status.
    """
    try:
        client = get_cloud_client()
        hosts = await client.list_hosts()
        return {"hosts": hosts, "count": len(hosts)}
    except AuthenticationError as e:
        return {"error": "authentication_failed", "message": str(e)}
    except APIError as e:
        return {"error": "api_error", "message": str(e)}


@server.tool()
async def unifi_list_sites() -> dict:
    """List all UniFi sites.

    Returns a list of sites with their IDs and names.
    """
    try:
        client = get_cloud_client()
        sites = await client.list_sites()
        return {"sites": sites, "count": len(sites)}
    except AuthenticationError as e:
        return {"error": "authentication_failed", "message": str(e)}
    except APIError as e:
        return {"error": "api_error", "message": str(e)}


@server.tool()
async def unifi_list_devices(host_id: str | None = None) -> dict:
    """List all UniFi devices across controllers.

    Args:
        host_id: Optional controller ID to filter devices by specific host

    Returns a list of devices with model, status, IP, and firmware info.
    """
    try:
        client = get_cloud_client()
        host_ids = [host_id] if host_id else None
        devices = await client.list_devices(host_ids=host_ids)
        return {"devices": devices, "count": len(devices)}
    except AuthenticationError as e:
        return {"error": "authentication_failed", "message": str(e)}
    except APIError as e:
        return {"error": "api_error", "message": str(e)}


@server.tool()
async def unifi_isp_metrics(
    interval: str = "1h",
    hours: int = 168,
) -> dict:
    """Get ISP performance metrics (latency, speeds, uptime).

    Args:
        interval: Data interval - '5m' (last 24h only) or '1h' (default, up to 30 days)
        hours: Hours of data to retrieve (default: 168 = 7 days)

    Returns ISP metrics including latency, download/upload speeds, and uptime.
    """
    try:
        client = get_cloud_client()
        metrics = await client.get_isp_metrics(metric_type=interval, duration_hours=hours)
        return {"metrics": metrics, "count": len(metrics), "interval": interval, "hours": hours}
    except AuthenticationError as e:
        return {"error": "authentication_failed", "message": str(e)}
    except APIError as e:
        return {"error": "api_error", "message": str(e)}


# =============================================================================
# Local Controller Tools - Clients
# =============================================================================


@server.tool()
async def unifi_lo_list_clients(
    filter: str | None = None,
) -> dict:
    """List connected clients on the local UniFi controller.

    Args:
        filter: Optional filter - 'wired', 'wireless', or a network/SSID name

    Returns connected clients with IP, MAC, hostname, and connection details.
    """
    try:
        client = get_local_client()
        clients = await client.list_clients()

        if filter:
            filter_lower = filter.lower()
            if filter_lower == "wired":
                clients = [c for c in clients if c.get("is_wired")]
            elif filter_lower == "wireless":
                clients = [c for c in clients if not c.get("is_wired")]
            else:
                # Filter by network/SSID name
                clients = [
                    c for c in clients
                    if filter_lower in c.get("network", "").lower()
                    or filter_lower in c.get("essid", "").lower()
                ]

        return {"clients": clients, "count": len(clients), "filter": filter}
    except LocalAuthenticationError as e:
        return {"error": "authentication_failed", "message": str(e)}
    except LocalConnectionError as e:
        return {"error": "connection_failed", "message": str(e)}
    except LocalAPIError as e:
        return {"error": "api_error", "message": str(e)}


@server.tool()
async def unifi_lo_all_clients() -> dict:
    """List all known clients including offline ones.

    Returns all clients that have ever connected, with their last seen time.
    """
    try:
        client = get_local_client()
        clients = await client.list_all_clients()
        return {"clients": clients, "count": len(clients)}
    except LocalAuthenticationError as e:
        return {"error": "authentication_failed", "message": str(e)}
    except LocalConnectionError as e:
        return {"error": "connection_failed", "message": str(e)}
    except LocalAPIError as e:
        return {"error": "api_error", "message": str(e)}


@server.tool()
async def unifi_lo_get_client(identifier: str) -> dict:
    """Get detailed information about a specific client.

    Args:
        identifier: Client name, hostname, or MAC address

    Returns detailed client info including IP, signal strength, traffic stats.
    """
    try:
        client = get_local_client()
        mac = await resolve_client_mac(client, identifier)
        client_data = await client.get_client(mac)
        if client_data:
            return {"client": client_data, "found": True}
        return {"found": False, "message": f"Client {identifier} not found"}
    except ValueError as e:
        return {"error": "not_found", "message": str(e)}
    except LocalAuthenticationError as e:
        return {"error": "authentication_failed", "message": str(e)}
    except LocalConnectionError as e:
        return {"error": "connection_failed", "message": str(e)}
    except LocalAPIError as e:
        return {"error": "api_error", "message": str(e)}


@server.tool()
async def unifi_lo_block_client(identifier: str) -> dict:
    """Block a client from the network.

    Args:
        identifier: Client name, hostname, or MAC address to block

    Blocked clients cannot connect to the network until unblocked.
    """
    try:
        client = get_local_client()
        mac = await resolve_client_mac(client, identifier)
        success = await client.block_client(mac)
        return {
            "success": success,
            "action": "blocked",
            "identifier": identifier,
            "mac": mac,
        }
    except ValueError as e:
        return {"error": "not_found", "message": str(e)}
    except LocalAuthenticationError as e:
        return {"error": "authentication_failed", "message": str(e)}
    except LocalConnectionError as e:
        return {"error": "connection_failed", "message": str(e)}
    except LocalAPIError as e:
        return {"error": "api_error", "message": str(e)}


@server.tool()
async def unifi_lo_unblock_client(identifier: str) -> dict:
    """Unblock a previously blocked client.

    Args:
        identifier: Client name, hostname, or MAC address to unblock
    """
    try:
        client = get_local_client()
        mac = await resolve_client_mac(client, identifier)
        success = await client.unblock_client(mac)
        return {
            "success": success,
            "action": "unblocked",
            "identifier": identifier,
            "mac": mac,
        }
    except ValueError as e:
        return {"error": "not_found", "message": str(e)}
    except LocalAuthenticationError as e:
        return {"error": "authentication_failed", "message": str(e)}
    except LocalConnectionError as e:
        return {"error": "connection_failed", "message": str(e)}
    except LocalAPIError as e:
        return {"error": "api_error", "message": str(e)}


@server.tool()
async def unifi_lo_kick_client(identifier: str) -> dict:
    """Disconnect (kick) a client from the network.

    Args:
        identifier: Client name, hostname, or MAC address to disconnect

    The client will be disconnected but can reconnect immediately.
    """
    try:
        client = get_local_client()
        mac = await resolve_client_mac(client, identifier)
        success = await client.kick_client(mac)
        return {
            "success": success,
            "action": "kicked",
            "identifier": identifier,
            "mac": mac,
        }
    except ValueError as e:
        return {"error": "not_found", "message": str(e)}
    except LocalAuthenticationError as e:
        return {"error": "authentication_failed", "message": str(e)}
    except LocalConnectionError as e:
        return {"error": "connection_failed", "message": str(e)}
    except LocalAPIError as e:
        return {"error": "api_error", "message": str(e)}


# =============================================================================
# Local Controller Tools - Devices
# =============================================================================


@server.tool()
async def unifi_lo_list_devices() -> dict:
    """List all network devices (APs, switches, gateways) on the controller.

    Returns devices with model, IP, firmware version, and status.
    """
    try:
        client = get_local_client()
        devices = await client.get_devices()
        return {"devices": devices, "count": len(devices)}
    except LocalAuthenticationError as e:
        return {"error": "authentication_failed", "message": str(e)}
    except LocalConnectionError as e:
        return {"error": "connection_failed", "message": str(e)}
    except LocalAPIError as e:
        return {"error": "api_error", "message": str(e)}


@server.tool()
async def unifi_lo_restart_device(identifier: str) -> dict:
    """Restart a network device.

    Args:
        identifier: Device name or MAC address

    The device will reboot and be offline for 1-3 minutes.
    """
    try:
        client = get_local_client()
        mac = await resolve_device_mac(client, identifier)
        success = await client.restart_device(mac)
        return {
            "success": success,
            "action": "restarting",
            "identifier": identifier,
            "mac": mac,
            "message": "Device will be offline for 1-3 minutes",
        }
    except ValueError as e:
        return {"error": "not_found", "message": str(e)}
    except LocalAuthenticationError as e:
        return {"error": "authentication_failed", "message": str(e)}
    except LocalConnectionError as e:
        return {"error": "connection_failed", "message": str(e)}
    except LocalAPIError as e:
        return {"error": "api_error", "message": str(e)}


@server.tool()
async def unifi_lo_locate_device(identifier: str, enabled: bool = True) -> dict:
    """Toggle the locate LED on a device for physical identification.

    Args:
        identifier: Device name or MAC address
        enabled: True to turn on locate LED, False to turn off
    """
    try:
        client = get_local_client()
        mac = await resolve_device_mac(client, identifier)
        success = await client.locate_device(mac, enabled=enabled)
        action = "locate_on" if enabled else "locate_off"
        return {
            "success": success,
            "action": action,
            "identifier": identifier,
            "mac": mac,
        }
    except ValueError as e:
        return {"error": "not_found", "message": str(e)}
    except LocalAuthenticationError as e:
        return {"error": "authentication_failed", "message": str(e)}
    except LocalConnectionError as e:
        return {"error": "connection_failed", "message": str(e)}
    except LocalAPIError as e:
        return {"error": "api_error", "message": str(e)}


@server.tool()
async def unifi_lo_upgrade_device(identifier: str) -> dict:
    """Upgrade device firmware to the latest version.

    Args:
        identifier: Device name or MAC address

    The device will download and install firmware, then reboot.
    """
    try:
        client = get_local_client()
        mac = await resolve_device_mac(client, identifier)
        success = await client.upgrade_device(mac)
        return {
            "success": success,
            "action": "upgrading",
            "identifier": identifier,
            "mac": mac,
            "message": "Firmware upgrade initiated",
        }
    except ValueError as e:
        return {"error": "not_found", "message": str(e)}
    except LocalAuthenticationError as e:
        return {"error": "authentication_failed", "message": str(e)}
    except LocalConnectionError as e:
        return {"error": "connection_failed", "message": str(e)}
    except LocalAPIError as e:
        return {"error": "api_error", "message": str(e)}


# =============================================================================
# Local Controller Tools - Networks & Firewall
# =============================================================================


@server.tool()
async def unifi_lo_list_networks() -> dict:
    """List all networks and VLANs configured on the controller.

    Returns networks with VLAN ID, subnet, DHCP settings, and purpose.
    """
    try:
        client = get_local_client()
        networks = await client.get_networks()
        return {"networks": networks, "count": len(networks)}
    except LocalAuthenticationError as e:
        return {"error": "authentication_failed", "message": str(e)}
    except LocalConnectionError as e:
        return {"error": "connection_failed", "message": str(e)}
    except LocalAPIError as e:
        return {"error": "api_error", "message": str(e)}


@server.tool()
async def unifi_lo_firewall_rules(ruleset: str | None = None) -> dict:
    """List firewall rules.

    Args:
        ruleset: Optional filter by ruleset (e.g., 'WAN_IN', 'WAN_OUT', 'LAN_IN')

    Returns firewall rules with action, protocol, ports, and source/destination.
    """
    try:
        client = get_local_client()
        rules = await client.get_firewall_rules()

        if ruleset:
            rules = [r for r in rules if r.get("ruleset", "").upper() == ruleset.upper()]

        return {"rules": rules, "count": len(rules), "ruleset": ruleset}
    except LocalAuthenticationError as e:
        return {"error": "authentication_failed", "message": str(e)}
    except LocalConnectionError as e:
        return {"error": "connection_failed", "message": str(e)}
    except LocalAPIError as e:
        return {"error": "api_error", "message": str(e)}


@server.tool()
async def unifi_lo_port_forwards() -> dict:
    """List port forwarding rules.

    Returns port forwards with name, ports, destination IP, and enabled status.
    """
    try:
        client = get_local_client()
        forwards = await client.get_port_forwards()
        return {"port_forwards": forwards, "count": len(forwards)}
    except LocalAuthenticationError as e:
        return {"error": "authentication_failed", "message": str(e)}
    except LocalConnectionError as e:
        return {"error": "connection_failed", "message": str(e)}
    except LocalAPIError as e:
        return {"error": "api_error", "message": str(e)}


# =============================================================================
# Local Controller Tools - Monitoring
# =============================================================================


@server.tool()
async def unifi_lo_health() -> dict:
    """Get site health summary.

    Returns health status for WAN, LAN, WLAN, and VPN subsystems.
    """
    try:
        client = get_local_client()
        health = await client.get_health()
        return {"health": health}
    except LocalAuthenticationError as e:
        return {"error": "authentication_failed", "message": str(e)}
    except LocalConnectionError as e:
        return {"error": "connection_failed", "message": str(e)}
    except LocalAPIError as e:
        return {"error": "api_error", "message": str(e)}


@server.tool()
async def unifi_lo_events(limit: int = 50) -> dict:
    """Get recent events from the controller.

    Args:
        limit: Maximum number of events to return (default: 50)

    Returns recent events like client connections, device status changes, etc.
    """
    try:
        client = get_local_client()
        events = await client.get_events(limit=limit)
        return {"events": events, "count": len(events)}
    except LocalAuthenticationError as e:
        return {"error": "authentication_failed", "message": str(e)}
    except LocalConnectionError as e:
        return {"error": "connection_failed", "message": str(e)}
    except LocalAPIError as e:
        return {"error": "api_error", "message": str(e)}


@server.tool()
async def unifi_lo_dpi_stats() -> dict:
    """Get Deep Packet Inspection (DPI) statistics.

    Returns application-level traffic breakdown by category.
    """
    try:
        client = get_local_client()
        stats = await client.get_site_dpi()
        return {"dpi_stats": stats}
    except LocalAuthenticationError as e:
        return {"error": "authentication_failed", "message": str(e)}
    except LocalConnectionError as e:
        return {"error": "connection_failed", "message": str(e)}
    except LocalAPIError as e:
        return {"error": "api_error", "message": str(e)}


@server.tool()
async def unifi_lo_daily_stats(days: int = 30) -> dict:
    """Get daily traffic statistics.

    Args:
        days: Number of days of data to retrieve (default: 30)

    Returns daily bandwidth usage and client counts.
    """
    try:
        client = get_local_client()
        stats = await client.get_daily_stats(days=days)
        return {"stats": stats, "count": len(stats), "days": days}
    except LocalAuthenticationError as e:
        return {"error": "authentication_failed", "message": str(e)}
    except LocalConnectionError as e:
        return {"error": "connection_failed", "message": str(e)}
    except LocalAPIError as e:
        return {"error": "api_error", "message": str(e)}


# =============================================================================
# Local Controller Tools - Vouchers
# =============================================================================


@server.tool()
async def unifi_lo_list_vouchers() -> dict:
    """List all guest vouchers.

    Returns vouchers with code, duration, quota, and usage status.
    """
    try:
        client = get_local_client()
        vouchers = await client.get_vouchers()
        return {"vouchers": vouchers, "count": len(vouchers)}
    except LocalAuthenticationError as e:
        return {"error": "authentication_failed", "message": str(e)}
    except LocalConnectionError as e:
        return {"error": "connection_failed", "message": str(e)}
    except LocalAPIError as e:
        return {"error": "api_error", "message": str(e)}


@server.tool()
async def unifi_lo_create_voucher(
    count: int = 1,
    duration_minutes: int = 1440,
    quota_mb: int = 0,
    upload_kbps: int = 0,
    download_kbps: int = 0,
    note: str | None = None,
) -> dict:
    """Create guest WiFi voucher(s).

    Args:
        count: Number of vouchers to create (default: 1)
        duration_minutes: Voucher duration in minutes (default: 1440 = 24 hours)
        quota_mb: Data quota in MB, 0 for unlimited (default: 0)
        upload_kbps: Upload speed limit in kbps, 0 for unlimited (default: 0)
        download_kbps: Download speed limit in kbps, 0 for unlimited (default: 0)
        note: Optional note/description for the voucher(s)

    Returns the created voucher codes.
    """
    try:
        client = get_local_client()
        vouchers = await client.create_voucher(
            count=count,
            duration=duration_minutes,
            quota=quota_mb,
            up_limit=upload_kbps,
            down_limit=download_kbps,
            note=note,
        )
        return {
            "success": True,
            "vouchers": vouchers,
            "count": len(vouchers),
            "duration_minutes": duration_minutes,
        }
    except LocalAuthenticationError as e:
        return {"error": "authentication_failed", "message": str(e)}
    except LocalConnectionError as e:
        return {"error": "connection_failed", "message": str(e)}
    except LocalAPIError as e:
        return {"error": "api_error", "message": str(e)}


# =============================================================================
# Entry Point
# =============================================================================


def main():
    """Run the MCP server."""
    server.run()


if __name__ == "__main__":
    main()
