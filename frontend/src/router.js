import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from './views/Dashboard.vue'
import Predictions from './views/Predictions.vue'
import Anomalies from './views/Anomalies.vue'
import System from './views/System.vue'

const routes = [
  { path: '/', name: 'Dashboard', component: Dashboard },
  { path: '/predictions', name: 'Predictions', component: Predictions },
  { path: '/anomalies', name: 'Anomalies', component: Anomalies },
  { path: '/system', name: 'System', component: System }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
