-- AgentKit — Layer 2: Project Memory Graph
-- SQLite schema for the persistent project knowledge graph.
-- Applied once via: sqlite3 memory.db < schema.sql

PRAGMA journal_mode = WAL;       -- better concurrency for hook writes
PRAGMA foreign_keys = ON;
PRAGMA synchronous = NORMAL;     -- safe + fast for our write pattern

-- ---------------------------------------------------------------------------
-- Entities: files, functions, API routes, packages, concepts
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS entities (
    id              TEXT PRIMARY KEY,       -- e.g. "file:src/auth/jwt.py", "api:POST /auth/login"
    type            TEXT NOT NULL,          -- file | function | api | package | concept | command
    name            TEXT NOT NULL,          -- human-readable name
    path            TEXT,                   -- filesystem path (if applicable)
    description     TEXT,                   -- 1-2 sentence summary
    raw_snippet     TEXT,                   -- short source snippet (≤300 chars)
    confidence      REAL    DEFAULT 1.0,    -- 0.0–1.0, decays when file changes
    source_session  TEXT    NOT NULL,       -- session ID that created this
    created_at      INTEGER NOT NULL,       -- unix timestamp
    updated_at      INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_entities_type     ON entities(type);
CREATE INDEX IF NOT EXISTS idx_entities_path     ON entities(path);
CREATE INDEX IF NOT EXISTS idx_entities_session  ON entities(source_session);
CREATE INDEX IF NOT EXISTS idx_entities_updated  ON entities(updated_at DESC);

-- Full-text search over name + description
CREATE VIRTUAL TABLE IF NOT EXISTS entities_fts USING fts5(
    id UNINDEXED,
    name,
    description,
    content = 'entities',
    content_rowid = 'rowid'
);

-- Keep FTS in sync with entities table
CREATE TRIGGER IF NOT EXISTS entities_fts_insert
    AFTER INSERT ON entities BEGIN
        INSERT INTO entities_fts(rowid, id, name, description)
        VALUES (new.rowid, new.id, new.name, COALESCE(new.description, ''));
    END;

CREATE TRIGGER IF NOT EXISTS entities_fts_update
    AFTER UPDATE ON entities BEGIN
        UPDATE entities_fts SET name = new.name, description = COALESCE(new.description, '')
        WHERE rowid = new.rowid;
    END;

CREATE TRIGGER IF NOT EXISTS entities_fts_delete
    AFTER DELETE ON entities BEGIN
        DELETE FROM entities_fts WHERE rowid = old.rowid;
    END;

-- ---------------------------------------------------------------------------
-- Relationships between entities
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS relationships (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    from_id         TEXT    NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    to_id           TEXT    NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    type            TEXT    NOT NULL,   -- depends-on | calls | tested-by | implements | uses | related-to
    weight          REAL    DEFAULT 1.0,
    source_session  TEXT,
    created_at      INTEGER NOT NULL,
    UNIQUE(from_id, to_id, type)        -- no duplicate edges
);

CREATE INDEX IF NOT EXISTS idx_rel_from   ON relationships(from_id);
CREATE INDEX IF NOT EXISTS idx_rel_to     ON relationships(to_id);
CREATE INDEX IF NOT EXISTS idx_rel_type   ON relationships(type);

-- ---------------------------------------------------------------------------
-- Decisions: architecture, security, patterns, conventions
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS decisions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    title           TEXT    NOT NULL,
    content         TEXT    NOT NULL,   -- the full decision text
    category        TEXT    NOT NULL,   -- architecture | api | db | security | pattern | convention | bug-fix
    tags            TEXT,               -- JSON array: ["auth", "jwt"]
    session_id      TEXT    NOT NULL,
    confidence      REAL    DEFAULT 1.0,
    created_at      INTEGER NOT NULL,
    updated_at      INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_decisions_category ON decisions(category);
CREATE INDEX IF NOT EXISTS idx_decisions_session  ON decisions(session_id);
CREATE INDEX IF NOT EXISTS idx_decisions_updated  ON decisions(updated_at DESC);

CREATE VIRTUAL TABLE IF NOT EXISTS decisions_fts USING fts5(
    id UNINDEXED,
    title,
    content,
    category,
    content = 'decisions',
    content_rowid = 'rowid'
);

CREATE TRIGGER IF NOT EXISTS decisions_fts_insert
    AFTER INSERT ON decisions BEGIN
        INSERT INTO decisions_fts(rowid, id, title, content, category)
        VALUES (new.rowid, new.id, new.title, new.content, new.category);
    END;

CREATE TRIGGER IF NOT EXISTS decisions_fts_update
    AFTER UPDATE ON decisions BEGIN
        UPDATE decisions_fts SET title = new.title, content = new.content, category = new.category
        WHERE rowid = new.rowid;
    END;

CREATE TRIGGER IF NOT EXISTS decisions_fts_delete
    AFTER DELETE ON decisions BEGIN
        DELETE FROM decisions_fts WHERE rowid = old.rowid;
    END;

-- ---------------------------------------------------------------------------
-- Sessions: per-session metadata + AI-compressed summary
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sessions (
    id              TEXT    PRIMARY KEY,
    started_at      INTEGER NOT NULL,
    ended_at        INTEGER,
    summary         TEXT,               -- AI-compressed ~500 token handoff
    entity_count    INTEGER DEFAULT 0,
    decision_count  INTEGER DEFAULT 0,
    total_tokens    INTEGER DEFAULT 0,
    total_cost      REAL    DEFAULT 0.0,
    cwd             TEXT
);

CREATE INDEX IF NOT EXISTS idx_sessions_started ON sessions(started_at DESC);
