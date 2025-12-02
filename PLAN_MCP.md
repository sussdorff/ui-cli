# UI-CLI MCP Server Implementation Plan

## Overview

Wrap existing ui-cli functionality as an MCP (Model Context Protocol) server, enabling Claude Desktop to manage UniFi infrastructure directly.

## Architecture

```
Claude Desktop (MCP enabled)
         ↓
    stdio | JSON-RPC 2.0
         ↓
UI-CLI MCP Server (src/mcp/)
  ├─ server.py          # FastMCP server + entry point
  ├─ cloud_tools.py     # Cloud API tools (5)
  └─ local_tools.py     # Local Controller tools (15+)
         ↓
    Direct Python imports
         ↓
┌─────────────────────┐  ┌─────────────────────────┐
│  ui_cli.client      │  │  ui_cli.local_client    │
│  UniFiClient        │  │  UniFiLocalClient       │
└──────────┬──────────┘  └────────────┬────────────┘
           ↓                          ↓
      api.ui.com              Local Controller
                              (192.168.x.x)
```

**Key Design Decision:** No intermediate HTTP API server - MCP tools call client classes directly.

---

## Package Structure

```
src/mcp/
├── __init__.py           # Package init, version
├── __main__.py           # Entry point: python -m mcp
├── server.py             # FastMCP server, tool registration
├── cloud_tools.py        # Cloud API tool implementations
├── local_tools.py        # Local Controller tool implementations
└── config.py             # MCP-specific configuration
```

---

## Tool Inventory

### Cloud API Tools (5 tools)

| Tool | Wraps | Parameters | Description |
|------|-------|------------|-------------|
| `unifi_status` | `UniFiClient` | - | Check Cloud API connection |
| `unifi_list_hosts` | `list_hosts()` | - | List all controllers |
| `unifi_list_sites` | `list_sites()` | - | List all sites |
| `unifi_list_devices` | `list_devices()` | `host_id?` | List devices, optionally by host |
| `unifi_isp_metrics` | `get_isp_metrics()` | `interval?, hours?` | ISP performance metrics |

### Local Controller Tools (18 tools)

**Clients (6 tools):**
| Tool | Wraps | Parameters | Description |
|------|-------|------------|-------------|
| `unifi_lo_list_clients` | `list_clients()` | `filter?` | Connected clients |
| `unifi_lo_get_client` | `get_client()` | `identifier` | Client details by name/MAC |
| `unifi_lo_block_client` | `block_client()` | `identifier` | Block a client |
| `unifi_lo_unblock_client` | `unblock_client()` | `identifier` | Unblock a client |
| `unifi_lo_kick_client` | `kick_client()` | `identifier` | Disconnect a client |
| `unifi_lo_all_clients` | `list_all_clients()` | - | All clients (inc. offline) |

**Devices (4 tools):**
| Tool | Wraps | Parameters | Description |
|------|-------|------------|-------------|
| `unifi_lo_list_devices` | `get_devices()` | - | List network devices |
| `unifi_lo_restart_device` | `restart_device()` | `identifier` | Restart a device |
| `unifi_lo_locate_device` | `locate_device()` | `identifier, enabled?` | Toggle locate LED |
| `unifi_lo_upgrade_device` | `upgrade_device()` | `identifier` | Upgrade firmware |

**Networks & Firewall (3 tools):**
| Tool | Wraps | Parameters | Description |
|------|-------|------------|-------------|
| `unifi_lo_list_networks` | `get_networks()` | - | List networks/VLANs |
| `unifi_lo_firewall_rules` | `get_firewall_rules()` | `ruleset?` | Firewall rules |
| `unifi_lo_port_forwards` | `get_port_forwards()` | - | Port forwarding rules |

**Monitoring (3 tools):**
| Tool | Wraps | Parameters | Description |
|------|-------|------------|-------------|
| `unifi_lo_health` | `get_health()` | - | Site health summary |
| `unifi_lo_events` | `get_events()` | `limit?` | Recent events |
| `unifi_lo_dpi_stats` | `get_site_dpi()` | - | DPI statistics |

**Vouchers (2 tools):**
| Tool | Wraps | Parameters | Description |
|------|-------|------------|-------------|
| `unifi_lo_list_vouchers` | `get_vouchers()` | - | List guest vouchers |
| `unifi_lo_create_voucher` | `create_voucher()` | `count?, duration?, quota?` | Create voucher(s) |

**Total: 23 MCP tools**

---

## Implementation Details

### 1. Dependencies

Add to `pyproject.toml`:
```toml
[project.optional-dependencies]
mcp = ["mcp>=1.0.0"]
```

### 2. Server Entry Point (`src/mcp/server.py`)

```python
from mcp.server import FastMCP
from ui_cli.client import UniFiClient
from ui_cli.local_client import UniFiLocalClient

# Initialize FastMCP server
server = FastMCP("ui-cli")

# Lazy client initialization (created on first tool call)
_cloud_client: UniFiClient | None = None
_local_client: UniFiLocalClient | None = None

def get_cloud_client() -> UniFiClient:
    global _cloud_client
    if _cloud_client is None:
        _cloud_client = UniFiClient()
    return _cloud_client

def get_local_client() -> UniFiLocalClient:
    global _local_client
    if _local_client is None:
        _local_client = UniFiLocalClient()
    return _local_client
```

### 3. Tool Registration Pattern

```python
@server.tool()
async def unifi_list_hosts() -> dict:
    """List all UniFi controllers associated with the account."""
    client = get_cloud_client()
    hosts = await client.list_hosts()
    return {"hosts": hosts, "count": len(hosts)}

@server.tool()
async def unifi_lo_list_clients(
    filter: str | None = None
) -> dict:
    """List connected clients on the local controller.

    Args:
        filter: Optional filter - 'wired', 'wireless', or network name
    """
    client = get_local_client()
    clients = await client.list_clients()

    if filter:
        if filter.lower() == "wired":
            clients = [c for c in clients if c.get("is_wired")]
        elif filter.lower() == "wireless":
            clients = [c for c in clients if not c.get("is_wired")]
        else:
            # Filter by network name
            clients = [c for c in clients if filter.lower() in c.get("network", "").lower()]

    return {"clients": clients, "count": len(clients)}
```

### 4. Client Identifier Resolution

Many tools accept a "name or MAC" identifier. Add a helper:

```python
async def resolve_client_mac(client: UniFiLocalClient, identifier: str) -> str:
    """Resolve a client name to MAC address, or return MAC if already valid."""
    # Check if already a MAC address
    if ":" in identifier or "-" in identifier:
        return identifier.lower().replace("-", ":")

    # Search by name
    clients = await client.list_clients()
    for c in clients:
        if c.get("name", "").lower() == identifier.lower():
            return c.get("mac", "")
        if c.get("hostname", "").lower() == identifier.lower():
            return c.get("mac", "")

    raise ValueError(f"Client not found: {identifier}")
```

### 5. Error Handling

```python
from ui_cli.client import APIError, AuthenticationError
from ui_cli.local_client import LocalAPIError, LocalAuthenticationError

@server.tool()
async def unifi_lo_block_client(identifier: str) -> dict:
    """Block a client by name or MAC address."""
    try:
        client = get_local_client()
        mac = await resolve_client_mac(client, identifier)
        success = await client.block_client(mac)
        return {"success": success, "mac": mac, "action": "blocked"}
    except LocalAuthenticationError as e:
        return {"error": "authentication_failed", "message": str(e)}
    except LocalAPIError as e:
        return {"error": "api_error", "message": str(e)}
    except ValueError as e:
        return {"error": "not_found", "message": str(e)}
```

---

## Configuration

### Environment Variables

MCP server uses same env vars as CLI:

```bash
# Cloud API
UNIFI_API_KEY=your-api-key

# Local Controller
UNIFI_CONTROLLER_URL=https://192.168.1.1
UNIFI_CONTROLLER_USERNAME=admin
UNIFI_CONTROLLER_PASSWORD=yourpassword
UNIFI_CONTROLLER_SITE=default
UNIFI_CONTROLLER_VERIFY_SSL=false
```

### Claude Desktop Configuration

`~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ui-cli": {
      "command": "/opt/anaconda3/envs/ui-cli/bin/python",
      "args": ["-m", "mcp"],
      "cwd": "/Users/vedanta/ui-cmd/src",
      "env": {
        "PYTHONUNBUFFERED": "1",
        "UNIFI_API_KEY": "your-api-key",
        "UNIFI_CONTROLLER_URL": "https://192.168.1.1",
        "UNIFI_CONTROLLER_USERNAME": "admin",
        "UNIFI_CONTROLLER_PASSWORD": "yourpassword",
        "UNIFI_CONTROLLER_SITE": "default",
        "UNIFI_CONTROLLER_VERIFY_SSL": "false"
      }
    }
  }
}
```

---

## Implementation Phases

### Phase 1: Core Setup
- [ ] Create `src/mcp/` package structure
- [ ] Add mcp dependency to pyproject.toml
- [ ] Implement server.py with FastMCP initialization
- [ ] Add `__main__.py` entry point

### Phase 2: Cloud API Tools
- [ ] `unifi_status` - connection check
- [ ] `unifi_list_hosts` - list controllers
- [ ] `unifi_list_sites` - list sites
- [ ] `unifi_list_devices` - list devices
- [ ] `unifi_isp_metrics` - ISP metrics

### Phase 3: Local Controller Tools (Clients)
- [ ] `unifi_lo_list_clients` - connected clients
- [ ] `unifi_lo_all_clients` - all clients
- [ ] `unifi_lo_get_client` - client details
- [ ] `unifi_lo_block_client` - block client
- [ ] `unifi_lo_unblock_client` - unblock client
- [ ] `unifi_lo_kick_client` - disconnect client

### Phase 4: Local Controller Tools (Devices & Network)
- [ ] `unifi_lo_list_devices` - network devices
- [ ] `unifi_lo_restart_device` - restart device
- [ ] `unifi_lo_locate_device` - locate LED
- [ ] `unifi_lo_upgrade_device` - upgrade firmware
- [ ] `unifi_lo_list_networks` - networks/VLANs
- [ ] `unifi_lo_firewall_rules` - firewall rules
- [ ] `unifi_lo_port_forwards` - port forwards

### Phase 5: Local Controller Tools (Monitoring & Vouchers)
- [ ] `unifi_lo_health` - site health
- [ ] `unifi_lo_events` - recent events
- [ ] `unifi_lo_dpi_stats` - DPI statistics
- [ ] `unifi_lo_list_vouchers` - guest vouchers
- [ ] `unifi_lo_create_voucher` - create vouchers

### Phase 6: Documentation & Testing
- [ ] Add MCP_GUIDE.md documentation
- [ ] Update README with MCP section
- [ ] Test with Claude Desktop
- [ ] Add troubleshooting guide

---

## Usage Examples

Once configured, users can interact naturally:

```
User: "How many devices are connected to my network?"
Claude: [calls unifi_lo_list_clients]
Response: "You have 23 clients connected - 8 wired and 15 wireless."

User: "Block the device called 'kids-ipad'"
Claude: [calls unifi_lo_block_client(identifier="kids-ipad")]
Response: "I've blocked kids-ipad (MAC: aa:bb:cc:dd:ee:ff)."

User: "What's my ISP latency looking like this week?"
Claude: [calls unifi_isp_metrics(hours=168)]
Response: "Your average latency this week was 12ms, with a max of 45ms..."

User: "Restart the office access point"
Claude: [calls unifi_lo_restart_device(identifier="Office-AP")]
Response: "Restarting Office-AP. It should be back online in about 2 minutes."
```

---

## File Deliverables

| File | Lines (est.) | Description |
|------|--------------|-------------|
| `src/mcp/__init__.py` | 10 | Package init |
| `src/mcp/__main__.py` | 15 | Entry point |
| `src/mcp/server.py` | 80 | FastMCP server setup |
| `src/mcp/cloud_tools.py` | 100 | 5 cloud tools |
| `src/mcp/local_tools.py` | 250 | 18 local tools |
| `src/mcp/helpers.py` | 50 | Shared utilities |
| `MCP_GUIDE.md` | 200 | User documentation |
| **Total** | **~700** | |

---

## Security Considerations

1. **Credentials in config** - Claude Desktop config contains passwords; protect file permissions
2. **Destructive actions** - Block/kick/restart are confirmed by Claude before execution
3. **Local-only by default** - No network exposure; MCP uses stdio
4. **Session management** - Reuses existing ui-cli session handling
5. **SSL verification** - Follows existing `UNIFI_CONTROLLER_VERIFY_SSL` setting
