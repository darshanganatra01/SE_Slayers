<template>
  <template v-if="route.meta.hideShell">
    <router-view />
  </template>
  <div v-else class="shell">
    <AppSidebar :order-count="orderStore.inprocessCount" />
    <router-view />
  </div>
</template>

<script>
import AppSidebar from './components/AppSidebar.vue'
import { useOrderStore } from './order_management/store.js'
import { useRoute } from 'vue-router'

export default {
  name: 'App',
  components: { AppSidebar },
  setup() {
    const orderStore = useOrderStore()
    const route = useRoute()
    return { orderStore, route }
  }
}
</script>

<style>
.shell { display: flex; height: 100vh; overflow: hidden; }
</style>