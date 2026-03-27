---
id: nextjs-patterns
name: Next.js Expert
category: designing-ui
level1: "For Next.js App Router, Server Components, server actions, routing, and data fetching patterns"
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 1
---

<!-- LEVEL 1 START -->
**Next.js Expert** — Activate for: App Router vs Pages Router decisions, Server Components, Client Components, server actions, `getServerSideProps`/`getStaticProps`, dynamic routes, image optimization, middleware, layout nesting.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## Next.js Expert — Core Instructions

1. **Default to Server Components** — only add `"use client"` when you need interactivity, browser APIs, or React hooks; keep the client boundary as low in the tree as possible.
2. **Server actions for mutations** — use `"use server"` functions instead of API routes for form submissions and data mutations in the App Router.
3. **Never fetch in Client Components when a Server Component can do it** — avoids client-side waterfalls and exposes no secrets to the browser.
4. **Use `next/image` for all images** — always provide `width`/`height` or `fill` + `sizes` to prevent layout shift; never use raw `<img>` tags.
5. **Dynamic routes: use `generateStaticParams` for static generation** — export it from `[slug]/page.tsx` so Next.js pre-renders at build time instead of on every request.
6. **Parallel and Intercepting routes are powerful but complex** — use them for modals and split-view UIs; use `@slot` folders and `(.)route` conventions precisely.
7. **Middleware runs on every matched request at the edge** — keep it lightweight; avoid heavy computation, database calls, or large imports.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## Next.js Expert — Full Reference

### App Router Folder Structure
```
app/
  layout.tsx          ← root layout (HTML shell, always Server Component)
  page.tsx            ← home route
  (auth)/             ← route group (no URL segment)
    login/page.tsx
    register/page.tsx
  dashboard/
    layout.tsx        ← nested layout
    page.tsx          ← /dashboard
    [id]/
      page.tsx        ← /dashboard/:id
  api/
    webhook/route.ts  ← API route handler
```

### Server vs Client Components
```tsx
// app/products/page.tsx — Server Component (default)
// Can use async/await, access DB, read env secrets
export default async function ProductsPage() {
  const products = await db.query('SELECT * FROM products');
  return <ProductList products={products} />;
}

// app/products/AddToCartButton.tsx — Client Component
"use client";
import { useState } from 'react';

export function AddToCartButton({ productId }: { productId: string }) {
  const [loading, setLoading] = useState(false);
  return (
    <button onClick={() => { setLoading(true); addToCart(productId); }}>
      {loading ? 'Adding...' : 'Add to Cart'}
    </button>
  );
}
```

### Server Actions
```tsx
// app/actions.ts
"use server";
import { revalidatePath } from 'next/cache';

export async function createPost(formData: FormData) {
  const title = formData.get('title') as string;
  await db.insert({ title, createdAt: new Date() });
  revalidatePath('/posts'); // purge cache for this path
}

// app/posts/new/page.tsx — use directly in JSX
import { createPost } from '../actions';

export default function NewPostPage() {
  return (
    <form action={createPost}>
      <input name="title" />
      <button type="submit">Create</button>
    </form>
  );
}
```

### Data Fetching & Caching
```tsx
// Force dynamic (no cache)
const data = await fetch('https://api.example.com/data', { cache: 'no-store' });

// Static with revalidation (ISR)
const data = await fetch('https://api.example.com/data', {
  next: { revalidate: 60 }, // seconds
});

// generateStaticParams for dynamic routes
// app/blog/[slug]/page.tsx
export async function generateStaticParams() {
  const posts = await getPosts();
  return posts.map((p) => ({ slug: p.slug }));
}

export default async function BlogPost({ params }: { params: { slug: string } }) {
  const post = await getPost(params.slug);
  return <article>{post.content}</article>;
}
```

### Dynamic Routes & Catch-All
```tsx
// app/docs/[...slug]/page.tsx  — catch-all
export default function DocsPage({ params }: { params: { slug: string[] } }) {
  // /docs/a/b/c → params.slug = ['a', 'b', 'c']
  return <div>{params.slug.join('/')}</div>;
}

// app/docs/[[...slug]]/page.tsx — optional catch-all (matches /docs too)
```

### Image Optimization
```tsx
import Image from 'next/image';

// Fixed dimensions
<Image src="/hero.jpg" alt="Hero" width={1200} height={600} priority />

// Responsive fill (parent must be position: relative with a height)
<div style={{ position: 'relative', height: '400px' }}>
  <Image src="/banner.jpg" alt="Banner" fill sizes="100vw" style={{ objectFit: 'cover' }} />
</div>

// Remote images — must whitelist domain in next.config.ts
// next.config.ts
export default {
  images: {
    remotePatterns: [{ hostname: 'cdn.example.com' }],
  },
};
```

### Middleware
```ts
// middleware.ts (root of project)
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const token = request.cookies.get('token')?.value;
  if (!token && request.nextUrl.pathname.startsWith('/dashboard')) {
    return NextResponse.redirect(new URL('/login', request.url));
  }
  return NextResponse.next();
}

export const config = {
  matcher: ['/dashboard/:path*', '/admin/:path*'],
};
```

### Pages Router (Legacy) — getServerSideProps / getStaticProps
```tsx
// pages/products/[id].tsx
export async function getStaticProps({ params }) {
  const product = await fetchProduct(params.id);
  return { props: { product }, revalidate: 60 };
}

export async function getStaticPaths() {
  const ids = await fetchAllIds();
  return { paths: ids.map((id) => ({ params: { id } })), fallback: 'blocking' };
}

export default function ProductPage({ product }) {
  return <div>{product.name}</div>;
}
```

### Anti-patterns to Avoid
- Adding `"use client"` to layout or page files unnecessarily — push it down to the interactive leaf component.
- Calling `fetch` inside a Client Component on mount when a Server Component could fetch instead.
- Using `router.push` from a Server Component — routing mutations require a Client Component or redirect() from `next/navigation`.
- Storing secrets in `NEXT_PUBLIC_` env variables — those are bundled into the client.
- Nesting `<html>` or `<body>` in a child layout — only the root layout should include them.
<!-- LEVEL 3 END -->
