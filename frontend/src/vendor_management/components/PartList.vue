<template>
  <div class="part-list">
    <div class="pl-header">Parts Catalog</div>
    <div v-if="loading" class="pl-state">
      <div class="es-icon">⌛</div>
      <div class="es-text">Loading parts catalog</div>
      <div class="es-sub">Fetching products and available sizes</div>
    </div>
    <div v-else-if="error" class="pl-state">
      <div class="es-icon">!</div>
      <div class="es-text">Unable to load parts</div>
      <div class="es-sub">{{ error }}</div>
    </div>
    <div class="pl-cards">
      <PartCard
        v-for="part in parts"
        :key="part.id"
        :part="part"
        :selected="selectedPartId === part.id"
        @select="$emit('select', $event)"
      />
    </div>
  </div>
</template>

<script>
import PartCard from './PartCard.vue'

export default {
  name: 'PartList',
  components: { PartCard },
  props: {
    loading:        { type: Boolean, default: false },
    error:          { type: String, default: '' },
    parts:          { type: Array, default: () => [] },
    selectedPartId: { type: String, default: null }
  },
  emits: ['select']
}
</script>

<style scoped>
.part-list {
  width: 280px;
  flex-shrink: 0;
  border-right: 1.5px solid var(--border);
  background: var(--white);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.pl-header {
  padding: 12px 14px;
  font-size: 11px;
  font-weight: 600;
  color: var(--ink-3);
  text-transform: uppercase;
  letter-spacing: 0.6px;
  border-bottom: 1.5px solid var(--border-2);
  flex-shrink: 0;
}
.pl-cards {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.pl-state {
  padding: 18px 14px 6px;
  border-bottom: 1.5px solid var(--border-2);
}
</style>
