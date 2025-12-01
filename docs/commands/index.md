# Command Reference

UI-CLI provides two sets of commands:

- **Cloud API** - Commands via `api.ui.com` for multi-site management
- **Local Controller** - Direct connection to your controller for real-time operations

## Command Tree

```
./ui
├── status              # Check API connection
├── version             # Show CLI version
├── speedtest           # Run speedtest on gateway
├── hosts               # Cloud: manage controllers
├── sites               # Cloud: manage sites
├── devices             # Cloud: manage devices
├── isp                 # Cloud: ISP metrics
├── sdwan               # Cloud: SD-WAN configs
└── local (lo)          # Local controller commands
```

## Quick Reference

### Cloud API

| Command | Description |
|---------|-------------|
| `./ui status` | Check API connection |
| `./ui hosts list` | List all controllers |
| `./ui sites list` | List all sites |
| `./ui devices list` | List all devices |
| `./ui devices count --by model` | Count devices by model |
| `./ui isp metrics` | ISP performance metrics |
| `./ui sdwan list` | List SD-WAN configs |

### Local Controller

| Command | Description |
|---------|-------------|
| `./ui lo health` | Site health summary |
| `./ui lo clients list` | List connected clients |
| `./ui lo clients status <name>` | Detailed client status |
| `./ui lo devices list` | List network devices |
| `./ui lo devices restart <name>` | Restart a device |
| `./ui lo networks list` | List networks/VLANs |
| `./ui lo firewall list` | List firewall rules |
| `./ui lo vouchers create` | Create guest voucher |
| `./ui lo dpi stats` | DPI statistics |
| `./ui lo stats daily` | Daily traffic stats |
| `./ui lo config show` | Export running config |

## Output Formats

All commands support multiple output formats:

```bash
./ui devices list              # Table (default)
./ui devices list -o json      # JSON
./ui devices list -o csv       # CSV
./ui lo config show -o yaml    # YAML (config only)
```

## Common Options

| Option | Short | Description |
|--------|-------|-------------|
| `--output` | `-o` | Output format: table/json/csv/yaml |
| `--verbose` | `-v` | Show additional details |
| `--yes` | `-y` | Skip confirmation prompts |
| `--help` | | Show command help |

## Getting Help

```bash
./ui --help                    # All commands
./ui devices --help            # Device commands
./ui lo --help                 # Local commands
./ui lo clients --help         # Client commands
```
