# Local Controller Commands

Commands that connect directly to your UniFi Controller. Use `./ui local` or the shorthand `./ui lo`.

## Prerequisites

- `UNIFI_CONTROLLER_URL` configured in `.env`
- `UNIFI_CONTROLLER_USERNAME` and `UNIFI_CONTROLLER_PASSWORD` configured
- Network access to your controller

## Health

Check site health status.

```bash
./ui lo health
./ui lo health -v              # Verbose
```

Shows status of WAN, LAN, WLAN, and VPN subsystems.

---

## Clients

Manage network clients.

### List Clients

```bash
./ui lo clients list           # Connected clients
./ui lo clients list -w        # Wired only
./ui lo clients list -W        # Wireless only
./ui lo clients list -n Guest  # Filter by network
./ui lo clients list -v        # Verbose
./ui lo clients all            # Include offline clients
```

### Get Client Details

```bash
./ui lo clients get my-iPhone          # By name
./ui lo clients get AA:BB:CC:DD:EE:FF  # By MAC
./ui lo clients get iPhone             # Partial match
```

### Client Status

Comprehensive client information including signal, experience, and data usage.

```bash
./ui lo clients status my-iPhone
```

### Block/Unblock Client

```bash
./ui lo clients block my-iPhone        # Block (with confirmation)
./ui lo clients block my-iPhone -y     # Skip confirmation
./ui lo clients unblock my-iPhone      # Unblock
```

### Disconnect Client

```bash
./ui lo clients kick my-iPhone         # Force reconnect
```

### Count Clients

```bash
./ui lo clients count                  # By connection type
./ui lo clients count --by network     # By network/SSID
./ui lo clients count --by vendor      # By manufacturer
./ui lo clients count --by ap          # By access point
./ui lo clients count --by experience  # By WiFi quality
./ui lo clients count -a               # Include offline
```

### Find Duplicates

Identify devices with multiple NICs or naming conflicts.

```bash
./ui lo clients duplicates
```

---

## Devices

Manage network devices (APs, switches, gateways).

### List Devices

```bash
./ui lo devices list
./ui lo devices list -v        # Verbose (channels, load, etc.)
```

### Get Device Details

```bash
./ui lo devices get UDM-Pro            # By name
./ui lo devices get 70:a7:41:xx:xx:xx  # By MAC
./ui lo devices get device-001         # By ID
```

### Restart Device

```bash
./ui lo devices restart UDM-Pro
./ui lo devices restart UDM-Pro -y     # Skip confirmation
```

### Upgrade Firmware

```bash
./ui lo devices upgrade Office-AP
./ui lo devices upgrade Office-AP -y   # Skip confirmation
```

### Locate Device

Toggle the locate LED for physical identification.

```bash
./ui lo devices locate Office-AP       # Turn on LED
./ui lo devices locate Office-AP --off # Turn off LED
```

### Adopt Device

Adopt a new device into the controller.

```bash
./ui lo devices adopt 70:a7:41:xx:xx:xx
```

---

## Networks

View network configuration.

### List Networks

```bash
./ui lo networks list
./ui lo networks list -v       # Include DHCP details
```

### Get Network Details

```bash
./ui lo networks get NETWORK_ID
```

---

## Firewall

Inspect firewall configuration.

### List Rules

```bash
./ui lo firewall list
./ui lo firewall list --ruleset WAN_IN    # Filter by ruleset
./ui lo firewall list --ruleset LAN_IN
./ui lo firewall list -v                   # Verbose
```

### List Groups

View address and port groups.

```bash
./ui lo firewall groups
./ui lo firewall groups -v     # Show group members
```

---

## Port Forwarding

View port forwarding rules.

```bash
./ui lo portfwd list
./ui lo portfwd list -v        # Verbose
```

---

## Vouchers

Manage guest hotspot vouchers.

### List Vouchers

```bash
./ui lo vouchers list
./ui lo vouchers list -v       # Verbose
```

### Create Vouchers

```bash
./ui lo vouchers create                    # Single voucher, 24h
./ui lo vouchers create -c 10              # Create 10 vouchers
./ui lo vouchers create -d 60              # 60 minute duration
./ui lo vouchers create -q 1024            # 1GB data quota
./ui lo vouchers create --up 5000          # 5 Mbps upload limit
./ui lo vouchers create --down 10000       # 10 Mbps download limit
./ui lo vouchers create -n "Conference"    # Add note
```

**Full Example:**

```bash
# Create 10 vouchers: 2 hours, 500MB quota, 5/10 Mbps limits
./ui lo vouchers create -c 10 -d 120 -q 500 --up 5000 --down 10000 -n "Event"
```

### Delete Voucher

```bash
./ui lo vouchers delete 12345-67890
./ui lo vouchers delete 12345-67890 -y     # Skip confirmation
```

---

## DPI (Deep Packet Inspection)

View traffic analytics.

!!! note "DPI must be enabled"
    DPI statistics require DPI to be enabled in your controller settings.

### Site Statistics

```bash
./ui lo dpi stats              # Top applications
./ui lo dpi stats -l 20        # Top 20
./ui lo dpi stats -v           # Verbose
```

### Client Statistics

```bash
./ui lo dpi client my-MacBook
./ui lo dpi client AA:BB:CC:DD:EE:FF
```

---

## Statistics

View traffic statistics.

### Daily Stats

```bash
./ui lo stats daily            # Last 30 days
./ui lo stats daily --days 7   # Last 7 days
./ui lo stats daily -o csv     # CSV export
```

### Hourly Stats

```bash
./ui lo stats hourly           # Last 24 hours
./ui lo stats hourly --hours 48
```

---

## Events

View recent events.

```bash
./ui lo events list            # Recent events
./ui lo events list -l 50      # Last 50 events
./ui lo events list -v         # Verbose
```

---

## Config

Export running configuration.

### Show Config

```bash
./ui lo config show            # All sections
./ui lo config show -o yaml    # YAML export
./ui lo config show -o json    # JSON export
./ui lo config show -v         # Include IDs
./ui lo config show --show-secrets  # Include passwords
```

### Specific Sections

```bash
./ui lo config show -s networks    # Networks and VLANs
./ui lo config show -s wireless    # SSIDs and WiFi settings
./ui lo config show -s firewall    # Firewall rules
./ui lo config show -s devices     # Device inventory
./ui lo config show -s portfwd     # Port forwarding
./ui lo config show -s dhcp        # DHCP reservations
./ui lo config show -s routing     # Static routes
```

### Backup to File

```bash
./ui lo config show -o yaml > backup-$(date +%Y%m%d).yaml
```
