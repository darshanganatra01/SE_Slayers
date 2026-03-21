<template>
  <div class="rating">
    <span v-for="i in 5" :key="i" class="star" :class="{ filled: i <= roundedRating }">★</span>
    <span class="rating-num">{{ rating.toFixed(1) }}</span>
  </div>
</template>

<script>
export default {
  name: 'RatingStars',
  props: {
    rating: { type: Number, required: true }
  },
  computed: {
    roundedRating() {
      return Math.round(this.rating)
    }
  }
}
</script>

<style scoped>
.rating {
  display: flex;
  align-items: center;
  gap: 1px;
}
.star {
  font-size: 11px;
  color: var(--border);
  line-height: 1;
}
.star.filled {
  color: var(--amber);
}
.rating-num {
  font-size: 11px;
  font-weight: 600;
  color: var(--ink-2);
  margin-left: 4px;
  font-family: 'Geist Mono', monospace;
}
</style>
