# UI-CLI MCP Server Guide

Complete guide to using the UI-CLI Model Context Protocol (MCP) server with Claude Desktop.

## Overview

The UI-CLI MCP server enables Claude Desktop to manage your UniFi infrastructure through natural language. It provides 23 tools for managing controllers, devices, clients, networks, and more.

### Architecture

```
Claude Desktop (with MCP enabled)
         ↓
    stdio | JSON-RPC 2.0
         ↓
UI-CLI MCP Server (Python)
  ├─ Cloud Tools (5)
  └─ Local Tools (18)
         ↓
    Direct Python calls
         ↓
┌─────────────────┐  ┌───────────────────┐
│  UniFiClient    │  │ UniFiLocalClient  │
│  (Cloud API)    │  │ (Local Controller)│
└────────┬────────┘  └─────────┬─────────┘
         ↓                     ↓
    api.ui.com           192.168.x.x
```

## Quick Start

### 1. Install Dependencies

```bash
cd /Users/vedanta/ui-cmd
pip install -e ".[mcp]"
```

### 2. Configure Environment

Ensure your `.env` file has the required credentials:

```bash
# Cloud API (api.ui.com)
UNIFI_API_KEY=your-api-key-here

# Local Controller (direct connection)
UNIFI_CONTROLLER_URL=https://192.168.1.1
UNIFI_CONTROLLER_USERNAME=admin
UNIFI_CONTROLLER_PASSWORD=yourpassword
UNIFI_CONTROLLER_SITE=default
UNIFI_CONTROLLER_VERIFY_SSL=false
```

### 3. Configure Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ui-cli": {
      "command": "/opt/anaconda3/envs/ui-cli/bin/python",
      "args": ["-m", "ui_mcp"],
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

**Note:** Update the Python path to match your environment (`which python`).

### 4. Restart Claude Desktop

- Quit Claude Desktop completely
- Restart it
- Tools should appear in the tools panel

## Available Tools

### Cloud API Tools (5 tools)

| Tool | Purpose | Example Prompt |
|------|---------|----------------|
| `unifi_status` | Check API connection | "Check my UniFi connection" |
| `unifi_list_hosts` | List controllers | "Show all my UniFi controllers" |
| `unifi_list_sites` | List sites | "What sites do I have?" |
| `unifi_list_devices` | List devices | "List all devices on controller X" |
| `unifi_isp_metrics` | ISP performance | "How's my ISP latency this week?" |

### Local Controller Tools - Clients (6 tools)

| Tool | Purpose | Example Prompt |
|------|---------|----------------|
| `unifi_lo_list_clients` | Connected clients | "Who's on my network?" |
| `unifi_lo_all_clients` | All known clients | "Show all devices that have connected" |
| `unifi_lo_get_client` | Client details | "Get info on my-iPhone" |
| `unifi_lo_block_client` | Block client | "Block the device called kids-ipad" |
| `unifi_lo_unblock_client` | Unblock client | "Unblock kids-ipad" |
| `unifi_lo_kick_client` | Disconnect client | "Disconnect my-laptop" |

### Local Controller Tools - Devices (4 tools)

| Tool | Purpose | Example Prompt |
|------|---------|----------------|
| `unifi_lo_list_devices` | Network devices | "Show all APs and switches" |
| `unifi_lo_restart_device` | Restart device | "Restart the office AP" |
| `unifi_lo_locate_device` | Toggle locate LED | "Help me find the basement AP" |
| `unifi_lo_upgrade_device` | Upgrade firmware | "Update firmware on Living-Room-AP" |

### Local Controller Tools - Networks (3 tools)

| Tool | Purpose | Example Prompt |
|------|---------|----------------|
| `unifi_lo_list_networks` | Networks/VLANs | "Show all my VLANs" |
| `unifi_lo_firewall_rules` | Firewall rules | "Show WAN_IN firewall rules" |
| `unifi_lo_port_forwards` | Port forwards | "What ports are forwarded?" |

### Local Controller Tools - Monitoring (4 tools)

| Tool | Purpose | Example Prompt |
|------|---------|----------------|
| `unifi_lo_health` | Site health | "Is my network healthy?" |
| `unifi_lo_events` | Recent events | "Show last 20 events" |
| `unifi_lo_dpi_stats` | DPI statistics | "What apps are using bandwidth?" |
| `unifi_lo_daily_stats` | Traffic stats | "Show bandwidth usage this month" |

### Local Controller Tools - Vouchers (2 tools)

| Tool | Purpose | Example Prompt |
|------|---------|----------------|
| `unifi_lo_list_vouchers` | List vouchers | "Show guest WiFi vouchers" |
| `unifi_lo_create_voucher` | Create vouchers | "Create 5 guest vouchers for 2 hours" |

## Usage Examples

### Example 1: Check Network Status
```
User: "How many devices are on my network right now?"
Claude: [calls unifi_lo_list_clients]
Response: "You have 23 clients connected - 8 wired and 15 wireless."
```

### Example 2: Block a Device
```
User: "Block the device called 'kids-ipad'"
Claude: [calls unifi_lo_block_client(identifier="kids-ipad")]
Response: "I've blocked kids-ipad (MAC: aa:bb:cc:dd:ee:ff). It can no longer access the network."
```

### Example 3: ISP Performance
```
User: "What's my ISP latency looking like this week?"
Claude: [calls unifi_isp_metrics(hours=168)]
Response: "Your average latency this week was 12ms, with a max of 45ms on Tuesday evening."
```

### Example 4: Restart a Device
```
User: "The office AP seems slow, can you restart it?"
Claude: [calls unifi_lo_restart_device(identifier="Office-AP")]
Response: "Restarting Office-AP. It should be back online in about 2 minutes."
```

### Example 5: Create Guest Vouchers
```
User: "Create 10 guest vouchers that last 4 hours each"
Claude: [calls unifi_lo_create_voucher(count=10, duration_minutes=240)]
Response: "Created 10 vouchers valid for 4 hours each: ABC123, DEF456, ..."
```

## Troubleshooting

### Tools Not Appearing in Claude Desktop

1. **Check config file exists:**
   ```bash
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

2. **Verify JSON is valid:** Use a JSON validator

3. **Check Python path:**
   ```bash
   which python
   # Use this exact path in config
   ```

4. **Test MCP server directly:**
   ```bash
   cd /Users/vedanta/ui-cmd/src
   python -m mcp
   # Should start without errors
   ```

5. **Check Claude Desktop logs:** Help → Logs

### Authentication Errors

**Cloud API:**
- Verify `UNIFI_API_KEY` is correct
- Get new key at [unifi.ui.com](https://unifi.ui.com) → Settings → API

**Local Controller:**
- Verify URL, username, password are correct
- Test credentials in UniFi web UI first
- Set `UNIFI_CONTROLLER_VERIFY_SSL=false` for self-signed certs

### Connection Errors

- Check controller URL is reachable: `curl -k https://192.168.1.1`
- Verify you're on the same network as the controller
- Check firewall isn't blocking the connection

## Security Considerations

1. **Credentials in config:** Claude Desktop config contains passwords. Protect file permissions:
   ```bash
   chmod 600 ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

2. **Destructive actions:** Block/kick/restart require confirmation from Claude

3. **Local-only:** MCP uses stdio - no network exposure

4. **Session management:** Uses existing ui-cli session handling with automatic re-auth

## Development

### Testing Manually

```bash
# Test Cloud API
cd /Users/vedanta/ui-cmd
./ui status

# Test Local API
./ui lo clients list

# Test MCP server startup
cd src && python -m ui_mcp
# Ctrl+C to stop
```

### Adding New Tools

1. Add method to `UniFiClient` or `UniFiLocalClient` if needed
2. Add tool function in `server.py`:
   ```python
   @server.tool()
   async def unifi_new_tool(param: str) -> dict:
       """Tool description."""
       client = get_local_client()
       result = await client.new_method(param)
       return {"result": result}
   ```

## Version Info

- **MCP Server Version:** 0.1.0
- **Python:** 3.10+
- **FastMCP SDK:** mcp>=1.0.0
