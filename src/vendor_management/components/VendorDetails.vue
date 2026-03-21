<template>
  <div class="vd-panel">
    <div class="vd-head">
      <button class="vd-back" @click="$emit('back')">
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M8 1L3 6l5 5"/>
        </svg>
        Back to list
      </button>
    </div>

    <div v-if="!vendor" class="empty-state">
      <div class="es-icon">📋</div>
      <div class="es-text">No vendor selected</div>
      <div class="es-sub">Click a vendor from the list to view details</div>
    </div>

    <template v-else>
      <div class="vd-profile">
        <div class="vd-avatar">{{ initials }}</div>
        <div>
          <div class="vd-name">{{ vendor.name }}</div>
          <div class="vd-id">{{ vendor.id }}</div>
        </div>
      </div>

      <div class="vd-sections">
        <!-- Contact info -->
        <div class="vd-section">
          <div class="vd-section-title">Contact Information</div>
          <div class="vd-grid">
            <div class="fg">
              <span class="fl">Phone</span>
              <span class="vd-val">{{ vendor.contact.phone }}</span>
            </div>
            <div class="fg">
              <span class="fl">Email</span>
              <span class="vd-val">{{ vendor.contact.email }}</span>
            </div>
            <div class="fg">
              <span class="fl">Location</span>
              <span class="vd-val">{{ vendor.location }}</span>
            </div>
          </div>
        </div>

        <!-- Performance -->
        <div class="vd-section">
          <div class="vd-section-title">Performance</div>
          <div class="vd-grid">
            <div class="fg">
              <span class="fl">Lead Time</span>
              <span class="vd-val vd-lead">
                <span class="vd-lead-dot" :style="{ background: leadColor }"></span>
                {{ vendor.leadTime }} day{{ vendor.leadTime !== 1 ? 's' : '' }}
              </span>
            </div>
          </div>
        </div>

        <!-- Parts supplied -->
        <div class="vd-section">
          <div class="vd-section-title">Parts Supplied</div>
          <div class="vd-parts">
            <span v-for="part in vendor.parts" :key="part" class="chip vd-part-chip">{{ part }}</span>
          </div>
        </div>

        <!-- Placeholder sections -->
        <div class="vd-section">
          <div class="vd-section-title">Order History</div>
          <div class="vd-placeholder">
            <span class="vd-placeholder-icon">📦</span>
            <span class="vd-placeholder-text">Order history will appear here once connected to backend</span>
          </div>
        </div>

        <div class="vd-section">
          <div class="vd-section-title">Notes</div>
          <div class="vd-placeholder">
            <span class="vd-placeholder-icon">📝</span>
            <span class="vd-placeholder-text">Add notes about this vendor — coming soon</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
export default {
  name: 'VendorDetails',
  props: {
    vendor: { type: Object, default: null }
  },
  emits: ['back'],
  computed: {
    initials() {
      if (!this.vendor) return ''
      return this.vendor.name
        .split(' ')
        .map(w => w[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    },
    leadColor() {
      if (!this.vendor) return ''
      if (this.vendor.leadTime <= 3) return 'var(--green)'
      if (this.vendor.leadTime <= 7) return 'var(--amber)'
      return 'var(--red)'
    }
  }
}
</script>

<style scoped>
.vd-panel {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
}

.vd-head {
  margin-bottom: 18px;
}
.vd-back {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: none;
  border: 1.5px solid var(--border);
  border-radius: 5px;
  padding: 5px 11px;
  font-size: 12px;
  font-weight: 500;
  color: var(--ink-3);
  cursor: pointer;
  font-family: 'Geist', sans-serif;
  transition: all 0.12s;
}
.vd-back:hover {
  border-color: var(--ink-3);
  color: var(--ink);
}

.vd-profile {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 24px;
}
.vd-avatar {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  background: var(--blue);
  color: #fff;
  font-size: 15px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.vd-name {
  font-size: 17px;
  font-weight: 600;
  color: var(--ink);
  letter-spacing: -0.3px;
}
.vd-id {
  font-size: 11.5px;
  color: var(--ink-4);
  font-family: 'Geist Mono', monospace;
  margin-top: 1px;
}

.vd-sections {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.vd-section {
  background: var(--white);
  border: 1.5px solid var(--border);
  border-radius: 8px;
  padding: 14px 16px;
}
.vd-section-title {
  font-size: 10.5px;
  font-weight: 600;
  color: var(--ink-4);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 10px;
}

.vd-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px 20px;
}
.vd-val {
  font-size: 13px;
  font-weight: 500;
  color: var(--ink);
}

.vd-lead {
  display: flex;
  align-items: center;
  gap: 6px;
}
.vd-lead-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}

.vd-parts {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.vd-part-chip {
  background: var(--blue-dim);
  color: var(--blue);
}

.vd-placeholder {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 0;
}
.vd-placeholder-icon {
  font-size: 16px;
  opacity: 0.3;
}
.vd-placeholder-text {
  font-size: 12px;
  color: var(--ink-4);
}
</style>
