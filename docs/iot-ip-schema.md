# IoT Netzwerk IP-Schema

**Netzwerk:** IoT (192.168.30.0/24)
**DHCP-Range:** 192.168.30.150 - 192.168.30.254

## IP-Bereiche

| Bereich | Verwendung | Kapazität |
|---------|------------|-----------|
| **10-19** | Energiemanagement (Core) | 10 |
| **20-39** | Shelly Energiemesser | 20 |
| **40-44** | X-Sense (Sicherheit) | 5 |
| **50-59** | Klimaanlagen | 10 |
| **60-69** | Meross Steckdosen | 10 |
| **70-79** | Beleuchtung (Meross Ambient Lights) | 10 |
| **80-89** | TP-Link Steckdosen | 10 |
| **90-99** | Haushaltsgeräte (AEG, etc.) | 10 |
| **100-109** | Garten (Gardena, Bewässerung) | 10 |
| **110-119** | Mobilität (Easee, Tesla Wall Connector) | 10 |
| **120-129** | Saugroboter | 10 |
| **130-149** | Sonstige IoT | 20 |
| **150-254** | **DHCP (dynamisch)** | 105 |

## Aktuelle Belegung (IoT-Netzwerk)

### 10-19: Energiemanagement (Core)

| IP | Gerät | MAC | Status |
|----|-------|-----|--------|
| .10 | Victron Cerbo GX | C0:61:9A:B4:A0:9E | ✓ Fixed |
| .11 | Enphase Envoy | 00:1D:C0:81:F1:0D | ✓ Fixed |
| .12 | Hoymiles Balkon DTU | 54:F2:9F:8F:90:19 | → Migration |
| .13 | Tibber Pulse | 58:BF:25:E5:61:E4 | → Migration |

### 20-39: Shelly Energiemesser

| IP | Gerät | MAC | Status |
|----|-------|-----|--------|
| .20 | Shelly Hoymiles (Balkon) | E4:B0:63:D5:4F:FC | ✓ Fixed |
| .21 | Shelly Keller | 2C:BC:BB:A7:3D:30 | ✓ Fixed |
| .22 | Shelly AirBnB | 2C:BC:BB:A7:46:E8 | ✓ Fixed |
| .23 | Shelly Enphase | 2C:BC:BB:A5:C5:88 | ✓ Fixed |
| .24 | Shelly Dach | 2C:BC:BB:B2:BC:AC | ✓ Fixed |

### 40-44: X-Sense (Sicherheit)

| IP | Gerät | MAC | Status |
|----|-------|-----|--------|
| .40 | X-Sense Base Station EG | 78:1C:3C:23:16:B0 | ✓ Fixed |
| .41 | (reserviert für Base Station 2) | - | - |
| .42 | (reserviert für Base Station 3) | - | - |
| .43 | (reserviert) | - | - |
| .44 | (reserviert) | - | - |

### 50-59: Klimaanlagen

| IP | Gerät | MAC | Status |
|----|-------|-----|--------|
| .50 | Klima Büro | E8:16:56:18:5A:D6 | ✓ Fixed |
| .51 | Klima Wohnzimmer | E8:16:56:18:2F:1D | ✓ Fixed |
| .52 | Klima Ofenzimmer | E8:16:56:18:2D:C3 | ✓ Fixed |

### 60-79: Meross Steckdosen

| IP | Gerät | MAC | Status |
|----|-------|-----|--------|
| .60 | meross-mss210p-4fe2 | 48:E1:E9:E6:4F:E2 | → set-ip |
| .61 | Meross Smart Switch | 48:E1:E9:1A:E1:12 | → set-ip |
| .62 | meross-mss210p-44fc | 48:E1:E9:E8:44:FC | → Migration |
| .63 | meross-mss210p-4fee | 48:E1:E9:E6:4F:EE | → Migration |
| .64 | Meross Smart Switch | 48:E1:E9:1A:EB:50 | → Migration |
| .65 | Meross Smart Switch | 48:E1:E9:1A:D8:3F | → Migration |
| .66 | Meross Smart Switch | 48:E1:E9:29:D0:91 | → Migration |
| .67 | Meross Smart Switch | 48:E1:E9:1A:E6:64 | → Migration |
| .68 | All-In-One_RasPi (Thermostat) | 1C:BC:EC:1B:E6:9C | → Migration |
| .69 | All-In-One_RasPi (Thermostat) | C0:4E:30:37:C8:70 | → Migration |

### 70-79: Beleuchtung

| IP | Gerät | MAC | Status |
|----|-------|-----|--------|
| .70 | Bettlampe Jenny | 48:E1:E9:DF:AB:E5 | ✓ Fixed |
| .71 | Bettlampe Malte | 48:E1:E9:DF:A8:A4 | ✓ Fixed |

### 80-89: TP-Link Steckdosen

| IP | Gerät | MAC | Status |
|----|-------|-----|--------|
| .80 | HS110 | E4:C3:2A:89:FD:7D | → set-ip (von .100) |
| .81 | HS110 | E4:C3:2A:89:FE:A0 | → set-ip (von .101) |

### 90-99: Haushaltsgeräte

| IP | Gerät | MAC | Status |
|----|-------|-----|--------|
| .90 | AEG Waschmaschine | 44:3E:07:4F:B1:46 | → set-ip (von .161) |
| .91 | AEG Dampfgarer | 44:3E:07:23:13:75 | → set-ip (von .174) |
| .92 | Smart Scale P3 | C8:C9:A3:1A:87:55 | → Migration |

### 100-109: Garten

| IP | Gerät | MAC | Status |
|----|-------|-----|--------|
| .100 | GARDENA-1a6836 | 94:BB:AE:1A:68:9A | → Migration |

### 110-119: Mobilität

| IP | Gerät | MAC | Status |
|----|-------|-----|--------|
| .110 | Easee-EH4HHAPZ | 9C:9C:1F:CD:25:68 | → Migration |

### 120-129: Saugroboter

| IP | Gerät | MAC | Status |
|----|-------|-----|--------|
| .120 | Roborock S6 MaxV | B0:4A:39:02:8C:C0 | → Migration |

### 130-149: Sonstige IoT

| IP | Gerät | MAC | Status |
|----|-------|-----|--------|
| .130 | iO Sense (Velux) | B0:A7:32:97:54:20 | → Migration |
| .131 | espressif | F0:08:D1:5D:69:2C | → Migration |
| .132 | espressif | 90:15:06:34:43:68 | → Migration |
| .133 | lwip0 | BC:35:1E:42:DE:AC | → Migration |

---

## Migration Checkliste

### Schritt 1: DHCP-Range anpassen

Im UniFi Controller: Networks → IoT → DHCP Range auf **150-254** setzen.

### Schritt 2: Bestehende Fixed IPs umziehen

```bash
# TP-Link von 100er auf 80er Bereich
ui lo clients set-ip "HS110" 192.168.30.80  # E4:C3:2A:89:FD:7D
ui lo clients set-ip "HS110" 192.168.30.81  # E4:C3:2A:89:FE:A0

# AEG von 160er auf 90er Bereich
ui lo clients set-ip "AEG Waschmaschine" 192.168.30.90
ui lo clients set-ip "AEG Dampfgarer" 192.168.30.91

# Neue Meross auf 60er Bereich
ui lo clients set-ip "meross-mss210p-4fe2" 192.168.30.60
ui lo clients set-ip "Meross Smart Switch" 192.168.30.61  # 48:E1:E9:1A:E1:12
```

### Schritt 3: Geräte aus Sussdorff ins IoT-WLAN migrieren

Siehe [iot-wlan-migration.md](iot-wlan-migration.md) für Anleitungen je Gerätetyp.

Nach WLAN-Wechsel Fixed IP setzen:
```bash
ui lo clients set-ip "<gerätename>" 192.168.30.<ziel-ip>
```

---

## Befehle

```bash
# Fixed IP setzen (erstellt DHCP-Reservation + kickt Client)
ui lo clients set-ip "Gerätename" 192.168.30.XX

# Mit MAC-Adresse
ui lo clients set-ip AA:BB:CC:DD:EE:FF 192.168.30.XX

# Ohne Kick (IP erst bei nächstem DHCP-Renew aktiv)
ui lo clients set-ip "Gerätename" 192.168.30.XX --no-kick

# Alle Fixed IPs im IoT-Netz anzeigen
ui lo clients all -o json | jq -r '.[] | select(.use_fixedip == true) | select(.fixed_ip | startswith("192.168.30.")) | "\(.fixed_ip)\t\(.name)\t\(.mac)"' | sort -t. -k4 -n
```
