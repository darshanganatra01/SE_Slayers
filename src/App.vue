<template>
  <div class="shell">
    <AppSidebar :order-count="orderStore.inprocessCount" />
    <router-view />
  </div>
</template>

<script>
import AppSidebar from './components/AppSidebar.vue'
import { useOrderStore } from './order_management/store.js'

export default {
  name: 'App',
  components: { AppSidebar },
  setup() {
    const orderStore = useOrderStore()
    return { orderStore }
  }
}
</script>

<style>
.shell { display: flex; height: 100vh; overflow: hidden; }
</style>