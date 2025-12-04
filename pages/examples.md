# Examples

Real-world usage examples and scripts for UI-CLI.

## Scripting with JSON

### Count Offline Devices

```bash
#!/bin/bash
OFFLINE=$(./ui devices list -o json | jq '[.[] | select(.status == "offline")] | length')
if [ "$OFFLINE" -gt 0 ]; then
    echo "⚠️  $OFFLINE devices offline!"
    ./ui devices list -o json | jq -r '.[] | select(.status == "offline") | .name'
fi
```

### Find High-Traffic Clients

```bash
# Clients with > 10GB downloaded
./ui lo clients list -o json | jq -r '.[] | select(.rx_bytes > 10737418240) | "\(.name): \(.rx_bytes / 1073741824 | floor)GB"'
```

### List All iPhones

```bash
./ui lo clients list -o json | jq '.[] | select(.name | test("iPhone"; "i"))'
```

### Export Client IPs

```bash
./ui lo clients list -o json | jq -r '.[].ip' > client-ips.txt
```

## Automation

### Daily Config Backup

```bash
#!/bin/bash
# backup-config.sh
BACKUP_DIR="$HOME/unifi-backups"
DATE=$(date +%Y%m%d)

mkdir -p "$BACKUP_DIR"
./ui lo config show -o yaml > "$BACKUP_DIR/config-$DATE.yaml"
echo "Config backed up to $BACKUP_DIR/config-$DATE.yaml"
```

Add to crontab:

```bash
# Daily at 2am
0 2 * * * /path/to/backup-config.sh
```

### Monitor ISP Latency

```bash
#!/bin/bash
# Check if latency exceeds threshold
THRESHOLD=50  # ms

LATENCY=$(./ui isp metrics -i 5m -o json | jq -r '.[-1].latency_avg // 0')
if (( $(echo "$LATENCY > $THRESHOLD" | bc -l) )); then
    echo "High latency detected: ${LATENCY}ms"
    # Send notification, etc.
fi
```

### Block Unknown Devices

```bash
#!/bin/bash
# Block clients not in allowed list
ALLOWED="allowed-macs.txt"

./ui lo clients list -o json | jq -r '.[].mac' | while read mac; do
    if ! grep -qi "$mac" "$ALLOWED"; then
        echo "Blocking unknown device: $mac"
        ./ui lo clients block "$mac" -y
    fi
done
```

## Guest Network Management

### Create Event Vouchers

```bash
# Create 50 vouchers for a 4-hour event with 1GB limit
./ui lo vouchers create -c 50 -d 240 -q 1024 -n "Company Event $(date +%Y-%m-%d)"
```

### Export Voucher Codes

```bash
./ui lo vouchers list -o json | jq -r '.[] | select(.note | contains("Event")) | .code' > voucher-codes.txt
```

### Clean Up Expired Vouchers

```bash
# List expired vouchers (used or past duration)
./ui lo vouchers list -o json | jq '.[] | select(.used >= .quota or .expired == true)'
```

## Network Monitoring

### Device Health Check

```bash
#!/bin/bash
echo "=== UniFi Network Health Check ==="
echo ""

echo "📡 Site Health:"
./ui lo health
echo ""

echo "📊 Device Status:"
./ui lo devices list | head -20
echo ""

echo "👥 Connected Clients:"
./ui lo clients count
echo ""

echo "🌐 ISP Status (last reading):"
./ui isp metrics -i 5m -o json | jq -r '.[-1] | "Latency: \(.latency_avg)ms | Down: \(.download_speed)Mbps | Up: \(.upload_speed)Mbps"'
```

### Find Devices with Poor Signal

```bash
# Wireless clients with signal worse than -70 dBm
./ui lo clients list -W -o json | jq '.[] | select(.rssi < -70) | {name, rssi, ap: .ap_name}'
```

### Track Bandwidth by Network

```bash
./ui lo clients list -o json | jq -r 'group_by(.network) | .[] | {network: .[0].network, total_rx: (map(.rx_bytes) | add), total_tx: (map(.tx_bytes) | add)}'
```

## Integration Examples

### Slack Notification

```bash
#!/bin/bash
WEBHOOK_URL="https://hooks.slack.com/services/xxx"
OFFLINE=$(./ui devices list -o json | jq '[.[] | select(.status == "offline")] | length')

if [ "$OFFLINE" -gt 0 ]; then
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"⚠️ $OFFLINE UniFi devices are offline!\"}" \
        "$WEBHOOK_URL"
fi
```

### InfluxDB Export

```bash
#!/bin/bash
# Export ISP metrics to InfluxDB
./ui isp metrics -i 5m -o json | jq -c '.[]' | while read line; do
    timestamp=$(echo $line | jq -r '.timestamp')
    latency=$(echo $line | jq -r '.latency_avg')
    download=$(echo $line | jq -r '.download_speed')

    curl -i -XPOST 'http://localhost:8086/write?db=unifi' \
        --data-binary "isp_metrics latency=$latency,download=$download $timestamp"
done
```

## Shell Aliases

Add to your `.bashrc` or `.zshrc`:

```bash
# UI-CLI aliases
alias ui='./ui'
alias clients='./ui lo clients'
alias devices='./ui lo devices'
alias health='./ui lo health'
alias config='./ui lo config show'

# Quick commands
alias whoson='./ui lo clients list'
alias offline='./ui devices list -o json | jq ".[] | select(.status == \"offline\")"'
alias backup='./ui lo config show -o yaml > ~/unifi-backup-$(date +%Y%m%d).yaml'
```

## Tips

### Use `watch` for Live Monitoring

```bash
# Update every 5 seconds
watch -n 5 './ui lo clients count'
```

### Combine with `grep`

```bash
# Quick search
./ui lo clients list | grep -i iphone
./ui lo devices list | grep -i offline
```

### Pretty JSON Output

```bash
./ui devices list -o json | jq '.'
```
