# IoT-Geräte WLAN-Migration

Migration der IoT-Geräte vom **Sussdorff**-WLAN ins **SussdorffIoT**-WLAN.

**Ziel-WLAN:** SussdorffIoT (192.168.30.x, nur 2.4 GHz)

---

## Checkliste

### Meross (HomeKit) - 7 Geräte

- [ ] meross-mss210p-44fc (192.168.10.148)
- [ ] meross-mss210p-4fee (192.168.10.163)
- [ ] Meross Smart Switch (192.168.10.143)
- [ ] All-In-One_RasPi (192.168.10.140)
- [ ] All-In-One_RasPi (192.168.10.171)
- [ ] All-In-One_RasPi (192.168.10.198)
- [ ] Elysium - Meross (192.168.10.144)

### Shelly - 2 Geräte

- [ ] shellypro3em-2cbcbba73d30 (192.168.10.142)
- [ ] shellypro3em-2cbcbba746e8 (192.168.10.169)

### ESP/Espressif - 5 Geräte

- [ ] Easee-EH4HHAPZ - Wallbox (192.168.10.112)
- [ ] Tibber Pulse (192.168.10.141)
- [ ] iO Sense (192.168.10.185)
- [ ] espressif (192.168.10.106)
- [ ] lwip0 (192.168.10.175)

### Andere IoT - 6 Geräte

- [ ] GARDENA-1a6836 (192.168.10.186)
- [ ] Hoymiles Balkon (192.168.10.122)
- [ ] Netatmo (192.168.10.190)
- [ ] Nuki Smart Lock (192.168.10.187)
- [ ] Roborock S6 MaxV (192.168.10.168)
- [ ] Solaris (192.168.10.123)

---

## Anleitungen nach Gerätetyp

### Meross (HomeKit)

**Wichtig:** mDNS Reflector ist aktiviert - HomeKit funktioniert über VLAN-Grenzen.

**Methode 1: Über Apple Home App (empfohlen)**

1. iPhone mit **SussdorffIoT**-WLAN verbinden
2. Home App öffnen → Gerät lange drücken → Einstellungen
3. "Gerät entfernen" wählen
4. Gerät in Pairing-Modus versetzen (siehe Reset unten)
5. In Home App "Gerät hinzufügen" → QR-Code scannen
6. SussdorffIoT-WLAN wird automatisch verwendet

**Methode 2: Über Meross App**

1. Meross App öffnen
2. Gerät auswählen → Einstellungen → "Gerät entfernen"
3. Reset am Gerät durchführen
4. iPhone ins SussdorffIoT-WLAN wechseln
5. Neu einrichten über "+" → Gerät hinzufügen

**Reset je nach Gerätetyp:**
- **Steckdose (MSS210):** Taste 5 Sekunden gedrückt halten bis LED blinkt
- **Schalter:** Taste gedrückt halten bis LED schnell blinkt
- **Thermostat:** Beide Pfeiltasten gleichzeitig halten bis Display aus

**Hinweise:**
- Nur 2.4 GHz wird unterstützt (SussdorffIoT ist bereits 2.4 GHz only)
- Wi-Fi 6 (802.11ax) kann Probleme machen
- Nach Umstellung iPhone zurück ins Sussdorff-WLAN - Steuerung funktioniert dank mDNS Reflector

> **Quellen:** [SmartApfel](https://smartapfel.de/wlan-aendern-homekit-geraete-richtig-umziehen/), [HomeKit Forum](https://forum.smartapfel.de/forum/thread/1745-homekit-wlan-ändern-wie-am-besten/)

---

### Shelly Pro 3EM

**Methode: Über Web-Interface**

1. **AP-Modus aktivieren:** Taste am Gerät 5 Sekunden gedrückt halten
2. Mit Smartphone zum WLAN "ShellyPro3EM-XXXX" verbinden
3. Browser öffnen → `192.168.33.1` aufrufen
4. **Settings → WiFi → WiFi 1**
5. SussdorffIoT auswählen und Passwort eingeben
6. Optional: Statische IP vergeben
7. Speichern → Gerät verbindet sich mit neuem WLAN

**LED-Status:**
- Blau = AP-Modus aktiv
- Rot = Nicht verbunden
- Gelb = WLAN verbunden, keine Cloud
- Grün = WLAN + Cloud verbunden

**Factory Reset (falls nötig):** Taste 10 Sekunden halten

**Tipp:** Shelly unterstützt 2 WiFi-Netzwerke gleichzeitig als Fallback.

> **Quelle:** [Shelly Knowledge Base](https://kb.shelly.cloud/knowledge-base/shelly-pro-3em-web-interface-guide)

---

### Easee Wallbox

**Methode 1: Über Easee App (wenn online)**

1. Easee App öffnen
2. Auf WLAN-Symbol (oben links auf Ladekarte) tippen
3. Oder: Ladegerät → Einstellungen → WLAN
4. Neues Netzwerk (SussdorffIoT) auswählen
5. Passwort eingeben und speichern

**Methode 2: Über lokales Web-Interface**

1. **Hotspot aktivieren:** Touch-Button über LED-Leiste 5 Sek. halten bis grün leuchtet
2. Mit Smartphone zum Easee-WLAN verbinden
3. Browser öffnen → `192.168.4.1`
4. WLAN-Einstellungen ändern
5. Hotspot deaktiviert sich nach 15 Min. automatisch

**Hinweise:**
- Nur 2.4 GHz (802.11 b/g/n)
- Kein WiFi 6 Support
- Keine Sonderzeichen im Passwort: `. / \ - &` werden nicht unterstützt
- DHCP erforderlich (keine statische IP möglich)

> **Quelle:** [Easee Support](https://support.easee.com/hc/de/articles/6845486573585-Verbinden-Sie-Ihr-Ladegerät-mit-WLAN)

---

### Tibber Pulse (Bridge)

**Methode: Access Point Modus**

1. **AP-Modus aktivieren:**
   - Bridge ausstecken
   - 3 Sek. warten → einstecken
   - 3 Sek. warten → ausstecken
   - 3 Sek. warten → einstecken
   - LED sollte grün leuchten

2. Mit Smartphone zum "Tibber Bridge"-WLAN verbinden
   - Passwort: Die 9 Zeichen auf der Bridge (inkl. Bindestrich, z.B. `AD56-54BA`)

3. Browser öffnen → `http://10.133.70.1/`
   - Benutzername: `admin`
   - Passwort: Die 9 Zeichen von der Bridge

4. WLAN-Einstellungen ändern:
   - `ssid`: SussdorffIoT
   - `psk`: WLAN-Passwort

5. Bridge ausstecken, 10 Sek. warten, wieder einstecken
6. LED sollte hellblau leuchten = verbunden

**Factory Reset (Alternative):**
- Bridge 10× ein- und ausstecken (jeweils 5 Sek. warten)
- Beim 10. Mal: LED rot → weiß → violett = Reset

**Hinweis:** Nur 2.4 GHz wird unterstützt.

> **Quellen:** [Tibber Support](https://support.tibber.com/de/articles/6498539-hilfestellung-rund-um-den-pulse-ir), [MASCHINFO](https://www.maschinfo.de/Tibber-Pulse-IR)

---

### GARDENA Smart Gateway

**Methode 1: Über GARDENA App**

1. GARDENA smart App öffnen
2. Einstellungen (Zahnrad) → Gartenprofil → WLAN
3. Anweisungen zur WLAN-Einrichtung folgen

**Methode 2: Über Gateway Interface**

1. **Konfigurations-WLAN aktivieren:** Reset-Taste kurz drücken
2. Mit Smartphone zu "GARDENA_config_XXXX" verbinden
3. Browser öffnen → Gateway-IP eingeben
4. WLAN-Netzwerk (SussdorffIoT) auswählen
5. Passwort eingeben und bestätigen
6. Warten bis Internet-LED dauerhaft grün leuchtet

**Hinweis:** Konfigurations-WLAN ist nur 15 Minuten aktiv.

**Factory Reset (falls nötig):**
1. Gateway per LAN-Kabel mit Router verbinden
2. Netzteil trennen
3. Reset-Taste gedrückt halten
4. Netzteil wieder anschließen
5. Warten bis Power-LED gelb leuchtet
6. Reset-Taste loslassen
7. Warten bis beide LEDs grün (bis zu 15 Min.)

> **Quelle:** [GARDENA Help Center](https://help.gardena.com/hc/de/articles/7991778755868-Gateway-kann-nicht-per-WLAN-verbunden-werden-Neueinrichtung-Router-Wechsel)

---

### Hoymiles DTU (Balkonkraftwerk)

**Methode: Über Installer App**

1. Hoymiles Installer App öffnen und anmelden
2. Unten auf "Ich" → "Netzwerkkonfiguration"
3. Netzwerkname: SussdorffIoT
4. Passwort eingeben
5. "An DTU senden" drücken

**Alternative: Über DTU-Hotspot**

1. Smartphone WLAN-Einstellungen öffnen
2. Mit "AP_XXXXXX" (DTU-Netzwerk) verbinden
3. Browser öffnen → Konfigurationsseite
4. WLAN-Daten eingeben → "Connect"

**Hinweise:**
- Nur 2.4 GHz
- **Keine Sonderzeichen im Passwort**
- Max. 30 Zeichen Passwortlänge
- Bei FRITZ!Box evtl. Sicherheitseinstellungen anpassen

**LED-Status:**
- Blau = WLAN verbunden
- Grün blinkend = Internet OK, keine Wechselrichter-Verbindung

**Bei Problemen:** Reset-Knopf auf Rückseite

> **Quellen:** [Aceflex](https://www.aceflex.de/magazin/hoymiles-dtu-wlite-s-anleitung-alle-wichtigen-infos/), [Yuma Support](https://support.yuma.de/hc/de/articles/12658250979997-WLAN-DTU-verbindet-nicht-was-tun)

---

### Netatmo Wetterstation

**Methode: Über Netatmo App**

1. Netatmo App öffnen
2. Einstellungen → Mein Zuhause verwalten
3. Raum mit Hauptmodul auswählen
4. Modul antippen
5. Information → "Konfigurieren..."
6. Neues WLAN (SussdorffIoT) einrichten

**Hinweise:**
- Smartphone muss mit dem neuen WLAN verbunden sein
- Nur 2.4 GHz
- **WPA3 wird NICHT unterstützt**
- Keine Firmen-/öffentliche Netzwerke
- Keine WLAN-Repeater

**MAC-Adresse:** Auf Unterseite des Innenmoduls

> **Quelle:** [Netatmo Help Center](https://helpcenter.netatmo.com/hc/en-us/articles/360021158611-I-have-changed-Wi-Fi-access-point-or-I-have-moved-How-do-I-reconfigure-my-connection)

---

### Nuki Smart Lock 3.0

**Methode: Über Nuki App**

1. Nuki App öffnen
2. Smart Lock auswählen → Einstellungen
3. Funktionen & Konfiguration → Integriertes WLAN
4. "WLAN konfigurieren" tippen
5. SussdorffIoT aus Liste auswählen
6. Passwort eingeben und speichern

**Bei Verbindungsproblemen:**
- Einstellungen → Integriertes WLAN → "Kompatibilitätsmodus" aktivieren

**Reset (falls nötig):**
1. Integriertes WLAN deaktivieren
2. Smartphone neu starten
3. WLAN wieder aktivieren

**Hinweise:**
- Nur 2.4 GHz
- Kein WiFi 6 / WPA3
- WPA2/WPA3-Mischmodus verwenden
- Gute Signalstärke zum Router sicherstellen

> **Quelle:** [Nuki Support](https://help.nuki.io/hc/en-us/articles/4402753572497-Activate-built-in-Wi-Fi)

---

### Roborock S6 MaxV

**Methode: WLAN zurücksetzen**

1. Obere Klappe öffnen (WLAN-Anzeige sichtbar)
2. **Gleichzeitig drücken:** "Punktreinigung" + "Station" (oder Charge + Clean)
3. Halten bis Sprachansage "WLAN zurücksetzen" ertönt
4. WLAN-Anzeige blinkt langsam

**Neues WLAN einrichten:**

1. Roborock App öffnen
2. Gerät hinzufügen oder WLAN-Einstellungen
3. SussdorffIoT auswählen
4. Passwort eingeben

**Wichtig:** Karten und Einstellungen bleiben beim WLAN-Reset erhalten!

**Hinweise:**
- Nur 2.4 GHz
- **Keine Sonderzeichen im Passwort** (`&/%$§` etc.)
- Kein WEP, nur WPA/WPA2

> **Quellen:** [Roborock Anleitung](https://us.roborock.com/pages/anleitung-zum-verbinden-mit-dem-netzwerk-deutsch), [Smart-Home-Fox](https://www.smart-home-fox.de/roborock-mit-wlan-verbinden)

---

### Generische ESP/Espressif-Geräte

Für Geräte wie `iO Sense`, `lwip0`, `espressif`:

**Typische Methoden:**

1. **Taste gedrückt halten** (5-10 Sek.) bis LED blinkt
2. Mit dem AP des Geräts verbinden (Name enthält oft "ESP" oder Gerätenamen)
3. Browser → `192.168.4.1` oder `192.168.1.1`
4. WLAN-Einstellungen ändern

**Bei Tasmota-Geräten:**
1. Taste 4× schnell drücken → AP-Modus
2. Mit "tasmota-XXXX" WLAN verbinden
3. Browser → `192.168.4.1`
4. Configuration → WiFi → Neue SSID/Passwort

**Bei ESPHome-Geräten:**
- Firmware mit neuen WLAN-Credentials neu flashen
- Oder Fallback-AP nutzen (falls konfiguriert)

---

## Allgemeine Hinweise

### Vor der Migration

- [ ] SussdorffIoT-WLAN Passwort bereithalten
- [ ] iPhone/iPad für HomeKit-Geräte ins SussdorffIoT verbinden können
- [ ] Home Assistant Integrationen nach Migration prüfen

### Nach der Migration

- [ ] Gerät in Home Assistant erreichbar?
- [ ] HomeKit-Steuerung funktioniert?
- [ ] Automationen testen

### Problemlösung

| Problem | Lösung |
|---------|--------|
| Gerät findet WLAN nicht | Nur 2.4 GHz aktiviert? |
| Verbindung bricht ab | Sonderzeichen im Passwort? |
| HomeKit findet Gerät nicht | mDNS Reflector aktiviert? (ist es!) |
| Pairing schlägt fehl | iPhone im gleichen WLAN wie Gerät? |

---

## Quellen

- [SmartApfel - HomeKit WLAN ändern](https://smartapfel.de/wlan-aendern-homekit-geraete-richtig-umziehen/)
- [Shelly Knowledge Base](https://kb.shelly.cloud/knowledge-base/shelly-pro-3em-web-interface-guide)
- [Easee Support](https://support.easee.com/hc/de/articles/6845486573585-Verbinden-Sie-Ihr-Ladegerät-mit-WLAN)
- [Tibber Support](https://support.tibber.com/de/articles/6498539-hilfestellung-rund-um-den-pulse-ir)
- [GARDENA Help Center](https://help.gardena.com/hc/de/articles/7991778755868)
- [Hoymiles Anleitung](https://www.aceflex.de/magazin/hoymiles-dtu-wlite-s-anleitung-alle-wichtigen-infos/)
- [Netatmo Help Center](https://helpcenter.netatmo.com/hc/en-us/articles/360021158611)
- [Nuki Support](https://help.nuki.io/hc/en-us/articles/4402753572497-Activate-built-in-Wi-Fi)
- [Roborock Support](https://us.roborock.com/pages/anleitung-zum-verbinden-mit-dem-netzwerk-deutsch)
