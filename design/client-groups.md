# Client Groups Design

## Overview

Client Groups is a native ui-cli feature that allows users to create, manage, and perform bulk actions on named groups of client devices. Groups are stored locally and persist across sessions.

This feature fills a gap in UniFi's native feature set - there is no built-in way to group arbitrary client devices for bulk actions.

## Use Cases

- **Parental Controls**: Group children's devices → block/unblock at bedtime
- **Smart Home**: Group IoT devices by type (bulbs, cameras, thermostats)
- **Guest Management**: Group guest devices for monitoring
- **Network Segments**: Group devices by location (office, living room)
- **Troubleshooting**: Group problematic devices for quick status checks
- **Vendor-based**: Auto-group all Apple, Samsung, or IoT vendor devices

## Storage

### Location
```
~/.config/ui-cli/groups.json
```

Same directory as existing `session.json`, keeping all ui-cli state together.

### Schema
```json
{
  "version": 1,
  "groups": {
    "kids-devices": {
      "name": "Kids Devices",
      "description": "Children's phones and tablets",
      "type": "static",
      "members": [
        {"mac": "AA:BB:CC:DD:EE:01", "alias": "Emma's iPad"},
        {"mac": "AA:BB:CC:DD:EE:02", "alias": "Jake's Phone"}
      ],
      "created_at": "2025-12-03T10:00:00Z",
      "updated_at": "2025-12-03T10:00:00Z"
    },
    "apple-devices": {
      "name": "Apple Devices",
      "description": "Auto-generated: vendor matches Apple",
      "type": "auto",
      "rules": {
        "vendor": ["Apple"]
      },
      "created_at": "2025-12-03T10:00:00Z",
      "updated_at": "2025-12-03T10:00:00Z"
    },
    "iot-devices": {
      "name": "IoT Devices",
      "description": "Smart home devices",
      "type": "auto",
      "rules": {
        "vendor": ["Philips", "LIFX", "Ring", "Nest", "ecobee", "TP-Link"],
        "name": ["*bulb*", "*camera*", "*thermostat*"]
      },
      "created_at": "2025-12-03T10:00:00Z",
      "updated_at": "2025-12-03T10:00:00Z"
    }
  }
}
```

### Design Decisions

1. **MAC-based membership**: Static groups store MAC addresses. MACs are stable identifiers; client names can change.

2. **Two group types**:
   - `static`: Manual membership, stored MAC addresses
   - `auto`: Dynamic membership based on rules, evaluated at runtime

3. **Optional aliases**: Each static member can have an alias for display purposes.

4. **Slug-based keys**: Group identifiers are URL-safe slugs (lowercase, hyphens).

5. **Version field**: Allows future schema migrations.

---

## Commands

### Command Structure

```
./ui groups <command>              # Group management (top-level, no controller needed)
./ui lo clients <command> --group  # Bulk actions (requires controller)
```

Groups are managed at the top level since they're local storage and don't require controller access (except auto-groups which query live data).

---

## Group Management Commands

### List Groups

```bash
./ui groups list                    # List all groups
./ui groups ls                      # Alias
./ui groups list -o json            # JSON output
```

### Create Static Group

```bash
./ui groups create <name>                           # Create empty group
./ui groups create <name> -d "description"          # With description

# Examples
./ui groups create "Kids Devices"
./ui groups create "Smart Bulbs" -d "Philips Hue and LIFX bulbs"
```

### Show Group

```bash
./ui groups show <name>             # Show group details and members
./ui groups show <name> -o json     # JSON output

# Examples
./ui groups show kids-devices
./ui groups show "Kids Devices"     # Name or slug works
```

### Delete Group

```bash
./ui groups delete <name>           # Delete a group (with confirmation)
./ui groups delete <name> -y        # Skip confirmation
./ui groups rm <name>               # Alias
```

---

## Group Edit Commands

### Rename Group

```bash
./ui groups edit <name> --name <new-name>
./ui groups edit <name> -n <new-name>

# Example
./ui groups edit kids-devices --name "Children's Devices"
```

### Update Description

```bash
./ui groups edit <name> --description <new-description>
./ui groups edit <name> -d <new-description>

# Example
./ui groups edit kids-devices -d "Tablets and phones for Emma and Jake"
```

### Combined Edit

```bash
./ui groups edit <name> --name "New Name" --description "New description"
```

---

## Member Management Commands (Static Groups)

### Add Members

```bash
./ui groups add <group> <client> [<client>...]      # Add by name or MAC
./ui groups add <group> <client> --alias "Name"     # Add with alias

# Examples
./ui groups add kids-devices "Emma's iPad"
./ui groups add kids-devices AA:BB:CC:DD:EE:01 AA:BB:CC:DD:EE:02
./ui groups add kids-devices "Xbox" --alias "Gaming Console"
```

### Remove Members

```bash
./ui groups remove <group> <client> [<client>...]   # Remove by name/MAC/alias

# Examples
./ui groups remove kids-devices "Emma's iPad"
./ui groups remove kids-devices AA:BB:CC:DD:EE:01
```

### Set/Update Member Alias

```bash
./ui groups alias <group> <client> <alias>          # Set alias
./ui groups alias <group> <client> --clear          # Remove alias

# Examples
./ui groups alias kids-devices AA:BB:CC:DD:EE:01 "Emma's iPad Pro"
```

### Clear All Members

```bash
./ui groups clear <group>                           # Remove all members
./ui groups clear <group> -y                        # Skip confirmation
```

### List Members Only

```bash
./ui groups members <group>                         # List members
./ui groups members <group> -o json                 # JSON output
```

---

## Auto Groups (Pattern-Based)

Auto groups dynamically match clients based on rules. Members are evaluated at runtime against live controller data.

### Create Auto Group

```bash
./ui groups auto <name> [options]

# Filter options (can combine multiple)
--vendor <pattern>          # Match by vendor/manufacturer (OUI)
--name <pattern>            # Match by client name
--hostname <pattern>        # Match by hostname
--network <name>            # Match by network/VLAN
--ip <pattern>              # Match by IP range (CIDR or wildcard)
--mac <pattern>             # Match by MAC prefix

# Pattern syntax
# - Exact match: "Apple"
# - Wildcard: "*camera*", "iPhone*"
# - Multiple values: "Apple,Samsung,Google"
# - Regex (prefix with ~): "~^iPhone-[0-9]+"
```

### Examples

```bash
# Group all Apple devices
./ui groups auto "Apple Devices" --vendor "Apple"

# Group common IoT vendors
./ui groups auto "IoT Devices" --vendor "Philips,LIFX,Ring,Nest,TP-Link,Tuya,Shelly"

# Group by name pattern
./ui groups auto "Cameras" --name "*camera*,*cam*"

# Group by network
./ui groups auto "Guest Devices" --network "Guest WiFi"

# Group by IP range
./ui groups auto "Servers" --ip "192.168.1.100-192.168.1.200"
./ui groups auto "IoT VLAN" --ip "10.0.50.0/24"

# Combine filters (AND logic)
./ui groups auto "Apple on Guest" --vendor "Apple" --network "Guest WiFi"

# Group by MAC prefix (same manufacturer)
./ui groups auto "Ubiquiti Devices" --mac "74:83:C2,78:45:58"

# Regex pattern
./ui groups auto "Numbered iPhones" --name "~^iPhone-[0-9]+"
```

### Edit Auto Group Rules

```bash
# Add a rule
./ui groups edit iot-devices --add-vendor "Govee,Wyze"
./ui groups edit cameras --add-name "*webcam*"

# Remove a rule
./ui groups edit iot-devices --remove-vendor "TP-Link"

# Replace all rules of a type
./ui groups edit iot-devices --vendor "Philips,LIFX,Ring"  # Replaces existing

# Clear rules of a type
./ui groups edit cameras --clear-name
```

### Convert Between Types

```bash
# Convert auto group to static (snapshot current members)
./ui groups convert <name> --to-static

# Convert static group to auto (define rules)
./ui groups convert <name> --to-auto --vendor "Apple"
```

### Preview Auto Group

```bash
# See what would match without creating
./ui groups auto "Test" --vendor "Apple" --dry-run
./ui groups auto "Test" --name "*phone*" --preview
```

---

## Auto Group Rule Reference

| Rule | Description | Examples |
|------|-------------|----------|
| `--vendor` | Match OUI/manufacturer | `Apple`, `Samsung,Google`, `*Link*` |
| `--name` | Match client name | `*phone*`, `Emma*`, `~^iPhone-\d+` |
| `--hostname` | Match system hostname | `*macbook*`, `raspberrypi*` |
| `--network` | Match network/SSID | `Main WiFi`, `Guest*`, `IoT` |
| `--ip` | Match IP address/range | `192.168.1.*`, `10.0.0.0/24`, `192.168.1.100-200` |
| `--mac` | Match MAC prefix | `AA:BB:CC`, `74:83:C2,78:45:58` |
| `--type` | Match connection type | `wired`, `wireless` |

### Pattern Syntax

- **Exact**: `Apple` - matches "Apple" exactly
- **Wildcard**: `*phone*` - matches anything containing "phone"
- **Prefix**: `iPhone*` - matches anything starting with "iPhone"
- **Suffix**: `*-Pro` - matches anything ending with "-Pro"
- **Multiple**: `Apple,Samsung` - matches any in list
- **Regex**: `~^iPhone-[0-9]+$` - prefix with `~` for regex

---

## Bulk Actions on Groups

These require controller access and live under `./ui lo clients`:

```bash
# List clients in a group (with live status from controller)
./ui lo clients list --group <name>
./ui lo clients list -g <name>

# Block all clients in a group
./ui lo clients block --group <name>

# Unblock all clients in a group
./ui lo clients unblock --group <name>

# Kick all clients in a group
./ui lo clients kick --group <name>

# Get status of all clients in a group
./ui lo clients status --group <name>
```

For auto groups, these commands evaluate the rules against current clients before performing the action.

---

## Interactive Mode

```bash
# Interactive group builder - select from current clients
./ui groups create "Kids Devices" --interactive
./ui groups create "Kids Devices" -i

# Interactive add - select clients to add
./ui groups add kids-devices --interactive
./ui groups add kids-devices -i
```

Shows a list of clients from the controller, user selects with arrow keys/space.

---

## Import/Export

```bash
# Export groups to file
./ui groups export                      # Print to stdout
./ui groups export > my-groups.json     # Save to file
./ui groups export -o my-groups.json    # Save to file (explicit)

# Import groups from file
./ui groups import my-groups.json               # Merge with existing
./ui groups import my-groups.json --replace     # Replace all groups
```

---

## Command Summary

| Command | Description |
|---------|-------------|
| `groups list` | List all groups |
| `groups create <name>` | Create a static group |
| `groups auto <name>` | Create an auto group with rules |
| `groups show <name>` | Show group details |
| `groups delete <name>` | Delete a group |
| `groups edit <name>` | Edit group name/description/rules |
| `groups add <group> <client>` | Add member(s) to static group |
| `groups remove <group> <client>` | Remove member(s) from static group |
| `groups alias <group> <client> <alias>` | Set member alias |
| `groups clear <group>` | Remove all members |
| `groups members <group>` | List group members |
| `groups convert <name>` | Convert between static/auto |
| `groups export` | Export groups to JSON |
| `groups import <file>` | Import groups from JSON |
| `lo clients list -g <group>` | List clients in group (live) |
| `lo clients block -g <group>` | Block all in group |
| `lo clients unblock -g <group>` | Unblock all in group |
| `lo clients kick -g <group>` | Kick all in group |
| `lo clients status -g <group>` | Status of all in group |

---

## Output Examples

### `./ui groups list`

```
┏━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Name           ┃ Type   ┃ Members   ┃ Description                     ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Kids Devices   │ static │ 3         │ Children's phones and tablets   │
│ Apple Devices  │ auto   │ 12        │ vendor: Apple                   │
│ IoT Devices    │ auto   │ 8         │ vendor: Philips,LIFX,Ring +2    │
│ Cameras        │ static │ 2         │ Security cameras                │
└────────────────┴────────┴───────────┴─────────────────────────────────┘
```

### `./ui groups show apple-devices`

```
Group: Apple Devices
Type: auto
Description: All Apple devices on the network

Rules:
  vendor: Apple

Matching Clients: 12

┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Name                ┃ MAC                ┃ IP             ┃ Network    ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ iPhone-Emma         │ AA:BB:CC:DD:EE:01  │ 192.168.1.45   │ Main WiFi  │
│ MacBook-Pro         │ AA:BB:CC:DD:EE:02  │ 192.168.1.46   │ Main WiFi  │
│ iPad-Kitchen        │ AA:BB:CC:DD:EE:03  │ 192.168.1.47   │ Main WiFi  │
│ ...                 │ ...                │ ...            │ ...        │
└─────────────────────┴────────────────────┴────────────────┴────────────┘
```

### `./ui groups show kids-devices`

```
Group: Kids Devices
Type: static
Description: Children's phones and tablets
Members: 3
Created: 2025-12-03 10:00 AM
Updated: 2025-12-03 02:30 PM

┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
┃ Alias             ┃ MAC                ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
│ Emma's iPad       │ AA:BB:CC:DD:EE:01  │
│ Jake's Phone      │ AA:BB:CC:DD:EE:02  │
│ Gaming Console    │ AA:BB:CC:DD:EE:03  │
└───────────────────┴────────────────────┘
```

### `./ui lo clients block -g kids-devices`

```
Blocking 3 clients in group "Kids Devices"...

✓ Emma's iPad (AA:BB:CC:DD:EE:01) - blocked
✓ Jake's Phone (AA:BB:CC:DD:EE:02) - blocked
✓ Gaming Console (AA:BB:CC:DD:EE:03) - already blocked

Blocked: 2 | Already blocked: 1 | Failed: 0
```

---

## Implementation

### New Files

```
src/ui_cli/
├── groups.py                      # GroupManager class, storage logic
└── commands/
    └── groups.py                  # Group CLI commands (top-level)
```

### Modified Files

```
src/ui_cli/
├── main.py                        # Register groups command
└── commands/local/
    └── clients.py                 # Add --group option to commands
```

---

## MCP Server Integration

Add group-aware tools to the MCP server for Claude Desktop:

```python
# New MCP tools in src/ui_mcp/server.py

@mcp.tool()
async def list_groups() -> str:
    """List all client groups"""
    return await run_cli("groups", "list", "-o", "json")

@mcp.tool()
async def get_group(name: str) -> str:
    """Get details of a client group including its members"""
    return await run_cli("groups", "show", name, "-o", "json")

@mcp.tool()
async def block_group(name: str) -> str:
    """Block all clients in a group (e.g., for bedtime restrictions)"""
    return await run_cli("lo", "clients", "block", "--group", name, "-o", "json")

@mcp.tool()
async def unblock_group(name: str) -> str:
    """Unblock all clients in a group"""
    return await run_cli("lo", "clients", "unblock", "--group", name, "-o", "json")

@mcp.tool()
async def group_status(name: str) -> str:
    """Get live status of all clients in a group"""
    return await run_cli("lo", "clients", "status", "--group", name, "-o", "json")
```

---

## Future Enhancements

1. **Schedules**: Time-based automatic block/unblock
   ```bash
   ./ui groups schedule kids-devices --block "22:00" --unblock "07:00"
   ```

2. **Group Templates**: Pre-built auto-group definitions
   ```bash
   ./ui groups template list
   # Templates: smart-home, gaming-consoles, streaming-devices, work-devices
   ./ui groups template apply smart-home
   ```

3. **Notifications**: Alert when group members come online/offline
   ```bash
   ./ui groups watch kids-devices --notify
   ```
