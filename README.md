# UniFi CLI

<p align="center">
  <img src="art/uicli_new.png" alt="UI-CLI" width="400">
</p>

<p align="center">
  <strong>Manage your UniFi infrastructure from the command line</strong>
</p>

<p align="center">
  <a href="https://vedanta.github.io/ui-cli">Documentation</a> •
  <a href="#installation">Installation</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="CHANGELOG.md">Changelog</a>
</p>

---

## Overview

UI-CLI provides complete command-line access to your UniFi network infrastructure with two connection modes:

| Mode | Connection | Best For |
|------|------------|----------|
| **Cloud API** | `api.ui.com` | Multi-site management, ISP metrics, SD-WAN |
| **Local API** | Direct to controller | Real-time client/device control, bulk actions |

**Key Features:**
- Manage clients, devices, networks, and firewall rules
- Create client groups for bulk actions (parental controls, IoT management)
- Export configuration backups in YAML/JSON
- Natural language control via Claude Desktop (MCP)
- Multiple output formats: table, JSON, CSV, YAML

**Compatibility:** UDM, UDM Pro, UDM SE, Cloud Key, self-hosted controllers

---

## Installation

### Using Conda (Recommended)

```bash
git clone https://github.com/vedanta/ui-cli.git
cd ui-cli
conda env create -f environment.yml
conda activate ui-cli
pip install -e .
```

### Using pip

```bash
git clone https://github.com/vedanta/ui-cli.git
cd ui-cli
python -m venv venv
source venv/bin/activate
pip install -e .
```

### Using Docker

```bash
docker build -t ui-cli .
docker run --rm --env-file .env ui-cli lo clients list
```

---

## Quick Start

### 1. Configure Credentials

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```bash
# Cloud API - get key from unifi.ui.com → Settings → API
UNIFI_API_KEY=your-api-key

# Local Controller
UNIFI_CONTROLLER_URL=https://192.168.1.1
UNIFI_CONTROLLER_USERNAME=admin
UNIFI_CONTROLLER_PASSWORD=yourpassword
UNIFI_CONTROLLER_SITE=default
UNIFI_CONTROLLER_VERIFY_SSL=false
```

### 2. Verify Connection

```bash
./ui status              # Cloud API
./ui lo health           # Local controller
```

### 3. Explore

```bash
./ui --help              # All commands
./ui lo clients list     # List connected clients
./ui lo devices list     # List network devices
```

---

## Commands

### Cloud API

Manage multiple sites via UniFi Site Manager.

```bash
# Controllers and sites
./ui hosts list                    # List all controllers
./ui sites list                    # List all sites

# Devices across all sites
./ui devices list                  # List all devices
./ui devices count --by model      # Count by model

# ISP performance
./ui isp metrics                   # Last 7 days
./ui isp metrics --hours 24        # Last 24 hours

# SD-WAN
./ui sdwan list                    # List configurations
```

### Local Controller

Direct connection for real-time control. Use `./ui lo` or `./ui local`.

```bash
# Health and monitoring
./ui lo health                     # Site health (WAN/LAN/WLAN/VPN)
./ui lo events list                # Recent events

# Clients
./ui lo clients list               # Connected clients
./ui lo clients list -W            # Wireless only
./ui lo clients list -n "Guest"    # Filter by network
./ui lo clients get "iPhone"       # Find by name
./ui lo clients block "iPhone"     # Block client
./ui lo clients kick "iPhone"      # Disconnect client

# Devices
./ui lo devices list               # Network devices (APs, switches)
./ui lo devices restart "Office-AP"
./ui lo devices locate "Office-AP" # Blink LED

# Networks and firewall
./ui lo networks list              # VLANs and subnets
./ui lo firewall list              # Firewall rules
./ui lo portfwd list               # Port forwarding

# Guest vouchers
./ui lo vouchers create -c 5 -d 60 # 5 vouchers, 60 min each
./ui lo vouchers list

# Traffic stats
./ui lo dpi stats                  # DPI by application
./ui lo stats daily                # Daily bandwidth

# Configuration backup
./ui lo config show -o yaml > backup.yaml
```

---

## Client Groups

Organize devices into groups for bulk actions. Perfect for parental controls, IoT management, or network segmentation.

### Static Groups (Manual Membership)

```bash
# Create group and add devices
./ui groups create "Kids Devices"
./ui groups add kids-devices AA:BB:CC:DD:EE:FF -a "iPad"
./ui groups add kids-devices 11:22:33:44:55:66 -a "Phone"

# View group
./ui groups show kids-devices
./ui groups members kids-devices
```

### Auto Groups (Pattern-Based)

```bash
# Match by vendor
./ui groups auto "Apple Devices" --vendor "Apple"

# Match by name pattern
./ui groups auto "Cameras" --name "*cam*"

# Match by network
./ui groups auto "Guests" --network "Guest"

# Match by IP range
./ui groups auto "Servers" --ip "192.168.1.100-200"

# Combine rules (AND logic)
./ui groups auto "Kids Apple" --vendor "Apple" --name "*kid*"
```

### Bulk Actions

```bash
# Block all devices in group (bedtime!)
./ui lo clients block -g kids-devices -y

# Unblock all (morning!)
./ui lo clients unblock -g kids-devices -y

# View group status
./ui lo clients list -g kids-devices
```

---

## Claude Desktop Integration

Control your network with natural language via [Claude Desktop](https://claude.ai/download).

### Setup

```bash
./ui mcp install         # Add to Claude Desktop
./ui mcp check           # Verify setup
# Restart Claude Desktop
```

### Example Prompts

| You say... | Claude does... |
|------------|----------------|
| "How many devices are connected?" | Counts clients |
| "Block the kids iPad" | Blocks specific client |
| "Block all kids devices" | Blocks entire group |
| "What's my internet speed?" | Shows speed test results |
| "Restart the garage AP" | Restarts device |
| "Create a guest voucher" | Creates WiFi voucher |

### Available Tools (21)

| Category | Tools |
|----------|-------|
| Status | `network_status`, `network_health`, `internet_speed`, `run_speedtest`, `isp_performance` |
| Lists | `client_count`, `device_list`, `network_list` |
| Lookup | `find_client`, `find_device`, `client_status` |
| Actions | `block_client`, `unblock_client`, `kick_client`, `restart_device`, `create_voucher` |
| Groups | `list_groups`, `get_group`, `block_group`, `unblock_group`, `group_status` |

---

## Output Formats

```bash
./ui devices list              # Table (default)
./ui devices list -o json      # JSON
./ui devices list -o csv       # CSV
./ui lo config show -o yaml    # YAML
```

### Scripting with JSON

```bash
# Count clients
./ui lo clients list -o json | jq 'length'

# Get all client IPs
./ui lo clients list -o json | jq -r '.[].ip'

# Find offline devices
./ui devices list -o json | jq '[.[] | select(.status == "offline")]'
```

---

## Command Reference

```
./ui
├── status                 # Check cloud API connection
├── version                # Show CLI version
├── hosts                  # Manage controllers
├── sites                  # Manage sites
├── devices                # Manage devices (cloud)
├── isp                    # ISP metrics
├── sdwan                  # SD-WAN configuration
├── groups                 # Client groups
├── lo / local             # Local controller commands
│   ├── health             # Site health
│   ├── clients            # Client management
│   ├── devices            # Device management
│   ├── networks           # Network/VLAN info
│   ├── firewall           # Firewall rules
│   ├── portfwd            # Port forwarding
│   ├── vouchers           # Guest vouchers
│   ├── dpi                # DPI statistics
│   ├── stats              # Traffic statistics
│   ├── events             # Event log
│   └── config             # Configuration export
└── mcp                    # Claude Desktop integration
```

<details>
<summary><strong>Full Command Tree</strong></summary>

```
./ui lo clients
├── list [-w|-W] [-n network] [-g group]
├── all                    # Include offline
├── get <name|MAC>
├── status <name|MAC>
├── block <name|MAC> [-g group]
├── unblock <name|MAC> [-g group]
├── kick <name|MAC> [-g group]
├── count [--by type|network|vendor|ap]
└── duplicates

./ui lo devices
├── list [-v]
├── get <name|MAC|ID>
├── restart <device>
├── upgrade <device>
├── locate <device> [--off]
└── adopt <MAC>

./ui lo vouchers
├── list
├── create [-c count] [-d minutes] [-q MB]
└── delete <code>

./ui groups
├── list
├── create <name> [-d desc]
├── show <name>
├── delete <name>
├── edit <name> [-n name] [-d desc]
├── add <group> <MAC> [-a alias]
├── remove <group> <MAC|alias>
├── members <group>
├── clear <group>
├── auto <name> [--vendor|--name|--network|--ip|--mac|--type]
├── export [-o file]
└── import <file>
```

</details>

---

## Troubleshooting

| Error | Solution |
|-------|----------|
| API key not configured | Add `UNIFI_API_KEY` to `.env` |
| Invalid API key | Regenerate at unifi.ui.com → Settings → API |
| Controller URL not configured | Add `UNIFI_CONTROLLER_URL` to `.env` |
| Invalid username/password | Verify credentials in UniFi web UI |
| SSL certificate error | Set `UNIFI_CONTROLLER_VERIFY_SSL=false` |
| Connection timeout | Use `./ui lo --timeout 60 health` |
| Session expired | Delete `~/.config/ui-cli/session.json` |

---

## Documentation

| Resource | Description |
|----------|-------------|
| [Online Docs](https://vedanta.github.io/ui-cli) | Full documentation site |
| [User Guide](USERGUIDE.md) | Detailed usage examples |
| [MCP Guide](src/ui_mcp/README.md) | Claude Desktop setup |
| [Changelog](CHANGELOG.md) | Version history |

---

## License

MIT License - see [LICENSE](LICENSE) for details.
