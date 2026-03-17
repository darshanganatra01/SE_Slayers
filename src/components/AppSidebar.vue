<template>
  <aside class="sidebar">

    <div class="logo">
      <div class="logo-mark">
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <rect x="1" y="1" width="5" height="5" rx="1" fill="white"/>
          <rect x="8" y="1" width="5" height="5" rx="1" fill="white" opacity=".6"/>
          <rect x="1" y="8" width="5" height="5" rx="1" fill="white" opacity=".6"/>
          <rect x="8" y="8" width="5" height="5" rx="1" fill="white" opacity=".3"/>
        </svg>
      </div>
      <span class="logo-name">VendorOS</span>
    </div>

    <nav>
      <div class="nav-group">
        <div class="nav-group-label">Workspace</div>

        <router-link to="/dashboard" class="nav-link">
          <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5">
            <rect x="1" y="1" width="5" height="5" rx="1"/>
            <rect x="8" y="1" width="5" height="5" rx="1"/>
            <rect x="1" y="8" width="5" height="5" rx="1"/>
            <rect x="8" y="8" width="5" height="5" rx="1"/>
          </svg>
          Overview
        </router-link>

        <router-link to="/orders" class="nav-link">
          <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M1 4h12M1 7h9M1 10h6"/>
          </svg>
          Orders
          <span v-if="orderCount > 0" class="nav-pip">{{ orderCount }}</span>
        </router-link>

        <router-link to="/customers" class="nav-link">
          <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5">
            <circle cx="7" cy="5" r="2.5"/><path d="M1.5 13c0-3 2.5-5 5.5-5s5.5 2 5.5 5"/>
          </svg>
          Customers
        </router-link>

        <router-link to="/vendors" class="nav-link">
          <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5">
            <rect x="2" y="4" width="10" height="8" rx="1"/><path d="M5 4V3a2 2 0 014 0v1"/>
          </svg>
          Vendors
        </router-link>

        <router-link to="/inventory" class="nav-link">
          <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M2 11V5l5-3 5 3v6"/><rect x="5" y="7" width="4" height="4"/>
          </svg>
          Inventory
        </router-link>
      </div>

      <div class="nav-group">
        <div class="nav-group-label">Reports</div>

        <router-link to="/analytics" class="nav-link">
          <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5">
            <rect x="1" y="1" width="12" height="12" rx="1"/><path d="M4 9l2-3 2 2 2-4"/>
          </svg>
          Analytics
        </router-link>

        <router-link to="/finance" class="nav-link">
          <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M7 1v12M1 7h12"/>
          </svg>
          Finance
        </router-link>
      </div>
    </nav>

    <div class="sidebar-bottom">
      <div class="user-av">{{ userInitials }}</div>
      <div>
        <div class="user-name">{{ user.name }}</div>
        <div class="user-role">{{ user.role }}</div>
      </div>
    </div>

  </aside>
</template>

<script>
export default {
  name: 'AppSidebar',
  props: {
    orderCount: { type: Number, default: 0 }
  },
  data() {
    return {
      user: { name: 'Raj Kumar', role: 'Admin' }
    }
  },
  computed: {
    userInitials() {
      return this.user.name.split(' ').map(n => n[0]).join('')
    }
  }
}
</script>

<style scoped>
.sidebar {
  width: 200px; flex-shrink: 0;
  background: #fafafa;
  border-right: 1.5px solid var(--border);
  display: flex; flex-direction: column;
}
.logo {
  padding: 18px 16px 16px;
  border-bottom: 1.5px solid var(--border);
  display: flex; align-items: center; gap: 8px;
}
.logo-mark {
  width: 26px; height: 26px; background: var(--blue); border-radius: 6px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.logo-name { font-size: 14px; font-weight: 600; color: var(--ink); letter-spacing: -0.3px; }

nav { padding: 8px; flex: 1; }
.nav-group        { margin-bottom: 16px; }
.nav-group-label  {
  font-size: 10px; font-weight: 500; color: var(--ink-4);
  letter-spacing: 0.6px; text-transform: uppercase;
  padding: 0 8px; margin-bottom: 2px;
}
.nav-link {
  display: flex; align-items: center; gap: 8px;
  padding: 6px 8px; border-radius: 5px;
  font-size: 13px; color: var(--ink-3);
  text-decoration: none; cursor: pointer;
  transition: background 0.1s, color 0.1s;
  font-family: 'Geist', sans-serif;
}
.nav-link svg     { width: 14px; height: 14px; flex-shrink: 0; }
.nav-link:hover   { background: var(--surface); color: var(--ink); }
.nav-link.router-link-active {
  background: var(--blue-dim); color: var(--blue);
  font-weight: 500; box-shadow: inset 2px 0 0 var(--blue);
}
.nav-pip {
  margin-left: auto; min-width: 16px; height: 16px;
  background: var(--red); color: #fff;
  font-size: 9.5px; font-weight: 600; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  padding: 0 5px; font-family: 'Geist Mono', monospace;
}
.nav-link.router-link-active .nav-pip { background: var(--blue); }

.sidebar-bottom {
  border-top: 1.5px solid var(--border); padding: 12px;
  display: flex; align-items: center; gap: 9px;
}
.user-av {
  width: 26px; height: 26px; border-radius: 50%;
  background: var(--ink); color: #fff;
  font-size: 10px; font-weight: 600;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.user-name { font-size: 12.5px; font-weight: 500; color: var(--ink); }
.user-role { font-size: 10.5px; color: var(--ink-4); }
</style>