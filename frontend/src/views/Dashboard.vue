<template>
  <div class="dashboard-view">
    <!-- Top bar -->
    <div class="dash-topbar">
      <div class="topbar-left">
        <span class="panel-title">// MONITORAMENTO EM TEMPO REAL</span>
      </div>
      <div class="topbar-right">
        <label class="hud-label">AUTO-REFRESH</label>
        <select v-model="localRefresh" class="hud-select" @change="changeRefresh">
          <option value="2">2s</option>
          <option value="5">5s</option>
          <option value="10">10s</option>
          <option value="30">30s</option>
        </select>
      </div>
    </div>

    <div v-if="!metrics" class="hud-loading">
      ■ AGUARDANDO SINAL DA API... ■
    </div>

    <template v-else>
      <!-- Gauge row -->
      <div class="metrics-grid">
        <div class="metric-tile" v-for="tile in tiles" :key="tile.key" :class="'accent-' + tile.accent">
          <div class="tile-label">{{ tile.label }}</div>
          <div class="gauge-wrap">
            <canvas :ref="el => gaugeRefs[tile.key] = el"></canvas>
            <div class="gauge-center">
              <span class="gauge-num">{{ formatNumber(metrics[tile.key]) }}</span>
              <span class="gauge-unit">{{ tile.unit }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Network & Disk -->
      <div class="metrics-grid mt-16">
        <div class="metric-tile">
          <div class="tile-label">NET ↑ UPLOAD</div>
          <div class="tile-value">{{ formatBytes(metrics.network?.bytes_sent) }}</div>
        </div>
        <div class="metric-tile accent-green">
          <div class="tile-label">NET ↓ DOWNLOAD</div>
          <div class="tile-value">{{ formatBytes(metrics.network?.bytes_recv) }}</div>
        </div>
        <div class="metric-tile">
          <div class="tile-label">DISK READ</div>
          <div class="tile-value">{{ formatNumber(metrics.disk_read) }}<span>B/s</span></div>
        </div>
        <div class="metric-tile accent-orange">
          <div class="tile-label">DISK WRITE</div>
          <div class="tile-value">{{ formatNumber(metrics.disk_write) }}<span>B/s</span></div>
        </div>
      </div>

      <!-- Charts row -->
      <div class="charts-row mt-16">
        <div class="hud-panel">
          <div class="panel-header">
            <span class="panel-title">HISTÓRICO CPU</span>
            <span class="panel-badge">ÚLTIMAS 20 LEITURAS</span>
          </div>
          <div class="chart-wrap">
            <canvas ref="historyChart"></canvas>
          </div>
        </div>

        <div class="hud-panel">
          <div class="panel-header">
            <span class="panel-title">PREVISÃO ML</span>
            <span class="panel-badge">HORIZON +12</span>
          </div>
          <div class="chart-wrap">
            <canvas ref="predChart"></canvas>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
import { ref, watch, onMounted, nextTick, reactive } from 'vue'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

const API_URL = 'http://localhost:8080'

const JARVIS_CHART_DEFAULTS = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false }, tooltip: { enabled: false } },
}

const COLORS = {
  blue: '#00c8ff',
  green: '#00ff9d',
  orange: '#ff6b35',
  red: '#ff2d55',
  yellow: '#ffd60a',
}

export default {
  name: 'Dashboard',
  props: ['metrics', 'refresh'],
  setup(props) {
    const localRefresh = ref(props.refresh || 5)
    const gaugeRefs = reactive({})
    const historyChart = ref(null)
    const predChart = ref(null)
    const chartInstances = {}

    const tiles = [
      { key: 'cpu_usage', label: 'CPU USAGE', unit: '%', accent: 'default', color: COLORS.blue, max: 100 },
      { key: 'ram_usage', label: 'RAM USAGE', unit: '%', accent: 'red', color: COLORS.red, max: 100 },
      { key: 'gpu_usage', label: 'GPU USAGE', unit: '%', accent: 'green', color: COLORS.green, max: 100 },
      { key: 'cpu_temp', label: 'CPU TEMP', unit: '°C', accent: 'orange', color: COLORS.orange, max: 120 },
    ]

    const formatNumber = (val) => {
      if (val === null || val === undefined) return '0'
      return Number(val).toFixed(1)
    }

    const formatBytes = (bytes) => {
      if (!bytes) return '0 B'
      if (bytes < 1024) return bytes + ' B'
      if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
      return (bytes / 1048576).toFixed(2) + ' MB'
    }

    const destroyChart = (key) => {
      if (chartInstances[key]) {
        chartInstances[key].destroy()
        delete chartInstances[key]
      }
    }

    const createGauge = (canvas, value, color, max = 100) => {
      if (!canvas) return
      const key = canvas
      destroyChart(key)
      const pct = Math.min(value / max, 1)
      const rem = 1 - pct
      chartInstances[key] = new Chart(canvas.getContext('2d'), {
        type: 'doughnut',
        data: {
          datasets: [{
            data: [pct * 100, rem * 100],
            backgroundColor: [color, 'rgba(0,200,255,0.06)'],
            borderWidth: 0,
          }]
        },
        options: {
          ...JARVIS_CHART_DEFAULTS,
          cutout: '76%',
          rotation: -90,
          circumference: 180,
        }
      })
    }

    const hudLineChart = (canvas, data, label, color) => {
      if (!canvas || !data?.length) return
      destroyChart(canvas)
      const labels = data.map(d => {
        try { return new Date(d.timestamp).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) } catch { return '' }
      })
      const values = data.map(d => d.value || d.predicted || 0)

      chartInstances[canvas] = new Chart(canvas.getContext('2d'), {
        type: 'line',
        data: {
          labels: labels.slice(-20),
          datasets: [{
            label,
            data: values.slice(-20),
            borderColor: color,
            backgroundColor: color + '18',
            fill: true,
            tension: 0.4,
            pointRadius: 2,
            pointBackgroundColor: color,
            borderWidth: 1.5,
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: {
              backgroundColor: 'rgba(2,11,20,0.9)',
              borderColor: color,
              borderWidth: 1,
              titleColor: color,
              bodyColor: '#7ab8d8',
              titleFont: { family: 'Share Tech Mono', size: 11 },
              bodyFont: { family: 'Share Tech Mono', size: 11 },
            }
          },
          scales: {
            x: {
              grid: { color: 'rgba(0,200,255,0.06)' },
              ticks: { color: '#7ab8d8', font: { family: 'Share Tech Mono', size: 9 }, maxTicksLimit: 6 }
            },
            y: {
              grid: { color: 'rgba(0,200,255,0.06)' },
              ticks: { color: '#7ab8d8', font: { family: 'Share Tech Mono', size: 9 } },
              min: 0, max: 100,
            }
          }
        }
      })
    }

    const updateGauges = (m) => {
      nextTick(() => {
        tiles.forEach(t => {
          const canvas = gaugeRefs[t.key]
          if (canvas) createGauge(canvas, m[t.key] || 0, t.color, t.max)
        })
      })
    }

    const fetchHistory = async () => {
      try {
        const r = await fetch(`${API_URL}/api/metrics/history?hours=1`)
        if (r.ok) {
          const data = await r.json()
          if (Array.isArray(data) && data.length > 0) {
            await nextTick()
            hudLineChart(historyChart.value, data, 'CPU %', COLORS.blue)
          }
        }
      } catch {}
    }

    const fetchPredictions = async () => {
      try {
        const r = await fetch(`${API_URL}/api/predict/forecast?horizon=12`)
        if (r.ok) {
          const data = await r.json()
          if (Array.isArray(data) && data.length > 0) {
            await nextTick()
            hudLineChart(predChart.value, data, 'Previsto', COLORS.orange)
          }
        }
      } catch {}
    }

    const changeRefresh = () => {}

    watch(() => props.metrics, (m) => { if (m) updateGauges(m) }, { immediate: true, deep: true })

    onMounted(() => {
      fetchHistory()
      fetchPredictions()
    })

    return {
      localRefresh, gaugeRefs, historyChart, predChart,
      tiles, formatNumber, formatBytes, changeRefresh
    }
  }
}
</script>

<style scoped>
.dashboard-view { display: flex; flex-direction: column; gap: 0; }

.dash-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.topbar-right { display: flex; align-items: center; gap: 10px; }
.hud-label {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-muted);
  letter-spacing: 2px;
}

.mt-16 { margin-top: 12px; }

.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-top: 12px;
}

.gauge-wrap {
  position: relative;
  width: 100px;
  height: 60px;
  margin: 8px auto 0;
}
.gauge-center {
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  text-align: center;
  line-height: 1;
}
.gauge-num {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 700;
  color: var(--tile-accent, var(--jarvis-blue));
}
.gauge-unit {
  font-family: var(--font-mono);
  font-size: 9px;
  color: var(--text-muted);
  margin-left: 2px;
}

.panel-badge {
  font-family: var(--font-mono);
  font-size: 9px;
  color: var(--text-muted);
  letter-spacing: 2px;
}

@media (max-width: 900px) {
  .charts-row { grid-template-columns: 1fr; }
}
</style>