---
id: css-layout
name: CSS Layout Expert (Flexbox/Grid/Tailwind)
category: designing-ui
level1: "For Flexbox, CSS Grid, Tailwind utilities, responsive design, dark mode, and common layout recipes"
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 1
---

<!-- LEVEL 1 START -->
**CSS Layout Expert (Flexbox/Grid/Tailwind)** — Activate for: Flexbox alignment, CSS Grid layouts, Tailwind utility classes, responsive breakpoints, dark mode, CSS custom properties, centering patterns, sidebar/card/form layout recipes.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## CSS Layout Expert — Core Instructions

1. **Choose Grid for two-dimensional layouts, Flexbox for one-dimensional** — rows AND columns = Grid; items in a single row or column = Flexbox.
2. **Use Tailwind utility classes in order: layout → spacing → typography → color → state** — consistency makes scanning easier and reduces merge conflicts.
3. **Mobile-first breakpoints** — write base styles for mobile, then add `sm:`, `md:`, `lg:` modifiers to override upward; never write desktop-first overrides.
4. **CSS custom properties for design tokens** — define colors, spacing, and radii as `--token` variables in `:root`; Tailwind `theme()` or `var()` both consume them.
5. **Dark mode via `dark:` variant** — configure `darkMode: 'class'` in `tailwind.config` and toggle `dark` on `<html>`; use `prefers-color-scheme` media query for pure-CSS fallback.
6. **Avoid magic numbers** — use Tailwind's spacing scale (`p-4` = 1rem) or named CSS variables; never write `margin: 13px` without a comment.
7. **`min-content`/`max-content`/`minmax()` over fixed pixel widths in Grid** — grids that use `minmax(0, 1fr)` handle overflow gracefully without `overflow: hidden` hacks.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## CSS Layout Expert — Full Reference

### Flexbox Cheat-Sheet
```css
.container {
  display: flex;
  flex-direction: row;          /* row | column | row-reverse | column-reverse */
  justify-content: space-between; /* main axis alignment */
  align-items: center;          /* cross axis alignment */
  flex-wrap: wrap;              /* allow wrapping */
  gap: 1rem;                    /* gutter between items */
}

.item {
  flex: 1 1 200px; /* grow shrink basis */
  align-self: flex-end; /* override align-items for one item */
}
```

### CSS Grid Cheat-Sheet
```css
.grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-template-rows: auto 1fr auto;
  gap: 1.5rem;
}

/* Named areas */
.layout {
  display: grid;
  grid-template-areas:
    "header header"
    "sidebar main"
    "footer footer";
  grid-template-columns: 250px 1fr;
  grid-template-rows: auto 1fr auto;
  min-height: 100vh;
}
.header  { grid-area: header; }
.sidebar { grid-area: sidebar; }
.main    { grid-area: main; }
.footer  { grid-area: footer; }

/* Auto-fill responsive cards — no media queries needed */
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
}
```

### Tailwind — Common Recipes
```html
<!-- Horizontal nav bar -->
<nav class="flex items-center justify-between px-6 h-16 border-b bg-white dark:bg-gray-900">
  <Logo />
  <div class="flex items-center gap-4">
    <NavLink />
  </div>
</nav>

<!-- Responsive 3-column grid -->
<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
  <Card />
</div>

<!-- Full-page centered layout -->
<div class="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-950">
  <div class="w-full max-w-md p-8 bg-white dark:bg-gray-800 rounded-2xl shadow-lg">
    <!-- form content -->
  </div>
</div>

<!-- Sidebar + main -->
<div class="flex h-screen overflow-hidden">
  <aside class="w-64 shrink-0 border-r overflow-y-auto">Sidebar</aside>
  <main class="flex-1 overflow-y-auto p-6">Content</main>
</div>
```

### Centering Patterns
```css
/* Flexbox center (most common) */
.center { display: flex; align-items: center; justify-content: center; }

/* Grid center */
.center { display: grid; place-items: center; }

/* Absolute center */
.center {
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
}

/* Tailwind: flex */
<div class="flex items-center justify-center">
/* Tailwind: grid */
<div class="grid place-items-center">
```

### CSS Custom Properties (Design Tokens)
```css
:root {
  --color-primary: #3b82f6;
  --color-surface: #ffffff;
  --color-text: #111827;
  --space-unit: 0.25rem;
  --radius-md: 0.5rem;
}

[data-theme="dark"] {
  --color-surface: #111827;
  --color-text: #f9fafb;
}

.card {
  background: var(--color-surface);
  color: var(--color-text);
  border-radius: var(--radius-md);
  padding: calc(var(--space-unit) * 4); /* = 1rem */
}
```

### Dark Mode (Tailwind)
```js
// tailwind.config.ts
export default {
  darkMode: 'class', // toggle by adding 'dark' class to <html>
  // ...
};
```
```tsx
// Toggle dark mode
document.documentElement.classList.toggle('dark');

// Usage in JSX
<div class="bg-white text-gray-900 dark:bg-gray-900 dark:text-gray-100">
```

### Responsive Breakpoints (Tailwind defaults)
```
sm:   640px+
md:   768px+
lg:   1024px+
xl:   1280px+
2xl:  1536px+
```

### Anti-patterns to Avoid
- Using `position: absolute` for layout flow — use Grid or Flexbox instead.
- Fixed pixel widths on containers — use `max-w-*` + `w-full` so content is responsive.
- Overriding Tailwind with `!important` — restructure component hierarchy instead.
- Using `vh` units for mobile heights without `dvh` fallback — `100vh` breaks on mobile browser chrome.
- Deeply nesting flex/grid without gap — use `gap` instead of margin on children to avoid double-spacing at edges.
<!-- LEVEL 3 END -->
