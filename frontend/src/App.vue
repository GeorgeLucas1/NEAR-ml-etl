<template>
  <div id="app">
    <!-- Scanline overlay -->
    <div class="scanlines"></div>

    <!-- Corner brackets -->
    <div class="corner corner-tl"></div>
    <div class="corner corner-tr"></div>
    <div class="corner corner-bl"></div>
    <div class="corner corner-br"></div>

    <!-- Animated grid background -->
    <div class="grid-bg"></div>

    <header class="header">
      <div class="header-left">
        <div class="logo-ring">
          <svg viewBox="0 0 40 40" width="40" height="40">
            <circle cx="20" cy="20" r="16" fill="none" stroke="#00c8ff" stroke-width="1.5" opacity="0.5"/>
            <circle cx="20" cy="20" r="10" fill="none" stroke="#00c8ff" stroke-width="1" stroke-dasharray="4 2"/>
            <circle cx="20" cy="20" r="4" fill="#00c8ff" opacity="0.9"/>
          </svg>
        </div>
        <div class="header-titles">
          <h1>J.A.R.V.I.S. <span class="subtitle-label">NEAR Health Intelligence</span></h1>
          <div class="system-id">SYS://MONITOR_V1.0 — novo PROJETO LULA DROID</div>
        </div>
      </div>

      <div class="header-right">
        <div class="status-module">
          <div class="pulse-dot" :class="isOnline ? 'pulse-green' : 'pulse-red'"></div>
          <span class="status-text">{{ isOnline ? 'SISTEMA ONLINE' : 'SISTEMA OFFLINE' }}</span>
        </div>
        <div class="timestamp-block">
          <span class="ts-label">ÚLTIMA ATUALIZAÇÃO</span>
          <span class="ts-value">{{ lastUpdate }}</span>
        </div>
      </div>
    </header>

    <nav class="nav">
      <router-link to="/" class="nav-link" :class="{ active: $route.path === '/' }">
        <span class="nav-icon">◈</span>
        <span>DASHBOARD</span>
      </router-link>
      <router-link to="/predictions" class="nav-link" :class="{ active: $route.path === '/predictions' }">
        <span class="nav-icon">◈</span>
        <span>PREVISÕES</span>
      </router-link>
      <router-link to="/anomalies" class="nav-link" :class="{ active: $route.path === '/anomalies' }">
        <span class="nav-icon">◈</span>
        <span>ANOMALIAS</span>
        <span v-if="anomalyCount > 0" class="nav-badge">{{ anomalyCount }}</span>
      </router-link>
      <router-link to="/system" class="nav-link" :class="{ active: $route.path === '/system' }">
        <span class="nav-icon">◈</span>
        <span>SISTEMA</span>
      </router-link>
    </nav>

    <main class="main-content">
      <router-view :metrics="metrics" :refresh="refreshInterval" @update:metrics="updateMetrics" />
    </main>

    <footer class="footer">
      <span>transumanismo  DE SOFTWARE </span>
      <span class="footer-sep">|</span>
      <span>PC HEALTH MONITOR v1.0</span>
      <span class="footer-sep">|</span>
      <span>ML ENGINE: ACTIVE</span>
      <span class="footer-sep">|</span>
      <span class="footer-ping">LATÊNCIA: {{ latency }}ms</span>
    </footer>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'

const API_URL = 'http://localhost:8080'

export default {
  name: 'App',
  setup() {
    const isOnline = ref(false)
    const lastUpdate = ref('--:--:--')
    const metrics = ref(null)
    const refreshInterval = ref(5)
    const anomalyCount = ref(0)
    const latency = ref(0)
    let intervalId = null

    const fetchMetrics = async () => {
      const t0 = performance.now()
      try {
        const response = await fetch(`${API_URL}/api/metrics/latest`)
        latency.value = Math.round(performance.now() - t0)
        if (response.ok) {
          const data = await response.json()
          if (data.error) {
            isOnline.value = false
          } else {
            metrics.value = data
            isOnline.value = true
            lastUpdate.value = new Date().toLocaleTimeString('pt-BR')
          }
        }
      } catch (e) {
        isOnline.value = false
        latency.value = 999
      }
    }

    const updateMetrics = (data) => {
      metrics.value = data
      isOnline.value = true
      lastUpdate.value = new Date().toLocaleTimeString('pt-BR')
    }

    onMounted(() => {
      fetchMetrics()
      intervalId = setInterval(fetchMetrics, refreshInterval.value * 1000)
    })

    onUnmounted(() => {
      if (intervalId) clearInterval(intervalId)
    })

    return {
      isOnline,
      lastUpdate,
      metrics,
      refreshInterval,
      anomalyCount,
      latency,
      updateMetrics
    }
  }
}
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@300;400;500;600;700&family=Share+Tech+Mono&family=Orbitron:wght@400;700;900&display=swap');

:root {
  --jarvis-blue: #00c8ff;
  --jarvis-blue-dim: rgba(0, 200, 255, 0.15);
  --jarvis-blue-glow: rgba(0, 200, 255, 0.4);
  --jarvis-cyan: #0ff;
  --jarvis-orange: #ff6b35;
  --jarvis-orange-dim: rgba(255, 107, 53, 0.15);
  --jarvis-red: #ff2d55;
  --jarvis-red-dim: rgba(255, 45, 85, 0.15);
  --jarvis-green: #00ff9d;
  --jarvis-green-dim: rgba(0, 255, 157, 0.15);
  --jarvis-yellow: #ffd60a;
  --jarvis-purple: #bf5af2;
  --bg-void: #020b14;
  --bg-panel: rgba(4, 20, 40, 0.85);
  --bg-panel-light: rgba(0, 80, 140, 0.12);
  --border-hud: rgba(0, 200, 255, 0.25);
  --border-hud-bright: rgba(0, 200, 255, 0.6);
  --text-primary: #e0f4ff;
  --text-secondary: #7ab8d8;
  --text-muted: rgba(120, 170, 200, 0.5);
  --font-hud: 'Rajdhani', sans-serif;
  --font-mono: 'Share Tech Mono', monospace;
  --font-display: 'Orbitron', monospace;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  background: var(--bg-void);
  color: var(--text-primary);
  font-family: var(--font-hud);
  min-height: 100vh;
  overflow-x: hidden;
}

#app {
  position: relative;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* Grid background */
.grid-bg {
  position: fixed;
  inset: 0;
  background-image:
    linear-gradient(rgba(0,200,255,0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,200,255,0.04) 1px, transparent 1px);
  background-size: 40px 40px;
  pointer-events: none;
  z-index: 0;
}

/* Scanlines */
.scanlines {
  position: fixed;
  inset: 0;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0,0,0,0.08) 2px,
    rgba(0,0,0,0.08) 4px
  );
  pointer-events: none;
  z-index: 999;
}

/* Corner brackets */
.corner {
  position: fixed;
  width: 24px;
  height: 24px;
  border-color: var(--jarvis-blue);
  border-style: solid;
  z-index: 100;
  opacity: 0.6;
}
.corner-tl { top: 8px; left: 8px; border-width: 1.5px 0 0 1.5px; }
.corner-tr { top: 8px; right: 8px; border-width: 1.5px 1.5px 0 0; }
.corner-bl { bottom: 8px; left: 8px; border-width: 0 0 1.5px 1.5px; }
.corner-br { bottom: 8px; right: 8px; border-width: 0 1.5px 1.5px 0; }

/* Header */
.header {
  position: relative;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 32px;
  background: var(--bg-panel);
  border-bottom: 1px solid var(--border-hud);
  backdrop-filter: blur(10px);
}

.header-left { display: flex; align-items: center; gap: 16px; }
.logo-ring { animation: spin 12s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.header-titles h1 {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 700;
  color: var(--jarvis-blue);
  letter-spacing: 3px;
  text-shadow: 0 0 20px var(--jarvis-blue-glow);
}
.subtitle-label {
  font-size: 10px;
  font-weight: 400;
  color: var(--text-secondary);
  letter-spacing: 2px;
  margin-left: 8px;
}
.system-id {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 2px;
  letter-spacing: 1px;
}

.header-right { display: flex; align-items: center; gap: 24px; }

.status-module { display: flex; align-items: center; gap: 8px; }
.pulse-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  animation: pulse 2s ease-in-out infinite;
}
.pulse-green { background: var(--jarvis-green); box-shadow: 0 0 8px var(--jarvis-green); }
.pulse-red { background: var(--jarvis-red); box-shadow: 0 0 8px var(--jarvis-red); }
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
.status-text {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--jarvis-green);
  letter-spacing: 2px;
}

.timestamp-block { display: flex; flex-direction: column; align-items: flex-end; }
.ts-label {
  font-size: 9px;
  color: var(--text-muted);
  letter-spacing: 2px;
  font-family: var(--font-mono);
}
.ts-value {
  font-family: var(--font-mono);
  font-size: 14px;
  color: var(--jarvis-blue);
  letter-spacing: 1px;
}

/* Nav */
.nav {
  position: relative;
  z-index: 10;
  display: flex;
  gap: 2px;
  padding: 0 32px;
  background: rgba(0,10,20,0.6);
  border-bottom: 1px solid var(--border-hud);
  backdrop-filter: blur(8px);
}

.nav-link {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  font-family: var(--font-display);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 3px;
  color: var(--text-secondary);
  text-decoration: none;
  transition: all 0.2s;
  border-bottom: 2px solid transparent;
}
.nav-link:hover {
  color: var(--jarvis-blue);
  background: var(--jarvis-blue-dim);
}
.nav-link.active {
  color: var(--jarvis-blue);
  border-bottom-color: var(--jarvis-blue);
  background: var(--jarvis-blue-dim);
}
.nav-icon { font-size: 10px; opacity: 0.6; }
.nav-badge {
  background: var(--jarvis-red);
  color: #fff;
  font-size: 9px;
  padding: 2px 6px;
  border-radius: 2px;
  font-family: var(--font-mono);
}

/* Main */
.main-content {
  position: relative;
  z-index: 5;
  flex: 1;
  padding: 24px 32px;
}

/* Footer */
.footer {
  position: relative;
  z-index: 10;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 32px;
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-muted);
  background: var(--bg-panel);
  border-top: 1px solid var(--border-hud);
  letter-spacing: 2px;
}
.footer-sep { opacity: 0.3; }
.footer-ping { color: var(--jarvis-green); margin-left: auto; }

/* ===== SHARED COMPONENT STYLES ===== */

/* HUD Panel */
.hud-panel {
  background: var(--bg-panel);
  border: 1px solid var(--border-hud);
  border-radius: 2px;
  position: relative;
  padding: 20px;
  backdrop-filter: blur(8px);
}
.hud-panel::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--jarvis-blue), transparent);
}

/* Panel header */
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-hud);
}
.panel-title {
  font-family: var(--font-display);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 3px;
  color: var(--jarvis-blue);
  display: flex;
  align-items: center;
  gap: 10px;
}
.panel-title::before {
  content: '//';
  opacity: 0.4;
  font-weight: 400;
}

/* Metrics grid */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
  margin-bottom: 20px;
}

.metric-tile {
  background: var(--bg-panel-light);
  border: 1px solid var(--border-hud);
  border-radius: 2px;
  padding: 16px;
  position: relative;
  overflow: hidden;
}
.metric-tile::after {
  content: '';
  position: absolute;
  bottom: 0; left: 0;
  height: 2px;
  width: 100%;
  background: var(--tile-accent, var(--jarvis-blue));
  opacity: 0.6;
}
.metric-tile.accent-green { --tile-accent: var(--jarvis-green); border-color: rgba(0,255,157,0.2); }
.metric-tile.accent-orange { --tile-accent: var(--jarvis-orange); border-color: rgba(255,107,53,0.2); }
.metric-tile.accent-red { --tile-accent: var(--jarvis-red); border-color: rgba(255,45,85,0.2); }
.metric-tile.accent-yellow { --tile-accent: var(--jarvis-yellow); border-color: rgba(255,214,10,0.2); }

.tile-label {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-muted);
  letter-spacing: 2px;
  margin-bottom: 8px;
  text-transform: uppercase;
}
.tile-value {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 700;
  color: var(--tile-accent, var(--jarvis-blue));
  line-height: 1;
}
.tile-value span {
  font-size: 12px;
  font-weight: 400;
  color: var(--text-muted);
  margin-left: 4px;
}

/* Data table */
.hud-table {
  width: 100%;
  border-collapse: collapse;
  font-family: var(--font-mono);
  font-size: 12px;
}
.hud-table thead tr {
  border-bottom: 1px solid var(--border-hud-bright);
}
.hud-table th {
  padding: 8px 12px;
  text-align: left;
  font-size: 9px;
  letter-spacing: 3px;
  color: var(--jarvis-blue);
  font-weight: 400;
  text-transform: uppercase;
}
.hud-table tbody tr {
  border-bottom: 1px solid rgba(0,200,255,0.05);
  transition: background 0.15s;
}
.hud-table tbody tr:hover {
  background: var(--jarvis-blue-dim);
}
.hud-table td {
  padding: 10px 12px;
  color: var(--text-secondary);
}

/* Severity badges */
.sev-high { color: var(--jarvis-red); }
.sev-medium { color: var(--jarvis-yellow); }
.sev-low { color: var(--jarvis-green); }

/* Alert */
.hud-alert {
  padding: 16px;
  border-radius: 2px;
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: 1px;
  display: flex;
  align-items: center;
  gap: 12px;
}
.hud-alert.alert-ok {
  background: var(--jarvis-green-dim);
  border: 1px solid rgba(0,255,157,0.3);
  color: var(--jarvis-green);
}
.hud-alert.alert-warn {
  background: var(--jarvis-red-dim);
  border: 1px solid rgba(255,45,85,0.3);
  color: var(--jarvis-red);
}

/* Loading */
.hud-loading {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--jarvis-blue);
  letter-spacing: 2px;
  padding: 40px;
  text-align: center;
  animation: blink 1.2s step-end infinite;
}
@keyframes blink { 50% { opacity: 0.3; } }

/* Gauge container */
.gauge-wrap {
  position: relative;
  width: 80px; height: 80px;
  margin: 12px auto 0;
}

/* Charts */
.chart-wrap {
  position: relative;
  height: 240px;
  width: 100%;
}
.chart-wrap-tall {
  position: relative;
  height: 380px;
  width: 100%;
}

/* Section title */
.section-title {
  font-family: var(--font-display);
  font-size: 10px;
  letter-spacing: 3px;
  color: var(--text-secondary);
  margin: 20px 0 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.section-title::before {
  content: '';
  display: block;
  width: 16px;
  height: 1px;
  background: var(--jarvis-blue);
}

/* Status text */
.status-ok { color: var(--jarvis-green); }
.status-warn { color: var(--jarvis-yellow); }
.status-crit { color: var(--jarvis-red); }

/* Select */
.hud-select {
  background: var(--bg-panel);
  border: 1px solid var(--border-hud);
  color: var(--jarvis-blue);
  font-family: var(--font-mono);
  font-size: 11px;
  padding: 6px 10px;
  border-radius: 2px;
  outline: none;
  letter-spacing: 1px;
  cursor: pointer;
}
.hud-select:focus {
  border-color: var(--jarvis-blue);
}

/* Map */
.map-frame {
  border: 1px solid var(--border-hud);
  border-radius: 2px;
  overflow: hidden;
  margin: 16px 0;
}

/* Code inline */
code {
  font-family: var(--font-mono);
  background: var(--jarvis-blue-dim);
  border: 1px solid var(--border-hud);
  padding: 2px 8px;
  font-size: 11px;
  color: var(--jarvis-blue);
  border-radius: 2px;
}

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--bg-void); }
::-webkit-scrollbar-thumb { background: var(--jarvis-blue-dim); border-radius: 2px; }
</style>