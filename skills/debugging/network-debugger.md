---
id: network-debugger
name: Network & HTTP Debugger
category: debugging
level1: "For HTTP errors, CORS failures, DNS issues, TLS, and timeouts"
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 1
---

<!-- LEVEL 1 START -->
**Network & HTTP Debugger** — Activate for: HTTP 4xx/5xx errors, CORS error, ECONNREFUSED, timeout, SSL certificate error, DNS resolution failure, network trace, curl debugging, slow API, request failing in production.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## Network & HTTP Debugger — Core Instructions

1. **Reproduce with curl first** — strip away application code; if curl reproduces it, it is a server/network issue, not your code.
2. **Read the full HTTP response, not just the status code** — the body almost always contains the real error message.
3. **CORS errors are always a server-side configuration problem** — the browser blocks the response; the server must send the right headers. Do not fix CORS in the frontend.
4. **Check DNS before assuming the server is down** — `dig` or `nslookup` to confirm the hostname resolves to the expected IP.
5. **TLS errors: check certificate expiry, hostname mismatch, and trust chain** — `openssl s_client` gives the full certificate chain and any errors.
6. **Timeouts: distinguish connect timeout from read timeout** — connect timeout means the host is unreachable or the port is filtered; read timeout means the server accepted but is not responding.
7. **Never disable TLS verification in production** — `curl -k` and `verify=False` are diagnostics only. Fix the underlying certificate issue.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## Network & HTTP Debugger — Full Reference

### HTTP Status Code Quick Reference

| Range | Meaning | First thing to check |
|-------|---------|----------------------|
| 400 | Bad Request | Request body/params malformed — read the error body |
| 401 | Unauthorized | Missing or expired auth token |
| 403 | Forbidden | Token valid but lacks permission for this resource |
| 404 | Not Found | Wrong URL, typo, or resource deleted |
| 405 | Method Not Allowed | Wrong HTTP verb (POST vs PUT vs PATCH) |
| 408 / 504 | Timeout | Server or upstream is slow; check server logs |
| 413 | Payload Too Large | Request body exceeds server limit |
| 422 | Unprocessable Entity | Schema validation failed — read the validation errors |
| 429 | Too Many Requests | Rate limited — check `Retry-After` header |
| 500 | Internal Server Error | Bug on the server — check server logs immediately |
| 502 / 503 | Bad Gateway / Unavailable | Upstream or load balancer issue |

### curl Debugging

```bash
# Full verbose output — shows TLS handshake, headers, timing
curl -v https://api.example.com/users

# Show only response headers (uppercase -I for HEAD request)
curl -sI https://api.example.com/health

# POST with JSON body, custom headers
curl -X POST https://api.example.com/users \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name": "Alice", "email": "alice@example.com"}' \
  -v

# Follow redirects, show timing breakdown
curl -Lv --write-out "\n\ntime_namelookup: %{time_namelookup}\ntime_connect: %{time_connect}\ntime_starttransfer: %{time_starttransfer}\ntotal: %{time_total}\n" \
  https://api.example.com/

# Ignore TLS errors (DIAGNOSTIC ONLY — never in production)
curl -k https://self-signed.example.com/

# Send a specific Host header (test virtual hosting / CDN)
curl -H "Host: api.example.com" http://203.0.113.10/users
```

### CORS Debugging

```bash
# Simulate a browser preflight request
curl -X OPTIONS https://api.example.com/data \
  -H "Origin: https://app.example.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type, Authorization" \
  -v

# Expected response headers for success:
# Access-Control-Allow-Origin: https://app.example.com
# Access-Control-Allow-Methods: GET, POST, PUT, DELETE
# Access-Control-Allow-Headers: Content-Type, Authorization
# Access-Control-Max-Age: 86400
```

```python
# FastAPI — correct CORS setup
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.example.com"],  # never use "*" with credentials
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Express.js — correct CORS setup
const cors = require('cors');
app.use(cors({
    origin: 'https://app.example.com',
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
}));
```

### DNS Debugging

```bash
# Basic resolution
dig api.example.com
nslookup api.example.com

# Query a specific DNS server
dig @8.8.8.8 api.example.com

# Check all record types
dig api.example.com ANY

# Trace the full DNS resolution chain
dig +trace api.example.com

# Check reverse DNS (PTR record)
dig -x 203.0.113.10

# Test from inside a container / Kubernetes pod
kubectl exec -it <pod> -- nslookup kubernetes.default
kubectl exec -it <pod> -- dig api.example.com
```

### TLS / SSL Debugging

```bash
# Full certificate chain and handshake details
openssl s_client -connect api.example.com:443 -servername api.example.com

# Check expiry date only
echo | openssl s_client -connect api.example.com:443 2>/dev/null \
  | openssl x509 -noout -dates

# Test with a specific TLS version
openssl s_client -connect api.example.com:443 -tls1_2
openssl s_client -connect api.example.com:443 -tls1_3

# Verify a certificate file
openssl x509 -in cert.pem -noout -text

# Check if a cert matches a private key (fingerprints must match)
openssl x509 -noout -modulus -in cert.pem | openssl md5
openssl rsa  -noout -modulus -in key.pem  | openssl md5
```

### Timeout Diagnosis

```bash
# Check if port is open (connect timeout vs filtered)
nc -zv api.example.com 443       # TCP connect test
nc -zv -w 5 api.example.com 443  # with 5s timeout

# Traceroute to find where packets are dropped
traceroute api.example.com
mtr --report api.example.com     # continuous, better output

# Check if a firewall is dropping vs rejecting
# TIMEOUT  = packet dropped (firewall)
# REFUSED  = port closed on the host
```

```python
# Python requests — distinguish timeout types
import requests
from requests.exceptions import ConnectTimeout, ReadTimeout

try:
    resp = requests.get(
        "https://api.example.com/data",
        timeout=(5, 30),   # (connect_timeout, read_timeout) in seconds
    )
    resp.raise_for_status()
except ConnectTimeout:
    # Host unreachable or port filtered — network/firewall issue
    raise
except ReadTimeout:
    # Server accepted connection but took too long — server-side issue
    raise
```

### Reading Network Traces (Wireshark / tcpdump)

```bash
# Capture HTTP traffic on port 80
sudo tcpdump -i eth0 'tcp port 80' -w capture.pcap

# Capture HTTPS (you won't see plaintext without key logging)
sudo tcpdump -i eth0 'tcp port 443' -w capture.pcap

# Enable TLS key logging for decryption in Wireshark
export SSLKEYLOGFILE=~/ssl-keys.log
# Then open capture.pcap in Wireshark:
# Edit > Preferences > Protocols > TLS > (Pre)-Master-Secret log filename

# Quick human-readable HTTP dump (no pcap file)
sudo tcpdump -i eth0 -A -s 0 'tcp port 80 and (((ip[2:2] - ((ip[0]&0xf)<<2)) - ((tcp[12]&0xf0)>>2)) != 0)'
```

### httpie (Friendlier Alternative to curl)

```bash
# Install: pip install httpie
# GET with auth
http GET https://api.example.com/users Authorization:"Bearer $TOKEN"

# POST JSON (automatic Content-Type)
http POST https://api.example.com/users name=Alice email=alice@example.com

# Show full request and response
http --verbose POST https://api.example.com/users name=Alice
```

### Anti-patterns to Avoid
- Disabling TLS verification (`-k`, `verify=False`) beyond initial diagnosis — commit it and you ship a security hole.
- Assuming CORS is a frontend fix — the browser is doing exactly what it should; the server must allow the origin.
- Reading only the status code and ignoring the response body — the body has the actual error.
- Using `ping` to test HTTP endpoints — ICMP and TCP/HTTP are independent; a host can respond to ping and still have port 443 blocked.
- Debugging production traffic without capturing first — always `tcpdump` or enable access logs before changing anything.
<!-- LEVEL 3 END -->
