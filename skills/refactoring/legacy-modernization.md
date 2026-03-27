---
id: legacy-modernization
name: Legacy Code Modernization Expert
category: refactoring
level1: "For modernizing legacy codebases — strangler fig, characterization tests, incremental refactoring"
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 2
---

<!-- LEVEL 1 START -->
**Legacy Code Modernization Expert** — Activate for: legacy codebase refactoring, modernizing old code, strangler fig pattern, untangling monoliths, adding tests to untested code, incremental rewrites, technical debt paydown.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## Legacy Code Modernization Expert — Core Instructions

1. **Never do a big-bang rewrite** — rewriting from scratch discards years of implicit bug fixes and edge-case handling. Use the strangler fig pattern: build the new system alongside the old and route traffic incrementally.
2. **Write characterization tests before touching anything** — capture the current behavior (including bugs) as tests. These tests protect you from accidental behavior changes during refactoring.
3. **Refactor one module at a time** — identify bounded contexts, extract them one at a time, and deploy each extraction independently before moving on.
4. **Inject dependencies instead of importing them** — untestable legacy code almost always uses global state or direct instantiation. Introduce interfaces and pass them in to enable testing.
5. **Use feature flags for safe rollout** — new code paths should start behind a flag, be enabled for internal users first, then rolled out gradually with a kill switch.
6. **Extract bounded contexts before extracting services** — don't jump to microservices. First separate concerns within the monolith; services come after you've found the right boundaries.
7. **Track progress with metrics, not feelings** — measure test coverage, cyclomatic complexity, and deployment frequency before and after. Modernization succeeds when those numbers improve measurably.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## Legacy Code Modernization Expert — Full Reference

### The Strangler Fig Pattern

The strangler fig is the core strategy: the new system grows around the old one until the old one can be removed. You never stop the world to rewrite.

```
                         ┌─────────────┐
                         │   Router /  │
  All traffic ──────────▶│  Proxy /    │
                         │  Feature    │
                         │  Flag       │
                         └──────┬──────┘
                      old  │        │ new (% traffic)
                     ┌─────▼──┐  ┌──▼──────┐
                     │ Legacy │  │  New    │
                     │ System │  │ Service │
                     └────────┘  └─────────┘
```

Steps:
1. Put a routing layer (reverse proxy, feature flag, or facade) in front of the legacy component
2. Build the new implementation behind that router
3. Route a small percentage of traffic (or specific users) to the new path
4. Monitor: errors, latency, data integrity
5. Increase traffic to new path until legacy path reaches 0%
6. Delete the legacy code

### Characterization Tests

Characterization tests record what the code *currently does* — not what it *should* do. They protect you from accidentally changing behavior during refactoring.

```python
# Legacy function with unclear intent
def calculate_fee(amount, days, tier):
    if tier == "A":
        base = amount * 0.02
    else:
        base = amount * 0.035
    if days > 30:
        base += base * 0.1
    return round(base, 2)

# Characterization test — no understanding of "why" needed
class TestCalculateFeeLegacyBehavior:
    def test_tier_a_under_30_days(self):
        assert calculate_fee(1000, 15, "A") == 20.0

    def test_tier_a_over_30_days(self):
        assert calculate_fee(1000, 45, "A") == 22.0

    def test_tier_b_under_30_days(self):
        assert calculate_fee(1000, 15, "B") == 35.0

    def test_tier_b_over_30_days(self):
        assert calculate_fee(1000, 45, "B") == 38.5

    # Document any surprising behavior you discover
    def test_zero_amount_returns_zero(self):
        assert calculate_fee(0, 45, "A") == 0.0
```

Run the full characterization test suite after every refactoring step. A red test means you changed behavior.

### Dependency Injection for Testability

```python
# LEGACY: untestable — hardcoded DB connection, hardcoded clock
class OrderProcessor:
    def process(self, order_id):
        conn = psycopg2.connect(DB_URL)          # hardcoded
        order = conn.execute("SELECT ...")
        order.processed_at = datetime.now()      # hardcoded clock
        conn.execute("UPDATE ...")

# MODERNIZED: injectable dependencies
class OrderProcessor:
    def __init__(self, db: Database, clock: Clock):
        self.db = db
        self.clock = clock

    def process(self, order_id):
        order = self.db.get_order(order_id)
        order.processed_at = self.clock.now()
        self.db.save(order)

# In tests
processor = OrderProcessor(db=FakeDatabase(), clock=FakeClock(fixed_time))
processor.process(order_id=42)
assert fake_db.saved_order.processed_at == fixed_time
```

### Extracting Bounded Contexts

Before splitting a monolith into services, find the natural seams inside it. Signs of a bounded context:
- A cluster of tables that are only joined to each other, never across to the rest
- A team that owns and understands a specific set of modules
- A deployment unit that changes at a different rate than the rest of the codebase

```
Monolith (before)
├── users/
├── orders/          ← high coupling to inventory
├── inventory/       ← high coupling to orders
├── notifications/   ← loosely coupled — good extraction candidate
├── billing/         ← loosely coupled — good extraction candidate
└── reports/

Step 1: Extract notifications (low risk, few dependencies)
Step 2: Extract billing (medium risk, depends on orders/users interface)
Step 3: Separate orders + inventory only after their interface stabilizes
```

### Feature Flags for Safe Rollout

```python
# Use a flag library (LaunchDarkly, Unleash, or a simple DB table)
from flags import flag_enabled

def get_shipping_cost(order):
    if flag_enabled("new-shipping-calculator", user=order.user_id):
        return new_shipping_service.calculate(order)   # new path
    else:
        return legacy_calculate_shipping(order)         # old path

# Rollout stages:
# 1. Flag OFF for everyone — deploy safely
# 2. Flag ON for internal users only — smoke test
# 3. Flag ON for 5% of users — monitor error rate
# 4. Ramp to 50%, then 100%
# 5. Remove flag and old code path after 1 stable week
```

### Incremental Refactoring Sequence

For any single legacy module, follow this order:

1. **Add characterization tests** to the existing code — do not change behavior
2. **Extract pure functions** — find logic with no side effects, pull it out first
3. **Introduce seam** — add an interface/abstraction at the dependency boundary
4. **Replace global state** — inject state instead of reading from globals
5. **Add real unit tests** — now that dependencies are injectable, write proper tests
6. **Rename and restructure** — only after tests are green and protect you
7. **Delete dead code** — use coverage reports to find unreachable paths

### Measuring Modernization Progress

| Metric | Measure with | Target direction |
|---|---|---|
| Test coverage | `pytest --cov`, `jest --coverage` | Increasing |
| Cyclomatic complexity | `radon cc`, `complexity-report` | Decreasing |
| Lines per function | `radon mi` | Decreasing |
| Time to onboard new dev | Team survey | Decreasing |
| Deploy frequency | CI/CD logs | Increasing |
| Change failure rate | Incident log | Decreasing |

### Anti-patterns to Avoid
- Starting a full rewrite ("we'll rebuild it properly in 6 months") — the new system inherits the same misunderstandings the old one solved
- Refactoring without characterization tests — you will break something silently
- Extracting microservices before finding stable bounded contexts — you bake the wrong seams in permanently
- "Boyscout rule" applied carelessly — changing unrelated code in every PR makes blame and bisect useless
- Using feature flags indefinitely without a removal plan — flag debt is tech debt
<!-- LEVEL 3 END -->
