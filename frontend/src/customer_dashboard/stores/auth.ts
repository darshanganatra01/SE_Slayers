import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { User } from '@cd/types';

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null);

  const login = (email: string, _password: string) => {
    user.value = { id: 'C001', name: email.split('@')[0], email };
    return true;
  };

  const register = (name: string, email: string, _password: string) => {
    user.value = { id: 'C001', name, email };
    return true;
  };

  const logout = () => {
    user.value = null;
  };

  const isAuthenticated = computed(() => !!user.value);

  return { user, login, register, logout, isAuthenticated };
});
