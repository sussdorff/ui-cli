# MCP Server

The UI-CLI MCP server exposes UniFi management tools to Claude Desktop via the Model Context Protocol.

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

## How It Works

1. **Claude Desktop** connects to the MCP server via stdio
2. **FastMCP Server** (`server.py`) registers 21 tools with friendly names
3. **CLI Runner** (`cli_runner.py`) executes `./ui` commands via subprocess
4. **UI CLI** performs the actual API calls and returns JSON
5. **Results** flow back through the chain to Claude

### Why Subprocess?

The architecture uses subprocess calls instead of direct Python imports because:

- **Single source of truth** - CLI handles all logic, formatting, error handling
- **Consistent behavior** - Same output as terminal usage
- **Easier debugging** - Test tools by running CLI directly
- **Simpler maintenance** - Add MCP tool = call existing CLI command

## File Structure

```
src/ui_mcp/
├── __init__.py       # Package init, version
├── __main__.py       # Entry point: python -m ui_mcp
├── server.py         # FastMCP server + 21 tool definitions
├── cli_runner.py     # Subprocess wrapper for CLI calls
└── README.md         # User documentation
```

## Available Tools

### Status & Health (5 tools)
- `network_status` - Check API connectivity
- `network_health` - Site health summary
- `internet_speed` - Last speed test result
- `run_speedtest` - Run new speed test
- `isp_performance` - ISP metrics over time

### Counts & Lists (3 tools)
- `client_count` - Count clients by category
- `device_list` - List UniFi devices
- `network_list` - List networks/VLANs

### Lookups (3 tools)
- `find_client` - Find client by name/MAC
- `find_device` - Find device by name/MAC/IP
- `client_status` - Check if client is online/blocked

### Actions (5 tools)
- `block_client` - Block from network
- `unblock_client` - Restore access
- `kick_client` - Force disconnect
- `restart_device` - Reboot device
- `create_voucher` - Create guest WiFi code

### Groups (5 tools)
- `list_groups` - List all client groups
- `get_group` - Get group details
- `block_group` - Block all in group
- `unblock_group` - Unblock all in group
- `group_status` - Live status of group members

## Adding New Tools

1. Add CLI command with `--output json` support
2. Add tool function in `server.py`:

```python
@server.tool()
async def my_new_tool(param: str) -> str:
    """Tool description shown to Claude.

    Args:
        param: Parameter description
    """
    result = run_cli(["lo", "mycommand", param])
    if "error" in result:
        return format_result(result)
    return format_result(result, "Human-readable summary")
```

3. Test with `python scripts/test-mcp-tools.py`

## Installation

```bash
# Install MCP server to Claude Desktop
./ui mcp install

# Verify installation
./ui mcp check

# View current config
./ui mcp show

# Remove from Claude Desktop
./ui mcp remove
```

## Configuration

The installer adds this to Claude Desktop's config:

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

## Debugging

Check MCP server logs in Claude Desktop:
- macOS: `~/Library/Logs/Claude/mcp*.log`

Test CLI runner directly:

```python
from ui_mcp.cli_runner import run_cli
result = run_cli(["lo", "health"])
print(result)
```
