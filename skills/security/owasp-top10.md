---
id: owasp-top10
name: OWASP Top 10 Security Expert
category: security
level1: "For SQL injection, XSS, IDOR, broken auth, security misconfiguration, vulnerable components, and SSRF"
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 1
---

<!-- LEVEL 1 START -->
**OWASP Top 10 Security Expert** — Activate for: SQL injection, XSS, IDOR, broken authentication, security misconfiguration, vulnerable dependencies, SSRF, and any OWASP vulnerability detection or remediation.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## OWASP Top 10 — Core Instructions

1. **Parameterized queries always** — never concatenate user input into SQL strings; use prepared statements or ORM parameterization for every database call.
2. **Encode all output** — HTML-encode user-supplied data before rendering in templates; use `textContent` not `innerHTML` for DOM insertion.
3. **Enforce object-level authorization** — validate that the requesting user owns the resource on every read/write, never rely on obscure IDs alone.
4. **Reject insecure defaults** — change default credentials, disable directory listing, remove debug endpoints and stack traces in production.
5. **Audit dependencies regularly** — run `npm audit`, `pip-audit`, or `trivy` in CI; block builds on high-severity CVEs; pin dependency versions.
6. **Validate and restrict outbound requests** — for SSRF, whitelist allowed hosts/schemas, block private IP ranges (169.254.x.x, 10.x, 172.16–31.x, 192.168.x.x).
7. **Use security headers on every response** — Content-Security-Policy, X-Frame-Options, X-Content-Type-Options, Strict-Transport-Security must be set by middleware.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## OWASP Top 10 — Full Reference

### A01 — Broken Access Control (IDOR fix)
```typescript
// VULNERABLE — user supplies id, no ownership check
app.get('/api/orders/:id', async (req, res) => {
  const order = await db.orders.findById(req.params.id);
  res.json(order);
});

// SECURE — enforce ownership at query level
app.get('/api/orders/:id', requireAuth, async (req, res) => {
  const order = await db.orders.findOne({
    id: req.params.id,
    userId: req.user.id,   // ownership enforced in the WHERE clause
  });
  if (!order) return res.status(404).json({ error: 'Not found' });
  res.json(order);
});
```

### A02 — Cryptographic Failures
```typescript
// VULNERABLE — MD5, no salt
const hash = crypto.createHash('md5').update(password).digest('hex');

// SECURE — bcrypt with cost factor ≥ 12
import bcrypt from 'bcrypt';
const hash = await bcrypt.hash(password, 12);
const valid = await bcrypt.compare(input, hash); // timing-safe compare
```

### A03 — SQL Injection
```python
# VULNERABLE
query = f"SELECT * FROM users WHERE email = '{email}'"
cursor.execute(query)

# SECURE — parameterized
cursor.execute("SELECT * FROM users WHERE email = %s", (email,))

# SECURE — SQLAlchemy ORM
user = session.query(User).filter(User.email == email).first()
```

### A07 — Cross-Site Scripting (XSS)
```typescript
// VULNERABLE — direct innerHTML
element.innerHTML = userInput;

// SECURE — textContent for plain text
element.textContent = userInput;

// SECURE — DOMPurify for rich HTML
import DOMPurify from 'dompurify';
element.innerHTML = DOMPurify.sanitize(userInput);

// SECURE — Content-Security-Policy header
res.setHeader(
  'Content-Security-Policy',
  "default-src 'self'; script-src 'self'; object-src 'none'"
);
```

### A10 — SSRF Prevention
```python
import ipaddress, urllib.parse, requests

ALLOWED_SCHEMES = {'https'}
BLOCKED_RANGES = [
    ipaddress.ip_network('10.0.0.0/8'),
    ipaddress.ip_network('172.16.0.0/12'),
    ipaddress.ip_network('192.168.0.0/16'),
    ipaddress.ip_network('169.254.0.0/16'),  # metadata services
]

def safe_fetch(url: str) -> requests.Response:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise ValueError('Scheme not allowed')
    ip = ipaddress.ip_address(parsed.hostname)
    for blocked in BLOCKED_RANGES:
        if ip in blocked:
            raise ValueError('Private IP blocked')
    return requests.get(url, timeout=5, allow_redirects=False)
```

### Security Headers Middleware (Express)
```typescript
import helmet from 'helmet';

app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'"],
      objectSrc: ["'none'"],
      upgradeInsecureRequests: [],
    },
  },
  hsts: { maxAge: 31536000, includeSubDomains: true },
}));
```

### Dependency Scanning in CI
```yaml
# GitHub Actions — block on high CVEs
- name: Audit dependencies
  run: |
    npm audit --audit-level=high
    npx better-npm-audit audit --level high
```

### Anti-patterns to Avoid
- Building SQL with string concatenation (`"SELECT ... WHERE id=" + id`)
- Using `eval()` or `Function()` with user input
- Trusting `X-Forwarded-For` for authorization without validation
- Storing secrets in source code or Docker image layers
- Disabling TLS certificate verification (`verify=False`, `rejectUnauthorized: false`)
- Returning full stack traces or internal paths in API error responses
- Using `SELECT *` and returning all columns including sensitive ones (password hashes, tokens)
<!-- LEVEL 3 END -->
