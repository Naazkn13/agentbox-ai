---
id: database-migrations
name: Database Migrations Expert
category: db-work
level1: "For writing safe database migrations — zero-downtime, rollback strategies, expand/contract"
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 1
---

<!-- LEVEL 1 START -->
**Database Migrations Expert** — Activate for: writing migrations, schema changes, renaming columns, adding indexes, zero-downtime deploys, rollback scripts, Alembic, Flyway, Knex, Liquibase, migration ordering.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## Database Migrations Expert — Core Instructions

1. **Additive changes only on first deploy** — never rename or drop a column in a single migration. Use the expand/contract pattern across multiple deploys.
2. **Always write a down migration** — every `up` must have a tested `down`. If a rollback is destructive (data loss), document it explicitly and gate it behind a flag.
3. **Never rename a column directly** — add the new column, backfill data, update all code, then drop the old column in a separate later migration.
4. **Test rollback before merging** — run `migrate up` then `migrate down` then `migrate up` in CI. If down is a no-op, mark it as intentional, never leave it blank.
5. **Add indexes concurrently on live tables** — `CREATE INDEX CONCURRENTLY` in Postgres; plain `CREATE INDEX` locks the table. Use the non-locking form in production migrations.
6. **Keep migrations idempotent** — wrap DDL in existence checks (`IF NOT EXISTS`, `IF EXISTS`) so re-running a migration does not error.
7. **Order and number migrations consistently** — use timestamp prefixes (e.g., `20240315_001_add_user_status.sql`) and never reorder or edit a migration that has already run in any environment.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## Database Migrations Expert — Full Reference

### The Expand/Contract Pattern (Zero-Downtime Column Rename)

Rename `users.name` to `users.full_name` across 3 deploys without downtime:

**Phase 1 — Expand (add new column, keep old)**
```sql
-- Migration: 20240315_001_expand_add_full_name.sql
ALTER TABLE users ADD COLUMN full_name VARCHAR(255);

-- Backfill existing rows
UPDATE users SET full_name = name WHERE full_name IS NULL;

-- Keep both columns in sync via trigger (Postgres)
CREATE OR REPLACE FUNCTION sync_name_columns()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.name IS DISTINCT FROM OLD.name THEN
    NEW.full_name := NEW.name;
  END IF;
  IF NEW.full_name IS DISTINCT FROM OLD.full_name THEN
    NEW.name := NEW.full_name;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_sync_name
BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION sync_name_columns();
```

**Phase 2 — Migrate application code** — update all reads and writes to use `full_name`. Deploy application. Both columns stay live.

**Phase 3 — Contract (drop old column)**
```sql
-- Migration: 20240402_001_contract_drop_name.sql
DROP TRIGGER IF EXISTS trg_sync_name ON users;
DROP FUNCTION IF EXISTS sync_name_columns();
ALTER TABLE users DROP COLUMN name;
```

---

### Alembic (Python / SQLAlchemy)

```python
# alembic/versions/20240315_001_add_user_status.py
"""add user status column

Revision ID: a1b2c3d4e5f6
Revises: 9f8e7d6c5b4a
Create Date: 2024-03-15 10:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = '9f8e7d6c5b4a'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'users',
        sa.Column('status', sa.String(50), nullable=False, server_default='active')
    )
    # Add index concurrently (Postgres only)
    op.create_index(
        'ix_users_status',
        'users',
        ['status'],
        postgresql_concurrently=True
    )


def downgrade():
    op.drop_index('ix_users_status', table_name='users')
    op.drop_column('users', 'status')
```

```bash
# Common Alembic commands
alembic upgrade head           # apply all pending migrations
alembic downgrade -1           # roll back one migration
alembic current                # show current revision
alembic history --verbose      # list all revisions
alembic revision --autogenerate -m "add user status"  # generate from model diff
```

---

### Flyway (Java / SQL-first)

```sql
-- V20240315__add_user_status.sql  (versioned migration)
ALTER TABLE users
  ADD COLUMN status VARCHAR(50) NOT NULL DEFAULT 'active';

CREATE INDEX CONCURRENTLY idx_users_status ON users(status);
```

```sql
-- U20240315__add_user_status.sql  (undo migration — Flyway Teams)
DROP INDEX IF EXISTS idx_users_status;
ALTER TABLE users DROP COLUMN status;
```

```bash
# flyway.conf
flyway.url=jdbc:postgresql://localhost:5432/mydb
flyway.user=myuser
flyway.password=secret
flyway.locations=filesystem:db/migrations

# Commands
flyway migrate    # apply pending
flyway info       # show status of all migrations
flyway validate   # verify checksums match
flyway repair     # fix failed migration records
```

---

### Knex (Node.js)

```js
// migrations/20240315_001_add_user_status.js
exports.up = async (knex) => {
  await knex.schema.alterTable('users', (table) => {
    table.string('status', 50).notNullable().defaultTo('active');
    table.index(['status'], 'idx_users_status');
  });
};

exports.down = async (knex) => {
  await knex.schema.alterTable('users', (table) => {
    table.dropIndex(['status'], 'idx_users_status');
    table.dropColumn('status');
  });
};
```

```bash
npx knex migrate:latest       # run pending migrations
npx knex migrate:rollback     # roll back last batch
npx knex migrate:status       # list migration state
```

---

### Liquibase (XML / YAML)

```yaml
# changelog/20240315-add-user-status.yaml
databaseChangeLog:
  - changeSet:
      id: 20240315-001
      author: ajay
      changes:
        - addColumn:
            tableName: users
            columns:
              - column:
                  name: status
                  type: VARCHAR(50)
                  constraints:
                    nullable: false
                  defaultValue: active
        - createIndex:
            indexName: idx_users_status
            tableName: users
            columns:
              - column:
                  name: status
      rollback:
        - dropIndex:
            indexName: idx_users_status
            tableName: users
        - dropColumn:
            tableName: users
            columnName: status
```

---

### Idempotent Migration Patterns

```sql
-- Safe column add (Postgres)
ALTER TABLE users ADD COLUMN IF NOT EXISTS status VARCHAR(50) NOT NULL DEFAULT 'active';

-- Safe index creation
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);

-- Safe index creation without locking (Postgres)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_status ON users(status);

-- Safe table creation
CREATE TABLE IF NOT EXISTS audit_log (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL,
  action VARCHAR(100) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

### Large Table Backfills

Never update millions of rows in a single transaction — it locks the table and can exhaust WAL/undo logs.

```python
# Alembic: batched backfill
def upgrade():
    op.add_column('events', sa.Column('processed', sa.Boolean(), nullable=True))

    # Backfill in batches of 10k to avoid long locks
    conn = op.get_bind()
    batch_size = 10_000
    while True:
        result = conn.execute(
            """
            UPDATE events
            SET processed = false
            WHERE processed IS NULL
              AND id IN (
                SELECT id FROM events WHERE processed IS NULL LIMIT :batch
              )
            """,
            {"batch": batch_size}
        )
        if result.rowcount == 0:
            break

    # Make NOT NULL only after backfill is complete
    op.alter_column('events', 'processed', nullable=False)
```

---

### CI/CD Integration

```yaml
# GitHub Actions: run migrations before deploying app
- name: Run database migrations
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
  run: |
    alembic upgrade head
    # or: flyway migrate / npx knex migrate:latest

- name: Verify migration state
  run: alembic current

- name: Deploy application
  run: ./deploy.sh
```

---

### Migration Ordering Rules

- Timestamp-prefix all files: `YYYYMMDD_NNN_description`
- Never edit a migration that has been applied to any environment — create a new one
- Never reorder migrations — the dependency chain (`down_revision` in Alembic, ordering in Flyway) is load-bearing
- Keep one migration per logical change — do not bundle unrelated DDL

---

### Anti-patterns to Avoid
- Renaming a column in a single migration while the app is live — this causes immediate downtime
- Leaving `downgrade()` / `rollback` empty — makes incident recovery impossible
- Using `CREATE INDEX` (non-concurrent) on a live table — takes an exclusive lock for minutes on large tables
- Bundling data migrations with schema migrations in the same transaction — data migrations can be slow and should run separately
- Editing or deleting an already-applied migration file — checksums will fail and tooling will refuse to run
- Adding `NOT NULL` columns without a `DEFAULT` on a non-empty table — most databases will reject this or lock the table during backfill
<!-- LEVEL 3 END -->
