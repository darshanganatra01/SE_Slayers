<template>
  <div class="toast" :class="{ show: visible }" :style="{ '--drain-duration': (duration / 1000) + 's' }">
    <div class="t-ic">{{ icon }}</div>
    <div>
      <div class="t-text">{{ text }}</div>
      <div class="t-sub">{{ sub }}</div>
    </div>
    <div class="t-prog"></div>
  </div>
</template>

<script>
export default {
  name: 'AppToast',
  data() {
    return { visible: false, icon: '✓', text: '', sub: '', timer: null, duration: 3100 }
  },
  methods: {
    show(icon, text, sub, duration) {
      clearTimeout(this.timer)
      this.icon = icon
      this.text = text
      this.sub  = sub
      this.duration = duration || 3100
      this.visible = false
      this.$nextTick(() => {
        this.visible = true
        this.timer = setTimeout(() => { this.visible = false }, this.duration)
      })
    }
  }
}
</script>

<style scoped>
.toast {
  position: fixed; bottom: 18px; right: 18px;
  background: var(--ink); color: #fff; border-radius: 8px;
  padding: 11px 15px; display: flex; align-items: flex-start; gap: 10px;
  z-index: 300; box-shadow: 0 4px 16px rgba(0,0,0,.2);
  transform: translateY(60px); opacity: 0;
  transition: all 0.28s cubic-bezier(0.34,1.56,0.64,1);
  font-family: 'Geist', sans-serif; min-width: 210px; max-width: 420px; pointer-events: none;
}
.toast.show  { transform: translateY(0); opacity: 1; }
.t-ic        { font-size: 14px; margin-top: 1px; }
.t-text      { font-size: 12.5px; font-weight: 600; color: #fff; }
.t-sub       { font-size: 11px; color: rgba(255,255,255,.45); margin-top: 1px; }
.t-prog {
  position: absolute; bottom: 0; left: 0; height: 2px;
  background: var(--blue); border-radius: 0 0 8px 8px;
}
.toast.show .t-prog { animation: drain var(--drain-duration, 3s) linear forwards; }
@keyframes drain { from { width: 100%; } to { width: 0; } }
</style>