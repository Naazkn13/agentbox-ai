---
id: cypress-e2e
name: Cypress E2E Testing
category: writing-tests
level1: "For writing Cypress end-to-end and component tests"
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 1
---

<!-- LEVEL 1 START -->
**Cypress E2E Testing** — Activate for: Cypress tests, cy.get, cy.intercept, data-cy selectors, custom commands, fixtures, component testing, flaky tests, API mocking in Cypress, end-to-end test setup.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## Cypress E2E Testing — Core Instructions

1. **Select elements with `data-cy` attributes, never CSS classes or IDs** — classes and IDs change with styling and refactoring; `data-cy` attributes are explicit test contracts.
2. **Use `cy.intercept` to stub API calls** — never let E2E tests depend on real backend responses for happy-path assertions. Use real requests only for integration smoke tests.
3. **Never use `cy.wait(N)` with arbitrary milliseconds** — always wait for a specific network event, element, or assertion: `cy.wait('@alias')` or `cy.contains('Loading...').should('not.exist')`.
4. **Chain assertions on the subject, not in a `.then()`** — Cypress commands are async queues; `.should()` retries automatically, `.then()` does not.
5. **Put reusable actions in custom commands in `cypress/support/commands.js`** — login flows, form fills, and navigation sequences used in multiple specs belong in commands, not in `beforeEach`.
6. **Use fixtures for static test data, not hardcoded strings** — `cy.fixture('user.json')` loads from `cypress/fixtures/`; data lives in one place.
7. **Group with `describe` / `context`, set up state with `beforeEach`** — avoid test interdependence; every `it` block should work in isolation.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## Cypress E2E Testing — Full Reference

### Project Structure

```
cypress/
├── e2e/
│   ├── auth/
│   │   ├── login.cy.js
│   │   └── signup.cy.js
│   └── dashboard/
│       └── dashboard.cy.js
├── fixtures/
│   ├── user.json
│   └── products.json
├── support/
│   ├── commands.js       # custom commands
│   └── e2e.js            # global hooks, imported automatically
└── cypress.config.js
```

```js
// cypress.config.js
const { defineConfig } = require('cypress');

module.exports = defineConfig({
  e2e: {
    baseUrl: 'http://localhost:3000',
    viewportWidth: 1280,
    viewportHeight: 720,
    video: true,
    screenshotOnRunFailure: true,
    retries: { runMode: 2, openMode: 0 },
    setupNodeEvents(on, config) {
      // register plugins here
    },
  },
});
```

### Selectors — data-cy Attributes

```html
<!-- In your React/Vue/HTML components -->
<button data-cy="submit-btn">Submit</button>
<input  data-cy="email-input" type="email" />
<div    data-cy="user-card"   class="card">...</div>
<li     data-cy="product-item">...</li>
```

```js
// In Cypress tests
cy.get('[data-cy="submit-btn"]').click();
cy.get('[data-cy="email-input"]').type('user@example.com');
cy.get('[data-cy="user-card"]').should('be.visible').within(() => {
  cy.contains('Alice');
});
cy.get('[data-cy="product-item"]').should('have.length', 5);
```

### Core Commands

```js
describe('User Authentication', () => {
  beforeEach(() => {
    cy.visit('/login');
  });

  it('logs in with valid credentials', () => {
    cy.get('[data-cy="email-input"]').type('alice@example.com');
    cy.get('[data-cy="password-input"]').type('secret{enter}');  // {enter} submits

    cy.url().should('include', '/dashboard');
    cy.get('[data-cy="welcome-msg"]').should('contain', 'Welcome, Alice');
  });

  it('shows error for invalid credentials', () => {
    cy.get('[data-cy="email-input"]').type('wrong@example.com');
    cy.get('[data-cy="password-input"]').type('badpassword');
    cy.get('[data-cy="login-btn"]').click();

    cy.get('[data-cy="error-banner"]')
      .should('be.visible')
      .and('contain', 'Invalid email or password');
  });
});
```

### cy.intercept — API Mocking

```js
describe('Dashboard', () => {
  beforeEach(() => {
    // Stub GET /api/users before visiting the page
    cy.intercept('GET', '/api/users', { fixture: 'users.json' }).as('getUsers');
    cy.visit('/dashboard');
    cy.wait('@getUsers');   // wait for the stubbed request
  });

  it('renders the user list', () => {
    cy.get('[data-cy="user-row"]').should('have.length', 3);
  });

  it('shows error state on API failure', () => {
    cy.intercept('GET', '/api/users', {
      statusCode: 500,
      body: { message: 'Internal Server Error' },
    }).as('getUsersFail');

    cy.visit('/dashboard');
    cy.wait('@getUsersFail');
    cy.get('[data-cy="error-state"]').should('be.visible');
  });

  it('intercepts POST and asserts request payload', () => {
    cy.intercept('POST', '/api/users').as('createUser');

    cy.get('[data-cy="add-user-btn"]').click();
    cy.get('[data-cy="name-input"]').type('Bob');
    cy.get('[data-cy="save-btn"]').click();

    cy.wait('@createUser').its('request.body').should('deep.equal', {
      name: 'Bob',
    });
  });
});
```

### Fixtures

```json
// cypress/fixtures/users.json
[
  { "id": 1, "name": "Alice", "email": "alice@example.com", "role": "admin" },
  { "id": 2, "name": "Bob",   "email": "bob@example.com",   "role": "user" },
  { "id": 3, "name": "Carol", "email": "carol@example.com", "role": "user" }
]
```

```js
// Loading fixtures in a test
it('displays fixture data', () => {
  cy.fixture('users.json').then((users) => {
    cy.intercept('GET', '/api/users', users).as('getUsers');
    cy.visit('/dashboard');
    cy.wait('@getUsers');
    cy.get('[data-cy="user-row"]').first().should('contain', users[0].name);
  });
});

// Or use as an alias
beforeEach(() => {
  cy.fixture('users.json').as('users');
  cy.intercept('GET', '/api/users', { fixture: 'users.json' });
});

it('uses aliased fixture', function () {
  // Note: use function() not arrow fn to access this.users
  expect(this.users).to.have.length(3);
});
```

### Custom Commands

```js
// cypress/support/commands.js

// Login command — avoids repeating login UI in every spec
Cypress.Commands.add('login', (email = 'alice@example.com', password = 'secret') => {
  cy.session([email, password], () => {
    cy.visit('/login');
    cy.get('[data-cy="email-input"]').type(email);
    cy.get('[data-cy="password-input"]').type(password);
    cy.get('[data-cy="login-btn"]').click();
    cy.url().should('include', '/dashboard');
  });
});

// Login via API (much faster — skips UI)
Cypress.Commands.add('loginByApi', (email, password) => {
  cy.request('POST', '/api/auth/login', { email, password })
    .its('body.token')
    .then((token) => {
      window.localStorage.setItem('auth_token', token);
    });
});

// Fill a form by data-cy field names
Cypress.Commands.add('fillForm', (fields) => {
  Object.entries(fields).forEach(([key, value]) => {
    cy.get(`[data-cy="${key}"]`).clear().type(value);
  });
});
```

```js
// Using custom commands in specs
describe('Dashboard (authenticated)', () => {
  beforeEach(() => {
    cy.login();            // uses cy.session — only logs in once per session
    cy.visit('/dashboard');
  });

  it('creates a new product', () => {
    cy.get('[data-cy="new-product-btn"]').click();
    cy.fillForm({ 'product-name': 'Widget', 'product-price': '9.99' });
    cy.get('[data-cy="save-btn"]').click();
    cy.get('[data-cy="success-toast"]').should('contain', 'Product created');
  });
});
```

### Assertions and Async Handling

```js
// CORRECT — .should() retries until the assertion passes (or timeout)
cy.get('[data-cy="loading-spinner"]').should('not.exist');
cy.get('[data-cy="results-list"]').should('have.length.greaterThan', 0);

// CORRECT — chain multiple assertions on the same element
cy.get('[data-cy="status-badge"]')
  .should('be.visible')
  .and('have.text', 'Active')
  .and('have.class', 'badge--green');

// CORRECT — wait for a network event, not a timer
cy.intercept('GET', '/api/data').as('loadData');
cy.visit('/page');
cy.wait('@loadData');
cy.get('[data-cy="data-table"]').should('be.visible');

// WRONG — never do this
cy.wait(3000);   // arbitrary wait — flaky
```

### Running Tests

```bash
# Open Cypress interactive runner
npx cypress open

# Run all E2E tests headlessly
npx cypress run

# Run a specific spec
npx cypress run --spec "cypress/e2e/auth/login.cy.js"

# Run with a specific browser
npx cypress run --browser firefox

# Run tagged tests (requires @cypress/grep)
npx cypress run --env grepTags="@smoke"
```

### Anti-patterns to Avoid
- Selecting by CSS class (`cy.get('.btn-primary')`) — classes are styling details that change without warning.
- Using `cy.wait(N)` with a number — it always either waits too long or not long enough; use network aliases or element assertions.
- Writing tests that depend on each other's state — every spec file should be runnable in any order.
- Putting login logic in every `beforeEach` — use `cy.session()` inside a custom command to cache and restore sessions.
- Testing third-party services without stubbing — `cy.intercept` external calls so tests are deterministic and fast.
<!-- LEVEL 3 END -->
