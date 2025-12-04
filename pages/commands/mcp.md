# Claude Desktop Integration

Control your UniFi network using natural language through Claude Desktop.

## Overview

UI-CLI includes an MCP (Model Context Protocol) server that enables Claude Desktop to manage your UniFi infrastructure. Ask questions like:

- "How many devices are connected to my network?"
- "What's my network health status?"
- "Block the kids iPad"
- "Restart the garage access point"

## Architecture

```
┌─────────────────┐
│  Claude Desktop │
└────────┬────────┘
         │ MCP Protocol (stdio)
         ▼
┌─────────────────┐
│   MCP Server    │  ← 21 AI-optimized tools
│   (ui_mcp)      │
└────────┬────────┘
         │ subprocess
         ▼
┌─────────────────┐
│    UI CLI       │  ← All business logic
│   (ui_cli)      │
└─────────────────┘
```

## Installation

### Prerequisites

- Python 3.11+ with conda environment `ui-cli`
- Claude Desktop installed
- UniFi credentials configured in `.env`

### Setup

```bash
# Install MCP server to Claude Desktop
./ui mcp install

# Verify installation
./ui mcp check

# View current config
./ui mcp show
```

After installation, restart Claude Desktop to load the new tools.

## Available Tools

### Status & Health

| Tool | Description | Example Prompt |
|------|-------------|----------------|
| `network_status` | Check API connectivity | "Is my network API working?" |
| `network_health` | Site health summary | "What's my network health?" |
| `internet_speed` | Last speed test result | "What's my internet speed?" |
| `run_speedtest` | Run new speed test | "Run a speed test" |
| `isp_performance` | ISP metrics over time | "How's my ISP been performing?" |

### Counts & Lists

| Tool | Description | Example Prompt |
|------|-------------|----------------|
| `client_count` | Count clients by category | "How many devices are connected?" |
| `device_list` | List UniFi devices | "What UniFi devices do I have?" |
| `network_list` | List networks/VLANs | "Show my networks" |

### Lookups

| Tool | Description | Example Prompt |
|------|-------------|----------------|
| `find_client` | Find client by name/MAC | "Find my iPhone" |
| `find_device` | Find device by name/MAC/IP | "Show the living room AP" |
| `client_status` | Check if client is online/blocked | "Is the TV online?" |

### Actions

| Tool | Description | Example Prompt |
|------|-------------|----------------|
| `block_client` | Block from network | "Block the kids iPad" |
| `unblock_client` | Restore access | "Unblock the kids iPad" |
| `kick_client` | Force disconnect | "Disconnect my laptop" |
| `restart_device` | Reboot device | "Restart the garage AP" |
| `create_voucher` | Create guest WiFi code | "Create a guest WiFi voucher" |

### Groups

| Tool | Description | Example Prompt |
|------|-------------|----------------|
| `list_groups` | List all client groups | "What groups do I have?" |
| `get_group` | Get group details | "Show the kids devices group" |
| `block_group` | Block all clients in group | "Block all kids devices" |
| `unblock_group` | Unblock all clients in group | "Unblock the kids devices" |
| `group_status` | Live status of group members | "Are the kids devices online?" |

## Example Conversations

### Checking Network Status

> **You:** How many devices are connected to my network?
>
> **Claude:** You have 87 devices connected:
> - 17 wired clients
> - 70 wireless clients
> - 52 on WiFi 6, 18 on WiFi 5

### Managing Clients

> **You:** Block the kids iPad
>
> **Claude:** I'll block that device. Looking for "kids iPad"...
>
> Found: Kids-iPad (MAC: aa:bb:cc:dd:ee:ff)
>
> Done! Kids-iPad has been blocked from the network.

### Device Management

> **You:** Restart the garage access point
>
> **Claude:** I'll restart that device. Looking for "garage"...
>
> Found: Garage-AP (U6-Lite)
>
> Restart initiated. The access point will be back online in about 2 minutes.

## Troubleshooting

### Tools Not Appearing

1. Restart Claude Desktop after running `./ui mcp install`
2. Check that `.env` file exists with credentials
3. Run `./ui mcp check` to verify setup

### "Conda environment not found"

Ensure the conda environment is activated when installing:

```bash
conda activate ui-cli
./ui mcp install
```

### Timeout Errors

Some operations like speed tests take longer. Claude will wait up to 60 seconds for these operations.

### View Logs

Check MCP server logs in Claude Desktop:

- **macOS:** `~/Library/Logs/Claude/mcp*.log`

## Configuration

The installer adds this to Claude Desktop's config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "ui-cli": {
      "command": "/path/to/ui-cmd/scripts/mcp-server.sh",
      "args": [],
      "env": {
        "PYTHON_PATH": "/path/to/conda/envs/ui-cli/bin/python"
      }
    }
  }
}
```

## Security Notes

- Credentials are stored in `.env` file (not in Claude Desktop config)
- Claude will ask for confirmation before performing destructive actions
- All operations are logged

## Version

Current MCP Server version: **0.3.0** (Tools Layer Architecture)
