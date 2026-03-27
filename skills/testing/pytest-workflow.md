---
id: pytest-workflow
name: Pytest Workflow
category: writing-tests
level1: "For writing and organising pytest tests with fixtures, mocks, and coverage"
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 1
---

<!-- LEVEL 1 START -->
**Pytest Workflow** — Activate for: writing pytest tests, fixtures, conftest.py, parametrize, mocking with unittest.mock or pytest-mock, async tests, test coverage, markers, test organisation.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## Pytest Workflow — Core Instructions

1. **One assertion per test concept** — each test should have a single reason to fail. Multiple unrelated assertions in one test make failures ambiguous.
2. **Use fixtures for setup/teardown, never `setUp`/`tearDown` methods** — fixtures are composable and scope-controlled; class-based test setup is the unittest way, not the pytest way.
3. **Parametrize to avoid copy-pasting tests** — if two tests differ only in input/output values, use `@pytest.mark.parametrize`.
4. **Put shared fixtures in `conftest.py`** — pytest discovers it automatically; you never import from it. Place it at the package boundary that needs the fixture.
5. **Mock at the boundary where it is used, not where it is defined** — patch `myapp.services.requests.get`, not `requests.get`.
6. **Use `pytest-mock`'s `mocker` fixture over `unittest.mock.patch` as a decorator** — `mocker` auto-resets after each test; decorators require careful ordering.
7. **Run coverage with `--cov` and check branch coverage** — line coverage hides untested conditional branches; use `--cov-branch`.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## Pytest Workflow — Full Reference

### Project Layout

```
project/
├── src/
│   └── myapp/
│       ├── __init__.py
│       ├── models.py
│       └── services.py
├── tests/
│   ├── conftest.py          # shared fixtures, session-scoped DB etc.
│   ├── unit/
│   │   ├── conftest.py      # unit-test-specific fixtures
│   │   ├── test_models.py
│   │   └── test_services.py
│   └── integration/
│       ├── conftest.py
│       └── test_api.py
└── pytest.ini               # or pyproject.toml [tool.pytest.ini_options]
```

```ini
# pytest.ini
[pytest]
testpaths = tests
addopts = -v --tb=short --cov=src --cov-branch --cov-report=term-missing
markers =
    unit: fast unit tests
    integration: tests that hit real services
    slow: long-running tests
```

### Fixtures

```python
# tests/conftest.py
import pytest
from myapp.database import Database
from myapp.app import create_app

@pytest.fixture(scope="session")
def db():
    """Real DB — created once per test session."""
    database = Database(url="sqlite:///:memory:")
    database.create_all()
    yield database
    database.drop_all()

@pytest.fixture(scope="function")   # default scope
def app(db):
    """App instance with a clean state per test."""
    application = create_app(testing=True, db=db)
    yield application

@pytest.fixture
def client(app):
    """Test HTTP client."""
    return app.test_client()

@pytest.fixture
def sample_user(db):
    user = db.create_user(name="Alice", email="alice@example.com")
    yield user
    db.delete_user(user.id)   # teardown after yield
```

```python
# Using fixtures in tests — just name them as parameters
def test_user_creation(sample_user):
    assert sample_user.name == "Alice"
    assert sample_user.email == "alice@example.com"

def test_get_user(client, sample_user):
    resp = client.get(f"/users/{sample_user.id}")
    assert resp.status_code == 200
    assert resp.json["name"] == "Alice"
```

### Parametrize

```python
import pytest
from myapp.validators import validate_email, validate_age

@pytest.mark.parametrize("email,expected", [
    ("user@example.com",    True),
    ("user+tag@example.io", True),
    ("notanemail",          False),
    ("@nodomain.com",       False),
    ("",                    False),
])
def test_validate_email(email, expected):
    assert validate_email(email) == expected

# Parametrize with ids for readable test names
@pytest.mark.parametrize("age,should_raise", [
    pytest.param(-1,  True,  id="negative"),
    pytest.param(0,   False, id="zero"),
    pytest.param(120, False, id="max_valid"),
    pytest.param(121, True,  id="over_max"),
], )
def test_validate_age(age, should_raise):
    if should_raise:
        with pytest.raises(ValueError):
            validate_age(age)
    else:
        validate_age(age)   # should not raise
```

### Mocking with pytest-mock

```python
# pip install pytest-mock
from myapp.services import UserService

def test_send_welcome_email(mocker):
    # Patch where it is used (myapp.services), not where defined (smtplib)
    mock_send = mocker.patch("myapp.services.send_email")

    service = UserService()
    service.register(name="Alice", email="alice@example.com")

    mock_send.assert_called_once_with(
        to="alice@example.com",
        subject="Welcome, Alice!",
        body=mocker.ANY,          # don't care about exact body
    )

def test_fetch_user_from_api(mocker):
    mock_get = mocker.patch("myapp.services.requests.get")
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"id": 1, "name": "Alice"}

    service = UserService()
    user = service.fetch_remote_user(1)

    assert user["name"] == "Alice"
    mock_get.assert_called_once_with("https://api.example.com/users/1", timeout=10)

def test_database_error_handling(mocker):
    mocker.patch("myapp.services.db.save", side_effect=Exception("DB down"))

    service = UserService()
    with pytest.raises(RuntimeError, match="Failed to save user"):
        service.create_user("Alice")
```

### Mocking with unittest.mock (without pytest-mock)

```python
from unittest.mock import patch, MagicMock, call
from myapp.services import UserService

def test_retry_on_failure():
    with patch("myapp.services.requests.get") as mock_get:
        # First call fails, second succeeds
        mock_get.side_effect = [
            ConnectionError("timeout"),
            MagicMock(status_code=200, json=lambda: {"id": 1}),
        ]
        service = UserService()
        result = service.fetch_with_retry(user_id=1, retries=2)

        assert result["id"] == 1
        assert mock_get.call_count == 2
```

### Async Tests with pytest-asyncio

```python
# pip install pytest-asyncio
# pytest.ini: asyncio_mode = auto  (or mark each test)
import pytest
import pytest_asyncio
from myapp.async_service import AsyncUserService

@pytest_asyncio.fixture
async def async_service():
    service = AsyncUserService()
    await service.connect()
    yield service
    await service.disconnect()

@pytest.mark.asyncio
async def test_async_fetch_user(async_service, mocker):
    mocker.patch.object(
        async_service, "http_get",
        return_value={"id": 1, "name": "Alice"}
    )
    user = await async_service.get_user(1)
    assert user["name"] == "Alice"
```

### Custom Markers and Skipping

```python
import pytest
import sys

@pytest.mark.slow
def test_large_data_processing():
    ...

@pytest.mark.integration
def test_real_database():
    ...

@pytest.mark.skipif(sys.platform == "win32", reason="POSIX only")
def test_file_permissions():
    ...

@pytest.mark.xfail(reason="Bug #123 — known failure, tracked")
def test_known_broken_feature():
    ...
```

```bash
# Run only fast unit tests
pytest -m "not slow and not integration"

# Run only integration tests
pytest -m integration

# Stop after first failure
pytest -x

# Show locals in traceback
pytest -l

# Re-run only last failed tests
pytest --lf
```

### Coverage

```bash
# Install
pip install pytest-cov

# Run with branch coverage
pytest --cov=src --cov-branch --cov-report=term-missing

# Generate HTML report
pytest --cov=src --cov-branch --cov-report=html
open htmlcov/index.html

# Fail if coverage drops below threshold
pytest --cov=src --cov-fail-under=85
```

```ini
# .coveragerc — exclude files from coverage
[run]
branch = True
source = src

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if TYPE_CHECKING:
```

### Anti-patterns to Avoid
- Importing from `conftest.py` — fixtures are discovered automatically; importing breaks pytest's scoping.
- Patching at the definition site (`requests.get`) instead of the usage site (`myapp.services.requests.get`) — the patch won't apply to already-imported names.
- Using `scope="session"` for fixtures that modify shared state — session-scoped fixtures must be read-only or use rollback/cleanup.
- Testing implementation details (private methods, internal state) instead of behaviour — tests that know too much break on every refactor.
- Writing tests that depend on execution order — each test must be independently runnable (`pytest --randomly` to verify).
<!-- LEVEL 3 END -->
