<template>
  <div class="system-view">
    <!-- Location panel -->
    <div class="hud-panel">
      <div class="panel-header">
        <span class="panel-title">LOCALIZAÇÃO DO SISTEMA</span>
        <span class="panel-badge">{{ location.ip || 'AGUARDANDO...' }}</span>
      </div>

      <div class="metrics-grid">
        <div class="metric-tile">
          <div class="tile-label">CIDADE</div>
          <div class="tile-value" style="font-size: 18px">{{ location.city || '—' }}</div>
        </div>
        <div class="metric-tile accent-green">
          <div class="tile-label">PAÍS</div>
          <div class="tile-value" style="font-size: 18px">{{ location.country || '—' }}</div>
        </div>
        <div class="metric-tile">
          <div class="tile-label">ENDEREÇO IP</div>
          <div class="tile-value" style="font-size: 14px; letter-spacing: 1px">{{ location.ip || '—' }}</div>
        </div>
        <div class="metric-tile">
          <div class="tile-label">PROVEDOR</div>
          <div class="tile-value" style="font-size: 13px">{{ location.isp || '—' }}</div>
        </div>
      </div>

      <div class="map-frame">
        <div ref="mapEl" id="hud-map" style="height: 320px;"></div>
        <div class="map-overlay-br">
          <span class="coord-text">{{ location.lat?.toFixed(4) }}°N {{ location.lon?.toFixed(4) }}°E</span>
        </div>
      </div>
    </div>

    <!-- System info panel -->
    <div class="hud-panel" style="margin-top: 12px;">
      <div class="panel-header">
        <span class="panel-title">INFORMAÇÕES DE HARDWARE</span>
        <span v-if="metrics" class="system-uptime">UPTIME: ATIVO</span>
      </div>

      <div v-if="!metrics" class="hud-loading">■ AGUARDANDO DADOS DO SISTEMA... ■</div>

      <template v-else>
        <div class="metrics-grid">
          <div class="metric-tile">
            <div class="tile-label">CPU MODEL</div>
            <div class="hw-value">{{ metrics.cpu_model || 'N/A' }}</div>
          </div>
          <div class="metric-tile accent-red">
            <div class="tile-label">RAM TOTAL</div>
            <div class="tile-value">{{ metrics.ram_total?.toFixed(1) || '0' }}<span>GB</span></div>
          </div>
          <div class="metric-tile accent-green">
            <div class="tile-label">GPU MODEL</div>
            <div class="hw-value">{{ metrics.gpu_model || 'N/A' }}</div>
          </div>
          <div class="metric-tile">
            <div class="tile-label">STORAGE TOTAL</div>
            <div class="tile-value">{{ metrics.disk_total?.toFixed(0) || '0' }}<span>GB</span></div>
          </div>
        </div>

        <div class="section-title">DIAGNÓSTICO DE MÉTRICAS</div>

        <div class="table-frame">
          <table class="hud-table">
            <thead>
              <tr>
                <th>MÉTRICA</th>
                <th>VALOR ATUAL</th>
                <th>STATUS</th>
                <th>BARRA</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in statusRows" :key="row.label">
                <td>{{ row.label }}</td>
                <td class="val-mono">{{ row.value }}</td>
                <td :class="row.statusClass">{{ row.statusText }}</td>
                <td style="padding: 8px 12px; min-width: 120px;">
                  <div class="prog-bar">
                    <div class="prog-fill" :class="row.statusClass.replace('status-', 'prog-')" :style="{ width: row.pct + '%' }"></div>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, nextTick } from 'vue'
import { escapeHtml, sanitizeMetricValue, validateApiResponse } from '@/utils/security.js'

export default {
  name: 'System',
  props: ['metrics'],
  setup(props) {
    const mapEl = ref(null)
    const location = ref({ city: '', country: '', ip: '', isp: '', lat: 0, lon: 0 })
    let map = null

    const formatBytes = (bytes) => {
      if (!bytes || typeof bytes !== 'number') return '0 B'
      if (bytes < 1024) return bytes + ' B'
      if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
      if (bytes < 1073741824) return (bytes / 1048576).toFixed(2) + ' MB'
      return (bytes / 1073741824).toFixed(2) + ' GB'
    }

    const getStatusClass = (val, warn = 80, crit = 95) => {
      if (typeof val !== 'number') return 'status-ok'
      if (val >= crit) return 'status-crit'
      if (val >= warn) return 'status-warn'
      return 'status-ok'
    }

    const getStatusText = (val, warn = 80, crit = 95) => {
      if (typeof val !== 'number') return '● NORMAL'
      if (val >= crit) return '● CRÍTICO'
      if (val >= warn) return '● ALERTA'
      return '● NORMAL'
    }

    const statusRows = computed(() => {
      if (!props.metrics) return []
      const m = props.metrics
      return [
        {
          label: 'CPU USAGE',
          value: (sanitizeMetricValue(m.cpu_usage, 'number')?.toFixed(1) || '0') + '%',
          statusClass: getStatusClass(m.cpu_usage),
          statusText: getStatusText(m.cpu_usage),
          pct: Math.min(sanitizeMetricValue(m.cpu_usage, 'number') || 0, 100),
        },
        {
          label: 'CPU TEMPERATURE',
          value: (sanitizeMetricValue(m.cpu_temp, 'number')?.toFixed(1) || '0') + '°C',
          statusClass: getStatusClass(m.cpu_temp, 50, 80),
          statusText: getStatusText(m.cpu_temp, 50, 80),
          pct: Math.min(((sanitizeMetricValue(m.cpu_temp, 'number') || 0) / 120) * 100, 100),
        },
        {
          label: 'RAM USAGE',
          value: (sanitizeMetricValue(m.ram_usage, 'number')?.toFixed(1) || '0') + '%',
          statusClass: getStatusClass(m.ram_usage),
          statusText: getStatusText(m.ram_usage),
          pct: Math.min(sanitizeMetricValue(m.ram_usage, 'number') || 0, 100),
        },
        {
          label: 'NET UPLOAD',
          value: formatBytes(sanitizeMetricValue(m.network?.bytes_sent, 'number')),
          statusClass: 'status-ok',
          statusText: '● ATIVO',
          pct: 0,
        },
        {
          label: 'NET DOWNLOAD',
          value: formatBytes(sanitizeMetricValue(m.network?.bytes_recv, 'number')),
          statusClass: 'status-ok',
          statusText: '● ATIVO',
          pct: 0,
        },
      ]
    })

    const fetchLocation = async () => {
      try {
        const resp = await fetch('http://ip-api.com/json/')
        const data = await resp.json()
        
        // Validate API response
        if (!validateApiResponse(data, ['city', 'country', 'query', 'lat', 'lon'])) {
          console.warn('Invalid location API response')
          return
        }
        
        if (data.status === 'success') {
          location.value = {
            city: escapeHtml(data.city),
            country: escapeHtml(data.country),
            ip: escapeHtml(data.query),
            isp: escapeHtml(data.isp),
            lat: sanitizeMetricValue(data.lat, 'number'),
            lon: sanitizeMetricValue(data.lon, 'number'),
          }
          await nextTick()
          initMap()
        }
      } catch (e) {
        console.error('Location fetch error:', e)
      }
    }

    const initMap = async () => {
      await nextTick()
      if (!mapEl.value || map) return
      const L = await import('leaflet')
      await import('leaflet/dist/leaflet.css')

      map = L.map(mapEl.value, { zoomControl: false }).setView([location.value.lat, location.value.lon], 12)

      L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '© CartoDB',
        subdomains: 'abcd',
      }).addTo(map)

      const icon = L.divIcon({
        html: `<div style="width:12px;height:12px;border-radius:50%;background:#00c8ff;box-shadow:0 0 12px #00c8ff;border:2px solid #fff;"></div>`,
        className: '',
        iconSize: [12, 12],
        iconAnchor: [6, 6],
      })

      // XSS-safe popup content
      const safeCity = escapeHtml(location.value.city)
      const safeCountry = escapeHtml(location.value.country)
      
      L.marker([location.value.lat, location.value.lon], { icon }).addTo(map)
        .bindPopup(`<span style="font-family:monospace;font-size:12px;color:#00c8ff">${safeCity}, ${safeCountry}</span>`)
        .openPopup()
    }

    onMounted(fetchLocation)

    return { mapEl, location, statusRows }
  }
}
</script>

<style scoped>
.system-view { display: flex; flex-direction: column; gap: 0; }

.map-frame {
  position: relative;
  border: 1px solid var(--border-hud);
  border-radius: 2px;
  overflow: hidden;
}

.map-overlay-br {
  position: absolute;
  bottom: 10px;
  right: 10px;
  background: rgba(2,11,20,0.85);
  border: 1px solid var(--border-hud);
  padding: 4px 10px;
  border-radius: 2px;
  z-index: 1000;
}
.coord-text {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--jarvis-blue);
  letter-spacing: 1px;
}

.hw-value {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-primary);
  margin-top: 4px;
  line-height: 1.4;
}

.system-uptime {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--jarvis-green);
  letter-spacing: 2px;
  animation: blink 2s step-end infinite;
}

.table-frame {
  overflow-x: auto;
  border: 1px solid var(--border-hud);
  border-radius: 2px;
}

.val-mono {
  font-family: var(--font-mono);
  color: var(--jarvis-blue);
}

.prog-bar {
  width: 100%;
  height: 4px;
  background: rgba(0,200,255,0.1);
  border-radius: 2px;
  overflow: hidden;
}
.prog-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.5s ease;
}
.prog-ok { background: var(--jarvis-green); }
.prog-warn { background: var(--jarvis-yellow); }
.prog-crit { background: var(--jarvis-red); }

:deep(#hud-map) {
  filter: hue-rotate(180deg) saturate(0.4) brightness(0.8);
}
:deep(.leaflet-popup-content-wrapper) {
  background: rgba(2,11,20,0.95) !important;
  border: 1px solid #00c8ff !important;
  border-radius: 2px !important;
  box-shadow: 0 0 12px rgba(0,200,255,0.3) !important;
}
:deep(.leaflet-popup-tip) {
  background: #00c8ff !important;
}
</style>