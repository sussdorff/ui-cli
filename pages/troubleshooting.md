# Troubleshooting

Common issues and solutions.

## Cloud API Issues

### "API key not configured"

**Problem:** Missing or empty `UNIFI_API_KEY` in `.env`

**Solution:**
```bash
# Check if .env exists
cat .env | grep UNIFI_API_KEY

# Add your API key
echo 'UNIFI_API_KEY=your-key-here' >> .env
```

### "Invalid API key"

**Problem:** API key is incorrect or expired

**Solution:**

1. Go to [unifi.ui.com](https://unifi.ui.com)
2. Navigate to **Settings** → **API**
3. Delete the old key and create a new one
4. Update `.env` with the new key

### "Connection timeout"

**Problem:** Cannot reach `api.ui.com`

**Solution:**

- Check internet connectivity
- Verify firewall allows outbound HTTPS
- Try: `curl -I https://api.ui.com`

---

## Local Controller Issues

### "Controller URL not configured"

**Problem:** Missing `UNIFI_CONTROLLER_URL` in `.env`

**Solution:**
```bash
# Add your controller URL
echo 'UNIFI_CONTROLLER_URL=https://192.168.1.1' >> .env
```

### "Invalid username or password"

**Problem:** Credentials don't match controller

**Solution:**

1. Verify credentials work in the UniFi web UI
2. Use a **local admin account** (not Ubiquiti SSO)
3. Check for typos in `.env`

!!! warning "SSO vs Local Accounts"
    UI-CLI requires a **local admin account**. Ubiquiti SSO accounts won't work for direct controller access.

### "SSL certificate verify failed"

**Problem:** Controller uses self-signed certificate

**Solution:**
```bash
# Disable SSL verification
echo 'UNIFI_CONTROLLER_VERIFY_SSL=false' >> .env
```

### "Connection refused"

**Problem:** Cannot connect to controller

**Solution:**

- Verify controller URL is correct
- Check controller is running
- Ensure network access to controller
- Try: `curl -k https://192.168.1.1`

### "Session expired"

**Problem:** Cached session is no longer valid

**Solution:**
```bash
# Delete cached session
rm ~/.config/ui-cli/session.json

# Try again
./ui lo health
```

---

## Client/Device Issues

### "Client not found"

**Problem:** Client name or MAC not recognized

**Solution:**

- Try partial name match: `./ui lo clients get iPhone`
- Use MAC address: `./ui lo clients get AA:BB:CC:DD:EE:FF`
- List all clients: `./ui lo clients all`

### "Device not found"

**Problem:** Device identifier not recognized

**Solution:**

- List devices first: `./ui lo devices list`
- Try by MAC: `./ui lo devices get 70:a7:41:xx:xx:xx`
- Try by ID: `./ui lo devices get device-001`

---

## DPI Issues

### "DPI unavailable"

**Problem:** DPI is not enabled on the controller

**Solution:**

1. Open UniFi web UI
2. Go to **Settings** → **Traffic & Security** → **Deep Packet Inspection**
3. Enable DPI
4. Wait a few hours for data to populate

---

## Output Issues

### JSON Output is Empty

**Problem:** Command returns `[]` or `{}`

**Possible Causes:**

- No data available (e.g., no vouchers created)
- Filter too restrictive
- API returned empty response

**Debug:**
```bash
# Remove filters and try verbose
./ui lo clients list -v
./ui lo vouchers list -v
```

### Table Output Truncated

**Problem:** Long values cut off in table view

**Solution:**
```bash
# Use JSON for full data
./ui devices list -o json | jq '.[0]'

# Or CSV
./ui devices list -o csv
```

---

## Installation Issues

### "ModuleNotFoundError"

**Problem:** Python dependencies not installed

**Solution:**
```bash
pip install -e .
# or
pip install -e ".[dev]"
```

### "Command not found: ui"

**Problem:** CLI not in PATH

**Solution:**
```bash
# Use the wrapper script
./ui --help

# Or add to PATH after pip install
which ui
```

---

## Getting Help

### Check Version

```bash
./ui version
```

### Command Help

```bash
./ui --help
./ui lo --help
./ui lo clients --help
```

### Debug Mode

```bash
# See what's happening
./ui lo health -v
```

### Report Issues

Found a bug? [Open an issue on GitHub](https://github.com/vedanta/ui-cli/issues)

Include:

- UI-CLI version (`./ui version`)
- Controller type (UDM, Cloud Key, etc.)
- Error message
- Steps to reproduce
