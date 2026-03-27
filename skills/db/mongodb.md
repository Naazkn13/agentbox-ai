---
id: mongodb
name: MongoDB Expert
category: db-work
level1: "For MongoDB schema design, aggregation pipelines, indexes, transactions, change streams, and Mongoose ODM"
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 1
---

<!-- LEVEL 1 START -->
**MongoDB Expert** — Activate for: MongoDB schema design, aggregation pipeline, indexes, BSON types, transactions, change streams, Atlas, Mongoose ODM patterns, and avoiding N+1 queries.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## MongoDB — Core Instructions

1. **Embed for locality, reference for sharing:** embed sub-documents when data is read together and owned by one parent; use references (`ObjectId`) when data is shared across many documents or grows unboundedly.
2. **Always create indexes for query patterns:** every field used in `.find()` filters, `.sort()`, and aggregation `$match` stages must have an index — use `explain("executionStats")` to confirm index usage.
3. **Avoid unbounded arrays:** never embed arrays that can grow indefinitely (e.g., all comments on a post) — this hits the 16 MB document limit; use a separate collection instead.
4. **Use the aggregation pipeline for complex reads:** `$lookup`, `$group`, `$project`, `$unwind` — never pull large datasets into application memory to compute what MongoDB can do server-side.
5. **Use multi-document transactions only when truly needed:** transactions carry overhead; prefer single-document atomicity by embedding related data, or use compensating writes (saga pattern) for cross-collection operations.
6. **Always project only needed fields:** pass a projection to `.find()` and aggregation `$project` — never return full documents when you need 3 fields.
7. **Avoid N+1 in Mongoose:** use `.populate()` sparingly; prefer aggregation with `$lookup` for bulk reads, and never call `.populate()` inside a loop.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## MongoDB — Full Reference

### Schema Design Patterns

**Embed (one-to-few, ownership):**
```javascript
// Good: address is owned by user, always read together
{
  _id: ObjectId("..."),
  name: "Alice",
  address: {
    street: "123 Main St",
    city: "Austin",
    zip: "78701"
  }
}
```

**Reference (one-to-many, shared):**
```javascript
// orders collection — references user by ID
{
  _id: ObjectId("..."),
  userId: ObjectId("user_id_here"),  // reference
  items: [
    { productId: ObjectId("..."), qty: 2, price: 1999 }
  ],
  totalCents: 3998,
  createdAt: ISODate("2026-03-26T10:00:00Z")
}
```

**Bucket pattern (unbounded time-series):**
```javascript
// Instead of one doc per measurement, bucket by hour
{
  _id: ObjectId("..."),
  sensorId: "sensor-42",
  hour: ISODate("2026-03-26T10:00:00Z"),
  count: 60,
  readings: [
    { ts: ISODate("2026-03-26T10:00:05Z"), value: 23.4 },
    // ... up to 60 readings per bucket
  ]
}
```

### Index Strategy
```javascript
// Single field
db.orders.createIndex({ userId: 1 });

// Compound — field order matters: equality first, sort second, range last
db.orders.createIndex({ userId: 1, createdAt: -1 });

// Partial index — only index completed orders (saves space)
db.orders.createIndex(
  { createdAt: -1 },
  { partialFilterExpression: { status: "completed" } }
);

// Text index for search
db.products.createIndex({ name: "text", description: "text" });

// TTL index — auto-delete documents after expiry
db.sessions.createIndex({ expiresAt: 1 }, { expireAfterSeconds: 0 });

// Check index usage
db.orders.find({ userId: ObjectId("...") }).explain("executionStats");
// Look for: IXSCAN (good) vs COLLSCAN (bad)
```

### Aggregation Pipeline
```javascript
// Report: total revenue per user for the last 30 days
db.orders.aggregate([
  // Stage 1: filter early to limit documents
  {
    $match: {
      status: "completed",
      createdAt: { $gte: new Date(Date.now() - 30 * 86400 * 1000) }
    }
  },
  // Stage 2: group and compute
  {
    $group: {
      _id: "$userId",
      totalRevenue: { $sum: "$totalCents" },
      orderCount:   { $sum: 1 },
      avgOrderValue: { $avg: "$totalCents" }
    }
  },
  // Stage 3: join with users collection
  {
    $lookup: {
      from: "users",
      localField: "_id",
      foreignField: "_id",
      as: "user",
      pipeline: [{ $project: { name: 1, email: 1 } }]  // sub-pipeline projection
    }
  },
  { $unwind: "$user" },
  // Stage 4: shape output
  {
    $project: {
      _id: 0,
      userId: "$_id",
      userName: "$user.name",
      userEmail: "$user.email",
      totalRevenueCents: "$totalRevenue",
      orderCount: 1
    }
  },
  { $sort: { totalRevenueCents: -1 } },
  { $limit: 100 }
]);
```

### Multi-Document Transactions
```javascript
const session = await client.startSession();
try {
  await session.withTransaction(async () => {
    // Both operations succeed or both roll back
    await db.collection("accounts").updateOne(
      { _id: fromAccountId },
      { $inc: { balanceCents: -amount } },
      { session }
    );
    await db.collection("accounts").updateOne(
      { _id: toAccountId },
      { $inc: { balanceCents: amount } },
      { session }
    );
  });
} finally {
  await session.endSession();
}
```

### Change Streams (Real-time)
```javascript
// Watch for new completed orders
const pipeline = [
  { $match: { "fullDocument.status": "completed", operationType: "update" } }
];
const changeStream = db.collection("orders").watch(pipeline, {
  fullDocument: "updateLookup"  // include the full updated document
});

changeStream.on("change", (change) => {
  console.log("Order completed:", change.fullDocument._id);
  // emit to websocket, trigger notification, etc.
});

// Resume after restart using resume token
const token = loadResumeToken(); // persist this to DB/file
const stream = db.collection("orders").watch(pipeline, {
  resumeAfter: token,
  fullDocument: "updateLookup"
});
stream.on("change", (change) => {
  persistResumeToken(change._id); // save after each event
});
```

### Mongoose ODM Patterns
```typescript
import mongoose, { Schema, Document, Model } from "mongoose";

interface IOrder extends Document {
  userId: mongoose.Types.ObjectId;
  totalCents: number;
  status: "pending" | "completed" | "failed";
  createdAt: Date;
}

const orderSchema = new Schema<IOrder>(
  {
    userId:     { type: Schema.Types.ObjectId, ref: "User", required: true, index: true },
    totalCents: { type: Number, required: true, min: 0 },
    status:     { type: String, enum: ["pending", "completed", "failed"], default: "pending" },
  },
  { timestamps: true }  // adds createdAt and updatedAt automatically
);

// Compound index at schema level
orderSchema.index({ userId: 1, createdAt: -1 });

// Instance method
orderSchema.methods.complete = async function () {
  this.status = "completed";
  return this.save();
};

// Static method
orderSchema.statics.findByUser = function (userId: string) {
  return this.find({ userId }).sort({ createdAt: -1 }).limit(50);
};

export const Order: Model<IOrder> = mongoose.model("Order", orderSchema);

// Efficient bulk read — aggregation instead of populate-in-loop
async function getUsersWithOrderCounts(userIds: string[]) {
  return Order.aggregate([
    { $match: { userId: { $in: userIds.map(id => new mongoose.Types.ObjectId(id)) } } },
    { $group: { _id: "$userId", count: { $sum: 1 } } }
  ]);
}
```

### Atlas Search (Full-Text)
```javascript
// Create a search index in Atlas UI or via API, then query:
db.products.aggregate([
  {
    $search: {
      index: "products_search",
      text: {
        query: "wireless headphones",
        path: ["name", "description"],
        fuzzy: { maxEdits: 1 }
      }
    }
  },
  { $limit: 20 },
  {
    $project: {
      name: 1, price: 1,
      score: { $meta: "searchScore" }
    }
  },
  { $sort: { score: -1 } }
]);
```

### Anti-patterns to Avoid
- Never design schemas around the data shape — design around your query patterns.
- Never embed arrays that grow without bound — use a separate collection with a reference.
- Never skip projections on large documents — always specify which fields you need.
- Never run aggregations without a `$match` as the first stage — always filter early.
- Never call `.populate()` inside a loop — use `$lookup` in the aggregation pipeline instead.
- Never ignore `_id` index efficiency — ObjectId values are time-ordered; use them for range queries on creation time when possible.
<!-- LEVEL 3 END -->
