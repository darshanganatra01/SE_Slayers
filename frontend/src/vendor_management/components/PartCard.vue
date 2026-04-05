<template>
  <div class="part-card" :class="{ selected }" @click="$emit('select', part.id)">
    <div v-if="part.image" class="pc-thumb">
      <img :src="part.image" :alt="part.name" class="pc-img" />
    </div>
    <div v-else class="pc-thumb pc-placeholder">
      <span class="pc-placeholder-text">IMG</span>
    </div>
    <div class="pc-body">
      <div class="pc-name">{{ part.name }}</div>
      <div class="pc-sizes">{{ part.sizes.length }} sizes available</div>
    </div>
    <svg class="pc-arrow" width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.5">
      <path d="M4 1l5 5-5 5"/>
    </svg>
  </div>
</template>

<script>
export default {
  name: 'PartCard',
  props: {
    part:     { type: Object, required: true },
    selected: { type: Boolean, default: false }
  },
  emits: ['select']
}
</script>

<style scoped>
.part-card {
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--white);
  border: 1.5px solid var(--border);
  border-radius: 8px;
  padding: 10px 12px;
  cursor: pointer;
  transition: all 0.12s;
}
.part-card:hover {
  border-color: var(--ink-4);
  background: var(--surface);
}
.part-card.selected {
  border-color: var(--blue);
  background: var(--blue-dim);
}

.pc-thumb {
  width: 44px;
  height: 44px;
  border-radius: 6px;
  border: 1px solid var(--border-2);
  flex-shrink: 0;
  background: var(--surface);
  display: flex;
  align-items: center;
  justify-content: center;
}
.pc-img {
  width: 44px;
  height: 44px;
  object-fit: cover;
  border-radius: 6px;
}
.pc-placeholder-text {
  font-size: 10px;
  font-weight: 700;
  color: var(--ink-4);
  letter-spacing: 0.8px;
}

.pc-body {
  flex: 1;
  min-width: 0;
}
.pc-name {
  font-size: 12.5px;
  font-weight: 600;
  color: var(--ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.pc-sizes {
  font-size: 10.5px;
  color: var(--ink-4);
  margin-top: 2px;
  font-family: 'Geist Mono', monospace;
}

.pc-arrow {
  color: var(--ink-4);
  flex-shrink: 0;
  transition: color 0.12s;
}
.part-card:hover .pc-arrow,
.part-card.selected .pc-arrow {
  color: var(--blue);
}
</style>
