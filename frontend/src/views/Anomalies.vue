<template>
  <div class="anomalies-view">
    <div class="hud-panel">
      <div class="panel-header">
        <span class="panel-title">DETECÇÃO DE ANOMALIAS</span>
        <div class="panel-header-right">
          <span class="blink-indicator" :class="{ active: hasHigh }">●</span>
          <span class="panel-badge">{{ hasHigh ? 'ALERTA CRÍTICO' : 'MONITORANDO' }}</span>
        </div>
      </div>

      <div v-if="loading" class="hud-loading">■ ESCANEANDO ANOMALIAS... ■</div>

      <template v-else-if="anomalies && anomalies.length > 0">
        <div class="metrics-grid">
          <div class="metric-tile accent-red">
            <div class="tile-label">CRÍTICAS</div>
            <div class="tile-value">{{ highCount }}</div>
            <div class="tile-sub">SEVERIDADE HIGH</div>
          </div>
          <div class="metric-tile accent-yellow">
            <div class="tile-label">MÉDIAS</div>
            <div class="tile-value">{{ mediumCount }}</div>
            <div class="tile-sub">SEVERIDADE MEDIUM</div>
          </div>
          <div class="metric-tile accent-green">
            <div class="tile-label">BAIXAS</div>
            <div class="tile-value">{{ lowCount }}</div>
            <div class="tile-sub">SEVERIDADE LOW</div>
          </div>
          <div class="metric-tile">
            <div class="tile-label">TOTAL</div>
            <div class="tile-value">{{ anomalies.length }}</div>
            <div class="tile-sub">ANOMALIAS DETECTADAS</div>
          </div>
        </div>

        <div class="section-title">REGISTRO DE EVENTOS</div>

        <div class="table-frame">
          <table class="hud-table">
            <thead>
              <tr>
                <th>DATA/HORA</th>
                <th>MÉTRICA</th>
                <th>VALOR</th>
                <th>LIMIAR</th>
                <th>TIPO</th>
                <th>SEVERIDADE</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(anomaly, i) in anomalies" :key="i" :class="'row-' + anomaly.severity">
                <td>{{ formatTime(anomaly.timestamp) }}</td>
                <td>{{ anomaly.metric }}</td>
                <td class="val-cell">{{ anomaly.value?.toFixed(2) }}</td>
                <td class="val-cell">{{ anomaly.threshold?.toFixed(2) }}</td>
                <td>{{ anomaly.type }}</td>
                <td>
                  <span class="sev-badge" :class="'sev-' + anomaly.severity">
                    {{ anomaly.severity?.toUpperCase() }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>

      <div v-else class="hud-alert alert-ok">
        <span class="alert-icon">✓</span>
        NENHUMA ANOMALIA DETECTADA — SISTEMA OPERANDO DENTRO DOS PARÂMETROS NORMAIS
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'

const API_URL = 'http://localhost:8080'

export default {
  name: 'Anomalies',
  setup() {
    const anomalies = ref([])
    const loading = ref(true)

    const formatTime = (timestamp) => {
      if (!timestamp) return '—'
      try { return new Date(timestamp).toLocaleString('pt-BR') } catch { return '—' }
    }

    const highCount = computed(() => anomalies.value.filter(a => a.severity === 'high').length)
    const mediumCount = computed(() => anomalies.value.filter(a => a.severity === 'medium').length)
    const lowCount = computed(() => anomalies.value.filter(a => a.severity === 'low').length)
    const hasHigh = computed(() => highCount.value > 0)

    const fetchAnomalies = async () => {
      loading.value = true
      try {
        const response = await fetch(`${API_URL}/api/anomalies`)
        if (response.ok) {
          const data = await response.json()
          if (Array.isArray(data)) anomalies.value = data
        }
      } catch {}
      loading.value = false
    }

    onMounted(fetchAnomalies)

    return { anomalies, loading, highCount, mediumCount, lowCount, hasHigh, formatTime }
  }
}
</script>

<style scoped>
.anomalies-view { }

.panel-header-right { display: flex; align-items: center; gap: 8px; }

.blink-indicator {
  font-size: 10px;
  color: var(--jarvis-green);
}
.blink-indicator.active {
  color: var(--jarvis-red);
  animation: blink 0.8s step-end infinite;
}

.tile-sub {
  font-family: var(--font-mono);
  font-size: 9px;
  color: var(--text-muted);
  margin-top: 4px;
  letter-spacing: 1px;
}

.table-frame {
  overflow-x: auto;
  border: 1px solid var(--border-hud);
  border-radius: 2px;
}

.row-high td:first-child { border-left: 2px solid var(--jarvis-red); }
.row-medium td:first-child { border-left: 2px solid var(--jarvis-yellow); }
.row-low td:first-child { border-left: 2px solid var(--jarvis-green); }

.val-cell { font-family: var(--font-mono); }

.sev-badge {
  font-family: var(--font-mono);
  font-size: 9px;
  letter-spacing: 2px;
  padding: 3px 8px;
  border-radius: 1px;
}
.sev-high { background: var(--jarvis-red-dim); color: var(--jarvis-red); border: 1px solid rgba(255,45,85,0.3); }
.sev-medium { background: rgba(255,214,10,0.1); color: var(--jarvis-yellow); border: 1px solid rgba(255,214,10,0.3); }
.sev-low { background: var(--jarvis-green-dim); color: var(--jarvis-green); border: 1px solid rgba(0,255,157,0.3); }

.alert-icon { font-size: 16px; }
</style>