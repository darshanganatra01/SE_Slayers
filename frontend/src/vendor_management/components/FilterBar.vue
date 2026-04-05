<template>
  <div class="filter-bar">
    <select
      v-if="showLeadTime"
      class="tb-select"
      :value="leadTime"
      @change="$emit('update:leadTime', $event.target.value)"
    >
      <option value="all">All Lead Times</option>
      <option value="fast">≤ 3 days</option>
      <option value="medium">4–7 days</option>
      <option value="slow">> 7 days</option>
    </select>


    <select class="tb-select" :value="location" @change="$emit('update:location', $event.target.value)">
      <option value="all">All Locations</option>
      <option v-for="loc in locations" :key="loc" :value="loc">{{ loc }}</option>
    </select>
  </div>
</template>

<script>
export default {
  name: 'FilterBar',
  props: {
    showLeadTime: { type: Boolean, default: true },
    leadTime:  { type: String, default: 'all' },
    location:  { type: String, default: 'all' },
    locations: { type: Array, default: () => [] }
  },
  emits: ['update:leadTime', 'update:location']
}
</script>

<style scoped>
.filter-bar {
  display: flex;
  align-items: center;
  gap: 6px;
}
.tb-select {
  padding: 5px 9px;
  background: var(--white);
  border: 1.5px solid var(--border);
  border-radius: 6px;
  color: var(--ink-2);
  font-size: 12px;
  outline: none;
  font-family: 'Geist', sans-serif;
  cursor: pointer;
}
.tb-select option { background: #fff; }
</style>
