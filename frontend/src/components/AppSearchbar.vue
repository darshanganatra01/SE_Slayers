<template>
  <div class="searchbar">
    <svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
      <circle cx="11" cy="11" r="8"/>
      <line x1="21" y1="21" x2="16.65" y2="16.65"/>
    </svg>
    <input
      :value="modelValue"
      :placeholder="placeholder"
      @input="$emit('update:modelValue', $event.target.value)"
    />
  </div>
</template>

<script>
export default {
  name: 'AppSearchbar',
  props: {
    modelValue:  { type: String, default: '' },
    placeholder: { type: String, default: 'Search…' }
  },
  emits: ['update:modelValue']
}
</script>

<style scoped>
.searchbar {
  display: flex; align-items: center; gap: 7px;
  background: var(--white); border: 1.5px solid var(--border);
  border-radius: 6px; padding: 5px 10px; width: 200px;
  transition: border-color 0.15s;
}
.searchbar:focus-within { border-color: var(--blue); }
.searchbar svg   { color: var(--ink-4); flex-shrink: 0; }
.searchbar input {
  background: none; border: none; outline: none;
  font-size: 12px; color: var(--ink); width: 100%;
  font-family: 'Geist', sans-serif;
}
.searchbar input::placeholder { color: var(--ink-4); }
</style>