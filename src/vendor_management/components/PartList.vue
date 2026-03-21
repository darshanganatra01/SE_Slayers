<template>
  <div class="part-list">
    <div class="pl-header">Parts Catalog</div>
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
</style>
