"""
AgentKit — Layer 2: Session Recorder
Captures high-value knowledge from tool use events and stores it in the
SQLite knowledge graph. Called by the memory_recorder hook (PostToolUse).

What gets captured:
  Read tool   → file purpose, functions, API routes, imports/packages
  Edit tool   → file change recorded, entity confidence updated
  Bash tool   → successful commands + working patterns
"""

import re
import os
import sys
import json
import time
import sqlite3
from dataclasses import dataclass, field
from typing import Optional

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    type: str           # file | function | api | package | concept | command
    name: str
    path: Optional[str] = None
    description: Optional[str] = None
    raw_snippet: Optional[str] = None
    confidence: float = 1.0


@dataclass
class Relationship:
    from_id: str
    to_id: str
    type: str           # depends-on | calls | tested-by | implements | uses | related-to
    weight: float = 1.0


# ---------------------------------------------------------------------------
# Entity extractors
# ---------------------------------------------------------------------------

# Python function / class definitions
_PY_FUNC_RE  = re.compile(r"^(?:async\s+)?def\s+(\w+)\s*\(", re.MULTILINE)
_PY_CLASS_RE = re.compile(r"^class\s+(\w+)[\s:(]", re.MULTILINE)
_PY_IMPORT_RE = re.compile(r"^(?:import|from)\s+([\w.]+)", re.MULTILINE)

# JS/TS function / class / arrow definitions
_JS_FUNC_RE  = re.compile(r"(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s*)?\()", re.MULTILINE)
_JS_CLASS_RE = re.compile(r"\bclass\s+(\w+)", re.MULTILINE)
_JS_IMPORT_RE = re.compile(r"""(?:import|require)\s*\(?['"]([\w@/.-]+)['"]""", re.MULTILINE)

# Express / FastAPI / NestJS route patterns
_ROUTE_PATTERNS = [
    re.compile(r"""(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*['"]([^'"]+)['"]"""),
    re.compile(r"""@(Get|Post|Put|Delete|Patch)\s*\(\s*['"]([^'"]+)['"]"""),   # NestJS
    re.compile(r"""@app\.(get|post|put|delete|patch)\s*\(\s*['"]([^'"]+)['"]"""),  # FastAPI
    re.compile(r"""router\.(get|post|put|delete|patch)\s*\(\s*['"]([^'"]+)['"]"""),  # Flask
]

# Successful bash command patterns worth remembering
_USEFUL_COMMANDS = re.compile(
    r"^(npm|yarn|pnpm|pip|python|pytest|jest|docker|git|npx|make|cargo|go)\s+.+",
    re.MULTILINE,
)


def _snippet(text: str, start: int, window: int = 120) -> str:
    """Extract a short snippet around a match position."""
    lo = max(0, start - 20)
    hi = min(len(text), start + window)
    return text[lo:hi].strip()


def extract_from_file(file_path: str, content: str, session_id: str) -> tuple[list[Entity], list[Relationship]]:
    """
    Extract entities and relationships from a file's content.
    Returns (entities, relationships).
    """
    entities: list[Entity] = []
    relationships: list[Relationship] = []
    ext = file_path.rsplit(".", 1)[-1].lower() if "." in file_path else ""
    file_id = f"file:{file_path}"

    # Always record the file itself
    entities.append(Entity(
        id=file_id,
        type="file",
        name=os.path.basename(file_path),
        path=file_path,
        description=_infer_file_purpose(file_path, content),
    ))

    if ext == "py":
        # Functions
        for m in _PY_FUNC_RE.finditer(content):
            fn_id = f"function:{file_path}::{m.group(1)}"
            entities.append(Entity(
                id=fn_id,
                type="function",
                name=m.group(1),
                path=file_path,
                raw_snippet=_snippet(content, m.start()),
            ))
            relationships.append(Relationship(from_id=file_id, to_id=fn_id, type="contains"))

        # Classes
        for m in _PY_CLASS_RE.finditer(content):
            cls_id = f"concept:{file_path}::{m.group(1)}"
            entities.append(Entity(id=cls_id, type="concept", name=m.group(1), path=file_path))
            relationships.append(Relationship(from_id=file_id, to_id=cls_id, type="contains"))

        # Imports → package entities + depends-on relationships
        for m in _PY_IMPORT_RE.finditer(content):
            pkg = m.group(1).split(".")[0]
            if pkg and pkg not in ("os", "sys", "re", "json", "time", "typing", "dataclasses"):
                pkg_id = f"package:{pkg}"
                entities.append(Entity(id=pkg_id, type="package", name=pkg))
                relationships.append(Relationship(from_id=file_id, to_id=pkg_id, type="depends-on"))

    elif ext in ("js", "ts", "jsx", "tsx"):
        # Functions / arrows
        for m in _JS_FUNC_RE.finditer(content):
            name = m.group(1) or m.group(2)
            if name:
                fn_id = f"function:{file_path}::{name}"
                entities.append(Entity(id=fn_id, type="function", name=name, path=file_path,
                                       raw_snippet=_snippet(content, m.start())))
                relationships.append(Relationship(from_id=file_id, to_id=fn_id, type="contains"))

        # Classes
        for m in _JS_CLASS_RE.finditer(content):
            cls_id = f"concept:{file_path}::{m.group(1)}"
            entities.append(Entity(id=cls_id, type="concept", name=m.group(1), path=file_path))
            relationships.append(Relationship(from_id=file_id, to_id=cls_id, type="contains"))

        # Imports
        for m in _JS_IMPORT_RE.finditer(content):
            pkg = m.group(1).lstrip("@").split("/")[0]
            if pkg and not pkg.startswith("."):
                pkg_id = f"package:{pkg}"
                entities.append(Entity(id=pkg_id, type="package", name=m.group(1)))
                relationships.append(Relationship(from_id=file_id, to_id=pkg_id, type="depends-on"))

    # API routes (any language)
    for pattern in _ROUTE_PATTERNS:
        for m in pattern.finditer(content):
            method = m.group(1).upper()
            route  = m.group(2)
            api_id = f"api:{method} {route}"
            entities.append(Entity(
                id=api_id,
                type="api",
                name=f"{method} {route}",
                path=file_path,
                raw_snippet=_snippet(content, m.start()),
            ))
            relationships.append(Relationship(from_id=file_id, to_id=api_id, type="defines"))

    return entities, relationships


def extract_from_command(command: str, output: str, exit_code: int) -> list[Entity]:
    """Record a successful shell command as a reusable entity."""
    if exit_code != 0:
        return []
    cmd = command.strip()[:300]
    if not _USEFUL_COMMANDS.match(cmd):
        return []
    cmd_id = f"command:{cmd[:60]}"
    purpose = _infer_command_purpose(cmd)
    return [Entity(id=cmd_id, type="command", name=cmd, description=purpose)]


def _infer_file_purpose(path: str, content: str) -> str:
    """Heuristic 1-line purpose from filename + content."""
    name = os.path.basename(path).lower()
    if "test" in name or "spec" in name:
        return f"Test file for {name.replace('.test','').replace('.spec','')}"
    if "route" in name or "router" in name:
        return "API route definitions"
    if "model" in name or "schema" in name:
        return "Data model / schema definitions"
    if "middleware" in name:
        return "Middleware layer"
    if "config" in name or "settings" in name:
        return "Configuration"
    if "util" in name or "helper" in name:
        return "Utility / helper functions"
    if "index" in name:
        return "Module entry point"
    # Fall back to first non-empty, non-comment line
    for line in content.splitlines()[:10]:
        line = line.strip()
        if line and not line.startswith(("#", "//", "/*", "*", "'")):
            return line[:100]
    return ""


def _infer_command_purpose(cmd: str) -> str:
    """Heuristic purpose description for a shell command."""
    if cmd.startswith("npm test") or cmd.startswith("pytest") or cmd.startswith("jest"):
        return "Run test suite"
    if cmd.startswith("npm run"):
        script = cmd.split("npm run", 1)[-1].strip()
        return f"npm script: {script}"
    if "migrate" in cmd:
        return "Run database migrations"
    if cmd.startswith("docker"):
        return "Docker operation"
    if cmd.startswith("git"):
        return "Git operation"
    return f"Shell command: {cmd[:60]}"


# ---------------------------------------------------------------------------
# Database writer
# ---------------------------------------------------------------------------

class SessionRecorder:
    """
    Writes captured entities and decisions to the SQLite memory graph.
    One instance per session — initialised by the hook, shared across calls.
    """

    def __init__(self, db_path: str, session_id: str):
        self.db_path = db_path
        self.session_id = session_id
        self._ensure_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    def _ensure_db(self) -> None:
        """Apply schema if this is a new DB."""
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        conn = self._connect()
        with open(schema_path) as f:
            conn.executescript(f.read())
        # Upsert session row
        now = int(time.time())
        conn.execute(
            "INSERT OR IGNORE INTO sessions(id, started_at) VALUES (?, ?)",
            (self.session_id, now),
        )
        conn.commit()
        conn.close()

    def record_entities(self, entities: list[Entity], relationships: list[Relationship]) -> None:
        now = int(time.time())
        conn = self._connect()
        try:
            for e in entities:
                conn.execute(
                    """INSERT INTO entities(id, type, name, path, description, raw_snippet,
                       confidence, source_session, created_at, updated_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?)
                       ON CONFLICT(id) DO UPDATE SET
                         description = COALESCE(excluded.description, description),
                         raw_snippet = COALESCE(excluded.raw_snippet, raw_snippet),
                         confidence  = 1.0,
                         updated_at  = excluded.updated_at""",
                    (e.id, e.type, e.name, e.path, e.description,
                     e.raw_snippet, e.confidence, self.session_id, now, now),
                )
            for r in relationships:
                conn.execute(
                    """INSERT OR IGNORE INTO relationships
                       (from_id, to_id, type, weight, source_session, created_at)
                       VALUES (?,?,?,?,?,?)""",
                    (r.from_id, r.to_id, r.type, r.weight, self.session_id, now),
                )
            conn.execute(
                "UPDATE sessions SET entity_count = entity_count + ? WHERE id = ?",
                (len(entities), self.session_id),
            )
            conn.commit()
        finally:
            conn.close()

    def record_decision(self, title: str, content: str, category: str, tags: list[str] | None = None) -> None:
        now = int(time.time())
        conn = self._connect()
        try:
            conn.execute(
                """INSERT INTO decisions(title, content, category, tags, session_id, created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?)""",
                (title, content, category, json.dumps(tags or []), self.session_id, now, now),
            )
            conn.execute(
                "UPDATE sessions SET decision_count = decision_count + 1 WHERE id = ?",
                (self.session_id,),
            )
            conn.commit()
        finally:
            conn.close()

    def decay_confidence(self, file_path: str, factor: float = 0.7) -> None:
        """Lower confidence for entities from a file that was just modified."""
        conn = self._connect()
        conn.execute(
            "UPDATE entities SET confidence = confidence * ? WHERE path = ? AND source_session != ?",
            (factor, file_path, self.session_id),
        )
        conn.commit()
        conn.close()


# ---------------------------------------------------------------------------
# CLI entry point — called by memory_recorder.sh
# ---------------------------------------------------------------------------

def main() -> None:
    """
    Reads Claude Code hook JSON from stdin, extracts entities, writes to DB.

    Hook stdin format (PostToolUse):
    {
      "session_id": "...",
      "cwd": "...",
      "tool_name": "Read|Edit|Bash",
      "tool_input": {...},
      "tool_response": {...}
    }
    """
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        sys.exit(0)

    session_id  = data.get("session_id", "unknown")
    tool_name   = data.get("tool_name", "")
    tool_input  = data.get("tool_input", {})
    tool_resp   = data.get("tool_response", {})
    cwd         = data.get("cwd", os.getcwd())

    # Resolve DB path
    agentkit_home = os.environ.get("AGENTKIT_HOME", _REPO_ROOT)
    db_dir  = os.path.join(cwd, ".agentkit")
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, "memory.db")

    recorder = SessionRecorder(db_path=db_path, session_id=session_id)

    if tool_name == "Read":
        file_path = tool_input.get("file_path", "")
        content   = tool_resp.get("content", "") if isinstance(tool_resp, dict) else str(tool_resp)
        if file_path and content:
            entities, rels = extract_from_file(file_path, content, session_id)
            recorder.record_entities(entities, rels)
            print(f"[AgentKit Memory] Recorded {len(entities)} entities from {file_path}", file=sys.stderr)

    elif tool_name in ("Edit", "Write", "MultiEdit"):
        file_path = tool_input.get("file_path", "")
        if file_path:
            recorder.decay_confidence(file_path)
            # Re-extract from new content if provided
            new_content = tool_input.get("new_string", "") or tool_input.get("content", "")
            if new_content:
                entities, rels = extract_from_file(file_path, new_content, session_id)
                recorder.record_entities(entities, rels)

    elif tool_name == "Bash":
        command   = tool_input.get("command", "")
        output    = str(tool_resp) if tool_resp else ""
        exit_code = 0 if tool_resp else 1   # simplistic; hook can pass exit code
        entities  = extract_from_command(command, output, exit_code)
        if entities:
            recorder.record_entities(entities, [])
            print(f"[AgentKit Memory] Recorded command: {command[:60]}", file=sys.stderr)


if __name__ == "__main__":
    main()
