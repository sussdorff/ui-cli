# Client Groups

Create named groups of client devices for bulk actions like blocking, unblocking, and monitoring. Groups are stored locally and do not require a network connection to manage.

## Overview

Client groups allow you to:

- **Organize devices** - Group devices by purpose (Kids, IoT, Guests)
- **Bulk actions** - Block/unblock/kick all devices in a group at once
- **Parental controls** - Implement bedtime rules by blocking a group
- **Network segmentation** - Monitor and manage device categories

## Group Types

### Static Groups

Static groups have a manually maintained list of members, identified by MAC address.

```bash
# Create a static group
./ui groups create "Kids Devices" -d "Tablets and phones for the kids"

# Add members with optional aliases
./ui groups add kids-devices AA:BB:CC:DD:EE:FF -a "Timmy iPad"
./ui groups add kids-devices 11:22:33:44:55:66 -a "Sarah Phone"
```

### Auto Groups

Auto groups dynamically match clients based on rules. Members are evaluated at query time against live client data.

```bash
# Create auto group matching Apple devices
./ui groups auto "Apple Devices" --vendor "Apple"

# Create auto group matching devices by name pattern
./ui groups auto "Cameras" --name "*camera*,*cam*"
```

## Pattern Syntax

Auto group rules support multiple pattern formats:

| Format | Example | Matches |
|--------|---------|---------|
| Exact | `Apple` | "Apple" only |
| Wildcard | `*phone*` | "iPhone", "Android Phone", "phone-1" |
| Prefix | `iPhone*` | "iPhone", "iPhone-12", "iPhoneXR" |
| Suffix | `*-TV` | "Living-TV", "Bedroom-TV" |
| Regex | `~^iPhone-[0-9]+$` | "iPhone-1", "iPhone-12" (not "iPhoneXR") |
| Multiple | `Apple,Samsung` | "Apple" OR "Samsung" |

**Pattern Rules:**
- Patterns are case-insensitive
- `*` matches any characters (including none)
- `?` matches exactly one character
- Prefix with `~` for regex patterns
- Comma-separated patterns use OR logic
- Different rule types use AND logic

## Commands Reference

### Group Management

```bash
# List all groups
./ui groups list
./ui groups ls                    # Alias

# Create static group
./ui groups create "My Group"
./ui groups create "My Group" -d "Description here"

# Show group details
./ui groups show "My Group"
./ui groups show my-group         # Use slug

# Edit group
./ui groups edit my-group -n "New Name"
./ui groups edit my-group -d "New description"

# Delete group
./ui groups delete my-group
./ui groups delete my-group -y    # Skip confirmation
./ui groups rm my-group           # Alias
```

### Member Management (Static Groups)

```bash
# Add members
./ui groups add my-group AA:BB:CC:DD:EE:FF
./ui groups add my-group AA:BB:CC:DD:EE:FF -a "Device Name"
./ui groups add my-group MAC1 MAC2 MAC3    # Multiple

# Remove members
./ui groups remove my-group AA:BB:CC:DD:EE:FF
./ui groups remove my-group "Device Name"   # By alias

# Set or clear alias
./ui groups alias my-group AA:BB:CC:DD:EE:FF "New Alias"
./ui groups alias my-group AA:BB:CC:DD:EE:FF --clear

# List members
./ui groups members my-group
./ui groups members my-group -o json

# Clear all members
./ui groups clear my-group
./ui groups clear my-group -y     # Skip confirmation
```

### Auto Groups

```bash
# Create auto group with rules
./ui groups auto "Group Name" [OPTIONS]

# Available rule options:
--vendor "Apple"              # Match by vendor/OUI
--name "*phone*"              # Match by client name
--hostname "iphone*"          # Match by hostname
--network "Guest"             # Match by network/SSID
--ip "192.168.1.100-200"      # Match by IP range
--mac "AA:BB:*"               # Match by MAC prefix
--type "wireless"             # Match by connection type

# Examples
./ui groups auto "Apple Devices" --vendor "Apple"
./ui groups auto "IoT" --vendor "Philips,LIFX,Ring,Nest"
./ui groups auto "Cameras" --name "*camera*,*cam*"
./ui groups auto "Guest WiFi" --network "Guest"
./ui groups auto "Servers" --ip "192.168.1.100-200"
./ui groups auto "Wireless" --type "wireless"

# Combine rules (AND logic)
./ui groups auto "Kids iPhones" --vendor "Apple" --name "*kid*"

# Preview without creating
./ui groups auto "Test" --vendor "Apple" --dry-run
```

### Import/Export

```bash
# Export all groups to JSON
./ui groups export
./ui groups export -o groups-backup.json

# Import groups from file
./ui groups import groups-backup.json
./ui groups import groups-backup.json --replace    # Replace all existing
./ui groups import groups-backup.json -y           # Skip confirmation
```

## Bulk Actions

Use the `-g` / `--group` flag with client commands to perform bulk operations.

### List Group Clients

```bash
# List all clients matching a group
./ui lo clients list -g kids-devices
./ui lo clients list -g apple-devices -o json
```

### Block All Clients

```bash
# Block all clients in a group
./ui lo clients block -g kids-devices
./ui lo clients block -g kids-devices -y    # Skip confirmation

# Returns summary:
# Blocked 3 clients (already blocked: 1, failed: 0)
```

### Unblock All Clients

```bash
# Unblock all clients in a group
./ui lo clients unblock -g kids-devices
./ui lo clients unblock -g kids-devices -y

# Returns summary:
# Unblocked 3 clients (not blocked: 1, failed: 0)
```

### Kick/Disconnect All Clients

```bash
# Force disconnect all clients in a group
./ui lo clients kick -g kids-devices
./ui lo clients kick -g kids-devices -y

# Returns summary:
# Kicked 3 clients (offline: 1, failed: 0)
```

## Use Cases

### Parental Controls

Create a group for kids' devices and block at bedtime:

```bash
# Setup (one time)
./ui groups create "Kids Devices"
./ui groups add kids-devices AA:BB:CC:DD:EE:FF -a "Timmy iPad"
./ui groups add kids-devices 11:22:33:44:55:66 -a "Sarah Phone"
./ui groups add kids-devices 22:33:44:55:66:77 -a "Gaming Console"

# Bedtime - block all
./ui lo clients block -g kids-devices -y

# Morning - unblock all
./ui lo clients unblock -g kids-devices -y
```

### IoT Device Management

Group smart home devices by vendor:

```bash
# Create auto groups for IoT vendors
./ui groups auto "Smart Lights" --vendor "Philips,LIFX,Hue"
./ui groups auto "Cameras" --vendor "Ring,Nest,Wyze"
./ui groups auto "Smart Speakers" --vendor "Amazon,Google,Sonos"

# Check status of all cameras
./ui lo clients list -g cameras

# Temporarily disconnect all smart speakers
./ui lo clients kick -g smart-speakers -y
```

### Guest Network Monitoring

Track devices on guest network:

```bash
# Create auto group for guest network
./ui groups auto "Guest Devices" --network "Guest"

# List current guests
./ui lo clients list -g guest-devices

# Count guests
./ui lo clients list -g guest-devices -o json | jq 'length'
```

### Server/Infrastructure Isolation

Group servers by IP range:

```bash
# Create auto group for server VLAN
./ui groups auto "Servers" --ip "10.0.10.0/24"

# Or by IP range
./ui groups auto "Servers" --ip "192.168.1.100-150"

# Monitor server connectivity
./ui lo clients list -g servers
```

## Storage

Groups are stored in `~/.config/ui-cli/groups.json`:

```json
{
  "version": 1,
  "groups": {
    "kids-devices": {
      "name": "Kids Devices",
      "description": "Tablets and phones",
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

## MCP Integration

Groups are available through Claude Desktop via MCP tools:

| Tool | Description | Example Prompt |
|------|-------------|----------------|
| `list_groups` | List all groups | "What groups do I have?" |
| `get_group` | Get group details | "Show the kids devices group" |
| `block_group` | Block all in group | "Block all kids devices" |
| `unblock_group` | Unblock all in group | "Unblock the kids devices" |
| `group_status` | Live status of group | "Are the kids devices online?" |

### Example Conversations

> **You:** Block all kids devices, it's bedtime
>
> **Claude:** I'll block all devices in the "Kids Devices" group.
>
> Done! Blocked 3 clients (1 was already blocked).

> **You:** What's the status of my IoT devices?
>
> **Claude:** Looking at your "IoT Devices" group...
>
> You have 12 IoT devices:
> - 10 online
> - 2 offline (Garage Sensor, Basement Camera)

## Tips

1. **Use slugs for scripting** - Group slugs (lowercase, hyphenated) are more reliable than names
2. **Combine with cron** - Automate bedtime rules with scheduled tasks
3. **Backup groups** - Use `./ui groups export` before major changes
4. **Preview auto groups** - Use `--dry-run` to test rules before creating
5. **MAC addresses** - Can use colons (AA:BB:CC) or hyphens (AA-BB-CC)
