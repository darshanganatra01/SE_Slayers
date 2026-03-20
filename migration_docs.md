# Migration Documentation

This file documents all the changes that were made outside of the `src/customer_dashboard` directory to support the migrated Vue 3 components from `vue-craft-studio`.

## Dependencies Added
To support the Vue 3 and Tailwind CSS components, the following dependencies were added to `package.json`:

**Production Dependencies:**
- `class-variance-authority`
- `clsx`
- `tailwind-merge`
- `tailwindcss-animate`
- `lucide-vue-next`
- `@vueuse/core`

**Development Dependencies:**
- `tailwindcss`
- `postcss`
- `autoprefixer`
- `typescript`
- `vue-tsc`
- `@types/node`

## Configuration Files Created/Modified
- `tailwind.config.js`: Added to configure Tailwind design tokens used by the components.
- `postcss.config.js`: Added to process Tailwind CSS.
- `vite.config.js`: Added a new Vite alias `@cd` pointing to `src/customer_dashboard/`. This allows the migrated TypeScript/Vue files, which originally used `@/` as a root alias in their own project, to correctly resolve all their internal imports within the `customer_dashboard` folder without conflicting with the existing `@/` alias (which points to `src/`).
- `src/main.js`: Added `import './customer_dashboard/index.css'` to load the Tailwind CSS base styles for the customer dashboard.
- `src/router/index.js`: Added a nested route block under `/store` path for all customer dashboard pages (store index, product detail, cart, checkout, orders, transaction detail, login, register, not-found).

## Import Path Changes in Customer Dashboard
All internal imports within `src/customer_dashboard/**` that originally used `@/` were updated to use `@cd/` to point correctly to the customer dashboard folder. This was done to avoid collision with the existing `@` → `src/` alias used by the rest of the SE_Slayers project. All router navigation calls (e.g. `router.push('/')` and `to="/"`) were also prefixed with `/store` to match the nested route.

## Notes
The `SE_Slayers` project natively uses JavaScript, but we introduced `typescript` and `vue-tsc` to the `devDependencies` since `vue-craft-studio` uses TypeScript within its `<script lang="ts">` Vue files. This allows Vite to process the files correctly during development.

The customer dashboard runs as a nested route under `/store` (e.g. `/store`, `/store/cart`, `/store/checkout`) to avoid URL path conflicts with other team members' modules.

---

## UI Refinements Applied

1. **Global Zoom (+20%)**: Added `html { font-size: 120%; }` to `src/customer_dashboard/index.css` to scale the UI uniformly. This uses `rem` units to ensure accessibility and layout consistency across the store.
2. **Order Timeline Fix**: Added the missing `success` color definition to `tailwind.config.js`. This restores the green circles and tracking lines in the order history timeline.
3. **Hidden Stock Information**: 
   - Removed the "stock quantity" label from the product detail page.
   - Removed "Only X left" low-stock warnings from product cards.
   - Simplified increment logic to remove stock-based caps (since stock is hidden).
4. **Redirect Fix (Checkout)**: Fixed a bug in `Checkout.vue` where clearing the cart after an order would trigger an immediate redirect to an unprefixed `/cart` route. It now correctly redirects to `/store/cart` (or continues to the intended `/store/orders`).

---

## Sidebar Shell Isolation

### Problem
The SE_Slayers root `src/App.vue` wraps every route in a fixed sidebar shell (`AppSidebar` + full-height flex container). When the customer dashboard renders under `/store`, it was being squeezed inside this shell, making the storefront unusable.

### Solution Applied
Two minimal, additive changes were made:

**1. `src/router/index.js`** — added `meta: { hideShell: true }` to the `/store` route:
```js
{
  path: '/store',
  meta: { hideShell: true },   // ← added
  component: () => import('../customer_dashboard/App.vue'),
  children: [ ... ]
}
```

**2. `src/App.vue`** — template and script changes:
```diff
- <template>
-   <div class="shell">
-     <AppSidebar :order-count="orderStore.inprocessCount" />
-     <router-view />
-   </div>
- </template>
+ <template>
+   <template v-if="route.meta.hideShell">
+     <router-view />
+   </template>
+   <div v-else class="shell">
+     <AppSidebar :order-count="orderStore.inprocessCount" />
+     <router-view />
+   </div>
+ </template>

+ import { useRoute } from 'vue-router'
  ...
  setup() {
    const orderStore = useOrderStore()
+   const route = useRoute()
+   return { orderStore, route }
  }
```

When `hideShell` is true the entire `.shell` flex wrapper is bypassed, giving the customer dashboard the full viewport. When it is false (all other team routes), the template is identical to the original.

**Impact on other team members:** Zero. All existing routes (`/dashboard`, `/orders`, `/customers`, `/inventory`, `/vendors`) do **not** have `meta.hideShell` set, so they fall into the `v-else` branch — the shell and sidebar render exactly as before.

---

### How to Revert This Change

**Step 1 — `src/router/index.js`:** Remove the `meta: { hideShell: true },` line from the `/store` route.

**Step 2 — `src/App.vue`:** Revert the template back to:
```html
<template>
  <div class="shell">
    <AppSidebar :order-count="orderStore.inprocessCount" />
    <router-view />
  </div>
</template>
```
And remove `import { useRoute } from 'vue-router'`, `const route = useRoute()`, and `route` from the `return` object in `setup()`.

