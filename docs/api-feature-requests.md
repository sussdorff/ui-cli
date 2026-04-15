# API Feature Requests

Dokumentation der identifizierten Lücken zwischen der UniFi Local Controller API und dem ui-cli.

Erstellt: 2025-12-16

---

## 1. Netzwerk-Details unvollständig

**Problem:** `ui lo networks list` zeigt nicht alle relevanten Netzwerk-Informationen.

**Fehlende Felder:**
- VLAN-ID (wird als "native" angezeigt, obwohl VLANs konfiguriert sind)
- Subnet/IP-Range
- Network Group (LAN, WAN, etc.)
- Inter-VLAN Routing Status
- Internet Access Enabled
- Intra-Network Access Enabled

**Workaround während Session:**
```python
response = await client.get('/rest/networkconf')
# Dann manuell relevante Felder extrahieren
```

**Erwartetes Verhalten:**
```bash
ui lo networks list -v  # Verbose sollte alle Details zeigen
```

---

## 2. Client-Gruppierung nach Netzwerk

**Problem:** `ui lo clients list` verliert beim Formatieren die Netzwerk-Zuordnung (network/essid Felder).

**Auswirkung:**
- Keine Möglichkeit, Clients nach Netzwerk zu filtern (außer `-n` Flag, das nur String-Match macht)
- Keine Übersicht "wie viele Clients pro Netzwerk"

**Workaround während Session:**
```python
data = await client.list_clients()
from collections import Counter
networks = Counter()
for c in data:
    net = c.get('network') or c.get('essid') or 'unknown'
    networks[net] += 1
```

**Erwartetes Verhalten:**
```bash
ui lo clients count --by network  # Existiert, aber nutzt formatierte Daten
ui lo clients list --network IoT  # Exakter Match auf Netzwerk-Name
```

---

## 3. VPN-Konfiguration nicht abrufbar

**Problem:** VPN-Netzwerke (WireGuard, etc.) werden in `networks list` angezeigt, aber VPN-spezifische Details fehlen.

**Fehlende Informationen:**
- VPN-Typ (wireguard-server, wireguard-client, etc.)
- WireGuard Public Key
- Local Port
- Remote IP Override (Domain)
- Firewall Zone ID
- Client-Konfiguration (für WireGuard-Clients)

**Workaround während Session:**
```python
response = await client.get('/rest/networkconf')
for n in networks:
    if n.get('purpose') == 'remote-user-vpn':
        # VPN-spezifische Felder manuell auslesen
```

**Erwartetes Verhalten:**
```bash
ui lo vpn list                    # Zeigt alle VPN-Konfigurationen
ui lo vpn show "Sussdorff Home"   # Details inkl. Public Key, Port, etc.
```

---

## 4. Firewall-Zonen und Policies (Policy Engine)

**Problem:** Keine Möglichkeit, Firewall-Konfiguration über das CLI abzurufen.

**Fehlende Funktionalität:**
- Liste aller Firewall-Zonen
- Zone-zu-Netzwerk Zuordnung
- Firewall-Policies (Inter-Zone Regeln)
- Traffic Rules

**API-Lösung gefunden (v2 API):**

Die klassische API (`/rest/...`) unterstützt die Zone-Based Firewall nicht.
Die **v2 API** über den Proxy-Pfad funktioniert:

```python
# Firewall Policies (104 Regeln in der Policy Engine Matrix)
GET /proxy/network/v2/api/site/default/firewall-policies

# Traffic Rules (benutzerdefinierte Regeln)
GET /proxy/network/v2/api/site/default/trafficrules

# Traffic Routes
GET /proxy/network/v2/api/site/default/trafficroutes
```

**Zone-IDs aus Netzwerk-Konfiguration:**
```python
# Zone-IDs sind in /rest/networkconf unter 'firewall_zone_id' gespeichert
response = await client.get('/rest/networkconf')
for n in networks:
    zone_id = n.get('firewall_zone_id')  # z.B. "6802707a63cb5d7e6a24b9d6"
```

**Erkannte Zonen (aus Analyse):**
| Zone-ID (letzte 4) | Zone-Name | Netzwerke |
|--------------------|-----------|-----------|
| `b9d6` | Internal | Management, Sussdorff, IoT, NordVPN, Multimedia |
| `b9d7` | Gateway | Telekom, Internet 2 (WAN) |
| `b9d9` | VPN | Sussdorff Home |
| `b9da` | Hotspot | AirBnB, Dachgeschoss, Gaeste |

**Policy-Struktur:**
```json
{
  "_id": "...",
  "action": "ALLOW|DROP|REJECT",
  "source": { "zone_id": "..." },
  "destination": { "zone_id": "..." },
  "enabled": true,
  "predefined": true,
  "name": "Allow All Traffic"
}
```

**Erwartetes CLI-Verhalten:**
```bash
ui lo firewall zones              # Liste aller Zonen mit zugewiesenen Netzwerken
ui lo firewall policies           # Policy-Matrix (Source → Dest)
ui lo firewall policies --from VPN --to Internal  # Gefiltert
ui lo firewall rules              # Benutzerdefinierte Traffic Rules
```

**Hinweis:** Die v2 API erfordert den UDM-Proxy-Pfad (`/proxy/network/v2/...`).
Der bestehende `UniFiLocalClient` muss erweitert werden, um diese Pfade zu unterstützen.

---

## 5. Routing-Tabelle

**Problem:** Keine Möglichkeit, Routing-Informationen abzurufen.

**Getestete API-Endpoints:**
- `/rest/routing` - Leer (0 Routen)

**Erwartetes Verhalten:**
```bash
ui lo routes list                 # Statische Routen
ui lo routes show                 # Routing-Tabelle
```

---

## 6. WLAN-zu-Netzwerk Zuordnung

**Problem:** `ui lo wlans list` zeigt nicht, welchem Netzwerk/VLAN ein WLAN zugeordnet ist.

**Fehlende Felder:**
- Network ID / Network Name
- VLAN Tag
- AP Group Zuordnung

**Workaround während Session:**
```bash
ui lo wlans list -o json | jq '.[] | {name, network_id}'
# network_id war immer null
```

**Erwartetes Verhalten:**
```bash
ui lo wlans list -v               # Zeigt Netzwerk-Zuordnung
```

---

## Priorisierung

| Feature | Priorität | Begründung | API verfügbar |
|---------|-----------|------------|---------------|
| Netzwerk-Details | Hoch | Grundlegende Netzwerk-Übersicht | ✅ `/rest/networkconf` |
| VPN-Konfiguration | Hoch | VPN-Verwaltung wichtig für Remote-Zugriff | ✅ `/rest/networkconf` |
| Firewall/Policies | Hoch | Sicherheitsübersicht, VPN-Zugriff | ✅ v2 API |
| WLAN-zu-Netzwerk | Mittel | Wichtig für VLAN-Planung | ❓ Feld fehlt in API |
| Client-Gruppierung | Mittel | Bereits teilweise vorhanden | ✅ Raw data verfügbar |
| Routing | Niedrig | Selten benötigt | ❓ Leer |

---

## Erkenntnisse zur API-Struktur

UniFi Network 10.x hat **zwei API-Schichten**:

### Klassische API (v1)
- Pfad: `/proxy/network/api/s/{site}/...` (UDM) oder `/api/s/{site}/...`
- Endpoints: `/rest/...`, `/stat/...`, `/list/...`, `/cmd/...`
- Gut dokumentiert durch Community (Art-of-WiFi)
- **Limitierung:** Keine Zone-Based Firewall, keine Traffic Rules

### Neue API (v2)
- Pfad: `/proxy/network/v2/api/site/{site}/...`
- Endpoints für neuere Features (Network 8+)
- **Gefundene Endpoints:**
  - `/firewall-policies` - Policy Engine Matrix (104 Regeln)
  - `/trafficrules` - Benutzerdefinierte Traffic Rules
  - `/trafficroutes` - Traffic Routes
- Benötigt gleiche Authentifizierung wie v1

### Empfehlung für `UniFiLocalClient`
Eine neue Methode `get_v2(endpoint)` hinzufügen, die den v2-Pfad verwendet:
```python
async def get_v2(self, endpoint: str) -> dict:
    """Request to v2 API (for newer features)."""
    url = f"{self.controller_url}/proxy/network/v2/api/site/{self.site}{endpoint}"
    # ... rest of request logic
```

---

## Offene Fragen

1. ~~Unterstützt die UniFi Local API (Network 8+) die Zone-Based Firewall überhaupt?~~
   **→ Ja, über v2 API `/firewall-policies`**

2. ~~Gibt es undokumentierte v2-API Endpoints für neuere Features?~~
   **→ Ja, `/proxy/network/v2/api/site/{site}/...`**

3. ~~Ist die `/proxy/network/...` API für manche Features nötig?~~
   **→ Ja, für alle v2 Features**

4. Welche weiteren v2-Endpoints gibt es? (Traffic Management, QoS, etc.)

5. Gibt es einen Endpoint für Zone-Definitionen oder nur Zone-IDs in Netzwerken?
