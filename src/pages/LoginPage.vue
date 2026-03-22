<template>
  <div class="login-root">
    <!-- Same light background blobs -->
    <div class="bg-blob blob-1"></div>
    <div class="bg-blob blob-2"></div>
    <div class="bg-dots"></div>

    <!-- Login card -->
    <div class="login-card">
      <!-- Back button -->
      <button class="back-btn" @click="goBack">
        <svg viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clip-rule="evenodd" />
        </svg>
        <span>Back</span>
      </button>

      <!-- Header -->
      <div class="card-header">
        <div class="card-logo">
          <img src="/metro-removebg-preview.png" alt="Metro" class="card-logo-img" />
        </div>
        <h1 class="card-title">Welcome back</h1>
        <p class="card-subtitle">Sign in to the Sales Agency dashboard</p>
      </div>

      <!-- Form -->
      <form class="login-form" @submit.prevent="handleLogin" novalidate>
        <!-- Email -->
        <div class="form-group" :class="{ 'has-error': errors.email }">
          <label class="form-label" for="login-email">Email address</label>
          <div class="input-wrap">
            <svg class="input-icon" viewBox="0 0 20 20" fill="currentColor">
              <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z"/>
              <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z"/>
            </svg>
            <input
              id="login-email"
              v-model="form.email"
              type="email"
              class="form-input"
              placeholder="you@company.com"
              autocomplete="email"
              @input="clearError('email')"
            />
          </div>
          <span v-if="errors.email" class="error-msg">{{ errors.email }}</span>
        </div>

        <!-- Password -->
        <div class="form-group" :class="{ 'has-error': errors.password }">
          <label class="form-label" for="login-password">Password</label>
          <div class="input-wrap">
            <svg class="input-icon" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clip-rule="evenodd"/>
            </svg>
            <input
              id="login-password"
              v-model="form.password"
              :type="showPw ? 'text' : 'password'"
              class="form-input"
              placeholder="Enter your password"
              autocomplete="current-password"
              @input="clearError('password')"
            />
            <button type="button" class="pw-toggle" @click="showPw = !showPw" tabindex="-1">
              <svg v-if="!showPw" viewBox="0 0 20 20" fill="currentColor">
                <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/>
                <path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"/>
              </svg>
              <svg v-else viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M3.707 2.293a1 1 0 00-1.414 1.414l14 14a1 1 0 001.414-1.414l-1.473-1.473A10.014 10.014 0 0019.542 10C18.268 5.943 14.478 3 10 3a9.958 9.958 0 00-4.512 1.074l-1.78-1.781zm4.261 4.26l1.514 1.515a2.003 2.003 0 012.45 2.45l1.514 1.514a4 4 0 00-5.478-5.478z" clip-rule="evenodd"/>
                <path d="M12.454 16.697L9.75 13.992a4 4 0 01-3.742-3.741L2.335 6.578A9.98 9.98 0 00.458 10c1.274 4.057 5.064 7 9.542 7 .847 0 1.669-.105 2.454-.303z"/>
              </svg>
            </button>
          </div>
          <span v-if="errors.password" class="error-msg">{{ errors.password }}</span>
        </div>

        <!-- General error -->
        <div v-if="errors.general" class="general-error">
          <svg viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
          </svg>
          {{ errors.general }}
        </div>

        <!-- Submit -->
        <button type="submit" class="submit-btn" :class="{ loading: isLoading }" :disabled="isLoading">
          <span v-if="!isLoading">Sign In</span>
          <span v-else class="spinner-wrap">
            <span class="spinner"></span>
            <span>Signing in…</span>
          </span>
        </button>
      </form>

      <p class="card-note">Authorized personnel only. Unauthorized access is prohibited.</p>
    </div>
  </div>
</template>

<script>
import { useRouter } from 'vue-router'
import { ref, reactive } from 'vue'

export default {
  name: 'LoginPage',
  setup() {
    const router = useRouter()
    const showPw = ref(false)
    const isLoading = ref(false)
    const form = reactive({ email: '', password: '' })
    const errors = reactive({ email: '', password: '', general: '' })

    const clearError = (field) => { errors[field] = ''; errors.general = '' }
    const goBack = () => router.push('/')

    const validate = () => {
      let ok = true
      if (!form.email.trim()) { errors.email = 'Email is required'; ok = false }
      else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) { errors.email = 'Enter a valid email'; ok = false }
      if (!form.password) { errors.password = 'Password is required'; ok = false }
      else if (form.password.length < 4) { errors.password = 'Password too short'; ok = false }
      return ok
    }

    const handleLogin = async () => {
      errors.email = ''; errors.password = ''; errors.general = ''
      if (!validate()) return
      isLoading.value = true
      await new Promise(r => setTimeout(r, 900))
      isLoading.value = false
      router.push('/dashboard')
    }

    return { form, errors, showPw, isLoading, goBack, handleLogin, clearError }
  }
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700&display=swap');

.login-root {
  position: relative;
  min-height: 100vh;
  background: #f5f6f7;
  display: flex; align-items: center; justify-content: center;
  overflow: hidden;
  font-family: 'Geist', sans-serif;
  padding: 24px;
}

/* ── Background ── */
.bg-blob {
  position: absolute; border-radius: 50%;
  filter: blur(90px); pointer-events: none;
}
.blob-1 {
  width: 480px; height: 400px;
  background: radial-gradient(circle, rgba(37,99,235,0.13) 0%, rgba(37,99,235,0.04) 60%, transparent 80%);
  top: -140px; left: -100px;
  animation: driftA 13s ease-in-out infinite alternate;
}
.blob-2 {
  width: 360px; height: 320px;
  background: radial-gradient(circle, rgba(59,130,246,0.1) 0%, rgba(37,99,235,0.03) 60%, transparent 80%);
  bottom: -100px; right: -70px;
  animation: driftB 16s ease-in-out infinite alternate;
}
@keyframes driftA { from { transform: translate(0,0); } to { transform: translate(35px, 22px); } }
@keyframes driftB { from { transform: translate(0,0); } to { transform: translate(-25px, -16px); } }
.bg-dots {
  position: absolute; inset: 0;
  background-image: radial-gradient(circle, rgba(37,99,235,0.1) 1px, transparent 1px);
  background-size: 28px 28px;
  mask-image: radial-gradient(ellipse 80% 70% at 50% 50%, black 25%, transparent 100%);
  pointer-events: none;
}

/* ── Card ── */
.login-card {
  position: relative; z-index: 10;
  width: 100%; max-width: 400px;
  background: #ffffff;
  border: 1.5px solid #e4e4e7;
  border-radius: 18px;
  padding: 38px 34px;
  box-shadow: 0 4px 24px rgba(37,99,235,0.08), 0 1px 4px rgba(0,0,0,0.05);
  animation: slideUp 0.5s cubic-bezier(0.34, 1.4, 0.64, 1) both;
}
@keyframes slideUp {
  from { opacity: 0; transform: translateY(24px) scale(0.97); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}

/* ── Back button ── */
.back-btn {
  position: absolute; top: 16px; left: 18px;
  display: inline-flex; align-items: center; gap: 5px;
  background: transparent; border: none;
  color: #71717a; cursor: pointer;
  font-size: 12px; font-family: 'Geist', sans-serif;
  padding: 4px 8px; border-radius: 6px;
  transition: color 0.15s, background 0.15s;
}
.back-btn svg { width: 13px; height: 13px; }
.back-btn:hover { color: #2563eb; background: #eff6ff; }

/* ── Header ── */
.card-header { text-align: center; margin-bottom: 26px; }
.card-logo {
  width: 64px; height: 64px; margin: 0 auto 14px;
  background: #eff6ff;
  border: 1.5px solid #dbeafe;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 2px 12px rgba(37,99,235,0.12);
}
.card-logo-img { width: 44px; height: auto; object-fit: contain; }
.card-title {
  font-size: 21px; font-weight: 700; letter-spacing: -0.03em;
  color: #09090b; margin-bottom: 4px;
}
.card-subtitle { font-size: 13px; color: #71717a; }

/* ── Form ── */
.login-form { display: flex; flex-direction: column; gap: 16px; }
.form-group { display: flex; flex-direction: column; gap: 5px; }
.form-label {
  font-size: 10.5px; font-weight: 600;
  color: #a1a1aa; letter-spacing: 0.7px; text-transform: uppercase;
}
.input-wrap { position: relative; }
.input-icon {
  position: absolute; left: 10px; top: 50%; transform: translateY(-50%);
  width: 14px; height: 14px; color: #a1a1aa; pointer-events: none;
}
.form-input {
  width: 100%; padding: 10px 10px 10px 34px;
  background: #f7f7f8;
  border: 1.5px solid #e4e4e7;
  border-radius: 8px; color: #09090b;
  font-size: 13px; font-family: 'Geist', sans-serif;
  outline: none;
  transition: border-color 0.18s, background 0.18s, box-shadow 0.18s;
}
.form-input::placeholder { color: #a1a1aa; }
.form-input:focus {
  border-color: #2563eb;
  background: #fff;
  box-shadow: 0 0 0 3px rgba(37,99,235,0.12);
}
.has-error .form-input { border-color: #dc2626; }
.has-error .form-input:focus { box-shadow: 0 0 0 3px rgba(220,38,38,0.1); }

.pw-toggle {
  position: absolute; right: 9px; top: 50%; transform: translateY(-50%);
  background: transparent; border: none; cursor: pointer;
  color: #a1a1aa; padding: 3px; display: flex; align-items: center;
  transition: color 0.15s;
}
.pw-toggle svg { width: 15px; height: 15px; }
.pw-toggle:hover { color: #2563eb; }
.error-msg { font-size: 11.5px; color: #dc2626; }

/* ── General error ── */
.general-error {
  display: flex; align-items: center; gap: 7px;
  padding: 9px 12px;
  background: #fee2e2; border: 1px solid #fca5a5;
  border-radius: 7px;
  font-size: 12.5px; color: #b91c1c;
}
.general-error svg { width: 14px; height: 14px; flex-shrink: 0; color: #dc2626; }

/* ── Submit ── */
.submit-btn {
  margin-top: 4px; width: 100%; padding: 12px;
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  color: #fff; border: none; border-radius: 8px;
  font-size: 14px; font-weight: 600; font-family: 'Geist', sans-serif;
  cursor: pointer;
  box-shadow: 0 3px 14px rgba(37,99,235,0.35), 0 1px 0 rgba(255,255,255,0.1) inset;
  transition: all 0.2s cubic-bezier(0.34, 1.4, 0.64, 1);
  position: relative; overflow: hidden;
}
.submit-btn::before {
  content: ''; position: absolute; inset: 0;
  background: linear-gradient(135deg, rgba(255,255,255,0.08), transparent);
}
.submit-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 22px rgba(37,99,235,0.45), 0 1px 0 rgba(255,255,255,0.12) inset;
}
.submit-btn:active:not(:disabled) { transform: translateY(0); }
.submit-btn:disabled { opacity: 0.65; cursor: not-allowed; }

.spinner-wrap { display: inline-flex; align-items: center; gap: 8px; }
.spinner {
  width: 14px; height: 14px;
  border: 2px solid rgba(255,255,255,0.3); border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Footer note ── */
.card-note {
  margin-top: 20px; text-align: center;
  font-size: 11px; color: #a1a1aa; line-height: 1.5;
}
</style>
