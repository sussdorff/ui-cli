# UI-CLI Project Instructions

## Project Overview
UI-CLI is a command-line tool for managing UniFi network infrastructure. It connects to both the UniFi Cloud API (`api.ui.com`) and local controllers (UDM, Cloud Key).

## UniFi Local Controller API Reference

**Es gibt keine offizielle Ubiquiti-Dokumentation für die lokale Controller-API.** Alle Informationen stammen aus Reverse Engineering.

### Primary Documentation Sources

Die UniFi-API-client Referenz ist als Git Submodule unter `vendor/unifi-api-client/` verfügbar:

| Resource | Location | Use For |
|----------|----------|---------|
| **API Reference** | `vendor/unifi-api-client/API_REFERENCE.md` | Methoden-Signaturen, Parameter, Return-Types |
| **PHP Source** | `vendor/unifi-api-client/src/Client.php` | Payload-Strukturen, Endpoint-Details |
| **Community Wiki** | [ubntwiki.com/api](https://ubntwiki.com/products/software/unifi-controller/api) | Endpoint-Übersicht |
| **API Browser** | [UniFi-API-browser](https://github.com/Art-of-WiFi/UniFi-API-browser) | Live-Daten vom eigenen Controller erkunden |

```bash
# Submodule initialisieren (falls noch nicht geschehen)
git submodule update --init --recursive
```

### Endpoint Pattern Mapping (Art-of-WiFi PHP → UI-CLI Python)
| PHP Pattern | Python Pattern | HTTP Method |
|-------------|----------------|-------------|
| `/api/s/{site}/list/...` | `self.get("/list/...")` | GET |
| `/api/s/{site}/rest/...` | `self.get("/rest/...")` | GET |
| `/api/s/{site}/rest/...` | `self.post("/rest/...", data)` | POST (create) |
| `/api/s/{site}/rest/{id}` | `self._request("PUT", "/rest/{id}", data)` | PUT (update) |
| `/api/s/{site}/rest/{id}` | `self._request("DELETE", "/rest/{id}")` | DELETE |
| `/api/s/{site}/stat/...` | `self.get("/stat/...")` | GET |
| `/api/s/{site}/upd/...` | `self.post("/upd/...", data)` | POST |
| `/api/s/{site}/cmd/...` | `self.post("/cmd/...", data)` | POST |

### Creating New API Methods in local_client.py

**Step 1:** Find method in `vendor/unifi-api-client/API_REFERENCE.md`

**Step 2:** Translate PHP to Python:
```php
// PHP (Art-of-WiFi):
public function list_wlan_groups(): array|bool
{
    return $this->fetch_results('/api/s/' . $this->site . '/list/wlangroup');
}
```

```python
# Python (UI-CLI) in src/ui_cli/local_client.py:
async def get_wlan_groups(self) -> list[dict[str, Any]]:
    """Get all WLAN groups."""
    response = await self.get("/list/wlangroup")
    return response.get("data", [])
```

**Step 3:** For methods with payloads, check `vendor/unifi-api-client/src/Client.php` for structure:
```python
# Success check pattern:
response.get("meta", {}).get("rc") == "ok"

# Data extraction pattern:
response.get("data", [])  # for lists
response.get("data", [{}])[0]  # for single item
```

### Key API Conventions
- MAC addresses: lowercase with colons (`aa:bb:cc:dd:ee:ff`)
- Device IDs: Use `_id` field from device objects
- WLAN group radios: `wlangroup_id_ng` (2.4GHz), `wlangroup_id_na` (5GHz)

## Code Patterns

### Adding New Local Commands
1. Create module in `src/ui_cli/commands/local/`
2. Use `networks.py` or `devices.py` as template
3. Register in `src/ui_cli/commands/local/__init__.py`

### Standard Imports for Local Commands
```python
from typing import Annotated, Any
import typer
from ui_cli.commands.local.utils import run_with_spinner
from ui_cli.local_client import LocalAPIError, UniFiLocalClient
from ui_cli.output import (
    OutputFormat, console, output_csv, output_json,
    print_error, print_success,
)
```

### Command Pattern
```python
@app.command("list")
def list_items(
    output: Annotated[OutputFormat, typer.Option("--output", "-o")] = OutputFormat.TABLE,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
) -> None:
    """List all items."""
    async def _list():
        client = UniFiLocalClient()
        return await client.get_items()

    try:
        items = run_with_spinner(_list(), "Fetching items...")
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    # Output handling...
```

## Testing
```bash
cd /Users/malte/code/house-projects/ui-cli
source .venv/bin/activate
ui lo health  # Test connection
ui lo --help  # List commands
```
