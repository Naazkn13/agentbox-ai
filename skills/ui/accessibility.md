---
id: accessibility
name: Web Accessibility (a11y) Expert
category: designing-ui
level1: "For WCAG 2.1 AA compliance, ARIA roles, keyboard navigation, screen readers, semantic HTML"
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 2
---

<!-- LEVEL 1 START -->
**Web Accessibility (a11y) Expert** — Activate for: WCAG 2.1 AA compliance, ARIA roles/labels, keyboard navigation, screen reader compatibility, focus management, color contrast, accessible forms, modal dialogs, skip links, VoiceOver, NVDA.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## Web Accessibility (a11y) Expert — Core Instructions

1. **Use semantic HTML before reaching for ARIA** — `<button>`, `<nav>`, `<main>`, `<article>`, `<label>` carry built-in roles and behavior for free; adding ARIA to a `<div>` requires you to manually replicate all that keyboard and screen-reader behavior.
2. **Every interactive element must be keyboard-reachable and operable** — tab order must follow visual reading order; never remove `:focus-visible` without a visible replacement; all actions triggerable by mouse must be triggerable by keyboard.
3. **Color contrast must meet 4.5:1 for normal text, 3:1 for large text and UI components** — test with a contrast checker; never rely on color alone to convey information (add icons, patterns, or labels).
4. **Every form input must have an associated `<label>`** — use `for`/`id` pairing or `aria-label`/`aria-labelledby`; `placeholder` is not a label; error messages must be associated with their input via `aria-describedby`.
5. **Modal dialogs must trap focus inside the dialog** — on open: move focus to the first focusable element inside; on close: return focus to the trigger element; Escape key must close the dialog.
6. **Live regions (`aria-live`) must be used for dynamic content** — use `aria-live="polite"` for non-critical updates (notifications); `aria-live="assertive"` only for urgent alerts; never for content that updates constantly.
7. **Test with an actual screen reader, not just automated tools** — run axe/Lighthouse for baseline, then manually test with NVDA+Chrome (Windows) or VoiceOver+Safari (macOS/iOS); automated tools catch ~30% of real issues.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## Web Accessibility (a11y) Expert — Full Reference

### Semantic HTML Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Page Title — Site Name</title>
</head>
<body>
  <!-- Skip navigation link — must be the first focusable element -->
  <a href="#main-content" class="skip-link">Skip to main content</a>

  <header role="banner">
    <nav aria-label="Primary navigation">
      <ul>
        <li><a href="/" aria-current="page">Home</a></li>
        <li><a href="/about">About</a></li>
      </ul>
    </nav>
  </header>

  <main id="main-content" tabindex="-1">   <!-- tabindex="-1" allows programmatic focus -->
    <article>
      <h1>Article Title</h1>
      <p>Content...</p>
    </article>

    <aside aria-label="Related links">
      <!-- Secondary content -->
    </aside>
  </main>

  <footer role="contentinfo">
    <nav aria-label="Footer navigation">...</nav>
  </footer>
</body>
</html>
```

### Skip Navigation Link

```css
/* Visually hidden but reachable by keyboard */
.skip-link {
  position: absolute;
  top: -100%;
  left: 0;
  padding: 0.5rem 1rem;
  background: #000;
  color: #fff;
  text-decoration: none;
  z-index: 9999;
}

.skip-link:focus {
  top: 0;   /* reveal on focus */
}
```

### Accessible Forms

```html
<!-- Input with label -->
<div class="field">
  <label for="email">Email address <span aria-hidden="true">*</span></label>
  <input
    id="email"
    type="email"
    name="email"
    autocomplete="email"
    required
    aria-required="true"
    aria-describedby="email-hint email-error"
  >
  <p id="email-hint" class="hint">We'll never share your email.</p>
  <p id="email-error" class="error" role="alert" hidden>
    Please enter a valid email address.
  </p>
</div>

<!-- Checkbox group with fieldset/legend -->
<fieldset>
  <legend>Notification preferences</legend>
  <label><input type="checkbox" name="notify" value="email"> Email</label>
  <label><input type="checkbox" name="notify" value="sms"> SMS</label>
</fieldset>

<!-- Select -->
<label for="country">Country</label>
<select id="country" name="country" autocomplete="country-name">
  <option value="">Select a country</option>
  <option value="us">United States</option>
</select>
```

### Focus Management (JavaScript)

```javascript
// Utility: get all focusable elements inside a container
const FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

function getFocusable(container) {
  return [...container.querySelectorAll(FOCUSABLE)];
}

// Move focus to an element, announcing it to screen readers
function moveFocus(element) {
  element.setAttribute("tabindex", "-1");
  element.focus();
}

// After client-side navigation: focus the <h1> or <main>
document.addEventListener("routeChange", () => {
  const heading = document.querySelector("h1") || document.querySelector("main");
  moveFocus(heading);
});
```

### Modal Dialog with Focus Trap

```javascript
class AccessibleModal {
  constructor(dialogEl, triggerEl) {
    this.dialog = dialogEl;
    this.trigger = triggerEl;
  }

  open() {
    this.dialog.removeAttribute("hidden");
    this.dialog.setAttribute("aria-modal", "true");

    // Move focus to first focusable element
    const focusable = getFocusable(this.dialog);
    focusable[0]?.focus();

    // Trap focus
    this.dialog.addEventListener("keydown", this._trapFocus);
    document.addEventListener("keydown", this._handleEscape);
  }

  close() {
    this.dialog.setAttribute("hidden", "");
    this.dialog.removeEventListener("keydown", this._trapFocus);
    document.removeEventListener("keydown", this._handleEscape);

    // Return focus to the element that opened the modal
    this.trigger.focus();
  }

  _trapFocus = (e) => {
    if (e.key !== "Tab") return;
    const focusable = getFocusable(this.dialog);
    const first = focusable[0];
    const last = focusable[focusable.length - 1];

    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  };

  _handleEscape = (e) => {
    if (e.key === "Escape") this.close();
  };
}
```

```html
<!-- Modal HTML -->
<div role="dialog" aria-modal="true" aria-labelledby="modal-title" hidden>
  <h2 id="modal-title">Confirm deletion</h2>
  <p>This action cannot be undone.</p>
  <button type="button" id="confirm-btn">Delete</button>
  <button type="button" id="cancel-btn">Cancel</button>
</div>
```

### ARIA Roles and Attributes Reference

```html
<!-- Button that expands content -->
<button aria-expanded="false" aria-controls="menu-list">Menu</button>
<ul id="menu-list" hidden>...</ul>

<!-- Live region for notifications -->
<div role="status" aria-live="polite" aria-atomic="true" class="visually-hidden">
  <!-- Inject success/info messages here dynamically -->
</div>

<!-- Alert for errors (assertive — interrupts screen reader immediately) -->
<div role="alert" aria-live="assertive">
  <!-- Inject urgent error messages here -->
</div>

<!-- Progress indicator -->
<div role="progressbar" aria-valuenow="65" aria-valuemin="0" aria-valuemax="100" aria-label="Upload progress">
  65%
</div>

<!-- Icon-only button -->
<button aria-label="Close dialog">
  <svg aria-hidden="true" focusable="false">...</svg>
</button>

<!-- Decorative image -->
<img src="decoration.png" alt="">

<!-- Informative image -->
<img src="chart.png" alt="Bar chart showing 40% increase in sales from Q1 to Q2 2024">
```

### Visually Hidden Utility Class

```css
/* Hides content visually but keeps it in the accessibility tree */
.visually-hidden,
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* Allow the element to become visible when focused (for skip links) */
.visually-hidden:focus,
.sr-only:focus {
  position: static;
  width: auto;
  height: auto;
  clip: auto;
  white-space: normal;
}
```

### Color Contrast Requirements (WCAG 2.1 AA)

```
Normal text (< 18pt / < 14pt bold):  4.5:1 minimum
Large text (≥ 18pt / ≥ 14pt bold):   3:1 minimum
UI components and graphical objects:  3:1 minimum
Disabled elements:                    No requirement

Tools:
- Chrome DevTools: CSS Overview > Colors
- https://webaim.org/resources/contrastchecker/
- axe DevTools browser extension
- Figma: Able plugin
```

### Screen Reader Testing Checklist

```
NVDA + Chrome (Windows):
  - NVDA+Space: browse vs forms mode
  - H: jump to next heading; 1-6: jump to heading level
  - Tab: navigate interactive elements
  - NVDA+F7: elements list (headings, links, form fields)

VoiceOver + Safari (macOS):
  - VO = Control+Option
  - VO+Right/Left: read next/previous element
  - VO+U: rotor (headings, links, landmarks)
  - VO+Space: activate

Manual test sequence:
  1. Tab through entire page — is every interactive element reachable?
  2. Activate all buttons/links with Enter/Space — do they work?
  3. Complete the primary form using only keyboard
  4. Open and close every modal — does focus trap and return correctly?
  5. Trigger form validation errors — are they announced?
  6. Check heading hierarchy with rotor (no skipped levels: h1 → h2 → h3)
```

### Anti-patterns to Avoid
- `<div onclick="...">` or `<span role="button">` without `tabindex="0"` and keyboard event handlers — not reachable or operable by keyboard
- `aria-label` on non-interactive elements like `<div>` or `<p>` — creates noise for screen readers without purpose
- `display: none` or `visibility: hidden` on content that should be screen-reader-visible — use `.visually-hidden` instead
- `tabindex` values greater than 0 — creates an unpredictable tab order; use 0 or -1 only
- Placeholder text as the only label — placeholder disappears on input, fails contrast, and is not reliably announced
- Triggering `aria-live` updates before the region is in the DOM — the region must exist in the DOM at page load even if empty
- Using `role="presentation"` or `aria-hidden="true"` on focusable elements — keyboard users will still reach them but screen readers will be silent
<!-- LEVEL 3 END -->
