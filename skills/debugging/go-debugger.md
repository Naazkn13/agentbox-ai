---
id: go-debugger
name: Go Debugger
category: debugging
level1: "For Go panics, nil dereferences, goroutine leaks, and race conditions"
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 1
---

<!-- LEVEL 1 START -->
**Go Debugger** — Activate for: Go panics, nil pointer dereference, goroutine leak, race condition, deadlock, pprof profiling, delve debugger, index out of range, interface conversion error.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## Go Debugger — Core Instructions

1. **Read the full panic stack trace** — Go prints every goroutine's stack. The failing goroutine is first; find the topmost frame inside your own package, not the stdlib.
2. **Nil pointer dereferences are always a missing initialization or unexpected nil return** — trace back to where the pointer was set; add a nil guard or return an explicit error instead of a bare nil.
3. **Run with the race detector before calling anything a race** — `go test -race ./...` or `go run -race main.go`. The data race report shows both conflicting goroutines with file/line numbers.
4. **Goroutine leaks: every goroutine you start must have a defined exit path** — use `context.Context` for cancellation; verify with `runtime.NumGoroutine()` or `goleak` in tests.
5. **Use `dlv` (Delve) for interactive debugging** — `dlv debug ./cmd/app` then `break`, `continue`, `print`, `goroutines`, `frame`. Never guess when you can inspect live state.
6. **Profile before optimising** — attach pprof, collect a CPU or heap profile, look at the top 5 functions. Never optimise by intuition in Go.
7. **One hypothesis at a time** — add a single `log.Printf` or breakpoint, confirm, then fix. Changing multiple things makes Go's deterministic tooling useless.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## Go Debugger — Full Reference

### Common Panic Patterns

**runtime error: invalid memory address or nil pointer dereference**
- The pointer was never initialised, or a function returned nil without an error check.
- Pattern: `resp, _ := http.Get(url)` then `resp.Body.Read(...)` — if `http.Get` failed, `resp` is nil.
- Fix: always check the error, never use blank identifier `_` for errors in production code.

**runtime error: index out of range [N] with length M**
- Slice/array access without a bounds check. Confirm length before indexing.
- Fix: use a range loop or guard with `if i < len(s)`.

**interface conversion: interface {} is nil, not T**
- A type assertion on a nil interface panics. Use the comma-ok form: `v, ok := i.(T)`.

**all goroutines are asleep — deadlock!**
- Every goroutine is blocked on a channel or mutex with no writer/unlocker.
- Cause: sending to an unbuffered channel with no receiver, or double-locking a non-RW mutex.
- Fix: use `select { case ch <- v: default: }` to avoid blocking sends, or switch to `sync.RWMutex`.

### Delve Debugger

```bash
# Install
go install github.com/go-delve/delve/cmd/dlv@latest

# Debug a main package
dlv debug ./cmd/server -- --port 8080

# Attach to a running process
dlv attach <PID>

# Debug tests
dlv test ./pkg/mypackage -- -run TestMyFunc
```

```
# Common Delve commands inside the session
(dlv) break main.go:42           # set breakpoint at line
(dlv) break pkg.(*Server).Start  # set breakpoint at method
(dlv) continue                   # run until next breakpoint
(dlv) next                       # step over
(dlv) step                       # step into
(dlv) stepout                    # step out of current function
(dlv) print req                  # inspect variable
(dlv) locals                     # print all local variables
(dlv) goroutines                 # list all goroutines
(dlv) goroutine 5 bt             # stack trace for goroutine 5
(dlv) frame 3                    # switch to stack frame 3
(dlv) watch -w myVar             # watchpoint on variable write
```

### Race Condition Detection

```bash
# Run tests with race detector (always do this in CI)
go test -race ./...

# Run a binary with race detector
go run -race main.go

# Example race detector output:
# WARNING: DATA RACE
# Write at 0x00c0001b4010 by goroutine 7:
#   main.increment()  main.go:14
# Previous read at 0x00c0001b4010 by goroutine 6:
#   main.increment()  main.go:12
```

```go
// WRONG — race on counter
var counter int
go func() { counter++ }()
go func() { fmt.Println(counter) }()

// CORRECT — use sync/atomic or a mutex
var counter int64
go func() { atomic.AddInt64(&counter, 1) }()
go func() { fmt.Println(atomic.LoadInt64(&counter)) }()

// CORRECT — mutex guard
var mu sync.Mutex
var counter int
go func() { mu.Lock(); counter++; mu.Unlock() }()
```

### Goroutine Leak Detection

```go
// In tests — use goleak
import "go.uber.org/goleak"

func TestServer(t *testing.T) {
    defer goleak.VerifyNone(t)
    // test code that starts goroutines
}

// Manual check during development
func printGoroutineCount(label string) {
    fmt.Printf("[%s] goroutines: %d\n", label, runtime.NumGoroutine())
}

// Pattern: always pass context for cancellation
func worker(ctx context.Context, jobs <-chan Job) {
    for {
        select {
        case <-ctx.Done():
            return  // clean exit — no leak
        case j, ok := <-jobs:
            if !ok {
                return
            }
            process(j)
        }
    }
}
```

### pprof Profiling

```go
// Add to your HTTP server
import _ "net/http/pprof"

func main() {
    go http.ListenAndServe("localhost:6060", nil)  // pprof endpoint
    // ... rest of app
}
```

```bash
# Capture 30-second CPU profile
go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30

# Capture heap profile
go tool pprof http://localhost:6060/debug/pprof/heap

# Inside pprof interactive shell
(pprof) top10           # top 10 functions by CPU/memory
(pprof) list myFunc     # annotated source for a function
(pprof) web             # open flame graph in browser (requires graphviz)

# One-shot flame graph (go 1.19+)
curl -s "http://localhost:6060/debug/pprof/profile?seconds=10" > cpu.prof
go tool pprof -http=:8080 cpu.prof
```

### Structured Logging for Debugging

```go
import "log/slog"

logger := slog.New(slog.NewJSONHandler(os.Stderr, &slog.HandlerOptions{
    Level: slog.LevelDebug,
}))

// Log with context fields — easy to grep
logger.Debug("processing request",
    "method", r.Method,
    "path", r.URL.Path,
    "user_id", userID,
)

// Wrap errors with context (errors package)
if err != nil {
    return fmt.Errorf("fetchUser(%d): %w", id, err)
}
```

### Anti-patterns to Avoid
- Ignoring errors with `_` — every ignored error is a potential nil dereference or silent failure.
- Launching goroutines without a cancellation mechanism — always pass `context.Context`.
- Catching panics with `recover` to hide bugs — only use `recover` at service boundaries, log the panic and the stack.
- Optimising without profiling — Go's inliner and escape analysis make intuition unreliable.
- Using `fmt.Println` in concurrent code for "quick" debugging — output interleaves and hides the actual sequence; use structured logging with timestamps.
<!-- LEVEL 3 END -->
