---
id: state-management
name: State Management Expert
category: designing-ui
level1: "For Redux Toolkit, Zustand, Jotai, React Query, and choosing the right state solution"
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 1
---

<!-- LEVEL 1 START -->
**State Management Expert** — Activate for: Redux Toolkit slices/thunks/RTK Query, Zustand stores, Jotai/Recoil atoms, deciding between local vs global state, avoiding over-engineering, React Query for server state.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## State Management Expert — Core Instructions

1. **Start with local state (`useState`/`useReducer`)** — only reach for a global store when genuinely multiple unrelated components need the same data; premature globalisation is the most common mistake.
2. **Separate server state from client state** — use React Query / TanStack Query for anything fetched from an API; don't duplicate server data into Redux/Zustand.
3. **Redux Toolkit only when you need its full feature set** — time-travel debugging, complex middleware, or an existing large Redux codebase; for new apps Zustand is lighter.
4. **RTK Query eliminates manual fetch boilerplate** — it handles loading/error states, caching, and refetching; prefer it over hand-rolled `createAsyncThunk` for API calls.
5. **Zustand stores should be small and focused** — one store per domain (auth, cart, UI preferences); avoid a single mega-store.
6. **Jotai atoms are ideal for fine-grained, independent pieces of state** — they only re-render components that consume that specific atom, unlike a large context value.
7. **Avoid storing derived data in the store** — compute it with `createSelector` (Redux), a getter function (Zustand), or a `derivedAtom` (Jotai) to stay DRY and consistent.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## State Management Expert — Full Reference

### Decision Tree
```
Is the data fetched from a server?
  YES → React Query / RTK Query (server state)
  NO  → Is it needed by only 1-2 closely related components?
          YES → useState / useReducer (local state)
          NO  → Is it simple global UI state (theme, sidebar open)?
                  YES → Zustand (lightweight)
                  NO  → Complex interactions, middleware, devtools?
                          YES → Redux Toolkit
                          NO  → Jotai atoms (atomic, fine-grained)
```

### Redux Toolkit — Slice + Thunk
```ts
// features/cart/cartSlice.ts
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';

export const fetchCart = createAsyncThunk('cart/fetch', async (userId: string) => {
  const res = await fetch(`/api/cart/${userId}`);
  return res.json() as Promise<CartItem[]>;
});

const cartSlice = createSlice({
  name: 'cart',
  initialState: { items: [] as CartItem[], status: 'idle' as 'idle' | 'loading' | 'error' },
  reducers: {
    addItem(state, action: PayloadAction<CartItem>) {
      state.items.push(action.payload); // Immer allows direct mutation
    },
    removeItem(state, action: PayloadAction<string>) {
      state.items = state.items.filter((i) => i.id !== action.payload);
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchCart.pending, (state) => { state.status = 'loading'; })
      .addCase(fetchCart.fulfilled, (state, action) => {
        state.items = action.payload;
        state.status = 'idle';
      })
      .addCase(fetchCart.rejected, (state) => { state.status = 'error'; });
  },
});

export const { addItem, removeItem } = cartSlice.actions;
export default cartSlice.reducer;
```

### RTK Query — API Slice
```ts
// services/productsApi.ts
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

export const productsApi = createApi({
  reducerPath: 'productsApi',
  baseQuery: fetchBaseQuery({ baseUrl: '/api/' }),
  tagTypes: ['Product'],
  endpoints: (builder) => ({
    getProducts: builder.query<Product[], void>({
      query: () => 'products',
      providesTags: ['Product'],
    }),
    createProduct: builder.mutation<Product, Partial<Product>>({
      query: (body) => ({ url: 'products', method: 'POST', body }),
      invalidatesTags: ['Product'], // auto-refetch getProducts
    }),
  }),
});

export const { useGetProductsQuery, useCreateProductMutation } = productsApi;

// Component usage
function ProductList() {
  const { data, isLoading, error } = useGetProductsQuery();
  const [create] = useCreateProductMutation();
  // ...
}
```

### Zustand
```ts
// stores/useAuthStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  user: User | null;
  token: string | null;
  login: (user: User, token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      login: (user, token) => set({ user, token }),
      logout: () => set({ user: null, token: null }),
    }),
    { name: 'auth-storage' } // persists to localStorage
  )
);

// Component
const { user, login, logout } = useAuthStore();
```

### React Query (TanStack Query)
```tsx
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// Fetch
function useUser(id: string) {
  return useQuery({
    queryKey: ['user', id],
    queryFn: () => fetch(`/api/users/${id}`).then((r) => r.json()),
    staleTime: 5 * 60 * 1000, // consider fresh for 5 min
  });
}

// Mutate + invalidate
function useUpdateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<User>) => fetch('/api/users', { method: 'PATCH', body: JSON.stringify(data) }),
    onSuccess: (_, variables) => {
      qc.invalidateQueries({ queryKey: ['user', variables.id] });
    },
  });
}
```

### Jotai — Atomic State
```ts
import { atom, useAtom, useAtomValue, useSetAtom } from 'jotai';

// Primitive atom
const countAtom = atom(0);

// Derived atom (read-only)
const doubledAtom = atom((get) => get(countAtom) * 2);

// Write atom
const incrementAtom = atom(null, (get, set) => {
  set(countAtom, get(countAtom) + 1);
});

// Components only re-render when their specific atom changes
function Counter() {
  const [count, setCount] = useAtom(countAtom);
  return <button onClick={() => setCount((c) => c + 1)}>{count}</button>;
}

function Display() {
  const doubled = useAtomValue(doubledAtom); // read-only
  return <p>{doubled}</p>;
}
```

### Memoized Selectors (Redux)
```ts
import { createSelector } from '@reduxjs/toolkit';

const selectCartItems = (state: RootState) => state.cart.items;

export const selectCartTotal = createSelector(
  selectCartItems,
  (items) => items.reduce((sum, item) => sum + item.price * item.qty, 0)
);
// Only recomputes when selectCartItems result changes
```

### Anti-patterns to Avoid
- Fetching data in Redux/Zustand when React Query could manage it — duplicates cache logic.
- Storing entire API responses in Redux state — use RTK Query cache instead.
- One giant Zustand store with 30 fields — split by domain for readability and performance.
- Calling `useStore()` without a selector in Zustand — subscribes the component to every state change; always pass a selector: `useStore((s) => s.user)`.
- Putting component UI state (modal open, input focus) into a global store — it belongs in local `useState`.
<!-- LEVEL 3 END -->
