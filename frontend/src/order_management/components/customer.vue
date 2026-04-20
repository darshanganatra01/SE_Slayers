<template>
  <main class="main">

    <div class="pg-head">
      <div class="head-row1">
        <div>
          <div class="pg-title">Customers</div>
          <div class="pg-meta">{{ today }} · {{ customers.length }} CUSTOMERS</div>
        </div>
        <div class="head-pills">
          <div class="hpill"><span class="hpill-dot" style="background:var(--blue)"></span><span class="hpill-val">{{ customers.length }}</span><span class="hpill-lbl">customers</span></div>
          <div class="hpill"><span class="hpill-dot" style="background:var(--amber)"></span><span class="hpill-val">{{ fmtINR(totalPending) }}</span><span class="hpill-lbl">pending</span></div>
          <div class="hpill"><span class="hpill-dot" style="background:var(--red)"></span><span class="hpill-val">{{ overdueCount }}</span><span class="hpill-lbl">overdue invoices</span></div>
        </div>
      </div>
      <div class="head-row2">
        <button class="ctab" :class="{ active: activeTab === 'list' }" @click="activeTab = 'list'">
          Customer List <span class="tab-count" :class="{ active: activeTab === 'list' }">{{ filteredCustomers.length }}</span>
        </button>
        <div class="tab-sep"></div>
        <button class="ctab" :class="{ active: activeTab === 'payments' }" @click="activeTab = 'payments'">
          Pending Payments <span class="tab-count" :class="{ active: activeTab === 'payments' }">{{ customers.filter(c => c.pending > 0).length }}</span>
        </button>
        <div class="head-search-row">
          <AppSearchbar v-model="searchQ" placeholder="Search customers…" style="width: 340px;" />
        </div>
      </div>
    </div>

    <div class="body-split">

      <template v-if="activeTab === 'list'">

        <!-- Left: customer list -->
        <div class="clist-panel">
          <div class="clist-toolbar">
            <span class="sort-label">Sort:</span>
            <button v-for="s in sortOptions" :key="s.key" class="sort-btn" :class="{ active: sortKey === s.key }" @click="sortKey = s.key">{{ s.label }}</button>
          </div>
          <div class="clist-scroll">
            <div v-for="(c, i) in filteredCustomers" :key="c.id"
              class="ccard" :class="{ selected: selectedId === c.id }"
              :style="{ animationDelay: i * 0.03 + 's' }"
              @click="selectedId = c.id">
              <div class="ring-wrap">
                <svg width="46" height="46" viewBox="0 0 46 46">
                  <circle cx="23" cy="23" r="18" fill="none" stroke="var(--border-2)" stroke-width="3.5"/>
                  <circle cx="23" cy="23" r="18" fill="none"
                    :stroke="acpColor(c.acp)" stroke-width="3.5" />
                </svg>
                <div class="ring-score" :style="{ color: acpColor(c.acp) }">{{ c.acp != null ? c.acp : 30 }}<span style="margin-left:2px;">D</span></div>
              </div>
              <div class="ccard-body">
                <div class="ccard-name">{{ c.biz }}</div>
                <div class="ccard-sub">{{ c.loc }}</div>
                <div class="ccard-tags">
                  <span v-if="hasOverdue(c)" class="chip" style="background:var(--red-dim);color:var(--red)">⚠ Overdue</span>
                </div>
              </div>
              <div class="ccard-right">
                <div class="ccard-pending" :class="{ overdue: hasOverdue(c) }">{{ c.pending > 0 ? fmtINR(c.pending) : '—' }}</div>
                <div class="ccard-dl">{{ c.pending > 0 ? 'pending' : c.totalOrders + ' orders' }}</div>
              </div>
            </div>
            <div v-if="filteredCustomers.length === 0" class="empty-state">
              <div class="es-icon">👥</div><div class="es-text">No customers found</div><div class="es-sub">Try adjusting filters</div>
            </div>
          </div>
        </div>

        <!-- Right: detail panel -->
        <div class="detail-panel">
          <div v-if="!selectedCustomer" class="dp-empty">
            <div class="dp-empty-icon">👥</div>
            <div class="dp-empty-text">Select a customer</div>
            <div class="dp-empty-sub">Click any customer to see profile, orders & payments</div>
          </div>

          <!-- key forces re-render + re-animation on every customer switch -->
          <div v-else class="dp-inner" :key="selectedId">

            <div class="dp-head">
              <div class="dp-head-row1">
                <div class="big-ring-wrap">
                  <svg width="72" height="72" viewBox="0 0 72 72">
                    <circle cx="36" cy="36" r="28" fill="none" stroke="var(--border-2)" stroke-width="5"/>
                    <circle cx="36" cy="36" r="28" fill="none"
                      :stroke="acpColor(selectedCustomer.acp)" stroke-width="5" />
                  </svg>
                  <div class="big-ring-score">
                    <div class="num" :style="{ color: acpColor(selectedCustomer.acp) }">{{ selectedCustomer.acp != null ? selectedCustomer.acp : 30 }}<span style="margin-left: 3px;">D</span></div>
                    <div class="lbl">ACP</div>
                  </div>
                </div>
                <div class="dp-head-info">
                  <div class="dp-cname">{{ selectedCustomer.biz }}</div>
                  <div class="dp-cmeta">{{ selectedCustomer.loc }} · {{ selectedCustomer.phone }}</div>
                  <div class="dp-chip-row" v-if="hasOverdue(selectedCustomer)">
                    <span class="chip" style="background:var(--red-dim);color:var(--red)">⚠ Overdue</span>
                  </div>
                </div>
                <button class="btn btn-outline" @click="openEdit(selectedCustomer)">Edit</button>
                <button class="btn btn-primary" v-if="selectedCustomer.pending > 0" style="margin-left: 8px;" @click="openCollectModal(selectedCustomer)">Collect Payment</button>
              </div>
              <div class="dp-stat-bar">
                <div class="dp-stat"><div class="dp-stat-val">{{ selectedCustomer.totalOrders }}</div><div class="dp-stat-lbl">Orders</div></div>
                <div class="dp-stat"><div class="dp-stat-val">{{ fmtINR(selectedCustomer.totalValue) }}</div><div class="dp-stat-lbl">Total Value</div></div>
                <div class="dp-stat">
                  <div class="dp-stat-val" :style="{ color: selectedCustomer.pending > 0 ? 'var(--amber)' : 'var(--green)' }">{{ selectedCustomer.pending > 0 ? fmtINR(selectedCustomer.pending) : '—' }}</div>
                  <div class="dp-stat-lbl">Pending</div>
                </div>
                <div class="dp-stat"><div class="dp-stat-val">{{ selectedCustomer.acp != null ? selectedCustomer.acp + 'd' : '30d' }}</div><div class="dp-stat-lbl">ACP</div></div>
              </div>
            </div>

            <!-- Scrollable body -->
            <div class="dp-body">

              <div class="dp-sec">
                <div class="dp-sec-head"><div class="dp-sec-title">Orders</div></div>
                <table class="ord-table">
                  <thead><tr><th>ID</th><th>Date</th><th>Value</th><th>Status</th><th>Payment</th></tr></thead>
                  <tbody>
                    <tr v-for="o in selectedCustomer.orders" :key="o.id">
                      <td class="cell-id">{{ o.id }}</td>
                      <td class="cell-meta">{{ o.date }}</td>
                      <td class="cell-val">{{ fmtINR(o.value) }}</td>
                      <td class="cell-meta">{{ o.status }}</td>
                      <td><span class="status-pill" :class="payClass(o.paid)">{{ o.paid }}</span></td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div class="dp-sec">
                <div class="dp-sec-head"><div class="dp-sec-title">Invoices</div></div>
                <div v-for="inv in selectedCustomer.invoices" :key="inv.id" class="inv-row">
                  <div class="inv-id">{{ inv.id }}</div>
                  <div class="inv-desc">{{ inv.desc }}</div>
                  <div class="inv-amount">{{ fmtINR(inv.amount) }}</div>
                  <div class="inv-due" :class="inv.status === 'overdue' ? 'overdue' : inv.status === 'pending' ? 'due-soon' : 'ok'">
                    {{ inv.status === 'overdue' ? '⚠ OVERDUE' : inv.status === 'pending' ? 'Due ' + inv.due : 'Paid' }}
                  </div>
                  <button class="inv-dl-btn" @click="downloadCustomerInvoice(inv, selectedCustomer)">Download Invoice</button>
                </div>
              </div>

              <div class="dp-sec">
                <div class="dp-sec-head"><div class="dp-sec-title">Payment History</div></div>
                <div class="timeline">
                  <div v-for="(t, i) in selectedCustomer.payHistory" :key="i" class="tl-item">
                    <div class="tl-dot" :style="{ borderColor: t.type==='payment'?'var(--green)':'var(--amber)', background: t.type==='payment'?'var(--green-dim)':'transparent' }"></div>
                    <div class="tl-body">
                      <div class="tl-title">{{ t.type === 'payment' ? 'Payment received' : 'Invoice raised' }}
                        <span class="tl-amount" :style="{ color: t.type==='payment'?'var(--green)':'var(--amber)' }">{{ fmtINR(t.amount) }}</span>
                      </div>
                      <div class="tl-meta">{{ t.date }} · {{ t.note }}</div>
                    </div>
                  </div>
                </div>
              </div>

            </div>
          </div>
        </div>

      </template>

      <!-- Payments tab -->
      <div v-else class="payments-view">
        <div class="ledger-grid">
          <div v-for="(c, i) in customersWithPending" :key="c.id"
            class="ledger-card" :style="{ animationDelay: i * 0.04 + 's' }"
            @click="activeTab='list'; selectedId=c.id">
            <div class="lc-head">
              <div class="lc-av" :style="{ background: avatarBg(c.name) }">{{ initials(c.name) }}</div>
              <div style="flex:1;min-width:0">
                <div class="lc-name">{{ c.biz }}</div>
                <div class="lc-type">{{ c.loc }}</div>
              </div>
              <div style="text-align:right">
                <div class="lc-score" :style="{ color: acpColor(c.acp) }">{{ c.acp != null ? c.acp : 30 }}<span style="margin-left: 2px;">D</span></div>
                <div style="font-size:9.5px;color:var(--ink-4)">ACP</div>
              </div>
            </div>
            <div class="lc-body">
              <div class="lc-amount-row">
                <div>
                  <div class="lc-pending-label">Pending</div>
                  <div v-if="hasOverdue(c)" style="font-size:10px;color:var(--red);font-weight:700;margin-top:2px">⚠ OVERDUE</div>
                </div>
                <div class="lc-pending-val" :style="{ color: hasOverdue(c)?'var(--red)':'var(--ink)' }">{{ fmtINR(c.pending) }}</div>
              </div>
              <div class="lc-foot">
                <span>ACP: <strong>{{ c.acp != null ? c.acp + 'd' : '30d' }}</strong></span>
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>

    <!-- Modal -->
    <div v-if="showModal" class="mo" @click.self="showModal=false">
      <div class="mo-box">
        <div class="mo-head">
          <div class="mo-title">{{ editingId ? 'Edit Customer' : 'Add Customer' }}</div>
          <div class="mo-x" @click="showModal=false">✕</div>
        </div>
        <div class="mo-body">
          <div class="mo-row">
            <div class="fg"><label class="fl">Full Name</label><input class="fi" v-model="form.name" placeholder="e.g. Arjun Mehta"/></div>
            <div class="fg"><label class="fl">Business / Shop</label><input class="fi" v-model="form.biz" placeholder="e.g. Mehta Garage"/></div>
          </div>
          <div class="mo-row">
            <div class="fg"><label class="fl">Phone</label><input class="fi" v-model="form.phone" placeholder="+91 98765 43210"/></div>
            <div class="fg"><label class="fl">Email</label><input class="fi" v-model="form.email" placeholder="arjun@example.com"/></div>
          </div>
          <div class="mo-row">
            <div class="fg"><label class="fl">Location</label><input class="fi" v-model="form.loc" placeholder="e.g. Chennai"/></div>
            <div class="fg"><label class="fl">Payment Type</label>
              <select class="fi" v-model="form.type">
                <option value="Platinum">High – Within 7 days</option>
                <option value="Gold">Medium – Within 15 days</option>
                <option value="Silver">Low – Within 30 days</option>
                <option value="At Risk">At Risk – Overdue/Slow</option>
              </select>
            </div>
          </div>
        </div>
        <div class="mo-foot">
          <button class="btn-cancel" @click="showModal=false">Cancel</button>
          <button class="btn btn-primary" @click="saveCustomer">{{ editingId ? 'Update' : 'Save Customer' }}</button>
        </div>
      </div>
    </div>

    <!-- Collect Payment Modal -->
    <div v-if="showCollectModal" class="mo" @click.self="showCollectModal=false">
      <div class="mo-box" style="width: 400px">
        <div class="mo-head">
          <div class="mo-title">Collect Payment (FIFO)</div>
          <div class="mo-x" @click="showCollectModal=false">✕</div>
        </div>
        <div class="mo-body">
          <div class="fg">
            <label class="fl">Amount to Collect (₹)</label>
            <input class="fi" type="number" v-model.number="collectAmount" :max="collectTargetCustomer?.pending" placeholder="0.00" />
            <div style="font-size: 11px; color: var(--ink-4); margin-top: 4px;">
              Will automatically settle the oldest pending invoices first. 
              Max pending: ₹{{ (collectTargetCustomer?.pending || 0).toLocaleString('en-IN') }}
            </div>
          </div>
        </div>
        <div class="mo-foot">
          <button class="btn-cancel" @click="showCollectModal=false">Cancel</button>
          <button class="btn btn-primary" :disabled="!collectAmount || collectAmount <= 0" @click="submitCollection">Collect</button>
        </div>
      </div>
    </div>

    <AppToast ref="toast" />
  </main>
</template>

<script>
import AppSearchbar from '../../components/AppSearchbar.vue'
import AppToast     from '../../components/AppToast.vue'

const TYPE_COLOR = { Platinum:'var(--green)', Gold:'var(--amber)', Silver:'var(--red)', 'At Risk':'var(--red)' }
const TYPE_BG    = { Platinum:'var(--green-dim)', Gold:'var(--amber-dim)', Silver:'var(--red-dim)', 'At Risk':'var(--red-dim)' }
const TYPE_LABEL = { Platinum:'High', Gold:'Medium', Silver:'Low', 'At Risk':'At Risk' }

export default {
  name: 'CustomerDashboard',
  components: { AppSearchbar, AppToast },
  data() {
    return {
      TYPE_COLOR, TYPE_BG, TYPE_LABEL,
      activeTab: 'list', selectedId: null, sortKey: 'name',
      searchQ: '', typeFilter: 'all',
      showModal: false, editingId: null,
      form: { name:'', biz:'', phone:'', email:'', loc:'', type:'Platinum' },
      showCollectModal: false, collectAmount: 0, collectTargetCustomer: null,
      sortOptions: [
        { key:'name',    label:'Name'      },
        { key:'pending', label:'Pending ↓' },
        { key:'score',   label:'ACP ↓'   }
      ],
      customers: []
    }
  },
  async mounted() {
    await this.fetchCustomers()
  },
  computed: {
    today() { return new Date().toLocaleDateString('en-IN',{weekday:'short',day:'2-digit',month:'short',year:'numeric'}).toUpperCase() },
    totalPending()        { return this.customers.reduce((a,c) => a+c.pending, 0) },
    overdueCount()        { return this.customers.flatMap(c => c.invoices).filter(i => i.status==='overdue').length },
    selectedCustomer()    { return this.customers.find(c => c.id===this.selectedId)||null },
    customersWithPending(){ return this.customers.filter(c=>c.pending>0).sort((a,b)=>b.pending-a.pending) },
    filteredCustomers() {
      let list = [...this.customers]
      const q = this.searchQ.toLowerCase()
      if (q) list = list.filter(c => c.name.toLowerCase().includes(q)||c.biz.toLowerCase().includes(q)||c.loc.toLowerCase().includes(q))
      if (this.typeFilter!=='all') list = list.filter(c=>c.type===this.typeFilter)
      if (this.sortKey==='pending')      list.sort((a,b)=>b.pending-a.pending)
      else if (this.sortKey==='score')   list.sort((a,b)=>this.typeScore(b.type)-this.typeScore(a.type))
      else                               list.sort((a,b)=>a.name.localeCompare(b.name))
      return list
    }
  },
  methods: {
    async fetchCustomers() {
      try {
        const token = localStorage.getItem('token');
        const headers = {};
        if (token) headers['Authorization'] = `Bearer ${token}`;
        
        const res = await fetch('http://127.0.0.1:5000/api/internal-portal/customers', { headers })
        if (res.ok) {
          this.customers = await res.json()
        }
      } catch (e) {
        console.error("Failed to load customers:", e)
      }
    },
    typeScore(type) { return {Platinum:95,Gold:80,Silver:50,'At Risk':20}[type]||50 },
    scoreColor(s)   { return s>=85?'var(--green)':s>=70?'var(--amber)':'var(--red)' },
    acpColor(acp)   { const v = acp != null ? acp : 30; return v <= 15 ? 'var(--green)' : v <= 30 ? 'var(--amber)' : 'var(--red)' },
    acpRingPct(acp) { const v = acp != null ? acp : 30; return Math.max(0, Math.min(100, 100 - v)) },
    fmtINR(n)       { return '₹'+Number(n).toLocaleString('en-IN') },
    initials(name)  { return name.split(' ').map(w=>w[0]).join('').slice(0,2).toUpperCase() },
    hasOverdue(c)   { return c.invoices.some(i=>i.status==='overdue') },
    payClass(paid)  { return paid==='Paid'?'sp-paid':paid==='Overdue'?'sp-overdue':'sp-pending' },
    avatarBg(name) {
      const p=['#2c3e50','#1a6b3a','#1e40af','#7b3f00','#5b2d8e','#8b6914','#0b5394','#3d5a80']
      let h=0; for(let i=0;i<name.length;i++) h=(h*31+name.charCodeAt(i))%p.length; return p[h]
    },
    openAdd()  { this.editingId=null; this.form={name:'',biz:'',phone:'',email:'',loc:'',type:'Platinum'}; this.showModal=true },
    openEdit(c){ this.editingId=c.id; this.form={name:c.name,biz:c.biz,phone:c.phone,email:c.email,loc:c.loc,type:c.type}; this.showModal=true },
    saveCustomer() {
      if (this.editingId) {
        const idx=this.customers.findIndex(c=>c.id===this.editingId)
        this.customers[idx]={...this.customers[idx],...this.form}
        this.$refs.toast.show('✓','Customer updated',this.form.biz)
      } else {
        const newId='CST-'+String(this.customers.length+1).padStart(3,'0')
        this.customers.push({id:newId,...this.form,credit:100000,pending:0,totalOrders:0,totalValue:0,avgPayDays:0,invoices:[],orders:[],payHistory:[]})
        this.$refs.toast.show('✓','Customer added',this.form.biz)
      }
      this.showModal=false; this.editingId=null
    },
    openCollectModal(c) {
      this.collectTargetCustomer = c;
      this.collectAmount = c.pending;
      this.showCollectModal = true;
    },
    async submitCollection() {
      if (!this.collectAmount || this.collectAmount <= 0) return;
      try {
        const res = await fetch('http://127.0.0.1:5000/api/internal-portal/collect-payment', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ cid: this.collectTargetCustomer.id, amount: this.collectAmount })
        });
        if (res.ok) {
          const data = await res.json();
          this.$refs.toast.show('✓', 'Payment collected', `₹${data.collected.toLocaleString('en-IN')} allocated via FIFO`);
          this.showCollectModal = false;
          await this.fetchCustomers(); // refresh the data and invoices
        } else {
          const err = await res.json();
          this.$refs.toast.show('❌', 'Collection Failed', err.message);
        }
      } catch (e) {
        this.$refs.toast.show('❌', 'Error', e.message);
      }
    },
    downloadCustomerInvoice(inv, customer) {
      const lines = `<tr style="border-bottom:none;">
          <td style="padding:20px;border-bottom:1px solid #e2e8f0;">
            <div style="display:flex; align-items:center; gap:12px;">
              <div style="width:40px;height:40px;background:#eff6ff;color:#2563eb;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:18px;">📄</div>
              <div>
                <div style="font-weight:600;color:#0f172a;">${inv.desc}</div>
                <div style="font-size:12px;color:#64748b;margin-top:2px;">Custom items package</div>
              </div>
            </div>
          </td>
          <td style="padding:20px;border-bottom:1px solid #e2e8f0;">
            <div style="text-align:center; padding:6px; background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; font-weight:600; color:#0f172a;">
              1
            </div>
          </td>
        </tr>`

      const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    body { font-family: 'Inter', sans-serif; background-color: #e2e8f0; padding: 40px 20px; margin: 0; -webkit-font-smoothing: antialiased; }
    .card { max-width: 800px; margin: 0 auto; background: #fff; border-radius: 16px; box-shadow: 0 20px 40px -15px rgba(0,0,0,0.05); overflow: hidden; }
    .head { background: #0f172a; color: #fff; padding: 40px; display: flex; justify-content: space-between; align-items: center; }
    .head h1 { font-size: 28px; margin: 0; font-weight: 700; letter-spacing: -0.5px; }
    .head p { margin: 4px 0 0; color: #94a3b8; font-size: 14px; }
    .badge { display: inline-block; background: rgba(255,255,255,0.1); padding: 6px 12px; border-radius: 99px; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; border: 1px solid rgba(255,255,255,0.2); }
    .body { padding: 40px; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 32px; margin-bottom: 40px; }
    .block h3 { font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; color: #64748b; margin: 0 0 12px 0; }
    .block p { margin: 0 0 6px 0; font-size: 14px; line-height: 1.5; color:#0f172a;}
    .block .prim { font-weight: 600; font-size: 16px; }
    table { width: 100%; border-collapse: separate; border-spacing: 0; margin-bottom: 32px; }
    th { background: #f8fafc; color: #64748b; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; padding: 16px 20px; text-align: left; border-top: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0; }
    th:first-child { border-radius: 8px 0 0 8px; border-left: 1px solid #e2e8f0; }
    th:last-child { border-radius: 0 8px 8px 0; text-align: center; border-right: 1px solid #e2e8f0; width: 100px; }
    td { padding: 0; }
    .tot-box { background: #eff6ff; border: 1px solid #dbeafe; border-radius: 12px; padding: 24px; display: flex; justify-content: space-between; align-items: center; margin-left: auto; max-width: 320px; }
    .tot-box span { font-size: 14px; color: #2563eb; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
    .tot-box strong { font-size: 28px; color: #2563eb; font-weight: 700; }
    .foot { text-align: center; padding-top: 32px; border-top: 1px dashed #e2e8f0; color: #64748b; font-size: 13px; }
  </style>
</head>
<body>
  <div class="card">
    <div class="head">
      <div>
        <h1>Invoice</h1>
        <p>${inv.id} • Generated ${new Date().toLocaleDateString('en-IN', {day:'numeric', month:'short', year:'numeric'})}</p>
      </div>
      <div><div class="badge">${inv.status.toUpperCase()}</div></div>
    </div>
    <div class="body">
      <div class="grid">
        <div class="block">
          <h3>Billed To</h3>
          <p class="prim">${customer.biz}</p>
          <p style="color:#64748b">${customer.loc}</p>
        </div>
        <div class="block">
          <h3>Invoice Details</h3>
          <p><span style="color:#64748b;display:inline-block;width:80px;">Due Date:</span> ${inv.due || '—'}</p>
          <p><span style="color:#64748b;display:inline-block;width:80px;">Status:</span> ${inv.status.toUpperCase()}</p>
        </div>
      </div>
      <table>
        <thead><tr><th>Description</th><th>Quantity</th></tr></thead>
        <tbody>${lines}</tbody>
      </table>
      <div class="tot-box">
        <span>Total Amount</span>
        <strong>${this.fmtINR(inv.amount)}</strong>
      </div>
      <div class="foot">Thank you for your business!</div>
    </div>
  </div>
</body>
</html>`

      const blob = new Blob([html], { type: 'text/html' })
      const url  = URL.createObjectURL(blob)
      const a    = document.createElement('a')
      a.href     = url
      a.download = `${inv.id}-${customer.biz.replace(/\s+/g, '-')}.html`
      a.click()
      URL.revokeObjectURL(url)
    }
  }
}
</script>

<style scoped>
.main { flex: 1; display: flex; flex-direction: column; overflow: hidden; background: var(--bg); }

/* ── Page head ── */
.pg-head   { background: var(--white); border-bottom: 1.5px solid var(--border); flex-shrink: 0; }
.head-row1 { display: flex; align-items: center; justify-content: space-between; padding: 16px 22px 12px; }
.pg-title  { font-size: 18px; font-weight: 600; color: var(--ink); letter-spacing: -0.4px; }
.pg-meta   { font-size: 10.5px; color: var(--ink-4); font-family: 'Geist Mono', monospace; margin-top: 2px; letter-spacing: 0.3px; }
.head-pills { display: flex; align-items: center; gap: 8px; }
.hpill      { display: flex; align-items: center; gap: 6px; padding: 6px 12px; border-radius: 20px; border: 1.5px solid var(--border); background: var(--surface); }
.hpill-dot  { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.hpill-val  { font-family: 'Geist Mono', monospace; font-weight: 500; font-size: 12px; color: var(--ink); }
.hpill-lbl  { color: var(--ink-3); font-size: 10.5px; font-weight: 500; }

.head-row2        { display: flex; align-items: center; border-top: 1.5px solid var(--border); }
.ctab             { display: flex; align-items: center; gap: 6px; padding: 10px 18px; border: none; background: transparent; cursor: pointer; color: var(--ink-4); font-family: 'Geist', sans-serif; font-size: 12px; font-weight: 500; border-bottom: 2px solid transparent; transition: all 0.12s; position: relative; top: 1.5px; }
.ctab:hover:not(.active) { color: var(--ink-2); }
.ctab.active      { color: var(--ink); border-bottom-color: var(--blue); font-weight: 600; }
.tab-count        { font-family: 'Geist Mono', monospace; font-size: 10px; background: var(--surface); border: 1px solid var(--border-2); border-radius: 10px; padding: 0 6px; color: var(--ink-4); line-height: 1.8; }
.tab-count.active { background: var(--blue); color: #fff; border-color: var(--blue); }
.tab-sep          { width: 1px; height: 18px; background: var(--border); margin: 0 2px; align-self: center; }
.head-search-row  { margin-left: auto; display: flex; align-items: center; gap: 8px; padding: 0 22px 0 12px; }
.tb-select        { padding: 5px 9px; background: var(--white); border: 1.5px solid var(--border); border-radius: 6px; color: var(--ink-2); font-size: 12px; outline: none; font-family: 'Geist', sans-serif; cursor: pointer; }

/* ── Body ── */
.body-split { flex: 1; display: flex; overflow: hidden; min-height: 0; }

/* ── Customer list ── */
.clist-panel   { width: 390px; flex-shrink: 0; border-right: 1.5px solid var(--border); display: flex; flex-direction: column; background: var(--white); overflow: hidden; min-height: 0; }
.clist-toolbar { padding: 9px 14px; border-bottom: 1.5px solid var(--border); display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
.sort-label    { font-size: 9.5px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; color: var(--ink-4); }
.sort-btn      { padding: 3px 10px; font-family: 'Geist', sans-serif; font-size: 10px; font-weight: 600; border: 1.5px solid var(--border); border-radius: 20px; background: transparent; cursor: pointer; color: var(--ink-3); transition: all 0.15s; }
.sort-btn.active, .sort-btn:hover { background: var(--blue); color: #fff; border-color: var(--blue); }
.clist-scroll  { flex: 1; overflow-y: auto; min-height: 0; }
.clist-scroll::-webkit-scrollbar { width: 3px; }
.clist-scroll::-webkit-scrollbar-thumb { background: var(--border-2); border-radius: 2px; }

.ccard        { display: flex; align-items: center; gap: 12px; padding: 12px 14px; border-bottom: 1px solid var(--border-2); cursor: pointer; transition: all 0.12s; border-left: 3px solid transparent; animation: fadeUp 0.18s ease both; }
.ccard:hover  { background: var(--surface); }
.ccard.selected { background: var(--surface); border-left-color: var(--blue); }
.ring-wrap    { position: relative; width: 46px; height: 46px; flex-shrink: 0; }
.ring-score   { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-family: 'Geist Mono', monospace; font-size: 11px; font-weight: 500; }
.ccard-body   { flex: 1; min-width: 0; }
.ccard-name   { font-weight: 600; font-size: 13px; color: var(--ink); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ccard-sub    { font-size: 11px; color: var(--ink-3); margin-top: 1px; }
.ccard-tags   { display: flex; gap: 4px; margin-top: 5px; flex-wrap: wrap; }
.ccard-right  { text-align: right; flex-shrink: 0; }
.ccard-pending { font-family: 'Geist Mono', monospace; font-size: 12.5px; font-weight: 500; color: var(--ink); }
.ccard-pending.overdue { color: var(--red); }
.ccard-dl     { font-size: 10.5px; color: var(--ink-3); margin-top: 2px; }

/* ── Detail panel ── */
.detail-panel { flex: 1; display: flex; flex-direction: column; overflow: hidden; background: var(--surface); min-height: 0; }
.dp-empty     { flex: 1; display: flex; align-items: center; justify-content: center; flex-direction: column; gap: 10px; }
.dp-empty-icon { font-size: 48px; opacity: 0.15; }
.dp-empty-text { font-size: 15px; font-weight: 600; color: var(--ink-3); }
.dp-empty-sub  { font-size: 12.5px; color: var(--ink-4); text-align: center; max-width: 220px; }

/* dp-inner fills the panel and enables scroll inside dp-body */
.dp-inner {
  flex: 1; display: flex; flex-direction: column;
  overflow: hidden; min-height: 0;
  animation: slideIn 0.2s ease both;
}

.dp-head      { padding: 18px 22px 14px; background: var(--white); border-bottom: 1.5px solid var(--border); flex-shrink: 0; }
.dp-head-row1 { display: flex; align-items: flex-start; gap: 14px; margin-bottom: 14px; }

.big-ring-wrap  { position: relative; width: 72px; height: 72px; flex-shrink: 0; }
.big-ring-score { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.big-ring-score .num { font-family: 'Geist Mono', monospace; font-size: 18px; font-weight: 500; line-height: 1; }
.big-ring-score .lbl { font-size: 7.5px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; color: var(--ink-3); margin-top: 2px; }

/* Ring arc animation — draws from 0 to target on mount */
.ring-arc {
  animation: drawRing 0.8s cubic-bezier(0.4, 0, 0.2, 1) 0.1s both;
  transform: rotate(-90deg);
  transform-origin: 36px 36px;
}
@keyframes drawRing {
  from { stroke-dashoffset: 175.9; }
  to   { stroke-dashoffset: var(--target-offset); }
}

.dp-head-info  { flex: 1; }
.dp-cname      { font-size: 19px; font-weight: 600; color: var(--ink); letter-spacing: -0.3px; margin-bottom: 4px; }
.dp-cmeta      { font-size: 11.5px; color: var(--ink-3); }
.dp-chip-row   { display: flex; gap: 5px; flex-wrap: wrap; margin-top: 6px; }

.dp-stat-bar { display: grid; grid-template-columns: repeat(4,1fr); gap: 1px; background: var(--border); border: 1.5px solid var(--border); border-radius: 8px; overflow: hidden; }
.dp-stat     { background: var(--surface); padding: 10px 14px; }
.dp-stat-val { font-family: 'Geist Mono', monospace; font-size: 14px; font-weight: 500; color: var(--ink); }
.dp-stat-lbl { font-size: 8.5px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; color: var(--ink-3); margin-top: 2px; }

/* THIS IS THE KEY FIX — dp-body must have min-height:0 and flex:1 to scroll */
.dp-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
}
.dp-body::-webkit-scrollbar { width: 3px; }
.dp-body::-webkit-scrollbar-thumb { background: var(--border-2); border-radius: 2px; }

.dp-sec      { background: var(--white); border: 1.5px solid var(--border); border-radius: 8px; overflow: hidden; flex-shrink: 0; }
.dp-sec-head { padding: 9px 14px; border-bottom: 1.5px solid var(--border-2); background: var(--surface); }
.dp-sec-title { font-size: 9.5px; font-weight: 600; letter-spacing: 1.5px; text-transform: uppercase; color: var(--ink-3); }

.ord-table    { width: 100%; border-collapse: collapse; font-size: 12px; }
.ord-table th { padding: 7px 12px; font-size: 9px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; color: var(--ink-4); text-align: left; border-bottom: 1.5px solid var(--border-2); background: var(--surface); }
.ord-table td { padding: 8px 12px; border-bottom: 1px solid var(--border-2); vertical-align: middle; }
.ord-table tbody tr:last-child td { border-bottom: none; }
.ord-table tbody tr:hover { background: var(--surface); }
.cell-id    { font-family: 'Geist Mono', monospace; font-size: 10.5px; color: var(--blue); }
.cell-meta  { font-size: 11.5px; color: var(--ink-3); }
.cell-val   { font-family: 'Geist Mono', monospace; font-weight: 500; }
.status-pill  { font-size: 9.5px; font-weight: 600; padding: 2px 8px; border-radius: 20px; }
.sp-paid      { background: var(--green-dim); color: var(--green); }
.sp-pending   { background: var(--amber-dim); color: var(--amber); }
.sp-overdue   { background: var(--red-dim);   color: var(--red); }

.inv-row      { display: flex; align-items: center; gap: 10px; padding: 9px 14px; border-bottom: 1px solid var(--border-2); font-size: 12px; }
.inv-row:last-child { border-bottom: none; }
.inv-id       { font-family: 'Geist Mono', monospace; font-size: 10.5px; color: var(--ink-3); width: 72px; flex-shrink: 0; }
.inv-desc     { flex: 1; color: var(--ink-2); }
.inv-amount   { font-family: 'Geist Mono', monospace; font-size: 12px; font-weight: 500; }
.inv-due      { font-size: 11px; text-align: right; min-width: 80px; flex-shrink: 0; }
.inv-due.overdue  { color: var(--red); font-weight: 700; }
.inv-due.due-soon { color: var(--amber); font-weight: 600; }
.inv-due.ok       { color: var(--green); }

.timeline { padding: 12px 14px; display: flex; flex-direction: column; }
.tl-item  { display: flex; gap: 12px; position: relative; }
.tl-item::before { content:''; position: absolute; left: 7px; top: 20px; bottom: -8px; width: 1px; background: var(--border-2); }
.tl-item:last-child::before { display: none; }
.tl-dot   { width: 15px; height: 15px; border-radius: 50%; flex-shrink: 0; border: 2px solid; margin-top: 3px; }
.tl-body  { padding-bottom: 14px; }
.tl-title { font-size: 12.5px; font-weight: 600; color: var(--ink); }
.tl-meta  { font-size: 11px; color: var(--ink-3); margin-top: 1px; }
.tl-amount { font-family: 'Geist Mono', monospace; font-size: 12px; font-weight: 500; }

/* ── Payments tab ── */
.payments-view { flex: 1; overflow-y: auto; padding: 18px 22px; }
.ledger-grid   { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px,1fr)); gap: 14px; }
.ledger-card   { background: var(--white); border: 1.5px solid var(--border); border-radius: 10px; overflow: hidden; transition: transform 0.15s, box-shadow 0.15s; cursor: pointer; animation: fadeUp 0.18s ease both; }
.ledger-card:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(37,99,235,.1); }
.lc-head     { padding: 13px 14px; border-bottom: 1.5px solid var(--border-2); display: flex; align-items: center; gap: 10px; }
.lc-av       { width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 12px; color: #fff; flex-shrink: 0; }
.lc-name     { font-weight: 600; font-size: 13px; color: var(--ink); }
.lc-type     { font-size: 11px; color: var(--ink-3); margin-top: 1px; }
.lc-score    { font-family: 'Geist Mono', monospace; font-size: 11px; font-weight: 600; }
.lc-body     { padding: 12px 14px; }
.lc-amount-row { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 9px; }
.lc-pending-label { font-size: 9px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; color: var(--ink-3); }
.lc-pending-val { font-family: 'Geist Mono', monospace; font-size: 24px; font-weight: 600; line-height: 1; }
.lc-foot     { display: flex; justify-content: space-between; font-size: 11px; color: var(--ink-3); }
.lc-foot strong { color: var(--ink); font-weight: 600; }

/* ── Modal ── */
.mo     { position: fixed; inset: 0; background: rgba(0,0,0,.45); z-index: 200; display: flex; align-items: center; justify-content: center; backdrop-filter: blur(2px); }
.mo-box { background: var(--white); border: 1.5px solid var(--border); border-radius: 10px; width: 480px; max-height: 86vh; overflow-y: auto; box-shadow: 0 8px 30px rgba(0,0,0,.12); }
.mo-head { padding: 18px 20px 14px; border-bottom: 1.5px solid var(--border); display: flex; justify-content: space-between; align-items: center; }
.mo-title { font-size: 16px; font-weight: 600; color: var(--ink); letter-spacing: -0.2px; }
.mo-x    { background: none; border: 1.5px solid var(--border); border-radius: 6px; width: 26px; height: 26px; display: flex; align-items: center; justify-content: center; color: var(--ink-3); font-size: 12px; cursor: pointer; transition: all 0.12s; }
.mo-x:hover { background: var(--ink); color: #fff; border-color: var(--ink); }
.mo-body { padding: 18px 20px; display: flex; flex-direction: column; gap: 12px; }
.mo-row  { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.mo-foot { padding: 12px 20px; border-top: 1.5px solid var(--border); display: flex; justify-content: flex-end; gap: 7px; }

/* ── Animations ── */
@keyframes fadeUp  { from { opacity: 0; transform: translateY(5px);  } to { opacity: 1; transform: translateY(0);  } }
@keyframes slideIn { from { opacity: 0; transform: translateX(10px); } to { opacity: 1; transform: translateX(0); } }

.inv-dl-btn {
  background: none; border: 1.5px solid var(--border); border-radius: 5px;
  padding: 2px 8px; font-size: 11px; cursor: pointer; color: var(--blue);
  font-family: 'Geist', sans-serif; transition: all 0.12s; flex-shrink: 0;
}
.inv-dl-btn:hover { background: var(--blue-dim); border-color: var(--blue); }
</style>