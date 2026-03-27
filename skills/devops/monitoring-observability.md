---
id: monitoring-observability
name: Monitoring & Observability Expert
category: deploying
level1: "For structured logging, Prometheus metrics, OpenTelemetry tracing, alerting, SLO/SLI"
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 2
---

<!-- LEVEL 1 START -->
**Monitoring & Observability Expert** — Activate for: structured logging, Prometheus, Grafana, OpenTelemetry, distributed tracing, alerting rules, SLO/SLI/SLA, Datadog, CloudWatch, correlation IDs, metrics instrumentation.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## Monitoring & Observability Expert — Core Instructions

1. **Emit structured JSON logs only** — every log line must be a valid JSON object with at minimum: `timestamp`, `level`, `message`, `service`, and `trace_id`; no free-form string concatenation in production logs.
2. **Propagate correlation IDs across every service boundary** — inject `trace_id` and `span_id` into all outbound HTTP headers (`traceparent`) and include them in every log line and metric label.
3. **Use the right Prometheus metric type** — Counter for monotonically increasing values (requests total), Gauge for values that go up and down (queue depth), Histogram for latency distributions (never use Summary in multi-instance deployments).
4. **Define SLOs before writing alerts** — derive alert thresholds from error budget burn rate, not arbitrary static thresholds; a 1-hour burn rate > 14.4x is a page-worthy fast burn.
5. **Instrument at the boundary, not the internals** — record duration and error status at every external call (HTTP, DB, queue, cache); internal function timing is noise until you have a proven bottleneck.
6. **Include exemplars in Histogram metrics** — link trace IDs to histogram buckets so you can jump from a slow p99 bucket directly to the offending trace in Jaeger/Tempo.
7. **Test your alerts with `promtool`** — write unit tests for alert rules in YAML (`rule_files`, `evaluation_interval`, `tests`) and run them in CI before deploying to production.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## Monitoring & Observability Expert — Full Reference

### Structured JSON Logging (Python)

```python
import logging
import json
import sys
from contextvars import ContextVar

trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S.%fZ"),
            "level": record.levelname,
            "message": record.getMessage(),
            "service": "my-service",
            "logger": record.name,
            "trace_id": trace_id_var.get(""),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JSONFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler])
logger = logging.getLogger(__name__)

# Usage
trace_id_var.set("4bf92f3577b34da6a3ce929d0e0e4736")
logger.info("Order processed", extra={"order_id": "ord-123", "amount_usd": 49.99})
```

### Structured JSON Logging (Node.js with pino)

```javascript
import pino from "pino";

const logger = pino({
  level: "info",
  formatters: {
    level: (label) => ({ level: label }),
  },
  base: { service: "checkout-service" },
});

// Bind request-scoped fields
const reqLogger = logger.child({ trace_id: req.headers["x-trace-id"], user_id: req.user.id });
reqLogger.info({ order_id: "ord-123" }, "Order created");
reqLogger.error({ err }, "Payment failed");
```

### Prometheus Metric Types

```python
from prometheus_client import Counter, Gauge, Histogram, start_http_server

# Counter — only ever increases
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

# Gauge — can increase or decrease
queue_depth = Gauge("worker_queue_depth", "Current jobs in queue", ["queue_name"])

# Histogram — latency / duration distributions
request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

# Instrument a handler
@request_duration_seconds.labels(method="POST", endpoint="/orders").time()
def create_order(payload):
    http_requests_total.labels(method="POST", endpoint="/orders", status_code="200").inc()
    queue_depth.labels(queue_name="fulfillment").inc()
    # ... business logic

start_http_server(9090)  # expose /metrics
```

### Prometheus Alert Rules

```yaml
# alerts/slo.yaml
groups:
  - name: api-slo
    rules:
      # Fast burn: error budget consumed in ~1 hour
      - alert: HighErrorBudgetBurnRate
        expr: |
          (
            rate(http_requests_total{status_code=~"5.."}[1h])
            / rate(http_requests_total[1h])
          ) > (14.4 * 0.001)   # 14.4x burn × 0.1% error budget
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error budget burn rate on {{ $labels.service }}"
          description: "Error rate {{ $value | humanizePercentage }} over last 1h"

      # Latency p99 > 500ms
      - alert: HighP99Latency
        expr: |
          histogram_quantile(0.99,
            rate(http_request_duration_seconds_bucket[5m])
          ) > 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "p99 latency above 500ms for {{ $labels.endpoint }}"
```

### Grafana Dashboard JSON Snippet

```json
{
  "title": "API Error Rate",
  "type": "timeseries",
  "targets": [
    {
      "expr": "sum(rate(http_requests_total{status_code=~\"5..\"}[5m])) by (endpoint) / sum(rate(http_requests_total[5m])) by (endpoint)",
      "legendFormat": "{{ endpoint }}"
    }
  ],
  "fieldConfig": {
    "defaults": {
      "unit": "percentunit",
      "thresholds": {
        "steps": [
          { "value": 0, "color": "green" },
          { "value": 0.001, "color": "yellow" },
          { "value": 0.01, "color": "red" }
        ]
      }
    }
  }
}
```

### OpenTelemetry Instrumentation (Python)

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

# Setup
provider = TracerProvider()
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint="http://otel-collector:4317")))
trace.set_tracer_provider(provider)

# Auto-instrument FastAPI + SQLAlchemy
FastAPIInstrumentor.instrument_app(app)
SQLAlchemyInstrumentor().instrument(engine=engine)

# Manual span with attributes
tracer = trace.get_tracer(__name__)

def process_payment(order_id: str, amount: float):
    with tracer.start_as_current_span("process_payment") as span:
        span.set_attribute("order.id", order_id)
        span.set_attribute("payment.amount_usd", amount)
        try:
            result = payment_gateway.charge(order_id, amount)
            span.set_attribute("payment.status", "success")
            return result
        except PaymentError as e:
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR, str(e))
            raise
```

### Correlation ID Middleware (FastAPI)

```python
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class CorrelationIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        trace_id = request.headers.get("x-trace-id") or str(uuid.uuid4())
        trace_id_var.set(trace_id)                     # context var for logging
        response = await call_next(request)
        response.headers["x-trace-id"] = trace_id     # echo back in response
        return response
```

### SLO / SLI / SLA Definitions

```
SLI (indicator):  rate(http_requests_total{status!~"5.."}[28d]) / rate(http_requests_total[28d])
SLO (objective):  99.9% of requests return non-5xx over a 28-day rolling window
Error budget:     0.1% = 43.2 minutes of downtime per 28 days
SLA (agreement):  Customer-facing commitment; typically SLO - buffer (e.g., 99.5% SLA, 99.9% internal SLO)
```

### CloudWatch Metric Filter + Alarm (Terraform)

```hcl
resource "aws_cloudwatch_log_metric_filter" "error_count" {
  name           = "error-log-count"
  log_group_name = aws_cloudwatch_log_group.app.name
  pattern        = "{ $.level = \"ERROR\" }"

  metric_transformation {
    name      = "ErrorCount"
    namespace = "MyApp"
    value     = "1"
  }
}

resource "aws_cloudwatch_metric_alarm" "high_errors" {
  alarm_name          = "high-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ErrorCount"
  namespace           = "MyApp"
  period              = 60
  statistic           = "Sum"
  threshold           = 10
  alarm_actions       = [aws_sns_topic.alerts.arn]
}
```

### Anti-patterns to Avoid
- Free-form string log messages without structured fields — impossible to query or aggregate at scale
- Using Prometheus Summary instead of Histogram in multi-replica deployments — quantiles cannot be aggregated across instances
- Alerting on CPU/memory thresholds alone — alert on symptoms (error rate, latency) not causes
- Missing `trace_id` in logs — without correlation IDs, cross-service debugging requires guessing timestamps
- Creating high-cardinality Prometheus labels (e.g., user_id, order_id as label values) — causes memory exhaustion in the Prometheus server
- No exemplars on histograms — you lose the link between a slow bucket and the actual trace that caused it
<!-- LEVEL 3 END -->
