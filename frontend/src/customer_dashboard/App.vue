<template>
  <div class="min-h-screen flex flex-col">
    <Navbar />
    <main class="flex-grow">
      <router-view />
    </main>
    <!-- Toaster/Sonner would go here -->
  </div>
</template>

<script setup lang="ts">
import Navbar from '@cd/components/Navbar.vue'
</script>
