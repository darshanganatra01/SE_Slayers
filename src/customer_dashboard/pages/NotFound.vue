<template>
  <div class="flex min-h-screen items-center justify-center bg-muted">
    <div class="text-center">
      <h1 class="mb-4 text-4xl font-bold">404</h1>
      <p class="mb-4 text-xl text-muted-foreground">Oops! Page not found</p>
      <RouterLink to="/store" class="text-primary underline hover:text-primary/90">
        Return to Home
      </RouterLink>
    </div>
  </div>
</template>

<script setup lang="ts">
import { watchEffect } from 'vue'
import { useRoute } from 'vue-router'
import { RouterLink } from 'vue-router'

const route = useRoute()

watchEffect(() => {
  console.error("404 Error: User attempted to access non-existent route:", route.path)
})
</script>
