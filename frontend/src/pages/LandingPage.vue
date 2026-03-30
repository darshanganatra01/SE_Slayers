<template>
  <div class="landing-root">
    <!-- Soft background blobs -->
    <div class="bg-blob blob-1"></div>
    <div class="bg-blob blob-2"></div>
    <!-- Subtle dot grid -->
    <div class="bg-dots"></div>

    <!-- Main content -->
    <div class="landing-content">
      <!-- Logo -->
      <div class="logo-card">
        <div class="logo-ring">
          <img src="/metro-removebg-preview.png" class="logo-img" alt="Metro Logo" />
        </div>
      </div>

      <!-- Brand text with character animation -->
      <div class="brand-block">
        <h1 class="brand-name">
          <span
            v-for="(char, i) in 'Sales Agency'.split('')"
            :key="i"
            class="brand-char"
            :style="{ animationDelay: `${0.5 + i * 0.055}s` }"
          >{{ char === ' ' ? '\u00A0' : char }}</span>
        </h1>
        <p class="brand-tagline">
          <span class="tagline-line">Streamline your operations.</span>
        </p>
      </div>

      <!-- CTA Button -->
      <div class="cta-block">
        <button class="cta-btn" @click="goToLogin">
          <span>Sign In to Dashboard</span>
          <svg class="cta-arrow" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clip-rule="evenodd" />
          </svg>
        </button>
      </div>

      <!-- Feature badges — no analytics -->
      <div class="feature-badges">
        <div class="badge" v-for="(f, i) in features" :key="i" :style="{ animationDelay: `${1.4 + i * 0.1}s` }">
          <span class="badge-icon">{{ f.icon }}</span>
          <span>{{ f.label }}</span>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <footer class="landing-footer">
      <span>© 2025 Metro Sales Agency</span>
      <span class="footer-dot">·</span>
      <span>All rights reserved</span>
    </footer>
  </div>
</template>

<script>
import { useRouter } from 'vue-router'

export default {
  name: 'LandingPage',
  setup() {
    const router = useRouter()
    const goToLogin = () => router.push('/login')
    const features = [
      { icon: '📦', label: 'Inventory Control' },
      { icon: '🤝', label: 'Vendor Management' },
      { icon: '🛒', label: 'Order Tracking' },
    ]
    return { goToLogin, features }
  }
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700;800&display=swap');

.landing-root {
  position: relative;
  min-height: 100vh;
  background: #f5f6f7;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  font-family: 'Geist', sans-serif;
}

/* ── Soft background blobs ── */
.bg-blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(90px);
  pointer-events: none;
}
.blob-1 {
  width: 560px; height: 480px;
  background: radial-gradient(circle, rgba(37,99,235,0.13) 0%, rgba(37,99,235,0.04) 60%, transparent 80%);
  top: -160px; left: -120px;
  animation: driftA 12s ease-in-out infinite alternate;
}
.blob-2 {
  width: 420px; height: 380px;
  background: radial-gradient(circle, rgba(59,130,246,0.11) 0%, rgba(37,99,235,0.03) 60%, transparent 80%);
  bottom: -120px; right: -80px;
  animation: driftB 15s ease-in-out infinite alternate;
}
@keyframes driftA {
  from { transform: translate(0, 0); }
  to   { transform: translate(40px, 28px); }
}
@keyframes driftB {
  from { transform: translate(0, 0); }
  to   { transform: translate(-30px, -20px); }
}

/* ── Dot grid ── */
.bg-dots {
  position: absolute; inset: 0;
  background-image: radial-gradient(circle, rgba(37,99,235,0.12) 1px, transparent 1px);
  background-size: 28px 28px;
  mask-image: radial-gradient(ellipse 72% 65% at 50% 50%, black 30%, transparent 100%);
  pointer-events: none;
}

/* ── Content ── */
.landing-content {
  position: relative; z-index: 10;
  display: flex; flex-direction: column; align-items: center;
  gap: 30px; padding: 40px 24px; text-align: center;
}

/* ── Logo ── */
.logo-card {
  animation: popIn 0.65s cubic-bezier(0.34, 1.56, 0.64, 1) 0.1s both;
}
.logo-ring {
  width: 148px; height: 148px; border-radius: 50%;
  background: #ffffff;
  border: 2px solid #dbeafe;
  display: flex; align-items: center; justify-content: center;
  box-shadow:
    0 0 0 8px rgba(37,99,235,0.06),
    0 8px 32px rgba(37,99,235,0.15),
    0 2px 8px rgba(0,0,0,0.05);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.logo-ring:hover {
  transform: scale(1.05) translateY(-2px);
  box-shadow:
    0 0 0 10px rgba(37,99,235,0.09),
    0 16px 40px rgba(37,99,235,0.22),
    0 2px 8px rgba(0,0,0,0.06);
}
.logo-img {
  width: 138px; height: auto; object-fit: contain;
}

/* ── Brand text ── */
.brand-block {
  display: flex; flex-direction: column; align-items: center; gap: 12px;
}
.brand-name {
  font-size: clamp(2.2rem, 6vw, 3.6rem);
  font-weight: 800; letter-spacing: -0.04em; line-height: 1.1;
  display: flex; flex-wrap: wrap; justify-content: center;
}
.brand-char {
  display: inline-block;
  color: transparent;
  background: linear-gradient(135deg, #1e40af 0%, #2563eb 45%, #3b82f6 100%);
  -webkit-background-clip: text; background-clip: text;
  opacity: 0; transform: translateY(18px);
  animation: charFall 0.45s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}
@keyframes charFall {
  to { opacity: 1; transform: translateY(0); }
}

.brand-tagline { display: flex; flex-direction: column; gap: 2px; }
.tagline-line {
  font-size: 15px; font-weight: 400; letter-spacing: 0.01em;
  color: #71717a;
  opacity: 0; transform: translateY(8px);
  animation: fadeUp 0.55s ease 1.35s forwards;
}
.tagline-line.delay-1 { animation-delay: 1.55s; }

@keyframes fadeUp {
  to { opacity: 1; transform: translateY(0); }
}

/* ── CTA ── */
.cta-block {
  display: flex; flex-direction: column; align-items: center; gap: 10px;
  opacity: 0;
  animation: fadeUp 0.55s ease 1.75s forwards;
}
.cta-btn {
  display: inline-flex; align-items: center; gap: 10px;
  padding: 13px 30px;
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  color: #fff; border: none; border-radius: 50px;
  font-size: 15px; font-weight: 600; font-family: 'Geist', sans-serif;
  cursor: pointer; letter-spacing: -0.01em;
  box-shadow: 0 4px 20px rgba(37,99,235,0.38), 0 1px 0 rgba(255,255,255,0.12) inset;
  transition: all 0.22s cubic-bezier(0.34, 1.56, 0.64, 1);
  position: relative; overflow: hidden;
}
.cta-btn::before {
  content: ''; position: absolute; top: 0; left: -100%;
  width: 100%; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.18), transparent);
  transition: left 0.45s ease;
}
.cta-btn:hover::before { left: 100%; }
.cta-btn:hover {
  transform: translateY(-2px) scale(1.03);
  box-shadow: 0 8px 32px rgba(37,99,235,0.5), 0 1px 0 rgba(255,255,255,0.14) inset;
}
.cta-btn:active { transform: translateY(0) scale(0.99); }
.cta-arrow { width: 17px; height: 17px; transition: transform 0.2s ease; flex-shrink: 0; }
.cta-btn:hover .cta-arrow { transform: translateX(4px); }
.cta-hint { font-size: 11.5px; color: #a1a1aa; letter-spacing: 0.03em; }

/* ── Feature badges ── */
.feature-badges {
  display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; max-width: 420px;
}
.badge {
  display: flex; align-items: center; gap: 6px;
  padding: 7px 14px;
  background: #ffffff;
  border: 1.5px solid #dbeafe;
  border-radius: 50px;
  font-size: 12.5px; color: #3f3f46;
  box-shadow: 0 1px 4px rgba(37,99,235,0.07);
  opacity: 0; transform: translateY(10px);
  animation: fadeUp 0.45s ease forwards;
  transition: all 0.2s ease;
}
.badge:hover {
  background: #eff6ff;
  border-color: #93c5fd;
  color: #1d4ed8;
  box-shadow: 0 2px 10px rgba(37,99,235,0.14);
  transform: translateY(-1px);
}
.badge-icon { font-size: 14px; }

/* ── Footer ── */
.landing-footer {
  position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%);
  display: flex; gap: 10px;
  font-size: 11.5px; color: #a1a1aa; white-space: nowrap;
}
.footer-dot { opacity: 0.45; }

@keyframes popIn {
  from { opacity: 0; transform: scale(0.72); }
  to   { opacity: 1; transform: scale(1); }
}
</style>
