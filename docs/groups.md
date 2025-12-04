# Client Groups

Client groups allow you to create named collections of devices for bulk actions like blocking, unblocking, and monitoring.

## Overview

- **Static Groups** - Manually managed membership by MAC address
- **Auto Groups** - Dynamic membership based on pattern rules (vendor, hostname, network, IP)
- **Bulk Actions** - Block/unblock/kick all devices in a group at once
- **Local Storage** - Groups stored in `~/.config/ui-cli/groups.json`

## Storage

Groups are stored locally at:

```
~/.config/ui-cli/groups.json
```

### Schema

```json
{
  "version": 1,
  "groups": {
    "kids-devices": {
      "name": "Kids Devices",
      "description": "Tablets and phones for the kids",
      "type": "static",
      "members": [
        {"mac": "AA:BB:CC:DD:EE:FF", "alias": "Timmy iPad"},
        {"mac": "11:22:33:44:55:66", "alias": "Sarah Phone"}
      ],
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:35:00Z"
    },
    "apple-devices": {
      "name": "Apple Devices",
      "type": "auto",
      "rules": {
        "vendor": ["Apple"]
      },
      "created_at": "2024-01-15T11:00:00Z",
      "updated_at": "2024-01-15T11:00:00Z"
    }
  }
}
```

## Implementation

### Core Module

`src/ui_cli/groups.py` - GroupManager class:

- Pydantic models for data validation
- JSON file persistence with lazy loading
- Group CRUD operations
- Member CRUD operations
- Auto group pattern matching

### CLI Commands

`src/ui_cli/commands/groups.py` - Typer commands:

| Command | Description |
|---------|-------------|
| `groups list` | List all groups |
| `groups create` | Create static group |
| `groups auto` | Create auto group with rules |
| `groups show` | Show group details |
| `groups delete` | Delete a group |
| `groups edit` | Edit name/description |
| `groups add` | Add member to group |
| `groups remove` | Remove member |
| `groups alias` | Set member alias |
| `groups members` | List members |
| `groups clear` | Remove all members |
| `groups export` | Export to JSON |
| `groups import` | Import from JSON |

### Bulk Actions

`src/ui_cli/commands/local/clients.py` - Added `--group` / `-g` flag:

- `list -g <group>` - Filter clients by group
- `block -g <group>` - Block all in group
- `unblock -g <group>` - Unblock all in group
- `kick -g <group>` - Kick all in group

### MCP Tools

`src/ui_mcp/server.py` - 5 new tools:

| Tool | Description |
|------|-------------|
| `list_groups` | List all groups |
| `get_group` | Get group details |
| `block_group` | Block all in group |
| `unblock_group` | Unblock all in group |
| `group_status` | Live status of group members |

## Pattern Matching

Auto groups support multiple pattern formats:

| Format | Example | Description |
|--------|---------|-------------|
| Exact | `Apple` | Exact match |
| Wildcard | `*phone*` | Contains "phone" |
| Regex | `~^iPhone-[0-9]+$` | Regex (prefix with ~) |
| Multiple | `Apple,Samsung` | OR logic (comma-separated) |

### Rule Types

| Rule | Matches Against |
|------|-----------------|
| `--vendor` | Device vendor/OUI |
| `--name` | Client display name |
| `--hostname` | Client hostname |
| `--network` | Network/SSID name |
| `--ip` | IP address (supports CIDR, ranges) |
| `--mac` | MAC address prefix |
| `--type` | Connection type (wired/wireless) |

Multiple rules of the same type use **OR** logic.
Different rule types use **AND** logic.

## Use Cases

1. **Parental Controls** - Block kids' devices at bedtime
2. **IoT Management** - Group smart home devices by vendor
3. **Guest Monitoring** - Track devices on guest network
4. **Server Isolation** - Group servers by IP range
