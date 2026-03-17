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

    <div class="content">

      <div class="page-title-row">
        <div class="page-title">Good {{ greeting }}, Bhargavi</div>
      </div>

      <div class="metrics">
        <div class="metric">
          <div class="metric-label">Pending orders</div>
          <div class="metric-value">{{ metrics.pending }}</div>
          <span class="metric-tag tag-a">+2 today</span>
        </div>
        <div class="metric">
          <div class="metric-label">High priority</div>
          <div class="metric-value">{{ metrics.highPriority }}</div>
          <span class="metric-tag tag-r">Action needed</span>
        </div>
        <div class="metric">
          <div class="metric-label">Low stock items</div>
          <div class="metric-value">{{ metrics.lowStock }}</div>
        </div>
        <div class="metric">
          <div class="metric-label">Quarterly revenue</div>
          <div class="metric-value lg">₹8,40,000</div>
          <span class="metric-tag tag-g">↑ 18% vs Q3</span>
        </div>
      </div>

      <div class="alert-bar">
        <svg width="14" height="14" fill="none" stroke="#dc2626" stroke-width="2" viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        <div>
          <strong>₹57,400 overdue</strong>
          <span>&nbsp;— 3 customers, longest outstanding 14 days</span>
        </div>
        <button class="alert-link" @click="$router.push('/customers')">View overdue →</button>
      </div>

      <div class="grid">

        <div class="panel">
          <div class="panel-top">
            <div class="panel-title">Priority orders</div>
            <button class="link-btn" @click="$router.push('/orders')">View all</button>
          </div>
          <table class="tbl">
            <thead>
              <tr><th>ID</th><th>Customer</th><th>Order Placed On</th><th>Value</th><th>Avg Collection Period</th></tr>
            </thead>
            <tbody>
              <tr v-for="o in priorityOrders" :key="o.id">
                <td class="cell-id">{{ o.id }}</td>
                <td class="cell-name">{{ o.name }}</td>
                <td class="cell-mono">{{ o.placedOn }}</td>
                <td class="cell-val">{{ o.val }}</td>
                <td><span class="score-n" :style="{ color: scoreColor(o.score) }">{{ o.score }} days</span></td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="panel">
          <div class="panel-top">
            <div>
              <div class="panel-title">Activity</div>
              <div class="panel-sub">Orders, payments & invoices</div>
            </div>
          </div>
          <div class="feed">
            <div v-for="(a, i) in activityFeed" :key="i" class="feed-item">
              <div class="feed-dot" :style="{ background: a.color }"></div>
              <div class="feed-text">
                <div class="feed-title">{{ a.title }}</div>
                <div class="feed-desc">{{ a.desc }}</div>
              </div>
              <div class="feed-right">
                <div class="feed-amt" :style="{ color: a.amtColor }">{{ a.amt }}</div>
                <div class="feed-time">{{ a.time }} ago</div>
              </div>
            </div>
          </div>
        </div>

        <div class="panel">
          <div class="panel-top">
            <div>
              <div class="panel-title">Low stock</div>
              <div class="panel-sub">Below threshold</div>
            </div>
          </div>
          <div class="stock">
            <div v-for="(s, i) in lowStockItems" :key="i" class="stock-item">
              <div class="stock-row">
                <div class="stock-name">{{ s.name }}</div>
                <div class="stock-count">{{ s.qty }}/{{ s.max }}</div>
              </div>
              <div class="stock-bar-wrap">
                <div class="stock-fill" :style="{ width: pct(s) + '%', background: stockColor(s) }"></div>
              </div>
              <button class="stock-reorder">+ Reorder</button>
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
        { id: 'ORD-4823', name: 'Arjun Mehta',  placedOn: 'Mar 8', val: '₹12,400', score: 0  },
        { id: 'ORD-4821', name: 'Priya Sharma', placedOn: 'Mar 8', val: '₹8,750',  score: 5  },
        { id: 'ORD-4818', name: 'Ravi Kumar',   placedOn: 'Mar 7', val: '₹22,100', score: 12 },
        { id: 'ORD-4815', name: 'Neha Patel',   placedOn: 'Mar 6', val: '₹5,300',  score: 27 },
        { id: 'ORD-4812', name: 'Meena Das',    placedOn: 'Mar 5', val: '₹14,600', score: 45 },
      ],
      activityFeed: [
        { color: '#2563eb', title: 'Order placed',    desc: 'ORD-4823 · Arjun Mehta',       amt: '₹12,400', amtColor: 'var(--ink)', time: '2m'  },
        { color: '#16a34a', title: 'Payment in',      desc: 'INV-309 · Priya Sharma',        amt: '₹8,750',  amtColor: '#16a34a',    time: '18m' },
        { color: '#dc2626', title: 'Invoice overdue', desc: 'INV-301 · Meena Das · 14 days', amt: '₹6,400',  amtColor: '#dc2626',    time: '1h'  },
        { color: '#2563eb', title: 'Order shipped',   desc: 'ORD-4809 · Suresh Babu',        amt: '₹18,900', amtColor: 'var(--ink)', time: '2h'  },
        { color: '#16a34a', title: 'Payment in',      desc: 'INV-305 · Raj Iyer',            amt: '₹4,400',  amtColor: '#16a34a',    time: '3h'  },
        { color: '#d97706', title: 'Invoice raised',  desc: 'INV-312 · Kiran Nair · Mar 20', amt: '₹5,100',  amtColor: 'var(--ink)', time: '4h'  },
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

<style>
.main    { flex: 1; display: flex; flex-direction: column; overflow: hidden; background: var(--bg); }
.content { flex: 1; overflow-y: auto; padding: 20px 22px; display: flex; flex-direction: column; gap: 16px; }
.content::-webkit-scrollbar { width: 3px; }
.content::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

.page-title-row { display: flex; align-items: flex-end; justify-content: space-between; }
.page-title     { font-size: 20px; font-weight: 600; color: var(--ink); letter-spacing: -0.5px; }

.metrics {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  border: 1.5px solid var(--border);
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,.04);
}
.metric {
  padding: 16px 18px;
  background: #ffffff;
  border-right: 1.5px solid var(--border);
  transition: background 0.15s, box-shadow 0.15s;
  cursor: default;
}
.metric:hover         { background: var(--surface); box-shadow: inset 0 -2px 0 var(--blue); }
.metric:last-child    { border-right: none; }
.metric-label { font-size: 11.5px; color: var(--ink-3); font-weight: 500; margin-bottom: 8px; }
.metric-value { font-size: 28px; font-weight: 700; color: var(--ink); letter-spacing: -1px; font-family: 'Geist Mono', monospace; line-height: 1; margin-bottom: 8px; }
.metric-value.lg { font-size: 22px; }
.metric-tag   { font-size: 10px; font-weight: 600; padding: 2px 8px; border-radius: 20px; }
.tag-a { background: var(--amber-dim); color: var(--amber); }
.tag-r { background: var(--red-dim);   color: var(--red);   }
.tag-g { background: var(--green-dim); color: var(--green); }

.alert-bar {
  display: flex; align-items: center; gap: 10px;
  background: var(--red-dim); border: 1.5px solid #fca5a5;
  border-radius: 8px; padding: 10px 14px;
  font-size: 12.5px; color: var(--ink-2);
}
.alert-link {
  margin-left: auto; background: none; border: none; color: var(--red);
  font-size: 12px; font-weight: 600; cursor: pointer;
  font-family: 'Geist', sans-serif; padding: 0; white-space: nowrap;
}
.alert-link:hover { text-decoration: underline; }

.grid {
  display: grid; grid-template-columns: 1.4fr 1fr 1fr;
  gap: 14px; align-items: start;
}

.panel        { background: #ffffff; border: 1.5px solid var(--border); border-radius: 10px; overflow: hidden; }
.panel-top    { display: flex; align-items: flex-start; justify-content: space-between; padding: 14px 16px 12px; border-bottom: 1.5px solid var(--border-2); }
.panel-title  { font-size: 13px; font-weight: 600; color: var(--ink); }
.panel-sub    { font-size: 11px; color: var(--ink-4); margin-top: 2px; }
.link-btn     { background: none; border: none; color: var(--blue); font-size: 11.5px; font-weight: 500; cursor: pointer; font-family: 'Geist', sans-serif; padding: 0; }
.link-btn:hover { text-decoration: underline; }

.tbl { width: 100%; border-collapse: collapse; font-size: 12px; }
.tbl thead tr  { background: var(--surface); }
.tbl th        { padding: 7px 12px; font-size: 9.5px; font-weight: 600; color: var(--ink-4); letter-spacing: 0.8px; text-transform: uppercase; text-align: left; border-bottom: 1.5px solid var(--border-2); }
.tbl td        { padding: 9px 12px; border-bottom: 1px solid var(--border-2); vertical-align: middle; }
.tbl tbody tr:last-child td { border-bottom: none; }
.tbl tbody tr:hover { background: var(--surface); }
.cell-id   { font-family: 'Geist Mono', monospace; font-size: 10.5px; color: var(--blue); }
.cell-name { font-weight: 500; color: var(--ink); }
.cell-mono { font-family: 'Geist Mono', monospace; font-size: 11px; color: var(--ink-3); }
.cell-val  { font-family: 'Geist Mono', monospace; font-size: 11.5px; font-weight: 500; color: var(--ink); }
.score-n   { font-family: 'Geist Mono', monospace; font-size: 11px; font-weight: 600; }

.feed { display: flex; flex-direction: column; }
.feed-item  { display: flex; align-items: flex-start; gap: 10px; padding: 10px 16px; border-bottom: 1px solid var(--border-2); }
.feed-item:last-child { border-bottom: none; }
.feed-dot   { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; margin-top: 4px; }
.feed-text  { flex: 1; min-width: 0; }
.feed-title { font-size: 12px; font-weight: 600; color: var(--ink); }
.feed-desc  { font-size: 10.5px; color: var(--ink-4); margin-top: 1px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.feed-right { text-align: right; flex-shrink: 0; }
.feed-amt   { font-family: 'Geist Mono', monospace; font-size: 12px; font-weight: 500; }
.feed-time  { font-size: 10.5px; color: var(--ink-4); margin-top: 2px; }

.stock { display: flex; flex-direction: column; }
.stock-item  { padding: 10px 16px; border-bottom: 1px solid var(--border-2); }
.stock-item:last-child { border-bottom: none; }
.stock-row   { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.stock-name  { font-size: 12px; font-weight: 500; color: var(--ink); }
.stock-count { font-family: 'Geist Mono', monospace; font-size: 11px; color: var(--ink-3); }
.stock-bar-wrap { height: 4px; background: var(--border-2); border-radius: 2px; overflow: hidden; margin-bottom: 7px; }
.stock-fill     { height: 100%; border-radius: 2px; transition: width .5s; }
.stock-reorder {
  background: none; border: 1.5px solid var(--border); border-radius: 4px;
  padding: 3px 10px; font-size: 10.5px; font-weight: 600; color: var(--blue);
  cursor: pointer; font-family: 'Geist', sans-serif; transition: all 0.12s;
}
.stock-reorder:hover { background: var(--blue-dim); border-color: var(--blue); }
</style>