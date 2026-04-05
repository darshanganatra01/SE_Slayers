<template>
  <div v-if="visible" class="mo" @click.self="$emit('close')">
    <div class="mo-box">

      <div class="mo-head">
        <div class="mo-title">New Order</div>
        <div class="mo-x" @click="$emit('close')">✕</div>
      </div>

      <div class="mo-body">
        <!-- Customer Select -->
        <div class="fg">
          <label class="fl">Customer</label>
          <div class="search-select">
            <input
              class="fi"
              v-model="customerSearch"
              placeholder="Search customer…"
              @focus="showCustDrop = true"
              @input="showCustDrop = true"
            />
            <div v-if="showCustDrop && filteredCustomers.length" class="ss-drop">
              <div
                v-for="c in filteredCustomers" :key="c.cid"
                class="ss-opt"
                @mousedown.prevent="selectCustomer(c)"
              >
                <div class="ss-name">{{ c.customer_name }}</div>
                <div class="ss-meta">{{ c.location }} · Priority: {{ c.priority }}</div>
              </div>
            </div>
          </div>
          <div v-if="selectedCustomer" class="cust-selected">
            <span class="cust-chip">{{ selectedCustomer.customer_name }}</span>
            <span class="cust-pri" :class="'pri-' + selectedCustomer.priority.toLowerCase()">{{ selectedCustomer.priority }}</span>
            <span class="cust-loc">{{ selectedCustomer.location }}</span>
          </div>
        </div>

        <!-- Product Lines -->
        <div class="fg">
          <label class="fl">Products</label>
          <div v-for="(line, idx) in lines" :key="idx" class="prod-line">
            <div class="pl-row1">
              <div class="search-select pl-prod">
                <input
                  class="fi"
                  style="width: 100%; box-sizing: border-box;"
                  v-model="line.search"
                  placeholder="Search product…"
                  @focus="line.showDrop = true"
                  @input="line.showDrop = true; line.pid = ''; onProductChange(idx)"
                  @blur="hideProductDrop(idx)"
                />
                <div v-if="line.showDrop && getFilteredProducts(line.search).length" class="ss-drop">
                  <div
                    v-for="p in getFilteredProducts(line.search)" :key="p.pid"
                    class="ss-opt"
                    @mousedown.prevent="selectProduct(idx, p)"
                  >
                    <div class="ss-name">{{ p.pname }}</div>
                  </div>
                </div>
              </div>
              <select class="fi pl-sku" v-model="line.skuid" @change="onSkuChange(idx)" :disabled="!line.skus.length">
                <option value="">Select variant…</option>
                <option v-for="s in line.skus" :key="s.skuid" :value="s.skuid">
                  {{ s.specs || s.skuid }}
                </option>
              </select>
              <div class="pl-price-col" v-if="line.sell_rate">₹{{ line.sell_rate.toLocaleString('en-IN') }}</div>
              <button class="pl-remove" @click="removeLine(idx)" v-if="lines.length > 1">✕</button>
            </div>
            <div class="pl-row2">
              <div class="pl-qty-wrap">
                <label class="pl-qlabel">Qty</label>
                <input class="fi pl-qty" type="number" min="1" v-model.number="line.quantity" @input="calcLineAmount(idx)" />
              </div>
              <div class="pl-rate" v-if="line.sell_rate">
                @ ₹{{ line.sell_rate.toLocaleString('en-IN') }}
              </div>
              <div class="pl-amount" v-if="line.amount">
                = <strong>₹{{ line.amount.toLocaleString('en-IN') }}</strong>
              </div>
              <div class="pl-stock" v-if="line.stock_qty !== null" :class="{ low: line.stock_qty < line.quantity }">
                Stock: {{ line.stock_qty }}
              </div>
            </div>
          </div>
          <button class="add-line-btn" @click="addLine">+ Add Product</button>
        </div>

        <!-- Order Total -->
        <div class="order-total-row" v-if="orderTotal > 0">
          <span class="ot-label">Order Total</span>
          <span class="ot-value">₹{{ orderTotal.toLocaleString('en-IN') }}</span>
        </div>
      </div>

      <div class="mo-foot">
        <button class="btn-cancel" @click="$emit('close')">Cancel</button>
        <button class="btn btn-primary" :disabled="!canSubmit || isSubmitting" @click="submit">
          {{ isSubmitting ? 'Creating…' : 'Create order' }}
        </button>
      </div>

    </div>
  </div>
</template>

<script>
export default {
  name: 'NewOrderModal',
  props: {
    visible: { type: Boolean, default: false }
  },
  emits: ['close', 'created'],
  data() {
    return {
      customers: [],
      products: [],
      selectedCustomer: null,
      customerSearch: '',
      showCustDrop: false,
      lines: [this.emptyLine()],
      isSubmitting: false
    }
  },
  computed: {
    filteredCustomers() {
      const q = this.customerSearch.toLowerCase()
      if (!q) return this.customers
      return this.customers.filter(c =>
        c.customer_name.toLowerCase().includes(q) || c.location.toLowerCase().includes(q)
      )
    },
    orderTotal() {
      return this.lines.reduce((sum, l) => sum + (l.amount || 0), 0)
    },
    canSubmit() {
      return this.selectedCustomer && this.lines.some(l => l.skuid && l.quantity > 0)
    }
  },
  watch: {
    visible(val) {
      if (val) {
        this.loadFormData()
        this.resetForm()
      }
    }
  },
  methods: {
    emptyLine() {
      return { pid: '', skuid: '', skus: [], quantity: 1, sell_rate: 0, amount: 0, stock_qty: null, search: '', showDrop: false }
    },
    resetForm() {
      this.selectedCustomer = null
      this.customerSearch = ''
      this.showCustDrop = false
      this.lines = [this.emptyLine()]
      this.isSubmitting = false
    },
    async loadFormData() {
      try {
        const res = await fetch('http://127.0.0.1:5000/api/internal-portal/new-order-data')
        if (res.ok) {
          const data = await res.json()
          this.customers = data.customers || []
          this.products = data.products || []
        }
      } catch (e) {
        console.error('Failed to load form data:', e)
      }
    },
    selectCustomer(c) {
      this.selectedCustomer = c
      this.customerSearch = c.customer_name
      this.showCustDrop = false
    },
    getFilteredProducts(search) {
      if (!search) return this.products;
      const q = search.toLowerCase();
      return this.products.filter(p => p.pname.toLowerCase().includes(q));
    },
    selectProduct(idx, p) {
      const line = this.lines[idx];
      line.pid = p.pid;
      line.search = p.pname;
      line.showDrop = false;
      this.onProductChange(idx);
    },
    hideProductDrop(idx) {
      setTimeout(() => {
        if (this.lines[idx]) this.lines[idx].showDrop = false;
      }, 150);
    },
    addLine() {
      this.lines.push(this.emptyLine())
    },
    removeLine(idx) {
      this.lines.splice(idx, 1)
    },
    async onProductChange(idx) {
      const line = this.lines[idx]
      line.skuid = ''
      line.skus = []
      line.sell_rate = 0
      line.amount = 0
      line.stock_qty = null
      if (!line.pid) return

      try {
        const res = await fetch(`http://127.0.0.1:5000/api/internal-portal/product-skus/${line.pid}`)
        if (res.ok) {
          line.skus = await res.json()
          // Auto-select if only one SKU
          if (line.skus.length === 1) {
            line.skuid = line.skus[0].skuid
            this.onSkuChange(idx)
          }
        }
      } catch (e) {
        console.error('Failed to load SKUs:', e)
      }
    },
    onSkuChange(idx) {
      const line = this.lines[idx]
      const sku = line.skus.find(s => s.skuid === line.skuid)
      if (sku) {
        line.sell_rate = sku.sell_rate
        line.stock_qty = sku.stock_qty
        this.calcLineAmount(idx)
      } else {
        line.sell_rate = 0
        line.amount = 0
        line.stock_qty = null
      }
    },
    calcLineAmount(idx) {
      const line = this.lines[idx]
      line.amount = (line.quantity || 0) * (line.sell_rate || 0)
    },
    async submit() {
      if (!this.canSubmit) return
      this.isSubmitting = true

      const items = this.lines
        .filter(l => l.skuid && l.quantity > 0)
        .map(l => ({ skuid: l.skuid, quantity: l.quantity }))

      try {
        const res = await fetch('http://127.0.0.1:5000/api/internal-portal/create-order', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ cid: this.selectedCustomer.cid, items })
        })
        if (res.ok) {
          const data = await res.json()
          this.$emit('created', data)
        } else {
          const err = await res.json()
          alert(err.message || 'Failed to create order')
        }
      } catch (e) {
        alert('Network error: ' + e.message)
      } finally {
        this.isSubmitting = false
      }
    }
  }
}
</script>

<style scoped>
.mo {
  position: fixed; inset: 0; background: rgba(0,0,0,.45); z-index: 200;
  display: flex; align-items: center; justify-content: center;
  backdrop-filter: blur(2px);
}
.mo-box {
  background: var(--white); border: 1.5px solid var(--border);
  border-radius: 10px; width: 560px;
  max-height: 86vh; overflow-y: auto;
  box-shadow: 0 8px 30px rgba(0,0,0,.12);
}
.mo-head {
  padding: 18px 20px 14px; border-bottom: 1.5px solid var(--border);
  display: flex; justify-content: space-between; align-items: center;
}
.mo-title { font-size: 16px; font-weight: 600; color: var(--ink); letter-spacing: -0.2px; }
.mo-x {
  background: none; border: 1.5px solid var(--border); border-radius: 6px;
  width: 26px; height: 26px; display: flex; align-items: center; justify-content: center;
  color: var(--ink-3); font-size: 12px; cursor: pointer; transition: all 0.12s;
}
.mo-x:hover { background: var(--ink); color: #fff; border-color: var(--ink); }
.mo-body { padding: 18px 20px; display: flex; flex-direction: column; gap: 16px; }
.mo-foot {
  padding: 12px 20px; border-top: 1.5px solid var(--border);
  display: flex; justify-content: flex-end; gap: 7px;
}

/* Search-select dropdown */
.search-select { position: relative; }
.ss-drop {
  position: absolute; top: 100%; left: 0; right: 0; z-index: 10;
  background: var(--white); border: 1.5px solid var(--border); border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0,0,0,.10); max-height: 200px; overflow-y: auto;
  margin-top: 4px;
}
.ss-opt {
  padding: 8px 12px; cursor: pointer; transition: background 0.1s;
}
.ss-opt:hover { background: var(--surface); }
.ss-name { font-size: 13px; font-weight: 600; color: var(--ink); }
.ss-meta { font-size: 10.5px; color: var(--ink-4); margin-top: 1px; }

/* Customer selected chip */
.cust-selected {
  display: flex; align-items: center; gap: 8px; margin-top: 8px;
  padding: 6px 10px; background: var(--surface); border-radius: 6px; border: 1px solid var(--border-2);
}
.cust-chip { font-size: 12px; font-weight: 600; color: var(--ink); }
.cust-pri {
  font-size: 9.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;
  padding: 1px 7px; border-radius: 4px;
}
.pri-high   { background: #fee2e2; color: #dc2626; }
.pri-medium { background: #fef3c7; color: #d97706; }
.pri-low    { background: #dcfce7; color: #16a34a; }
.cust-loc { font-size: 11px; color: var(--ink-4); margin-left: auto; }

/* Product lines */
.prod-line {
  background: var(--surface); border: 1px solid var(--border-2);
  border-radius: 8px; padding: 10px 12px; margin-bottom: 8px;
}
.pl-row1 { display: flex; gap: 8px; align-items: center; margin-bottom: 6px; }
.pl-prod { flex: 1.2; }
.pl-sku  { flex: 1.5; }
.pl-price-col {
  font-size: 13px; font-weight: 700; color: var(--ink); white-space: nowrap;
  min-width: 60px; text-align: right;
}
.pl-remove {
  background: none; border: 1px solid var(--border); border-radius: 5px;
  width: 26px; height: 26px; display: flex; align-items: center; justify-content: center;
  color: var(--ink-4); font-size: 11px; cursor: pointer; flex-shrink: 0;
  transition: all 0.12s;
}
.pl-remove:hover { background: var(--red); color: #fff; border-color: var(--red); }

.pl-row2 { display: flex; align-items: center; gap: 10px; font-size: 12px; }
.pl-qty-wrap { display: flex; align-items: center; gap: 4px; }
.pl-qlabel { font-size: 10.5px; color: var(--ink-4); font-weight: 600; }
.pl-qty { width: 60px; text-align: center; }
.pl-rate { color: var(--ink-4); }
.pl-amount { color: var(--green); font-weight: 600; }
.pl-stock { margin-left: auto; font-size: 10.5px; color: var(--ink-4); font-family: 'Geist Mono', monospace; }
.pl-stock.low { color: var(--red); font-weight: 600; }

.add-line-btn {
  background: none; border: 1.5px dashed var(--border); border-radius: 6px;
  padding: 7px; width: 100%; font-size: 12px; font-weight: 600;
  color: var(--blue); cursor: pointer; transition: all 0.12s;
  font-family: 'Geist', sans-serif;
}
.add-line-btn:hover { background: var(--surface); border-color: var(--blue); }

/* Order total */
.order-total-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 14px; background: var(--green-dim); border-radius: 8px;
  border: 1px solid #86efac;
}
.ot-label { font-size: 13px; font-weight: 600; color: var(--ink-2); }
.ot-value { font-size: 18px; font-weight: 700; color: var(--green); }

.btn-primary:disabled { opacity: 0.45; cursor: not-allowed; }
</style>