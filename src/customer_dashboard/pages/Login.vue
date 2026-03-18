<template>
  <div class="flex min-h-[calc(100vh-3.5rem)] items-center justify-center bg-secondary p-4">
    <Card class="w-full max-w-md">
      <CardHeader class="text-center">
        <CardTitle class="text-2xl">🔧 HardwareHub</CardTitle>
        <CardDescription>Sign in to your account</CardDescription>
      </CardHeader>
      <CardContent>
        <form @submit.prevent="handleSubmit" class="space-y-4">
          <div class="space-y-2">
            <Label for="email">Email</Label>
            <Input id="email" type="email" placeholder="you@example.com" v-model="email" required />
          </div>
          <div class="space-y-2">
            <Label for="password">Password</Label>
            <Input id="password" type="password" placeholder="••••••••" v-model="password" required />
          </div>
          <Button type="submit" class="w-full">Sign In</Button>
        </form>
        <p class="mt-4 text-center text-sm text-muted-foreground">
          No account?
          <RouterLink to="/store/register" class="font-medium text-primary underline">
            Register
          </RouterLink>
        </p>
      </CardContent>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { useAuthStore } from '@cd/stores/auth'
import Button from '@cd/components/ui/Button.vue'
import Input from '@cd/components/ui/Input.vue'
import Card from '@cd/components/ui/Card.vue'
import CardHeader from '@cd/components/ui/CardHeader.vue'
import CardTitle from '@cd/components/ui/CardTitle.vue'
import CardContent from '@cd/components/ui/CardContent.vue'
import CardDescription from '@cd/components/ui/CardDescription.vue'
import Label from '@cd/components/ui/Label.vue'

const email = ref('')
const password = ref('')
const authStore = useAuthStore()
const router = useRouter()

const handleSubmit = () => {
  if (authStore.login(email.value, password.value)) {
    router.push('/store')
  }
}
</script>
