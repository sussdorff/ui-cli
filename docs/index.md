---
hide:
  - navigation
  - toc
---

<style>
.md-content__button {
  display: none;
}
.hero {
  text-align: center;
  padding: 2rem 0;
}
.hero img {
  max-width: 300px;
  margin-bottom: 1rem;
}
.hero h1 {
  font-size: 3rem;
  margin-bottom: 0.5rem;
}
.hero .tagline {
  font-size: 1.5rem;
  color: #ffc107;
  margin-bottom: 1rem;
}
.hero .subtitle {
  font-size: 1.2rem;
  opacity: 0.8;
  margin-bottom: 2rem;
}
.hero .buttons {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
}
.hero .buttons a {
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  text-decoration: none;
  font-weight: bold;
}
.hero .buttons .primary {
  background: #7c4dff;
  color: white;
}
.hero .buttons .secondary {
  border: 2px solid #7c4dff;
  color: #7c4dff;
}
.features {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
  margin-top: 3rem;
}
.feature {
  padding: 1.5rem;
  border-radius: 0.5rem;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.1);
}
.feature h3 {
  margin-top: 0;
}
.install-box {
  background: #1e1e1e;
  border-radius: 0.5rem;
  padding: 1rem;
  margin: 2rem auto;
  max-width: 600px;
  text-align: left;
}
.install-box code {
  color: #4caf50;
}
</style>

<div class="hero">
  <img src="assets/gorilla.png" alt="UI-CLI Gorilla">
  <h1>UI-CLI</h1>
  <p class="tagline">⚡ Gorilla Powered! ⚡</p>
  <p class="subtitle">Manage your UniFi infrastructure from the command line</p>

  <div class="buttons">
    <a href="getting-started/" class="primary">Get Started</a>
    <a href="https://github.com/vedanta/ui-cli" class="secondary">View on GitHub</a>
  </div>
</div>

<div class="install-box">
```bash
git clone https://github.com/vedanta/ui-cli.git && cd ui-cli
pip install -e .
./ui status
```
</div>

<div class="features">
  <div class="feature">
    <h3>🌐 Cloud API</h3>
    <p>Manage multiple sites from anywhere via <code>api.ui.com</code>. View hosts, sites, devices, ISP metrics, and SD-WAN configurations.</p>
  </div>

  <div class="feature">
    <h3>🏠 Local Controller</h3>
    <p>Connect directly to your UDM, Cloud Key, or self-hosted controller. Full client and device management with real-time data.</p>
  </div>

  <div class="feature">
    <h3>👥 Client Management</h3>
    <p>List, search, block, unblock, and monitor network clients. View detailed status including signal strength and WiFi experience.</p>
  </div>

  <div class="feature">
    <h3>📡 Device Control</h3>
    <p>Restart, upgrade firmware, locate with LED, and adopt new devices. Full control over your UniFi infrastructure.</p>
  </div>

  <div class="feature">
    <h3>📊 Traffic Analytics</h3>
    <p>Deep packet inspection (DPI) statistics, per-client traffic breakdown, and daily/hourly bandwidth reports.</p>
  </div>

  <div class="feature">
    <h3>🎫 Guest Vouchers</h3>
    <p>Create and manage hotspot vouchers with custom duration, data limits, and speed caps.</p>
  </div>

  <div class="feature">
    <h3>🔥 Firewall Inspection</h3>
    <p>View firewall rules, address/port groups, and port forwarding configurations.</p>
  </div>

  <div class="feature">
    <h3>💾 Config Export</h3>
    <p>Backup your running configuration to YAML or JSON. Filter by section for targeted exports.</p>
  </div>
</div>

---

<div style="text-align: center; margin-top: 3rem; opacity: 0.7;">
  <p>Works with <strong>UDM</strong> • <strong>UDM Pro</strong> • <strong>UDM SE</strong> • <strong>Cloud Key</strong> • <strong>Self-hosted Controllers</strong></p>
</div>
