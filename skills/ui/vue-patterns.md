---
id: vue-patterns
name: Vue.js Expert
category: designing-ui
level1: "For Vue 3 Composition API, reactivity, components, Pinia, Vue Router, and script setup patterns"
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 1
---

<!-- LEVEL 1 START -->
**Vue.js Expert** — Activate for: Vue 3 Composition API, `ref`/`reactive`/`computed`/`watch`, component props/emits, `provide`/`inject`, Pinia state management, Vue Router navigation, `<script setup>` syntax.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## Vue.js Expert — Core Instructions

1. **Use `<script setup>` syntax** — it is the recommended, terser form of the Composition API; all top-level bindings are automatically available in the template.
2. **`ref` for primitives, `reactive` for objects** — but prefer `ref` throughout for consistency; unwrap with `.value` in `<script>`, not in `<template>`.
3. **`computed` is lazy and cached** — use it for derived values instead of methods called in the template; avoid side effects inside `computed`.
4. **Define props and emits with TypeScript generics** — use `defineProps<{ ... }>()` and `defineEmits<{ ... }>()` for full type safety without runtime validators.
5. **`watchEffect` for automatic dependency tracking, `watch` for explicit sources** — use `watch` when you need old/new values or want to fire only on specific reactive changes.
6. **Pinia over Vuex** — use `defineStore` with the Composition API style; keep stores focused on a single domain (auth, cart, notifications).
7. **`provide`/`inject` for deep prop passing** — create a typed injection key with `InjectionKey<T>` to preserve type safety across the provide/inject boundary.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## Vue.js Expert — Full Reference

### Script Setup Basics
```vue
<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue';

const count = ref(0);
const doubled = computed(() => count.value * 2);

watch(count, (newVal, oldVal) => {
  console.log(`changed from ${oldVal} to ${newVal}`);
});

onMounted(() => {
  console.log('component mounted');
});
</script>

<template>
  <button @click="count++">{{ count }} (doubled: {{ doubled }})</button>
</template>
```

### Props & Emits with TypeScript
```vue
<script setup lang="ts">
const props = defineProps<{
  title: string;
  count?: number; // optional
}>();

const emit = defineEmits<{
  update: [value: number];
  close: [];
}>();

function increment() {
  emit('update', (props.count ?? 0) + 1);
}
</script>
```

### ref vs reactive
```ts
// ref — use for primitives and when you need to reassign
const name = ref('Alice');
name.value = 'Bob';

// reactive — use for plain objects (loses reactivity if destructured!)
const state = reactive({ x: 0, y: 0 });
state.x = 10; // OK
const { x } = state; // BREAKS reactivity — use toRefs()

// Safe destructure
import { toRefs } from 'vue';
const { x, y } = toRefs(state);
```

### Composables (Custom Hooks)
```ts
// composables/useFetch.ts
import { ref, watchEffect } from 'vue';

export function useFetch<T>(url: string) {
  const data = ref<T | null>(null);
  const error = ref<Error | null>(null);
  const loading = ref(false);

  watchEffect(async () => {
    loading.value = true;
    error.value = null;
    try {
      const res = await fetch(url);
      data.value = await res.json();
    } catch (e) {
      error.value = e as Error;
    } finally {
      loading.value = false;
    }
  });

  return { data, error, loading };
}

// Usage
const { data, loading } = useFetch<User[]>('/api/users');
```

### Provide / Inject with Typed Keys
```ts
// keys.ts
import type { InjectionKey, Ref } from 'vue';
export const ThemeKey: InjectionKey<Ref<'light' | 'dark'>> = Symbol('theme');

// Parent.vue
import { provide, ref } from 'vue';
import { ThemeKey } from './keys';
const theme = ref<'light' | 'dark'>('light');
provide(ThemeKey, theme);

// DeepChild.vue
import { inject } from 'vue';
import { ThemeKey } from './keys';
const theme = inject(ThemeKey); // type: Ref<'light' | 'dark'> | undefined
```

### Pinia Store
```ts
// stores/useCartStore.ts
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

export const useCartStore = defineStore('cart', () => {
  const items = ref<CartItem[]>([]);

  const total = computed(() =>
    items.value.reduce((sum, item) => sum + item.price * item.qty, 0)
  );

  function addItem(item: CartItem) {
    const existing = items.value.find((i) => i.id === item.id);
    if (existing) existing.qty++;
    else items.value.push({ ...item, qty: 1 });
  }

  function removeItem(id: string) {
    items.value = items.value.filter((i) => i.id !== id);
  }

  return { items, total, addItem, removeItem };
});

// Component usage
const cart = useCartStore();
cart.addItem(product);
console.log(cart.total);
```

### Vue Router
```ts
// router/index.ts
import { createRouter, createWebHistory } from 'vue-router';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: () => import('@/views/Home.vue') },
    {
      path: '/dashboard',
      component: () => import('@/views/Dashboard.vue'),
      meta: { requiresAuth: true },
      children: [
        { path: 'settings', component: () => import('@/views/Settings.vue') },
      ],
    },
  ],
});

// Navigation guard
router.beforeEach((to, _from) => {
  const auth = useAuthStore();
  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    return { path: '/login', query: { redirect: to.fullPath } };
  }
});

// In component
import { useRouter, useRoute } from 'vue-router';
const router = useRouter();
const route = useRoute();
router.push({ name: 'dashboard' });
console.log(route.params.id);
```

### Anti-patterns to Avoid
- Destructuring `reactive()` objects without `toRefs()` — breaks reactivity silently.
- Using `watch` with `immediate: true` when `watchEffect` is clearer.
- Mutating props directly — always emit an event to the parent instead.
- Storing non-serializable values (class instances, DOM refs) in Pinia — state should be plain JSON-serializable objects.
- Using `v-if` and `v-for` on the same element — always put `v-if` on a wrapping element or use `<template>`.
<!-- LEVEL 3 END -->
