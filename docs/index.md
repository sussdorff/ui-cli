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
  padding: 1.5rem 0 1rem;
}
.hero img {
  max-width: 200px;
  margin-bottom: 0.5rem;
}
.hero h1 {
  font-size: 2.5rem;
  margin: 0.5rem 0;
}
.hero .tagline {
  font-size: 1.3rem;
  color: #ffc107;
  margin: 0.25rem 0;
}
.hero .subtitle {
  font-size: 1rem;
  opacity: 0.8;
  margin: 0.5rem 0 1rem;
}
.hero .buttons {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
  margin-bottom: 1rem;
}
.hero .buttons a {
  padding: 0.6rem 1.25rem;
  border-radius: 0.5rem;
  text-decoration: none;
  font-weight: bold;
  font-size: 0.9rem;
}
.hero .buttons .primary {
  background: #7c4dff;
  color: white;
}
.hero .buttons .secondary {
  border: 2px solid #7c4dff;
  color: #7c4dff;
}
.install-box {
  background: #1e1e1e;
  border-radius: 0.5rem;
  padding: 0.5rem 1rem;
  margin: 0 auto 1.5rem;
  max-width: 500px;
  font-size: 0.85rem;
}
.features {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  max-width: 900px;
  margin: 0 auto;
}
@media (max-width: 800px) {
  .features {
    grid-template-columns: repeat(2, 1fr);
  }
}
.feature {
  padding: 1rem;
  border-radius: 0.5rem;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.1);
  text-align: center;
}
.feature .icon {
  font-size: 1.5rem;
  margin-bottom: 0.25rem;
}
.feature h3 {
  margin: 0.25rem 0;
  font-size: 0.95rem;
}
.feature p {
  margin: 0;
  font-size: 0.8rem;
  opacity: 0.8;
}
.footer-note {
  text-align: center;
  margin-top: 1.5rem;
  font-size: 0.85rem;
  opacity: 0.6;
}
</style>

<div class="hero">
  <img src="assets/gorilla.png" alt="UI-CLI Gorilla">
  <h1>UI-CLI</h1>
  <p class="tagline">⚡ Gorilla Powered! ⚡</p>
  <p class="subtitle">Manage your UniFi infrastructure from the command line</p>

  <div class="buttons">
    <a href="getting-started/" class="primary">Get Started</a>
    <a href="https://github.com/vedanta/ui-cli" class="secondary">GitHub</a>
  </div>

  <div class="install-box">

```bash
git clone https://github.com/vedanta/ui-cli.git && cd ui-cli && pip install -e .
```

  </div>
</div>

<div class="features">
  <div class="feature">
    <div class="icon">🌐</div>
    <h3>Cloud API</h3>
    <p>Multi-site management via api.ui.com</p>
  </div>
  <div class="feature">
    <div class="icon">🏠</div>
    <h3>Local Controller</h3>
    <p>Direct UDM & Cloud Key access</p>
  </div>
  <div class="feature">
    <div class="icon">👥</div>
    <h3>Client Control</h3>
    <p>List, block, monitor clients</p>
  </div>
  <div class="feature">
    <div class="icon">📡</div>
    <h3>Device Mgmt</h3>
    <p>Restart, upgrade, locate</p>
  </div>
  <div class="feature">
    <div class="icon">📊</div>
    <h3>Analytics</h3>
    <p>DPI stats & traffic reports</p>
  </div>
  <div class="feature">
    <div class="icon">🔥</div>
    <h3>Firewall</h3>
    <p>Rules, groups, port forwards</p>
  </div>
  <div class="feature">
    <div class="icon">🎫</div>
    <h3>Vouchers</h3>
    <p>Guest hotspot management</p>
  </div>
  <div class="feature">
    <div class="icon">💾</div>
    <h3>Config Export</h3>
    <p>Backup to YAML/JSON</p>
  </div>
</div>

<p class="footer-note">Works with UDM • UDM Pro • UDM SE • Cloud Key • Self-hosted</p>
