---
id: redis-caching
name: Redis Caching Expert
category: db-work
level1: "For Redis caching, pub/sub, TTL strategy, data structures, and eviction policies"
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 2
---

<!-- LEVEL 1 START -->
**Redis Caching Expert** — Activate for: Redis data structures, caching patterns, TTL, pub/sub, sorted sets, eviction, ioredis, redis-py, cache-aside, write-through.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## Redis Caching — Core Instructions

1. **Choose the right data structure.** String for simple values, Hash for objects, List for queues, Sorted Set for leaderboards/rate-limiting, Set for membership checks.
2. **Always set a TTL.** Every cache key must have an expiry — `SET key value EX 3600`. Keys without TTL accumulate and cause memory pressure.
3. **Use cache-aside pattern by default.** Read from cache → on miss, read DB → write to cache. Never write to cache and DB in the same transaction.
4. **Namespace your keys.** Use `app:entity:id` format (`user:session:abc123`). Avoids collisions and enables pattern-based deletion.
5. **Handle cache stampede.** On TTL expiry, multiple processes may hit DB simultaneously. Use a lock or probabilistic early expiration.
6. **Set maxmemory + eviction policy.** Default is `noeviction` (errors on full). Set `allkeys-lru` for caches, `volatile-lru` when only TTL keys should be evicted.
7. **Don't cache mutable results without invalidation.** Either use short TTLs or delete the key on write (`DEL user:123`) to prevent stale data.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## Redis Caching — Full Reference

### Core Data Structures

```python
import redis
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# String — simple values, counters
r.set('user:42:name', 'Alice', ex=3600)
r.incr('page:views:home')          # atomic counter
r.getdel('session:abc')            # get and delete atomically

# Hash — structured objects (avoids serializing entire JSON)
r.hset('user:42', mapping={'name': 'Alice', 'role': 'admin'})
r.hget('user:42', 'name')
r.hgetall('user:42')

# List — queues, recent items
r.lpush('job:queue', 'task1')      # push to head
r.rpop('job:queue')                # pop from tail (FIFO)
r.lrange('feed:42', 0, 9)          # last 10 items

# Sorted Set — leaderboards, rate limiting
r.zadd('leaderboard', {'alice': 1500, 'bob': 1200})
r.zrevrange('leaderboard', 0, 9, withscores=True)  # top 10

# Set — unique membership, tags
r.sadd('tags:post:1', 'python', 'redis')
r.sismember('tags:post:1', 'redis')   # O(1) membership check
```

### Caching Patterns

```python
# Cache-aside (lazy loading) — most common
def get_user(user_id: int) -> dict:
    cache_key = f"user:{user_id}"
    cached = r.get(cache_key)
    if cached:
        return json.loads(cached)
    user = db.query("SELECT * FROM users WHERE id = %s", user_id)
    r.set(cache_key, json.dumps(user), ex=300)
    return user

# Write-through — update cache on every write
def update_user(user_id: int, data: dict):
    db.execute("UPDATE users SET ... WHERE id = %s", user_id)
    r.set(f"user:{user_id}", json.dumps(data), ex=300)

# Cache invalidation on write
def delete_user_cache(user_id: int):
    r.delete(f"user:{user_id}")
    # Also delete related list caches
    r.delete("users:list:all")
```

### Rate Limiting with Sorted Sets

```python
def is_rate_limited(user_id: str, limit: int = 100, window: int = 60) -> bool:
    key = f"ratelimit:{user_id}"
    now = time.time()
    pipe = r.pipeline()
    pipe.zremrangebyscore(key, 0, now - window)     # remove old
    pipe.zadd(key, {str(now): now})                  # add current
    pipe.zcard(key)                                  # count
    pipe.expire(key, window)
    _, _, count, _ = pipe.execute()
    return count > limit
```

### Node.js with ioredis

```typescript
import Redis from 'ioredis';
const redis = new Redis({ host: 'localhost', port: 6379 });

// Pipeline for batching commands
const pipeline = redis.pipeline();
pipeline.set('key1', 'val1', 'EX', 3600);
pipeline.hset('user:42', 'name', 'Alice');
await pipeline.exec();

// Pub/Sub
const sub = new Redis();
const pub = new Redis();
sub.subscribe('events', (err, count) => {});
sub.on('message', (channel, message) => console.log(message));
pub.publish('events', JSON.stringify({ type: 'user.created' }));
```

### Eviction Policies

| Policy | Behavior | Use Case |
|--------|----------|----------|
| `allkeys-lru` | Evict least recently used keys | General cache |
| `volatile-lru` | Evict LRU among keys with TTL | Mixed cache+store |
| `allkeys-lfu` | Evict least frequently used | Hot/cold data |
| `noeviction` | Return error when full | Not for caches |

```bash
# redis.conf
maxmemory 512mb
maxmemory-policy allkeys-lru
```

### Anti-patterns to Avoid
- Storing large objects (> 100KB) — serialize to smaller structures or use S3
- Keys without TTL in a cache — causes unbounded growth
- Using `KEYS *` in production — O(N), blocks server; use `SCAN` instead
- One giant hash for all users — use separate keys per entity
- Relying on Redis as a primary datastore without persistence configured
<!-- LEVEL 3 END -->
