<template>
  <div class="predictions-view">
    <div class="hud-panel">
      <div class="panel-header">
        <span class="panel-title">PREVISÕES DE CPU — ENGINE ML</span>
        <span class="panel-badge">MODELO: ACTIVE</span>
      </div>

      <div v-if="loading" class="hud-loading">■ CARREGANDO MODELO PREDITIVO... ■</div>

      <template v-else-if="predictions && predictions.length > 0">
        <div class="metrics-grid">
          <div class="metric-tile">
            <div class="tile-label">MÉDIA PREVISTA</div>
            <div class="tile-value">{{ avgPred.toFixed(1) }}<span>%</span></div>
          </div>
          <div class="metric-tile accent-red">
            <div class="tile-label">MÁXIMO PREVISTO</div>
            <div class="tile-value">{{ maxPred.toFixed(1) }}<span>%</span></div>
          </div>
          <div class="metric-tile accent-green">
            <div class="tile-label">MÍNIMO PREVISTO</div>
            <div class="tile-value">{{ minPred.toFixed(1) }}<span>%</span></div>
          </div>
          <div class="metric-tile accent-orange">
            <div class="tile-label">HORIZON</div>
            <div class="tile-value">24<span>h</span></div>
          </div>
        </div>

        <div class="chart-wrap-tall">
          <canvas ref="chart"></canvas>
        </div>

        <div class="section-title">DETALHAMENTO DE PREVISÕES</div>

        <div class="table-frame">
          <table class="hud-table">
            <thead>
              <tr>
                <th>HORÁRIO</th>
                <th>PREVISTO</th>
                <th>LIM. INFERIOR</th>
                <th>LIM. SUPERIOR</th>
                <th>VARIÂNCIA</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(pred, i) in predictions" :key="i">
                <td>{{ formatTime(pred.timestamp) }}</td>
                <td class="pred-val">{{ pred.predicted?.toFixed(1) }}%</td>
                <td>{{ pred.lower?.toFixed(1) }}%</td>
                <td>{{ pred.upper?.toFixed(1) }}%</td>
                <td class="variance-cell">
                  <span class="var-bar">
                    <span class="var-fill" :style="{ width: getVariance(pred) + '%' }"></span>
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>

      <div v-else class="hud-alert alert-warn">
        <span class="alert-icon">⚠</span>
        MODELO NÃO TREINADO — EXECUTE: <code>python ml/train.py</code>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, nextTick } from 'vue'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

const API_URL = 'http://localhost:8080'

export default {
  name: 'Predictions',
  setup() {
    const chart = ref(null)
    const predictions = ref([])
    const loading = ref(true)

    const formatTime = (ts) => {
      if (!ts) return '—'
      try { return new Date(ts).toLocaleString('pt-BR') } catch { return '—' }
    }

    const getVariance = (pred) => {
      if (!pred.upper || !pred.lower) return 0
      return Math.min(((pred.upper - pred.lower) / pred.upper) * 100, 100)
    }

    const avgPred = computed(() => {
      if (!predictions.value.length) return 0
      return predictions.value.reduce((a, p) => a + (p.predicted || 0), 0) / predictions.value.length
    })
    const maxPred = computed(() => predictions.value.length ? Math.max(...predictions.value.map(p => p.predicted || 0)) : 0)
    const minPred = computed(() => predictions.value.length ? Math.min(...predictions.value.map(p => p.predicted || 0)) : 0)

    const fetchPredictions = async () => {
      loading.value = true
      try {
        const r = await fetch(`${API_URL}/api/predict/forecast?horizon=24`)
        if (r.ok) {
          const data = await r.json()
          if (Array.isArray(data)) predictions.value = data
        }
      } catch {}
      loading.value = false
    }

    const createChart = () => {
      if (!chart.value || !predictions.value.length) return
      const labels = predictions.value.map(p => { try { return new Date(p.timestamp).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }) } catch { return '' } })
      const predicted = predictions.value.map(p => p.predicted || 0)
      const upper = predictions.value.map(p => p.upper || 0)
      const lower = predictions.value.map(p => p.lower || 0)

      const sharedScales = {
        x: {
          grid: { color: 'rgba(0,200,255,0.06)' },
          ticks: { color: '#7ab8d8', font: { family: 'Share Tech Mono', size: 9 }, maxTicksLimit: 8 }
        },
        y: {
          grid: { color: 'rgba(0,200,255,0.06)' },
          ticks: { color: '#7ab8d8', font: { family: 'Share Tech Mono', size: 9 } }
        }
      }

      new Chart(chart.value.getContext('2d'), {
        type: 'line',
        data: {
          labels,
          datasets: [
            {
              label: 'PREVISTO',
              data: predicted,
              borderColor: '#ff6b35',
              backgroundColor: 'rgba(255,107,53,0.1)',
              fill: true,
              tension: 0.4,
              borderWidth: 2,
              pointRadius: 2,
              pointBackgroundColor: '#ff6b35',
            },
            {
              label: 'LIM. SUPERIOR',
              data: upper,
              borderColor: 'rgba(255,214,10,0.5)',
              borderDash: [4, 3],
              fill: false,
              tension: 0.4,
              borderWidth: 1,
              pointRadius: 0,
            },
            {
              label: 'LIM. INFERIOR',
              data: lower,
              borderColor: 'rgba(0,255,157,0.4)',
              borderDash: [4, 3],
              fill: false,
              tension: 0.4,
              borderWidth: 1,
              pointRadius: 0,
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: true,
              labels: {
                color: '#7ab8d8',
                font: { family: 'Share Tech Mono', size: 10 },
                boxWidth: 12,
                padding: 16,
              }
            },
            tooltip: {
              backgroundColor: 'rgba(2,11,20,0.95)',
              borderColor: '#00c8ff',
              borderWidth: 1,
              titleColor: '#00c8ff',
              bodyColor: '#7ab8d8',
              titleFont: { family: 'Share Tech Mono', size: 11 },
              bodyFont: { family: 'Share Tech Mono', size: 10 },
            }
          },
          scales: sharedScales,
        }
      })
    }

    onMounted(async () => {
      await fetchPredictions()
      await nextTick()
      createChart()
    })

    return { chart, predictions, loading, avgPred, maxPred, minPred, formatTime, getVariance }
  }
}
</script>

<style scoped>
.table-frame {
  overflow-x: auto;
  border: 1px solid var(--border-hud);
  border-radius: 2px;
}

.pred-val {
  font-family: var(--font-mono);
  color: var(--jarvis-orange);
  font-weight: 700;
}

.variance-cell { padding: 8px 12px !important; }
.var-bar {
  display: block;
  width: 80px;
  height: 4px;
  background: rgba(0,200,255,0.1);
  border-radius: 2px;
  overflow: hidden;
}
.var-fill {
  display: block;
  height: 100%;
  background: var(--jarvis-orange);
  border-radius: 2px;
  transition: width 0.3s;
}
</style>