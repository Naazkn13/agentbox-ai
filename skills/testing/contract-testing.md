---
id: contract-testing
name: Contract Testing (Pact)
category: writing-tests
level1: "For consumer-driven contract testing with Pact between services"
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 1
---

<!-- LEVEL 1 START -->
**Contract Testing (Pact)** — Activate for: consumer-driven contract testing, Pact framework, microservices integration, pact broker, consumer pact definition, provider verification, avoiding integration test hell, keeping API contracts in sync.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## Contract Testing (Pact) — Core Instructions

1. **Consumers define the contract, providers verify it** — the consumer writes exactly what it needs from the provider (no more); the provider runs Pact verification against that contract without deploying the consumer.
2. **Only describe what the consumer actually uses** — do not describe every field in a response, only the fields your consumer code reads. Contracts that over-specify become fragile and block provider evolution.
3. **Use type matchers, not exact value matchers, for non-deterministic fields** — `like()`, `eachLike()`, `integer()`, `string()` match by type; exact matching breaks on IDs, timestamps, and generated values.
4. **Publish pacts to a Pact Broker after every consumer build** — the broker stores versioned pacts and makes them available to providers without file sharing.
5. **Verify the contract in the provider's own test suite against the real provider code** — spin up the provider with test data; never mock the provider's internal dependencies.
6. **Use `can-i-deploy` before every deployment** — the Pact Broker's CLI command checks whether the consumer/provider versions you are deploying are mutually verified. Fail the pipeline if not.
7. **Record consumer interactions before the provider even exists** — contract testing enables parallel development; consumers work against the pact mock server from day one.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## Contract Testing (Pact) — Full Reference

### How Pact Works

```
Consumer (e.g. frontend / BFF)           Provider (e.g. User API)
─────────────────────────────────────    ─────────────────────────────
1. Write consumer pact test               4. Pull pact from Pact Broker
2. Pact mock server runs locally          5. Start real provider service
3. Publish pact to Pact Broker            6. Replay interactions → verify
                                          7. Publish verification results
                                          8. can-i-deploy? ✓
```

### Consumer Side — JavaScript (Pact JS v10+)

```ts
// user-service.pact.spec.ts
import { PactV3, MatchersV3 } from '@pact-foundation/pact';
import { UserService } from './user.service';
import path from 'path';

const { like, integer, string, eachLike } = MatchersV3;

const provider = new PactV3({
  consumer: 'WebApp',
  provider: 'UserService',
  dir: path.resolve(__dirname, '../pacts'),   // where to write the pact file
  logLevel: 'warn',
});

describe('UserService — Pact consumer tests', () => {
  describe('GET /users/:id', () => {
    it('returns a user when the user exists', () => {
      return provider
        .given('user 42 exists')           // provider state
        .uponReceiving('a request for user 42')
        .withRequest({
          method: 'GET',
          path: '/users/42',
          headers: { Accept: 'application/json' },
        })
        .willRespondWith({
          status: 200,
          headers: { 'Content-Type': 'application/json' },
          body: {
            // Only describe what the consumer actually uses
            id:    integer(42),
            name:  string('Alice'),
            email: string('alice@example.com'),
            // Do NOT include fields we don't read (e.g. internalId, auditLog)
          },
        })
        .executeTest(async (mockServer) => {
          const service = new UserService(mockServer.url);
          const user    = await service.getUser(42);

          expect(user.id).toBe(42);
          expect(user.name).toBe('Alice');
          expect(user.email).toBe('alice@example.com');
        });
    });

    it('returns 404 when user does not exist', () => {
      return provider
        .given('user 99 does not exist')
        .uponReceiving('a request for a non-existent user')
        .withRequest({ method: 'GET', path: '/users/99' })
        .willRespondWith({ status: 404, body: { message: string('Not found') } })
        .executeTest(async (mockServer) => {
          const service = new UserService(mockServer.url);
          await expect(service.getUser(99)).rejects.toThrow('Not found');
        });
    });
  });

  describe('GET /users', () => {
    it('returns a list of users', () => {
      return provider
        .given('users exist')
        .uponReceiving('a request for all users')
        .withRequest({ method: 'GET', path: '/users' })
        .willRespondWith({
          status: 200,
          body: eachLike({      // array of at least one element matching this shape
            id:   integer(),
            name: string(),
          }),
        })
        .executeTest(async (mockServer) => {
          const service = new UserService(mockServer.url);
          const users   = await service.listUsers();
          expect(users.length).toBeGreaterThanOrEqual(1);
          expect(users[0]).toHaveProperty('id');
          expect(users[0]).toHaveProperty('name');
        });
    });
  });
});
```

### Consumer Side — Python (pact-python)

```python
# test_user_consumer.py
import pytest
from pact import Consumer, Provider, Like, EachLike, Term
from myapp.clients.user_client import UserClient

PACT_DIR = "pacts"

@pytest.fixture(scope="module")
def pact():
    pact = Consumer("WebApp").has_pact_with(
        Provider("UserService"),
        pact_dir=PACT_DIR,
        host_name="localhost",
        port=1234,
    )
    pact.start_service()
    yield pact
    pact.stop_service()

def test_get_existing_user(pact):
    expected = {
        "id":    Like(42),
        "name":  Like("Alice"),
        "email": Like("alice@example.com"),
    }

    (
        pact
        .given("user 42 exists")
        .upon_receiving("a request for user 42")
        .with_request("GET", "/users/42", headers={"Accept": "application/json"})
        .will_respond_with(200, body=expected)
    )

    with pact:
        client = UserClient("http://localhost:1234")
        user   = client.get_user(42)

        assert user["id"]    == 42
        assert user["name"]  == "Alice"
        assert user["email"] == "alice@example.com"
```

### Provider Side — Verification (Node.js)

```ts
// user-service.provider.spec.ts  (in the provider's repo)
import { Verifier } from '@pact-foundation/pact';
import { startServer, stopServer } from './test-server';

describe('Pact provider verification', () => {
  let server: ReturnType<typeof startServer>;

  beforeAll(async () => {
    server = await startServer({ port: 8080 });
  });

  afterAll(async () => {
    await stopServer(server);
  });

  it('validates the consumer pacts', async () => {
    const opts = {
      providerBaseUrl: 'http://localhost:8080',
      provider: 'UserService',
      providerVersion: process.env.GIT_COMMIT,          // tag with git SHA
      providerVersionBranch: process.env.GIT_BRANCH,

      // Pull pacts from broker (recommended)
      pactBrokerUrl: 'https://your-broker.pactflow.io',
      pactBrokerToken: process.env.PACT_BROKER_TOKEN,
      publishVerificationResult: process.env.CI === 'true',

      // OR load local pact files during development
      // pactUrls: [path.resolve(__dirname, '../pacts/WebApp-UserService.json')],

      // Provider states — set up test data before each interaction
      stateHandlers: {
        'user 42 exists': async () => {
          await db.users.upsert({ id: 42, name: 'Alice', email: 'alice@example.com' });
        },
        'user 99 does not exist': async () => {
          await db.users.delete({ where: { id: 99 } });
        },
        'users exist': async () => {
          await db.users.createMany({ data: [{ id: 1, name: 'Bob' }] });
        },
      },
    };

    await new Verifier(opts).verifyProvider();
  });
});
```

### Pact Broker

```bash
# Install Pact CLI tools
npm install -g @pact-foundation/pact-node
# or via standalone binary: https://github.com/pact-foundation/pact-ruby-standalone

# Publish pacts from the consumer repo
pact-broker publish pacts/ \
  --broker-base-url https://your-broker.pactflow.io \
  --broker-token $PACT_BROKER_TOKEN \
  --consumer-app-version $(git rev-parse --short HEAD) \
  --branch $(git rev-parse --abbrev-ref HEAD)

# Check if this version can be deployed
pact-broker can-i-deploy \
  --pacticipant WebApp \
  --version $(git rev-parse --short HEAD) \
  --to-environment production \
  --broker-base-url https://your-broker.pactflow.io \
  --broker-token $PACT_BROKER_TOKEN

# Record a deployment (after successful deploy)
pact-broker record-deployment \
  --pacticipant WebApp \
  --version $(git rev-parse --short HEAD) \
  --environment production
```

### CI Pipeline Integration

```yaml
# .github/workflows/consumer.yml
name: Consumer
on: [push]
jobs:
  test-and-publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm test                         # runs pact consumer tests, writes pact files
      - name: Publish pacts
        run: |
          npx pact-broker publish pacts/ \
            --broker-base-url ${{ vars.PACT_BROKER_URL }} \
            --broker-token ${{ secrets.PACT_BROKER_TOKEN }} \
            --consumer-app-version ${{ github.sha }} \
            --branch ${{ github.ref_name }}
      - name: Can I deploy?
        run: |
          npx pact-broker can-i-deploy \
            --pacticipant WebApp \
            --version ${{ github.sha }} \
            --to-environment production \
            --broker-base-url ${{ vars.PACT_BROKER_URL }} \
            --broker-token ${{ secrets.PACT_BROKER_TOKEN }}
```

### Matchers Quick Reference

```ts
import { MatchersV3 } from '@pact-foundation/pact';
const { like, eachLike, integer, decimal, string, boolean,
        datetime, regex, fromProviderState } = MatchersV3;

// Exact value (avoid for non-deterministic fields)
{ status: 'active' }

// Match by type only
like('any string value')     // string
integer(42)                  // integer number
decimal(3.14)                // decimal number
boolean(true)                // boolean

// Array of at least one matching element
eachLike({ id: integer(), name: string() })

// Regex match
regex('2024-01-15', /\d{4}-\d{2}-\d{2}/)

// ISO 8601 datetime
datetime("yyyy-MM-dd'T'HH:mm:ss.SSSX", '2024-01-15T12:00:00.000Z')

// Value injected from provider state (e.g. a generated ID)
fromProviderState('/users/${userId}', '/users/42')
```

### Anti-patterns to Avoid
- Writing provider-driven contracts (the provider writes what it sends) — Pact is consumer-driven; providers verifying their own assumptions defeats the purpose.
- Using exact matchers on IDs, timestamps, and generated values — these change per test run and cause verification failures that are unrelated to breaking changes.
- Checking fields the consumer does not actually use — over-specifying makes the provider unable to evolve its response without breaking the contract.
- Skipping `can-i-deploy` before deploying — this is the whole point of the Pact Broker; without it you lose the deployment safety guarantee.
- Running provider verification against a mocked or stubbed version of the provider — the provider must run real code against real (test) data for verification to be meaningful.
<!-- LEVEL 3 END -->
