<template>
  <header class="topbar">
    <span class="topbar-title">{{ title }}</span>
    <div class="topbar-sep"></div>
    <span class="topbar-meta">{{ meta }}</span>
    <div class="topbar-right">
      <slot name="actions" />
    </div>
  </header>
</template>

<script>
export default {
  name: 'AppTopbar',
  props: {
    title: { type: String, default: '' },
    meta:  { type: String, default: '' }
  }
}
</script>

<style scoped>
.topbar {
  min-height: 48px; background: var(--white);
  border-bottom: 1.5px solid var(--border);
  display: flex; align-items: center;
  padding: 8px 22px; gap: 10px; flex-shrink: 0;
}
.topbar-title { font-size: 13.5px; font-weight: 600; color: var(--ink); }
.topbar-sep   { width: 1px; height: 14px; background: var(--border); }
.topbar-meta  {
  font-size: 11.5px; color: var(--ink-4); font-family: 'Geist Mono', monospace;
  min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.topbar-right {
  margin-left: auto; display: flex; align-items: center; justify-content: flex-end; gap: 6px;
  min-width: 0; flex: 1 1 auto;
}
</style>
