<template>
  <main class="main">

    <AppTopbar title="Overview" :meta="today">
      <template #actions>
        <AppSearchbar v-model="searchQ" placeholder="Search…" />
        <button class="btn btn-outline">
          <svg width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
            <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
          </svg>
        </button>
        <button class="btn btn-primary" @click="$router.push('/orders')">New order</button>
      </template>
    </AppTopbar>

    <div class="ov-content">

      <div class="ov-title">Good {{ greeting }}, Bhargavi</div>

      <div class="ov-metrics">
        <div class="ov-metric">
          <div class="ov-metric-label">Pending orders</div>
          <div class="ov-metric-value">{{ metrics.pending }}</div>
          <span class="ov-tag ov-tag-a">+2 today</span>
        </div>
        <div class="ov-metric">
          <div class="ov-metric-label">High priority</div>
          <div class="ov-metric-value">{{ metrics.highPriority }}</div>
          <span class="ov-tag ov-tag-r">Action needed</span>
        </div>
        <div class="ov-metric">
          <div class="ov-metric-label">Low stock items</div>
          <div class="ov-metric-value">{{ metrics.lowStock }}</div>
        </div>
        <div class="ov-metric">
          <div class="ov-metric-label">Quarterly revenue</div>
          <div class="ov-metric-value ov-metric-lg">₹8,40,000</div>
          <span class="ov-tag ov-tag-g">↑ 18% vs Q3</span>
        </div>
      </div>

      <div class="ov-alert">
        <svg width="14" height="14" fill="none" stroke="#dc2626" stroke-width="2" viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        <div><strong>₹57,400 overdue</strong><span>&nbsp;— 3 customers, longest outstanding 14 days</span></div>
        <button class="ov-alert-link" @click="$router.push('/customers')">View overdue →</button>
      </div>

      <div class="ov-grid">

        <div class="ov-panel">
          <div class="ov-panel-top">
            <div class="ov-panel-title">Priority orders</div>
            <button class="ov-link-btn" @click="$router.push('/orders')">View all</button>
          </div>
          <table class="ov-tbl">
            <thead>
              <tr><th>ID</th><th>Customer</th><th>Order Placed On</th><th>Value</th><th>Avg Collection Period</th></tr>
            </thead>
            <tbody>
              <tr v-for="o in priorityOrders" :key="o.id">
                <td class="ov-cell-id">{{ o.id }}</td>
                <td class="ov-cell-name">{{ o.name }}</td>
                <td class="ov-cell-mono">{{ o.placedOn }}</td>
                <td class="ov-cell-val">{{ o.val }}</td>
                <td><span :style="{ fontFamily: '\'Geist Mono\', monospace', fontSize: '11px', fontWeight: '600', color: scoreColor(o.score) }">{{ o.score }} days</span></td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="ov-panel">
          <div class="ov-panel-top">
            <div>
              <div class="ov-panel-title">Activity</div>
              <div class="ov-panel-sub">Orders, payments & invoices</div>
            </div>
          </div>
          <div class="ov-feed">
            <div v-for="(a, i) in activityFeed" :key="i" class="ov-feed-item">
              <div class="ov-feed-dot" :style="{ background: a.color }"></div>
              <div class="ov-feed-text">
                <div class="ov-feed-title">{{ a.title }}</div>
                <div class="ov-feed-desc">{{ a.desc }}</div>
              </div>
              <div class="ov-feed-right">
                <div :style="{ fontFamily: '\'Geist Mono\', monospace', fontSize: '12px', fontWeight: '500', color: a.amtColor }">{{ a.amt }}</div>
                <div class="ov-feed-time">{{ a.time }} ago</div>
              </div>
            </div>
          </div>
        </div>

        <div class="ov-panel">
          <div class="ov-panel-top">
            <div>
              <div class="ov-panel-title">Low stock</div>
              <div class="ov-panel-sub">Below threshold</div>
            </div>
          </div>
          <div class="ov-stock">
            <div v-for="(s, i) in lowStockItems" :key="i" class="ov-stock-item">
              <div class="ov-stock-row">
                <div class="ov-stock-name">{{ s.name }}</div>
                <div class="ov-stock-count">{{ s.qty }}/{{ s.max }}</div>
              </div>
              <div class="ov-stock-track">
                <div class="ov-stock-fill" :style="{ width: pct(s) + '%', background: stockColor(s) }"></div>
              </div>
              <button class="ov-reorder">+ Reorder</button>
            </div>
          </div>
        </div>

      </div>
    </div>
  </main>
</template>

<script>
import AppTopbar    from '../../components/AppTopbar.vue'
import AppSearchbar from '../../components/AppSearchbar.vue'

export default {
  name: 'OverviewDashboard',
  components: { AppTopbar, AppSearchbar },
  data() {
    return {
      searchQ: '',
      metrics: { pending: 10, highPriority: 12, lowStock: 9 },
      priorityOrders: [
        { id: 'ORD-4823', name: 'Arjun Mehta',  placedOn: 'March 8 2026', val: '₹12,400', score: 0  },
        { id: 'ORD-4821', name: 'Priya Sharma', placedOn: 'March 8 2026', val: '₹8,750',  score: 5  },
        { id: 'ORD-4818', name: 'Ravi Kumar',   placedOn: 'March 7 2026', val: '₹22,100', score: 12 },
        { id: 'ORD-4815', name: 'Neha Patel',   placedOn: 'March 6 2026', val: '₹5,300',  score: 27 },
        { id: 'ORD-4812', name: 'Meena Das',    placedOn: 'March 5 2026', val: '₹14,600', score: 45 },
      ],
      activityFeed: [
        { color: '#2563eb', title: 'Order placed',    desc: 'ORD-4823 · Arjun Mehta',       amt: '₹12,400', amtColor: '#09090b', time: '2m'  },
        { color: '#16a34a', title: 'Payment in',      desc: 'INV-309 · Priya Sharma',        amt: '₹8,750',  amtColor: '#16a34a', time: '18m' },
        { color: '#dc2626', title: 'Invoice overdue', desc: 'INV-301 · Meena Das · 14 days', amt: '₹6,400',  amtColor: '#dc2626', time: '1h'  },
        { color: '#2563eb', title: 'Order shipped',   desc: 'ORD-4809 · Suresh Babu',        amt: '₹18,900', amtColor: '#09090b', time: '2h'  },
        { color: '#16a34a', title: 'Payment in',      desc: 'INV-305 · Raj Iyer',            amt: '₹4,400',  amtColor: '#16a34a', time: '3h'  },
        { color: '#d97706', title: 'Invoice raised',  desc: 'INV-312 · Kiran Nair · Mar 20', amt: '₹5,100',  amtColor: '#09090b', time: '4h'  },
      ],
      lowStockItems: [
        { name: 'Brake Pads B200',    qty: 4, max: 10 },
        { name: 'Engine Filter EF-X', qty: 2, max: 8  },
        { name: 'Spark Plug SP-9',    qty: 7, max: 15 },
        { name: 'Oil Filter OF-44',   qty: 3, max: 12 },
      ]
    }
  },
  computed: {
    today() {
      return new Date().toLocaleDateString('en-IN', { month: 'short', day: 'numeric', year: 'numeric' })
    },
    greeting() {
      const h = new Date().getHours()
      return h < 12 ? 'morning' : h < 17 ? 'afternoon' : 'evening'
    }
  },
  methods: {
    scoreColor(s) { return s <= 7 ? '#16a34a' : s <= 20 ? '#d97706' : '#dc2626' },
    pct(s)        { return Math.round((s.qty / s.max) * 100) },
    stockColor(s) {
      const p = this.pct(s)
      return p < 30 ? '#dc2626' : p < 55 ? '#d97706' : '#16a34a'
    }
  }
}
</script>

<style scoped>
.main       { flex: 1; display: flex; flex-direction: column; overflow: hidden; background: #f5f6f7; }
.ov-content { flex: 1; overflow-y: auto; padding: 20px 22px; display: flex; flex-direction: column; gap: 16px; }
.ov-content::-webkit-scrollbar       { width: 3px; }
.ov-content::-webkit-scrollbar-thumb { background: #c9cad0; border-radius: 2px; }

.ov-title { font-size: 20px; font-weight: 600; color: #09090b; letter-spacing: -0.5px; }

.ov-metrics {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  border: 1.5px solid #c9cad0;
  border-radius: 10px;
  overflow: hidden;
  background: #c9cad0;
  gap: 1px;
  flex-shrink: 0;
}
.ov-metric {
  padding: 18px 20px;
  background: #ffffff;
  cursor: default;
  transition: background 0.15s;
}
.ov-metric:hover     { background: #f7f7f8; }
.ov-metric-label     { font-size: 11.5px; color: #71717a; font-weight: 500; margin-bottom: 10px; }
.ov-metric-value     { font-size: 30px; font-weight: 700; color: #09090b; letter-spacing: -1.5px; font-family: 'Geist', sans-serif; line-height: 1; margin-bottom: 10px; }
.ov-metric-lg        { font-size: 22px; letter-spacing: -1px; }
.ov-tag              { display: inline-block; font-size: 10px; font-weight: 600; padding: 2px 8px; border-radius: 20px; }
.ov-tag-a            { background: #fef3c7; color: #d97706; }
.ov-tag-r            { background: #fee2e2; color: #dc2626; }
.ov-tag-g            { background: #dcfce7; color: #16a34a; }

.ov-alert {
  display: flex; align-items: center; gap: 10px;
  background: #fee2e2; border: 1.5px solid #fca5a5;
  border-radius: 8px; padding: 10px 14px;
  font-size: 12.5px; color: #3f3f46;
  flex-shrink: 0;
}
.ov-alert-link {
  margin-left: auto; background: none; border: none; color: #dc2626;
  font-size: 12px; font-weight: 600; cursor: pointer;
  font-family: 'Geist', sans-serif; padding: 0;
}
.ov-alert-link:hover { text-decoration: underline; }

.ov-grid  { display: grid; grid-template-columns: 1.4fr 1fr 1fr; gap: 14px; align-items: start; }
.ov-panel { background: #ffffff; border: 1.5px solid #c9cad0; border-radius: 10px; overflow: hidden; }

.ov-panel-top   { display: flex; align-items: flex-start; justify-content: space-between; padding: 14px 16px 12px; border-bottom: 1.5px solid #e4e4e7; }
.ov-panel-title { font-size: 13px; font-weight: 600; color: #09090b; }
.ov-panel-sub   { font-size: 11px; color: #a1a1aa; margin-top: 2px; }
.ov-link-btn    { background: none; border: none; color: #2563eb; font-size: 11.5px; font-weight: 500; cursor: pointer; font-family: 'Geist', sans-serif; padding: 0; }
.ov-link-btn:hover { text-decoration: underline; }

.ov-tbl                    { width: 100%; border-collapse: collapse; font-size: 12px; }
.ov-tbl thead tr           { background: #f7f7f8; }
.ov-tbl th                 { padding: 7px 12px; font-size: 9.5px; font-weight: 600; color: #a1a1aa; letter-spacing: 0.8px; text-transform: uppercase; text-align: left; border-bottom: 1.5px solid #e4e4e7; }
.ov-tbl td                 { padding: 9px 12px; border-bottom: 1px solid #e4e4e7; vertical-align: middle; }
.ov-tbl tbody tr:last-child td { border-bottom: none; }
.ov-tbl tbody tr:hover     { background: #f7f7f8; }
.ov-cell-id   { font-family: 'Geist Mono', monospace; font-size: 10.5px; color: #2563eb; }
.ov-cell-name { font-weight: 500; color: #09090b; }
.ov-cell-mono { font-family: 'Geist Mono', monospace; font-size: 11px; color: #71717a; }
.ov-cell-val  { font-family: 'Geist Mono', monospace; font-size: 11.5px; font-weight: 500; color: #09090b; }

.ov-feed                   { display: flex; flex-direction: column; }
.ov-feed-item              { display: flex; align-items: flex-start; gap: 10px; padding: 10px 16px; border-bottom: 1px solid #e4e4e7; }
.ov-feed-item:last-child   { border-bottom: none; }
.ov-feed-dot               { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; margin-top: 4px; }
.ov-feed-text              { flex: 1; min-width: 0; }
.ov-feed-title             { font-size: 12px; font-weight: 600; color: #09090b; }
.ov-feed-desc              { font-size: 10.5px; color: #a1a1aa; margin-top: 1px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ov-feed-right             { text-align: right; flex-shrink: 0; }
.ov-feed-time              { font-size: 10.5px; color: #a1a1aa; margin-top: 2px; }

.ov-stock                  { display: flex; flex-direction: column; }
.ov-stock-item             { padding: 10px 16px; border-bottom: 1px solid #e4e4e7; }
.ov-stock-item:last-child  { border-bottom: none; }
.ov-stock-row              { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.ov-stock-name             { font-size: 12px; font-weight: 500; color: #09090b; }
.ov-stock-count            { font-family: 'Geist Mono', monospace; font-size: 11px; color: #71717a; }
.ov-stock-track            { height: 4px; background: #e4e4e7; border-radius: 2px; overflow: hidden; margin-bottom: 7px; }
.ov-stock-fill             { height: 100%; border-radius: 2px; transition: width 0.5s; }
.ov-reorder {
  background: none; border: 1.5px solid #c9cad0; border-radius: 4px;
  padding: 3px 10px; font-size: 10.5px; font-weight: 600; color: #2563eb;
  cursor: pointer; font-family: 'Geist', sans-serif; transition: all 0.12s;
}
.ov-reorder:hover { background: #dbeafe; border-color: #2563eb; }
</style>