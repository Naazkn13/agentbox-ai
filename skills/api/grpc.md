---
id: grpc
name: gRPC & Protobuf Expert
category: api-work
level1: "For defining .proto files, gRPC services, code generation, streaming, interceptors, and buf tooling"
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 1
---

<!-- LEVEL 1 START -->
**gRPC & Protobuf Expert** — Activate for: .proto file design, gRPC service definitions, unary/streaming RPCs, protobuf code generation, gRPC error codes, metadata, interceptors, deadlines, gRPC-web, buf tool.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## gRPC & Protobuf — Core Instructions

1. **Use proto3 syntax always:** declare `syntax = "proto3";` at the top; never use proto2 for new services.
2. **Never change field numbers:** once a field number is used in production, it is permanent — removing a field means reserving its number with `reserved`.
3. **Map gRPC status codes correctly:** use `NOT_FOUND` (5), `INVALID_ARGUMENT` (3), `ALREADY_EXISTS` (6), `UNAUTHENTICATED` (16), `PERMISSION_DENIED` (7), `INTERNAL` (13) — never return raw `UNKNOWN`.
4. **Always set deadlines on the client side:** never make an RPC without a context deadline/timeout; servers must respect `ctx.Done()`.
5. **Use interceptors for cross-cutting concerns:** logging, auth token injection, retry, and metrics belong in unary/stream interceptors, not in handler code.
6. **Prefer server-streaming over polling:** if a client needs to watch for updates, use server-streaming RPC instead of repeated unary calls.
7. **Manage .proto files with buf:** use `buf.yaml` + `buf.gen.yaml` for linting, breaking-change detection, and multi-language code generation instead of raw `protoc`.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## gRPC & Protobuf — Full Reference

### .proto File Structure
```protobuf
syntax = "proto3";

package payments.v1;

option go_package = "github.com/myorg/myapp/gen/go/payments/v1;paymentsv1";
option java_package = "com.myorg.payments.v1";

import "google/protobuf/timestamp.proto";
import "google/protobuf/empty.proto";

// ---- Messages ----

message Payment {
  string id           = 1;
  int64  amount_cents = 2;
  string currency     = 3;
  PaymentStatus status = 4;
  google.protobuf.Timestamp created_at = 5;
}

enum PaymentStatus {
  PAYMENT_STATUS_UNSPECIFIED = 0;  // always have a zero/unspecified value
  PAYMENT_STATUS_PENDING     = 1;
  PAYMENT_STATUS_COMPLETED   = 2;
  PAYMENT_STATUS_FAILED      = 3;
}

message CreatePaymentRequest {
  int64  amount_cents = 1;
  string currency     = 2;
  string idempotency_key = 3;
}

message CreatePaymentResponse {
  Payment payment = 1;
}

// ---- Service ----

service PaymentService {
  rpc CreatePayment(CreatePaymentRequest) returns (CreatePaymentResponse);
  rpc GetPayment(GetPaymentRequest)       returns (Payment);
  rpc ListPayments(ListPaymentsRequest)   returns (stream Payment);    // server-streaming
  rpc SubscribeEvents(google.protobuf.Empty) returns (stream PaymentEvent); // server-streaming watch
}
```

### Reserved Fields (Safe Deletion Pattern)
```protobuf
message User {
  string id    = 1;
  string email = 2;
  // string phone = 3;  <-- removed in v2
  reserved 3;
  reserved "phone";  // prevents future reuse of both number and name
  string name  = 4;
}
```

### buf Setup
```yaml
# buf.yaml
version: v2
lint:
  use:
    - DEFAULT
breaking:
  use:
    - FILE
```

```yaml
# buf.gen.yaml
version: v2
plugins:
  - plugin: buf.build/protocolbuffers/go
    out: gen/go
    opt: paths=source_relative
  - plugin: buf.build/grpc/go
    out: gen/go
    opt: paths=source_relative
  - plugin: buf.build/protocolbuffers/python
    out: gen/python
```

```bash
# lint and check for breaking changes
buf lint
buf breaking --against '.git#branch=main'
# generate code
buf generate
```

### gRPC Server (Go) with Interceptors
```go
package main

import (
    "context"
    "log"
    "net"
    "time"

    "google.golang.org/grpc"
    "google.golang.org/grpc/codes"
    "google.golang.org/grpc/metadata"
    "google.golang.org/grpc/status"
    pb "github.com/myorg/myapp/gen/go/payments/v1"
)

// Unary interceptor for auth + logging
func authInterceptor(ctx context.Context, req interface{}, info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (interface{}, error) {
    md, ok := metadata.FromIncomingContext(ctx)
    if !ok {
        return nil, status.Error(codes.Unauthenticated, "missing metadata")
    }
    tokens := md.Get("authorization")
    if len(tokens) == 0 {
        return nil, status.Error(codes.Unauthenticated, "missing authorization token")
    }
    // validate token...
    start := time.Now()
    resp, err := handler(ctx, req)
    log.Printf("method=%s duration=%s err=%v", info.FullMethod, time.Since(start), err)
    return resp, err
}

func main() {
    lis, _ := net.Listen("tcp", ":50051")
    srv := grpc.NewServer(
        grpc.UnaryInterceptor(authInterceptor),
        grpc.MaxRecvMsgSize(4*1024*1024), // 4 MB
    )
    pb.RegisterPaymentServiceServer(srv, &paymentServer{})
    log.Fatal(srv.Serve(lis))
}
```

### gRPC Client (Go) with Deadline
```go
conn, err := grpc.NewClient("localhost:50051",
    grpc.WithTransportCredentials(insecure.NewCredentials()),
)
client := pb.NewPaymentServiceClient(conn)

// Always set a deadline
ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
defer cancel()

resp, err := client.CreatePayment(ctx, &pb.CreatePaymentRequest{
    AmountCents:    1000,
    Currency:       "USD",
    IdempotencyKey: "order-abc-123",
})
if err != nil {
    st, _ := status.FromError(err)
    switch st.Code() {
    case codes.AlreadyExists:
        // idempotent — treat as success
    case codes.DeadlineExceeded:
        // retry with backoff
    default:
        log.Printf("RPC failed: %v", st.Message())
    }
}
```

### Server-Streaming RPC (Go)
```go
func (s *paymentServer) ListPayments(req *pb.ListPaymentsRequest, stream pb.PaymentService_ListPaymentsServer) error {
    payments := fetchPayments(req)
    for _, p := range payments {
        if err := stream.Context().Err(); err != nil {
            return status.FromContextError(err).Err() // client disconnected
        }
        if err := stream.Send(p); err != nil {
            return err
        }
    }
    return nil
}
```

### gRPC Status Codes Reference
```
OK (0)                — success
CANCELLED (1)         — caller cancelled the request
UNKNOWN (2)           — avoid; use a specific code
INVALID_ARGUMENT (3)  — bad input from caller (like 400)
DEADLINE_EXCEEDED (4) — timeout before completion
NOT_FOUND (5)         — resource not found (like 404)
ALREADY_EXISTS (6)    — resource already exists (like 409)
PERMISSION_DENIED (7) — authenticated but not authorized (like 403)
RESOURCE_EXHAUSTED (8)— quota exceeded / rate limited (like 429)
FAILED_PRECONDITION(9)— system not in required state
ABORTED (10)          — concurrency conflict (retry at higher level)
INTERNAL (13)         — unexpected server error (like 500)
UNAVAILABLE (14)      — server temporarily unavailable (retry)
UNAUTHENTICATED (16)  — no valid credentials (like 401)
```

### gRPC-Web (Browser Clients)
```typescript
// Using @connectrpc/connect-web (modern alternative to grpc-web)
import { createConnectTransport } from "@connectrpc/connect-web";
import { createClient } from "@connectrpc/connect";
import { PaymentService } from "./gen/payments/v1/payment_connect";

const transport = createConnectTransport({ baseUrl: "https://api.example.com" });
const client = createClient(PaymentService, transport);

const response = await client.createPayment({
  amountCents: BigInt(1000),
  currency: "USD",
  idempotencyKey: crypto.randomUUID(),
});
```

### Anti-patterns to Avoid
- Never reuse a field number after removing a field — always `reserved` it.
- Never skip deadlines on the client; a missing timeout can block goroutines indefinitely.
- Never put business logic inside interceptors — they are for cross-cutting concerns only.
- Never return `UNKNOWN` status — pick the most specific code available.
- Never expose internal error messages to callers — wrap with `status.Errorf(codes.Internal, "internal error")`.
- Never mutate a proto message after sending it over a stream — proto messages are not thread-safe for writes.
<!-- LEVEL 3 END -->
