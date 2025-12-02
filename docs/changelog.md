# Changelog

All notable changes to UI-CLI are documented here.

---

## [0.3.0] - December 2, 2024

### Highlights

🤖 **Claude Desktop Integration** - Manage your UniFi network using natural language!

### Added

**MCP Server v2 (Tools Layer Architecture)**

- 16 AI-optimized tools for Claude Desktop integration
- Natural language network management
- `./ui mcp install` - One-command setup
- `./ui mcp check` - Verify installation
- `./ui mcp show` - View configuration

**Available Tools**

| Category | Tools |
|----------|-------|
| Status & Health | `network_status`, `network_health`, `internet_speed`, `run_speedtest`, `isp_performance` |
| Counts & Lists | `client_count`, `device_list`, `network_list` |
| Lookups | `find_client`, `find_device`, `client_status` |
| Actions | `block_client`, `unblock_client`, `kick_client`, `restart_device`, `create_voucher` |

### Architecture

- Subprocess-based tools layer for consistent behavior
- CLI remains single source of truth
- JSON output for all action commands

### Documentation

- Claude Desktop integration guide
- MCP architecture documentation

---

## [0.2.0] - December 1, 2024

### Highlights

🦍 **Local Controller API** - Direct connection to UDM, Cloud Key, and self-hosted controllers!

### Added

#### Local Controller Commands (`./ui lo`)

**Health & Monitoring**

- `./ui lo health` - Site health summary
- `./ui lo events list` - View recent events

**Client Management**

- `./ui lo clients list` - List connected clients with filters
- `./ui lo clients all` - All clients including offline
- `./ui lo clients get` - Client details by name or MAC
- `./ui lo clients status` - Comprehensive client status
- `./ui lo clients block/unblock` - Block or unblock clients
- `./ui lo clients kick` - Disconnect clients
- `./ui lo clients count` - Count by type/network/vendor/AP
- `./ui lo clients duplicates` - Find duplicate names

**Device Management**

- `./ui lo devices list` - List network devices
- `./ui lo devices get` - Device details
- `./ui lo devices restart` - Restart a device
- `./ui lo devices upgrade` - Upgrade firmware
- `./ui lo devices locate` - Toggle locate LED
- `./ui lo devices adopt` - Adopt new device

**Network Configuration**

- `./ui lo networks list` - List networks/VLANs
- `./ui lo config show` - Export running config (table/JSON/YAML)

**Security & Firewall**

- `./ui lo firewall list` - Firewall rules
- `./ui lo firewall groups` - Address/port groups
- `./ui lo portfwd list` - Port forwarding rules

**Guest Management**

- `./ui lo vouchers list` - List vouchers
- `./ui lo vouchers create` - Create vouchers
- `./ui lo vouchers delete` - Delete vouchers

**DPI & Statistics**

- `./ui lo dpi stats` - Site DPI statistics
- `./ui lo dpi client` - Per-client DPI
- `./ui lo stats daily` - Daily traffic stats
- `./ui lo stats hourly` - Hourly traffic stats

**Other**

- `./ui speedtest` - Run speedtest via controller
- `./ui status` - Enhanced with local controller info

### Testing

- 87 tests (71 unit, 16 integration)
- pytest-asyncio for async testing

### Documentation

- Complete user guide
- Command reference
- Examples and troubleshooting

---

## [0.1.0] - November 29, 2024

### Initial Release

🚀 **Site Manager API** - Cloud-based multi-site management!

### Added

**Authentication**

- API key authentication via `UNIFI_API_KEY`
- `./ui status` - Connection check

**Hosts**

- `./ui hosts list` - List all controllers
- `./ui hosts get` - Controller details

**Sites**

- `./ui sites list` - List all sites

**Devices**

- `./ui devices list` - List all devices
- `./ui devices count` - Count by model/status/host

**ISP Metrics**

- `./ui isp metrics` - ISP performance with intervals

**SD-WAN**

- `./ui sdwan list` - List configurations
- `./ui sdwan get` - Configuration details
- `./ui sdwan status` - Deployment status

**Output Formats**

- Table (default)
- JSON
- CSV

### Infrastructure

- Typer CLI framework
- Rich terminal formatting
- httpx async HTTP client
- pydantic-settings configuration
