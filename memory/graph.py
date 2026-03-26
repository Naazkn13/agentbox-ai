"""
AgentKit — Layer 2: Knowledge Graph
Query interface for the SQLite memory graph.
Used by the injector to find relevant entities for the current task.
"""

import os
import time
import sqlite3
from dataclasses import dataclass
from typing import Optional


@dataclass
class GraphEntity:
    id: str
    type: str
    name: str
    path: Optional[str]
    description: Optional[str]
    confidence: float
    updated_at: int
    raw_snippet: Optional[str] = None


@dataclass
class GraphDecision:
    id: int
    title: str
    content: str
    category: str
    confidence: float
    updated_at: int


@dataclass
class ContextNode:
    """A single memory node ready for injection."""
    entity_or_decision: object       # GraphEntity | GraphDecision
    relevance_score: float
    formatted_text: str


class KnowledgeGraph:
    """
    Read/query interface for the project memory graph.
    Write operations go through SessionRecorder.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    # ------------------------------------------------------------------
    # Entity queries
    # ------------------------------------------------------------------

    def get_entity(self, entity_id: str) -> Optional[GraphEntity]:
        conn = self._connect()
        row = conn.execute("SELECT * FROM entities WHERE id = ?", (entity_id,)).fetchone()
        conn.close()
        return self._row_to_entity(row) if row else None

    def get_related(
        self,
        entity_id: str,
        rel_type: Optional[str] = None,
        direction: str = "outgoing",   # outgoing | incoming | both
        depth: int = 1,
        min_confidence: float = 0.2,
    ) -> list[GraphEntity]:
        """
        Get entities related to entity_id up to `depth` hops.
        direction: outgoing (entity → ?), incoming (? → entity), both.
        """
        visited: set[str] = {entity_id}
        frontier: set[str] = {entity_id}
        results: list[GraphEntity] = []

        conn = self._connect()
        for _ in range(depth):
            if not frontier:
                break
            next_frontier: set[str] = set()
            for eid in frontier:
                if direction in ("outgoing", "both"):
                    q = "SELECT to_id FROM relationships WHERE from_id = ?"
                    params: tuple = (eid,)
                    if rel_type:
                        q += " AND type = ?"
                        params = (eid, rel_type)
                    rows = conn.execute(q, params).fetchall()
                    for r in rows:
                        if r["to_id"] not in visited:
                            next_frontier.add(r["to_id"])
                            visited.add(r["to_id"])

                if direction in ("incoming", "both"):
                    q = "SELECT from_id FROM relationships WHERE to_id = ?"
                    params = (eid,)
                    if rel_type:
                        q += " AND type = ?"
                        params = (eid, rel_type)
                    rows = conn.execute(q, params).fetchall()
                    for r in rows:
                        if r["from_id"] not in visited:
                            next_frontier.add(r["from_id"])
                            visited.add(r["from_id"])

            # Fetch entities for this hop
            for nid in next_frontier:
                row = conn.execute(
                    "SELECT * FROM entities WHERE id = ? AND confidence >= ?",
                    (nid, min_confidence),
                ).fetchone()
                if row:
                    results.append(self._row_to_entity(row))
            frontier = next_frontier

        conn.close()
        return results

    def get_entities_for_files(self, file_paths: list[str], min_confidence: float = 0.3) -> list[GraphEntity]:
        """Get all entities associated with the given file paths."""
        if not file_paths:
            return []
        conn = self._connect()
        placeholders = ",".join("?" * len(file_paths))
        rows = conn.execute(
            f"SELECT * FROM entities WHERE path IN ({placeholders}) AND confidence >= ? ORDER BY updated_at DESC",
            (*file_paths, min_confidence),
        ).fetchall()
        conn.close()
        return [self._row_to_entity(r) for r in rows]

    def search_entities(self, query: str, limit: int = 10) -> list[GraphEntity]:
        """Full-text search over entity names and descriptions."""
        conn = self._connect()
        try:
            rows = conn.execute(
                """SELECT e.* FROM entities e
                   JOIN entities_fts fts ON e.rowid = fts.rowid
                   WHERE entities_fts MATCH ?
                   ORDER BY rank LIMIT ?""",
                (query, limit),
            ).fetchall()
        except sqlite3.OperationalError:
            # FTS not available — fall back to LIKE
            rows = conn.execute(
                "SELECT * FROM entities WHERE name LIKE ? OR description LIKE ? LIMIT ?",
                (f"%{query}%", f"%{query}%", limit),
            ).fetchall()
        conn.close()
        return [self._row_to_entity(r) for r in rows]

    # ------------------------------------------------------------------
    # Decision queries
    # ------------------------------------------------------------------

    def get_decisions(
        self,
        category: Optional[str] = None,
        limit: int = 20,
        min_confidence: float = 0.2,
    ) -> list[GraphDecision]:
        conn = self._connect()
        if category:
            rows = conn.execute(
                "SELECT * FROM decisions WHERE category = ? AND confidence >= ? ORDER BY updated_at DESC LIMIT ?",
                (category, min_confidence, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM decisions WHERE confidence >= ? ORDER BY updated_at DESC LIMIT ?",
                (min_confidence, limit),
            ).fetchall()
        conn.close()
        return [self._row_to_decision(r) for r in rows]

    def search_decisions(self, query: str, limit: int = 10) -> list[GraphDecision]:
        conn = self._connect()
        try:
            rows = conn.execute(
                """SELECT d.* FROM decisions d
                   JOIN decisions_fts fts ON d.rowid = fts.rowid
                   WHERE decisions_fts MATCH ?
                   ORDER BY rank LIMIT ?""",
                (query, limit),
            ).fetchall()
        except sqlite3.OperationalError:
            rows = conn.execute(
                "SELECT * FROM decisions WHERE title LIKE ? OR content LIKE ? LIMIT ?",
                (f"%{query}%", f"%{query}%", limit),
            ).fetchall()
        conn.close()
        return [self._row_to_decision(r) for r in rows]

    # ------------------------------------------------------------------
    # Composite context query (used by injector)
    # ------------------------------------------------------------------

    def get_context_for_task(
        self,
        task_category: str,
        current_files: list[str],
        prompt_keywords: list[str],
        max_nodes: int = 30,
    ) -> list[ContextNode]:
        """
        Score and return the most relevant memory nodes for the current task.
        Priority:
          1. Entities matching current files (score +1.0)
          2. Decisions matching task category (score +0.7)
          3. Entities 1-hop from current files (score +0.5)
          4. Recent high-confidence decisions (score +0.3)
          5. Keyword-matched entities/decisions (score +0.2 per keyword hit)
        """
        now = int(time.time())
        nodes: list[ContextNode] = []
        seen_ids: set[str] = set()

        # 1. File-matched entities
        file_entities = self.get_entities_for_files(current_files)
        for e in file_entities:
            score = 1.0 + self._keyword_bonus(e, prompt_keywords) + self._recency_bonus(e.updated_at, now)
            nodes.append(ContextNode(e, score, self._format_entity(e)))
            seen_ids.add(e.id)

        # 2. Decisions matching task category
        category_map = {
            "api-work": "api", "db-work": "db", "security": "security",
            "architecting": "architecture", "debugging": "bug-fix",
            "refactoring": "pattern", "writing-tests": "pattern",
        }
        decision_cat = category_map.get(task_category)
        for d in self.get_decisions(category=decision_cat, limit=10):
            if str(d.id) not in seen_ids:
                score = 0.7 + self._keyword_bonus_decision(d, prompt_keywords) + self._recency_bonus(d.updated_at, now)
                nodes.append(ContextNode(d, score, self._format_decision(d)))
                seen_ids.add(str(d.id))

        # 3. 1-hop neighbours of current files
        for file_path in current_files[:3]:   # limit to top 3 files
            file_id = f"file:{file_path}"
            for neighbour in self.get_related(file_id, depth=1):
                if neighbour.id not in seen_ids:
                    score = 0.5 + self._recency_bonus(neighbour.updated_at, now)
                    nodes.append(ContextNode(neighbour, score, self._format_entity(neighbour)))
                    seen_ids.add(neighbour.id)

        # 4. Recent decisions (any category)
        for d in self.get_decisions(limit=5):
            if str(d.id) not in seen_ids:
                score = 0.3 + self._keyword_bonus_decision(d, prompt_keywords)
                nodes.append(ContextNode(d, score, self._format_decision(d)))
                seen_ids.add(str(d.id))

        # Sort by score descending
        nodes.sort(key=lambda n: n.relevance_score, reverse=True)
        return nodes[:max_nodes]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _recency_bonus(self, updated_at: int, now: int) -> float:
        days_old = (now - updated_at) / 86400
        return max(0.0, 0.3 * (1 - days_old / 30))  # 0.3 at 0 days, 0 at 30 days

    def _keyword_bonus(self, e: GraphEntity, keywords: list[str]) -> float:
        text = f"{e.name} {e.description or ''}".lower()
        return 0.1 * sum(1 for kw in keywords if kw.lower() in text)

    def _keyword_bonus_decision(self, d: GraphDecision, keywords: list[str]) -> float:
        text = f"{d.title} {d.content}".lower()
        return 0.1 * sum(1 for kw in keywords if kw.lower() in text)

    def _format_entity(self, e: GraphEntity) -> str:
        parts = [f"**[{e.type.upper()}]** `{e.name}`"]
        if e.path:
            parts.append(f"({e.path})")
        if e.description:
            parts.append(f"— {e.description}")
        if e.raw_snippet:
            parts.append(f"\n  ```\n  {e.raw_snippet[:120]}\n  ```")
        return " ".join(parts)

    def _format_decision(self, d: GraphDecision) -> str:
        return f"**[DECISION/{d.category.upper()}]** {d.title}: {d.content[:200]}"

    @staticmethod
    def _row_to_entity(row: sqlite3.Row) -> GraphEntity:
        return GraphEntity(
            id=row["id"], type=row["type"], name=row["name"],
            path=row["path"], description=row["description"],
            confidence=row["confidence"], updated_at=row["updated_at"],
            raw_snippet=row["raw_snippet"] if "raw_snippet" in row.keys() else None,
        )

    @staticmethod
    def _row_to_decision(row: sqlite3.Row) -> GraphDecision:
        return GraphDecision(
            id=row["id"], title=row["title"], content=row["content"],
            category=row["category"], confidence=row["confidence"],
            updated_at=row["updated_at"],
        )
