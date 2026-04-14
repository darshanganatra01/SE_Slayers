<template>
  <main class="inv-main">
    <AppTopbar title="Demand Prediction" :meta="headMeta">
      <template #actions>
        <button class="btn btn-primary" @click="fetchForecast" :disabled="loading">
          <svg v-if="loading" class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          Refreshed Forecast
        </button>
      </template>
    </AppTopbar>

    <div class="inv-body">
      <!-- Summary Cards -->
      <div class="stat-grid">
        <div class="stat-card">
          <div class="stat-label">Total SKUs Tracked</div>
          <div class="stat-val">{{ forecasts.length }}</div>
        </div>
        <div class="stat-card urgent">
          <div class="stat-label">Restock Alerts</div>
          <div class="stat-val">{{ restockAlertCount }}</div>
          <div class="stat-sub">Stockout within 14 days</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Avg. Daily Predicted Demand</div>
          <div class="stat-val">{{ avgDailyTotal }}</div>
          <div class="stat-sub">Across all high-demand SKUs</div>
        </div>
      </div>

      <!-- Forecast Table -->
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Running AutoETS inference on historical order data...</p>
      </div>

      <div v-else class="table-container">
        <table class="forecast-table">
          <thead>
            <tr>
              <th>Product / SKU</th>
              <th>Category</th>
              <th>14-Day Demand</th>
              <th>Current Stock</th>
              <th>Days to Stockout</th>
              <th>Status</th>
              <th>Trend (30d Hist + 14d Pred)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in forecasts" :key="item.skuid" :class="{ 'row-urgent': item.restock_alert }">
              <td>
                <div class="prod-name">{{ item.product_name }}</div>
                <div class="prod-sku">SKU: {{ item.skuid }}</div>
              </td>
              <td><span class="badge">{{ item.category }}</span></td>
              <td class="num-cell">
                <div class="pred-qty">~{{ item.total_predicted_14d }}</div>
                <div class="pred-sub">{{ item.avg_daily_predicted }}/day</div>
              </td>
              <td class="num-cell">
                <div class="stock-qty">{{ item.current_stock }}</div>
                <div class="stock-sub">Min: {{ item.threshold }}</div>
              </td>
              <td class="num-cell">
                <div class="stockout-days" :class="getStockoutClass(item.days_until_stockout)">
                  {{ item.days_until_stockout > 90 ? '> 90' : item.days_until_stockout }} days
                </div>
              </td>
              <td>
                <span v-if="item.restock_alert" class="status-badge critical">🔴 CRITICAL</span>
                <span v-else-if="item.days_until_stockout < 30" class="status-badge warning">🟡 WARNING</span>
                <span v-else class="status-badge ok">🟢 OK</span>
              </td>
              <td class="chart-cell">
                <div class="sparkline">
                  <div
                    v-for="(dp, idx) in combinedSeries(item)"
                    :key="idx"
                    class="spark-bar"
                    :class="{ 'is-pred': idx >= 30 }"
                    :style="{ height: (dp.qty / maxQty(item) * 100) + '%' }"
                    :title="`${dp.date}: ${dp.qty} units`"
                  ></div>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </main>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import AppTopbar from '../components/AppTopbar.vue'

const forecasts = ref([])
const loading = ref(false)
const generatedAt = ref(null)

const headMeta = computed(() => {
  if (!generatedAt.value) return 'Initializing model...'
  const date = new Date(generatedAt.value).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
  return `Forecast generated at ${date} · 14-day horizon`
})

const restockAlertCount = computed(() => forecasts.value.filter(f => f.restock_alert).length)
const avgDailyTotal = computed(() => {
  if (forecasts.value.length === 0) return 0
  const total = forecasts.value.reduce((acc, f) => acc + f.avg_daily_predicted, 0)
  return (total / forecasts.value.length).toFixed(1)
})

const fetchForecast = async () => {
  loading.value = true
  try {
    const res = await fetch('/api/demand-forecast/predict', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    const data = await res.json()
    if (data.forecasts) {
      forecasts.value = data.forecasts
      generatedAt.value = data.generated_at
    }
  } catch (err) {
    console.error('Forecast failed:', err)
  } finally {
    loading.value = false
  }
}

const combinedSeries = (item) => {
  return [...item.historical, ...item.predicted]
}

const maxQty = (item) => {
  const all = combinedSeries(item).map(d => d.qty)
  return Math.max(...all, 1)
}

const getStockoutClass = (days) => {
  if (days <= 7) return 'text-red'
  if (days <= 14) return 'text-orange'
  return ''
}

onMounted(() => {
  fetchForecast()
})
</script>

<style scoped>
.inv-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
  background: var(--bg);
}
.inv-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
  overflow-y: auto;
  min-height: 0;
  padding: 18px 20px 28px;
}

.stat-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.stat-card {
  background: var(--surface); border: 1.5px solid var(--border); border-radius: 10px; padding: 16px;
  display: flex; flex-direction: column; gap: 4px;
}
.stat-card.urgent { border-color: var(--red); background: #fff5f5; }
.stat-label { font-size: 11px; font-weight: 500; color: var(--ink-4); text-transform: uppercase; letter-spacing: 0.5px; }
.stat-val { font-size: 24px; font-weight: 600; color: var(--ink); }
.stat-sub { font-size: 12px; color: var(--ink-4); }

.loading-state {
  display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 80px 0; gap: 16px;
  color: var(--ink-3);
}
.spinner {
  width: 32px; height: 32px; border: 3px solid var(--border); border-top-color: var(--blue); border-radius: 50%;
  animation: spin 1s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.table-container { background: var(--surface); border: 1.5px solid var(--border); border-radius: 10px; overflow: hidden; }
.forecast-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.forecast-table th {
  text-align: left; background: #fafafa; padding: 10px 14px; border-bottom: 1.5px solid var(--border);
  color: var(--ink-3); font-weight: 500; font-size: 11px; text-transform: uppercase;
}
.forecast-table td { padding: 12px 14px; border-bottom: 1px solid var(--border); color: var(--ink); vertical-align: middle; }
.forecast-table tr:last-child td { border-bottom: none; }
.forecast-table tr.row-urgent { background: #fffefe; }

.prod-name { font-weight: 500; margin-bottom: 2px; }
.prod-sku { font-size: 11px; color: var(--ink-4); font-family: 'Geist Mono', monospace; }

.badge {
  background: var(--bg); border: 1px solid var(--border); border-radius: 4px; padding: 2px 6px; font-size: 11px;
  color: var(--ink-3);
}

.num-cell { font-family: 'Geist Mono', monospace; }
.pred-qty { font-weight: 600; color: var(--blue); }
.pred-sub, .stock-sub { font-size: 10px; color: var(--ink-4); }

.stockout-days { font-weight: 600; font-size: 14px; }
.text-red { color: var(--red); }
.text-orange { color: #d97706; }

.status-badge {
  font-size: 10px; font-weight: 700; border-radius: 12px; padding: 2px 8px; white-space: nowrap;
}
.status-badge.critical { background: #fecaca; color: #b91c1c; }
.status-badge.warning { background: #fef3c7; color: #d97706; }
.status-badge.ok { background: #d1fae5; color: #059669; }

.sparkline {
  display: flex; align-items: flex-end; gap: 1px; height: 30px; width: 140px;
}
.spark-bar {
  flex: 1; background: var(--blue-dim); border-radius: 1px; min-height: 2px;
}
.spark-bar.is-pred { background: var(--blue); opacity: 0.8; box-shadow: 0 0 2px var(--blue); }
.spark-bar:hover { opacity: 1 !important; transform: scaleY(1.1); }

.chart-cell { width: 150px; }

.animate-spin { animation: spin 1s linear infinite; }
</style>
