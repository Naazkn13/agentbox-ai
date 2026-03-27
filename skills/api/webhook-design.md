---
id: webhook-design
name: Webhook Design Expert
category: api-work
level1: "For designing reliable webhooks — HMAC verification, idempotency, retries, event schemas, and local testing"
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 1
---

<!-- LEVEL 1 START -->
**Webhook Design Expert** — Activate for: webhook endpoint design, HMAC signature verification, idempotency, retry logic with exponential backoff, event payload schemas, delivery guarantees, and testing webhooks locally with ngrok.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## Webhook Design — Core Instructions

1. **Always verify HMAC signatures first:** before processing any webhook payload, verify the `X-Signature` header using a shared secret — reject with `401` if invalid, `400` if the header is missing.
2. **Respond 200 immediately, process async:** return `200 OK` within 5 seconds; push the verified payload to a queue or background job for actual processing — never do slow work in the handler.
3. **Make all handlers idempotent:** use the event `id` field as an idempotency key stored in a DB/cache — if already processed, return `200` without re-processing.
4. **Use a consistent event schema:** every event must have `id`, `type`, `created_at`, and `data` fields — consumers rely on this contract.
5. **Implement exponential backoff with jitter on retries:** wait `min(base * 2^attempt, maxDelay) + random jitter` between delivery attempts; stop after a configurable max (e.g., 10 attempts over 24 hours).
6. **Sign payloads with a timestamp to prevent replay attacks:** include the timestamp in the signed string (e.g., `t=<unix>&v1=<hmac>`) and reject payloads older than 5 minutes.
7. **Test locally with ngrok or smee.io:** use `ngrok http 3000` to expose a local server and paste the HTTPS URL as the webhook endpoint during development.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## Webhook Design — Full Reference

### Event Payload Schema
```json
{
  "id": "evt_01HQZ5K2X3V8N7P4M6C9B0D1E2",
  "type": "payment.completed",
  "created_at": "2026-03-26T10:30:00Z",
  "api_version": "2026-03-01",
  "data": {
    "object": {
      "id": "pay_abc123",
      "amount_cents": 1000,
      "currency": "USD",
      "status": "completed"
    }
  }
}
```

### HMAC Signature Generation (Sender Side)
```typescript
import crypto from "crypto";

const WEBHOOK_SECRET = process.env.WEBHOOK_SECRET!;

function signPayload(payload: string): string {
  const timestamp = Math.floor(Date.now() / 1000);
  const signedString = `t=${timestamp}&v1=${payload}`;
  const hmac = crypto
    .createHmac("sha256", WEBHOOK_SECRET)
    .update(signedString)
    .digest("hex");
  return `t=${timestamp},v1=${hmac}`;
}

async function deliverWebhook(endpoint: string, event: object): Promise<void> {
  const body = JSON.stringify(event);
  const signature = signPayload(body);

  const response = await fetch(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Webhook-Signature": signature,
      "X-Webhook-ID": (event as any).id,
    },
    body,
  });

  if (!response.ok) {
    throw new Error(`Delivery failed: ${response.status}`);
  }
}
```

### HMAC Signature Verification (Receiver Side)
```typescript
import crypto from "crypto";
import express from "express";

const router = express.Router();
const WEBHOOK_SECRET = process.env.WEBHOOK_SECRET!;
const TOLERANCE_SECONDS = 300; // 5 minutes

function verifySignature(rawBody: string, header: string): boolean {
  // header format: t=1234567890,v1=abc123...
  const parts = Object.fromEntries(
    header.split(",").map((p) => p.split("=") as [string, string])
  );
  const timestamp = parseInt(parts["t"], 10);
  const receivedHmac = parts["v1"];

  // Replay attack guard
  const age = Math.floor(Date.now() / 1000) - timestamp;
  if (age > TOLERANCE_SECONDS) return false;

  const signedString = `t=${timestamp}&v1=${rawBody}`;
  const expected = crypto
    .createHmac("sha256", WEBHOOK_SECRET)
    .update(signedString)
    .digest("hex");

  // Constant-time comparison to prevent timing attacks
  return crypto.timingSafeEqual(
    Buffer.from(receivedHmac, "hex"),
    Buffer.from(expected, "hex")
  );
}

// Use raw body middleware — JSON parsing must happen AFTER signature check
router.post(
  "/webhooks",
  express.raw({ type: "application/json" }),
  async (req, res) => {
    const sigHeader = req.headers["x-webhook-signature"] as string;
    if (!sigHeader) return res.status(400).send("Missing signature");

    const rawBody = req.body.toString("utf8");
    if (!verifySignature(rawBody, sigHeader)) {
      return res.status(401).send("Invalid signature");
    }

    // Respond immediately — process async
    res.status(200).send("OK");

    const event = JSON.parse(rawBody);
    await enqueueForProcessing(event); // push to queue
  }
);
```

### Idempotency Check (Node.js + Redis)
```typescript
import { createClient } from "redis";

const redis = createClient();

async function processEventOnce(event: WebhookEvent): Promise<void> {
  const key = `webhook:processed:${event.id}`;
  const alreadyProcessed = await redis.set(key, "1", {
    NX: true,       // only set if not exists
    EX: 86400 * 7,  // expire after 7 days
  });

  if (!alreadyProcessed) {
    console.log(`Duplicate event ${event.id} — skipping`);
    return;
  }

  // Safe to process exactly once
  await handleEvent(event);
}
```

### Retry with Exponential Backoff + Jitter
```typescript
interface RetryConfig {
  maxAttempts: number;   // e.g. 10
  baseDelayMs: number;   // e.g. 1000 (1s)
  maxDelayMs: number;    // e.g. 3_600_000 (1h)
}

function computeDelay(attempt: number, config: RetryConfig): number {
  const exponential = config.baseDelayMs * Math.pow(2, attempt);
  const capped = Math.min(exponential, config.maxDelayMs);
  const jitter = Math.random() * capped * 0.2; // ±20% jitter
  return Math.floor(capped + jitter);
}

async function deliverWithRetry(
  endpoint: string,
  event: object,
  config: RetryConfig
): Promise<void> {
  for (let attempt = 0; attempt < config.maxAttempts; attempt++) {
    try {
      await deliverWebhook(endpoint, event);
      return; // success
    } catch (err) {
      if (attempt === config.maxAttempts - 1) throw err; // exhausted
      const delay = computeDelay(attempt, config);
      console.log(`Retry ${attempt + 1} in ${delay}ms`);
      await new Promise((r) => setTimeout(r, delay));
    }
  }
}

// Retry schedule example (base=1s, max=1h):
// attempt 0 → immediate
// attempt 1 → ~2s
// attempt 2 → ~4s
// attempt 3 → ~8s
// attempt 7 → ~2m
// attempt 9 → ~1h (capped)
```

### Python Receiver (Flask)
```python
import hashlib, hmac, json, os, time
from flask import Flask, request, abort

app = Flask(__name__)
WEBHOOK_SECRET = os.environ["WEBHOOK_SECRET"].encode()
TOLERANCE = 300  # 5 minutes

def verify_signature(raw_body: bytes, header: str) -> bool:
    parts = dict(p.split("=", 1) for p in header.split(","))
    timestamp = int(parts["t"])
    received = parts["v1"]

    if abs(time.time() - timestamp) > TOLERANCE:
        return False

    signed = f"t={timestamp}&v1={raw_body.decode()}".encode()
    expected = hmac.new(WEBHOOK_SECRET, signed, hashlib.sha256).hexdigest()
    return hmac.compare_digest(received, expected)

@app.post("/webhooks")
def webhook():
    sig = request.headers.get("X-Webhook-Signature", "")
    if not sig:
        abort(400, "Missing signature")
    if not verify_signature(request.data, sig):
        abort(401, "Invalid signature")

    event = request.get_json()
    # process async (celery task, rq job, etc.)
    process_event.delay(event)
    return "", 200
```

### Local Testing with ngrok
```bash
# Install ngrok: https://ngrok.com/download
ngrok http 3000

# Output:
# Forwarding  https://abc123.ngrok-free.app -> http://localhost:3000
# Use https://abc123.ngrok-free.app/webhooks as your webhook URL

# smee.io alternative (no account required)
npx smee-client --url https://smee.io/your-channel-id --target http://localhost:3000/webhooks
```

### Delivery Status Tracking Schema
```sql
CREATE TABLE webhook_deliveries (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_id     TEXT NOT NULL,
  endpoint_url TEXT NOT NULL,
  attempt      INT  NOT NULL DEFAULT 0,
  status       TEXT NOT NULL CHECK (status IN ('pending','delivered','failed','exhausted')),
  status_code  INT,
  error        TEXT,
  next_retry_at TIMESTAMPTZ,
  delivered_at  TIMESTAMPTZ,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX ON webhook_deliveries (status, next_retry_at)
  WHERE status IN ('pending', 'failed');
```

### Anti-patterns to Avoid
- Never parse the JSON body before verifying the HMAC — body parsing can alter whitespace and break the signature.
- Never do slow processing inside the HTTP handler — always respond 200 first, then process asynchronously.
- Never retry without jitter — synchronized retries from multiple callers will hammer a recovering server.
- Never skip the timestamp/replay check — without it, an attacker can replay captured valid requests.
- Never use `==` for comparing HMACs — always use constant-time comparison to prevent timing attacks.
- Never expose your webhook secret in logs, error responses, or the spec.
<!-- LEVEL 3 END -->
