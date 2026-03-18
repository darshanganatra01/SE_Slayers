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

