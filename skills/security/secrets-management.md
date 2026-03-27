---
id: secrets-management
name: Secrets Management Expert
category: security
level1: "For hardcoded secrets, .env files, Vault/AWS/GCP secret managers, secret rotation, and credential leak detection"
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 1
---

<!-- LEVEL 1 START -->
**Secrets Management Expert** — Activate for: hardcoded API keys, .env setup, HashiCorp Vault, AWS Secrets Manager, GCP Secret Manager, secret rotation, pre-commit secret scanning, leaked credential detection.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## Secrets Management — Core Instructions

1. **Never hardcode secrets** — no API keys, passwords, tokens, or connection strings in source code, ever; use environment variables or a secrets manager.
2. **Add .env to .gitignore immediately** — also `.env.local`, `.env.production`; provide a `.env.example` with placeholder values.
3. **Use a secrets manager in production** — AWS Secrets Manager, GCP Secret Manager, or HashiCorp Vault instead of environment variables on the host.
4. **Rotate secrets on suspected exposure** — invalidate the old secret first, then update all consumers; treat rotation as a drill to automate.
5. **Install pre-commit hooks for secret scanning** — `gitleaks` or `detect-secrets` must block commits containing high-entropy strings or known patterns.
6. **Scope secrets minimally** — each service gets its own secret with least-privilege; never share a single root credential across services.
7. **Audit secret access** — enable CloudTrail / Vault audit logs; alert on unusual access patterns or reads outside deployment windows.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## Secrets Management — Full Reference

### .env Setup Pattern
```bash
# .env.example  (committed — safe placeholder values only)
DATABASE_URL=postgres://user:password@localhost:5432/mydb
OPENAI_API_KEY=sk-...
JWT_SECRET=change-me-256-bit-random-string

# .gitignore  (always include)
.env
.env.local
.env.*.local
.env.production
.env.staging
```

### Loading Secrets in Node.js
```typescript
// Use dotenv only in development — production uses real env vars
import 'dotenv/config';  // reads .env if present

function requireEnv(key: string): string {
  const value = process.env[key];
  if (!value) throw new Error(`Missing required env var: ${key}`);
  return value;
}

const config = {
  databaseUrl: requireEnv('DATABASE_URL'),
  openaiKey:   requireEnv('OPENAI_API_KEY'),
  jwtSecret:   requireEnv('JWT_SECRET'),
};
```

### AWS Secrets Manager
```python
import boto3, json
from functools import lru_cache

@lru_cache(maxsize=None)          # cache per process — add TTL for rotation
def get_secret(secret_name: str, region: str = 'us-east-1') -> dict:
    client = boto3.client('secretsmanager', region_name=region)
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# Usage
db_creds = get_secret('prod/myapp/postgres')
conn_str = f"postgresql://{db_creds['username']}:{db_creds['password']}@{db_creds['host']}/mydb"
```

### HashiCorp Vault (KV v2)
```python
import hvac

client = hvac.Client(url='https://vault.internal', token=os.environ['VAULT_TOKEN'])

def read_secret(path: str) -> dict:
    """Read from KV v2 mount."""
    resp = client.secrets.kv.v2.read_secret_version(path=path)
    return resp['data']['data']

secret = read_secret('myapp/prod/db')
```

### GCP Secret Manager
```python
from google.cloud import secretmanager

def get_gcp_secret(project_id: str, secret_id: str, version: str = 'latest') -> str:
    client = secretmanager.SecretManagerServiceClient()
    name = f'projects/{project_id}/secrets/{secret_id}/versions/{version}'
    response = client.access_secret_version(request={'name': name})
    return response.payload.data.decode('utf-8')
```

### Pre-commit Hook with Gitleaks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks

  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
```

```bash
# Install and run
pip install pre-commit detect-secrets
pre-commit install
detect-secrets scan > .secrets.baseline   # initial baseline
```

### Secret Rotation Checklist
```
1. Generate new secret value
2. Update secret in secrets manager (add new version, keep old active)
3. Deploy application with new secret (zero-downtime)
4. Verify application healthy with new secret
5. Deactivate / delete old secret version
6. Audit logs confirm no reads of old version
```

### Anti-patterns to Avoid
- Hardcoding any credential directly in source files or Dockerfiles
- Committing `.env` files (even "just for development")
- Logging secret values — mask them with `***` in log output
- Sharing one API key across dev/staging/prod environments
- Storing secrets in CI/CD UI as plain text instead of encrypted secret store
- Using short, guessable secrets (`secret`, `password123`, `changeme`)
- Not rotating secrets after team member offboarding
<!-- LEVEL 3 END -->
