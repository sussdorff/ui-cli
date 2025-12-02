"""Helper utilities for MCP tools."""

from typing import Any

from ui_cli.local_client import UniFiLocalClient


async def resolve_client_mac(client: UniFiLocalClient, identifier: str) -> str:
    """Resolve a client name to MAC address, or return MAC if already valid.

    Args:
        client: UniFi local client instance
        identifier: Client name, hostname, or MAC address

    Returns:
        MAC address in lowercase colon-separated format

    Raises:
        ValueError: If client cannot be found by name
    """
    # Check if already a MAC address
    if ":" in identifier or "-" in identifier:
        return identifier.lower().replace("-", ":")

    # Search by name in connected clients
    clients = await client.list_clients()
    for c in clients:
        name = c.get("name", "").lower()
        hostname = c.get("hostname", "").lower()
        if name == identifier.lower() or hostname == identifier.lower():
            return c.get("mac", "")

    # Also check all known clients (including offline)
    all_clients = await client.list_all_clients()
    for c in all_clients:
        name = c.get("name", "").lower()
        hostname = c.get("hostname", "").lower()
        if name == identifier.lower() or hostname == identifier.lower():
            return c.get("mac", "")

    raise ValueError(f"Client not found: {identifier}")


async def resolve_device_mac(client: UniFiLocalClient, identifier: str) -> str:
    """Resolve a device name to MAC address, or return MAC if already valid.

    Args:
        client: UniFi local client instance
        identifier: Device name or MAC address

    Returns:
        MAC address in lowercase colon-separated format

    Raises:
        ValueError: If device cannot be found by name
    """
    # Check if already a MAC address
    if ":" in identifier or "-" in identifier:
        return identifier.lower().replace("-", ":")

    # Search by name
    devices = await client.get_devices()
    for d in devices:
        name = d.get("name", "").lower()
        if name == identifier.lower():
            return d.get("mac", "")

    raise ValueError(f"Device not found: {identifier}")


def format_bytes(bytes_val: int | float | None) -> str:
    """Format bytes to human readable string."""
    if bytes_val is None:
        return "N/A"

    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(bytes_val) < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} PB"


def safe_get(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Safely get nested dictionary value."""
    result = data
    for key in keys:
        if isinstance(result, dict):
            result = result.get(key, default)
        else:
            return default
    return result
