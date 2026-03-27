---
id: playwright-testing
name: Playwright Testing
category: writing-tests
level1: "For writing Playwright browser automation and end-to-end tests"
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 1
---

<!-- LEVEL 1 START -->
**Playwright Testing** — Activate for: Playwright tests, page.goto, page.click, locator, expect(locator), network mocking, route.fulfill, trace viewer, screenshot comparison, page object model, parallel test execution.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## Playwright Testing — Core Instructions

1. **Use `locator()` not `$()` or `page.querySelector`** — locators are lazy and auto-retry; direct element handles are point-in-time snapshots that go stale.
2. **Prefer role-based and accessible locators** — `getByRole`, `getByLabel`, `getByPlaceholder` are resilient to DOM restructuring and double as accessibility checks.
3. **Always `await` Playwright calls** — Playwright is fully async; missing an `await` silently skips the action and causes phantom failures later.
4. **Use `page.route()` to intercept network requests** — never let E2E tests depend on real external APIs for deterministic test runs.
5. **Use the Page Object Model for anything accessed in more than one test** — encapsulate selectors and actions in a class; tests become readable and selectors are changed in one place.
6. **Enable traces in CI** — `trace: 'on-first-retry'` in `playwright.config.ts` gives a complete timeline, network log, and DOM snapshot for every failure.
7. **Run tests in parallel by default** — Playwright isolates tests in separate browser contexts; parallel execution is safe and dramatically faster.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## Playwright Testing — Full Reference

### Configuration

```ts
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 4 : undefined,
  reporter: [['html'], ['list']],
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',      // capture trace on first retry
    screenshot: 'only-on-failure',
    video: 'on-first-retry',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox',  use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit',   use: { ...devices['Desktop Safari'] } },
    { name: 'mobile',   use: { ...devices['iPhone 13'] } },
  ],
  webServer: {
    command: 'npm run start',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

### Locators — Preferred Strategies

```ts
// Role-based (most resilient)
await page.getByRole('button', { name: 'Submit' }).click();
await page.getByRole('heading', { name: 'Dashboard' }).isVisible();
await page.getByRole('textbox', { name: 'Email' }).fill('user@example.com');

// Label-based (great for forms)
await page.getByLabel('Password').fill('secret');

// Placeholder
await page.getByPlaceholder('Search products...').fill('widget');

// Text content
await page.getByText('Welcome, Alice').isVisible();

// Test ID (data-testid attribute — equivalent to Cypress data-cy)
await page.getByTestId('submit-btn').click();

// CSS / XPath — last resort
await page.locator('[data-cy="user-card"]').first().click();
await page.locator('table > tbody > tr').nth(2);
```

### Core Actions and Assertions

```ts
import { test, expect } from '@playwright/test';

test('user can log in', async ({ page }) => {
  await page.goto('/login');

  await page.getByLabel('Email').fill('alice@example.com');
  await page.getByLabel('Password').fill('secret');
  await page.getByRole('button', { name: 'Log in' }).click();

  await expect(page).toHaveURL(/.*dashboard/);
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
});

test('form validation shows errors', async ({ page }) => {
  await page.goto('/signup');
  await page.getByRole('button', { name: 'Create account' }).click();

  // Auto-retries until visible or timeout
  await expect(page.getByText('Email is required')).toBeVisible();
  await expect(page.getByText('Password is required')).toBeVisible();

  // Element count
  await expect(page.locator('[data-testid="field-error"]')).toHaveCount(2);
});

test('dropdown selection', async ({ page }) => {
  await page.goto('/settings');
  await page.getByLabel('Country').selectOption('US');
  await expect(page.getByLabel('Country')).toHaveValue('US');
});
```

### Network Mocking with page.route

```ts
test('shows user list from API', async ({ page }) => {
  // Mock before navigation
  await page.route('**/api/users', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        { id: 1, name: 'Alice', role: 'admin' },
        { id: 2, name: 'Bob',   role: 'user' },
      ]),
    });
  });

  await page.goto('/users');
  await expect(page.getByTestId('user-row')).toHaveCount(2);
  await expect(page.getByText('Alice')).toBeVisible();
});

test('shows error state when API fails', async ({ page }) => {
  await page.route('**/api/users', (route) => route.fulfill({
    status: 500,
    body: 'Internal Server Error',
  }));

  await page.goto('/users');
  await expect(page.getByTestId('error-banner')).toBeVisible();
});

// Assert the request that was sent
test('sends correct payload on form submit', async ({ page }) => {
  let requestBody: Record<string, unknown>;

  await page.route('**/api/users', async (route) => {
    requestBody = JSON.parse(route.request().postData() ?? '{}');
    await route.fulfill({ status: 201, body: JSON.stringify({ id: 99 }) });
  });

  await page.goto('/new-user');
  await page.getByLabel('Name').fill('Carol');
  await page.getByRole('button', { name: 'Save' }).click();

  expect(requestBody!.name).toBe('Carol');
});
```

### Page Object Model

```ts
// tests/pages/LoginPage.ts
import { type Page, type Locator, expect } from '@playwright/test';

export class LoginPage {
  readonly page: Page;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page           = page;
    this.emailInput     = page.getByLabel('Email');
    this.passwordInput  = page.getByLabel('Password');
    this.submitButton   = page.getByRole('button', { name: 'Log in' });
    this.errorMessage   = page.getByTestId('error-banner');
  }

  async goto() {
    await this.page.goto('/login');
  }

  async login(email: string, password: string) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }

  async expectError(message: string) {
    await expect(this.errorMessage).toBeVisible();
    await expect(this.errorMessage).toContainText(message);
  }
}
```

```ts
// tests/auth.spec.ts — clean tests using POM
import { test, expect } from '@playwright/test';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';

test('successful login redirects to dashboard', async ({ page }) => {
  const login = new LoginPage(page);
  const dashboard = new DashboardPage(page);

  await login.goto();
  await login.login('alice@example.com', 'secret');

  await expect(page).toHaveURL(/dashboard/);
  await dashboard.expectWelcomeMessage('Alice');
});

test('invalid credentials show error', async ({ page }) => {
  const login = new LoginPage(page);
  await login.goto();
  await login.login('wrong@example.com', 'bad');
  await login.expectError('Invalid email or password');
});
```

### Authentication State — storageState

```ts
// tests/global-setup.ts — run once, save auth state
import { chromium } from '@playwright/test';

async function globalSetup() {
  const browser = await chromium.launch();
  const page    = await browser.newPage();

  await page.goto('http://localhost:3000/login');
  await page.getByLabel('Email').fill('alice@example.com');
  await page.getByLabel('Password').fill('secret');
  await page.getByRole('button', { name: 'Log in' }).click();
  await page.waitForURL('**/dashboard');

  // Save cookies + localStorage to file
  await page.context().storageState({ path: 'tests/.auth/user.json' });
  await browser.close();
}

export default globalSetup;
```

```ts
// playwright.config.ts — use saved auth state in tests
export default defineConfig({
  globalSetup: './tests/global-setup.ts',
  projects: [
    {
      name: 'authenticated',
      use: { storageState: 'tests/.auth/user.json' },
      testMatch: '**/*.auth.spec.ts',
    },
  ],
});
```

### Trace Viewer and Debugging

```bash
# Run tests and always record traces
npx playwright test --trace on

# Open trace viewer after a run
npx playwright show-trace test-results/path-to/trace.zip

# Run in headed mode (watch the browser)
npx playwright test --headed

# Debug mode — opens inspector, pauses on first action
npx playwright test --debug

# Run a single test file
npx playwright test tests/auth.spec.ts

# Run tests matching a title pattern
npx playwright test -g "user can log in"
```

### Visual / Screenshot Comparison

```ts
test('homepage matches snapshot', async ({ page }) => {
  await page.goto('/');
  // First run creates the baseline; subsequent runs compare
  await expect(page).toHaveScreenshot('homepage.png', {
    maxDiffPixels: 100,   // allow minor rendering differences
  });
});

// Update snapshots after intentional UI changes
// npx playwright test --update-snapshots
```

### Anti-patterns to Avoid
- Using `page.$()` or `page.waitForSelector()` instead of `locator()` — locators have built-in retry; `$()` is a point-in-time query that goes stale.
- Forgetting `await` on Playwright calls — the action silently does not happen; the test may pass or fail for the wrong reason.
- Hard-coding `page.waitForTimeout(2000)` — use `waitForURL`, `waitForResponse`, or `expect(locator).toBeVisible()` instead.
- Sharing browser context between tests — Playwright creates isolated contexts per test for good reason; sharing state makes failures cascade.
- Storing selectors as bare strings scattered across tests — put them in a Page Object; one place to update when the UI changes.
<!-- LEVEL 3 END -->
