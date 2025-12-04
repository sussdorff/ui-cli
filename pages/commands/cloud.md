# Cloud API Commands

Commands that use the UniFi Site Manager API (`api.ui.com`). These allow you to manage multiple sites from anywhere.

## Prerequisites

- `UNIFI_API_KEY` configured in `.env`
- Internet access to `api.ui.com`

## Status

Check API connection and authentication.

```bash
./ui status
./ui status -o json      # JSON output for scripting
```

## Hosts

Manage UniFi controllers (UDM, Cloud Key, etc.)

### List Hosts

```bash
./ui hosts list
./ui hosts list -v              # Verbose
./ui hosts list -o json         # JSON output
./ui hosts list -o csv          # CSV export
```

### Get Host Details

```bash
./ui hosts get HOST_ID
./ui hosts get HOST_ID -v       # Verbose
```

## Sites

Manage UniFi sites.

### List Sites

```bash
./ui sites list
./ui sites list -v              # Verbose
./ui sites list -o json         # JSON output
```

## Devices

Manage UniFi devices across all sites.

### List Devices

```bash
./ui devices list
./ui devices list --host HOST_ID    # Filter by controller
./ui devices list -v                # Verbose
./ui devices list -o csv            # CSV export
```

### Count Devices

Group and count devices by various fields.

```bash
./ui devices count                  # Total count
./ui devices count --by model       # By device model
./ui devices count --by status      # By online/offline status
./ui devices count --by host        # By controller
./ui devices count --by product-line # By type (network, protect, etc.)
```

## ISP Metrics

View ISP performance metrics.

```bash
./ui isp metrics                    # Last 7 days, hourly
./ui isp metrics -i 5m              # 5-minute intervals (last 24h)
./ui isp metrics --hours 48         # Last 48 hours
./ui isp metrics -o csv             # CSV export
```

**Available Intervals:**

| Interval | Data Range |
|----------|------------|
| `5m` | Last 24 hours |
| `1h` | Last 7 days (default) |

**Metrics Returned:**

- Latency (average and max)
- Download/upload speeds
- Uptime percentage
- Packet loss
- ISP name

## SD-WAN

Manage SD-WAN configurations.

### List Configurations

```bash
./ui sdwan list
./ui sdwan list -v              # Verbose
```

### Get Configuration

```bash
./ui sdwan get CONFIG_ID
./ui sdwan get CONFIG_ID -v     # Verbose
```

### Check Status

```bash
./ui sdwan status CONFIG_ID
```

## Version

```bash
./ui version
```

## Examples

### Export All Devices to CSV

```bash
./ui devices list -o csv > devices.csv
```

### Find Offline Devices

```bash
./ui devices count --by status
# or with jq
./ui devices list -o json | jq '[.[] | select(.status == "offline")]'
```

### Check ISP Performance

```bash
./ui isp metrics -i 5m -o json | jq '.[-1]'  # Latest reading
```

### Script: Alert on Offline Devices

```bash
#!/bin/bash
OFFLINE=$(./ui devices count --by status -o json | jq '.counts.offline // 0')
if [ "$OFFLINE" -gt 0 ]; then
    echo "Warning: $OFFLINE devices offline"
    ./ui devices list -o json | jq '.[] | select(.status == "offline") | .name'
fi
```
