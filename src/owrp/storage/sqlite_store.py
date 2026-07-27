from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from datetime import datetime

from owrp.core.config import load_config
from owrp.core.hashing import similarity, stable_hash
from owrp.core.types import Interaction, QueryHit

SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS interactions (
    event_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    user_id TEXT NOT NULL,
    repo_id TEXT NOT NULL,
    source TEXT NOT NULL,
    model_name TEXT NOT NULL,
    prompt TEXT NOT NULL,
    response TEXT NOT NULL,
    prompt_tokens INTEGER NOT NULL,
    completion_tokens INTEGER NOT NULL,
    total_tokens INTEGER NOT NULL,
    cost_usd REAL NOT NULL,
    classification TEXT NOT NULL,
    files_read_json TEXT NOT NULL,
    files_modified_json TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    ingested_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_interactions_repo ON interactions(repo_id);
CREATE INDEX IF NOT EXISTS idx_interactions_class ON interactions(classification);
CREATE TABLE IF NOT EXISTS duplicate_pairs (
    pair_id TEXT PRIMARY KEY,
    left_id TEXT NOT NULL,
    right_id TEXT NOT NULL,
    similarity REAL NOT NULL,
    avoidable_tokens INTEGER NOT NULL,
    avoidable_cost_usd REAL NOT NULL,
    detected_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS context_capsules (
    capsule_id TEXT PRIMARY KEY,
    repo_id TEXT NOT NULL,
    capsule_text TEXT NOT NULL,
    source_count INTEGER NOT NULL,
    estimated_tokens_saved INTEGER NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


class SQLiteStore:
    def __init__(self, root: Path):
        self.root = root
        config = load_config(root)
        config.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.path = config.db_path
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

    def close(self) -> None:
        self.conn.close()

    def _upsert(self, event: Interaction) -> None:
        self.conn.execute(
            """
            INSERT INTO interactions (
                event_id, timestamp, user_id, repo_id, source, model_name,
                prompt, response, prompt_tokens, completion_tokens, total_tokens,
                cost_usd, classification, files_read_json, files_modified_json,
                metadata_json, ingested_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(event_id) DO UPDATE SET
                timestamp = excluded.timestamp,
                user_id = excluded.user_id,
                repo_id = excluded.repo_id,
                source = excluded.source,
                model_name = excluded.model_name,
                prompt = excluded.prompt,
                response = excluded.response,
                prompt_tokens = excluded.prompt_tokens,
                completion_tokens = excluded.completion_tokens,
                total_tokens = excluded.total_tokens,
                cost_usd = excluded.cost_usd,
                classification = excluded.classification,
                files_read_json = excluded.files_read_json,
                files_modified_json = excluded.files_modified_json,
                metadata_json = excluded.metadata_json,
                ingested_at = CURRENT_TIMESTAMP
            """,
            (
                event.event_id, event.timestamp, event.user_id, event.repo_id,
                event.source, event.model_name, event.prompt, event.response,
                event.prompt_tokens, event.completion_tokens, event.total_tokens,
                event.cost_usd, event.classification, json.dumps(event.files_read),
                json.dumps(event.files_modified), json.dumps(event.metadata, sort_keys=True),
            ),
        )

    def insert(self, event: Interaction) -> str:
        with self.conn:
            self._upsert(event)
        return event.event_id

    def insert_many(self, events: list[Interaction]) -> int:
        with self.conn:
            for event in events:
                self._upsert(event)
        return len(events)

    def rows(self) -> list[sqlite3.Row]:
        return list(self.conn.execute("SELECT * FROM interactions ORDER BY timestamp, event_id"))

    def clear_analysis(self) -> None:
        self.conn.execute("DELETE FROM duplicate_pairs")
        self.conn.execute("DELETE FROM context_capsules")
        self.conn.commit()

    def analyze(self, threshold: float = 0.72) -> dict[str, int | float]:
        if not 0 <= threshold <= 1:
            raise ValueError("duplicate threshold must be between 0 and 1")

        self.clear_analysis()
        rows = self.rows()
        duplicate_pairs = 0
        avoidable_tokens = 0
        avoidable_cost = 0.0

        for index, left in enumerate(rows):
            for right in rows[index + 1 :]:
                if left["repo_id"] != right["repo_id"]:
                    continue
                score = similarity(left["prompt"], right["prompt"])
                if score < threshold:
                    continue
                tokens = min(left["total_tokens"], right["total_tokens"])
                cost = min(left["cost_usd"], right["cost_usd"])
                pair_id = stable_hash(f"{left['event_id']}:{right['event_id']}", 24)
                self.conn.execute(
                    """
                    INSERT OR REPLACE INTO duplicate_pairs (
                        pair_id, left_id, right_id, similarity,
                        avoidable_tokens, avoidable_cost_usd, detected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (pair_id, left["event_id"], right["event_id"], score, tokens, cost),
                )
                duplicate_pairs += 1
                avoidable_tokens += tokens
                avoidable_cost += cost

        grouped: dict[str, list[sqlite3.Row]] = {}
        for row in rows:
            grouped.setdefault(row["repo_id"], []).append(row)

        capsule_count = 0
        for repo_id, group in grouped.items():
            if len(group) < 2:
                continue
            files: dict[str, int] = {}
            classifications: dict[str, int] = {}
            for row in group:
                for file_path in json.loads(row["files_read_json"]):
                    files[file_path] = files.get(file_path, 0) + 1
                classification = row["classification"]
                classifications[classification] = classifications.get(classification, 0) + 1

            top_files = ", ".join(
                key for key, _ in sorted(files.items(), key=lambda item: (-item[1], item[0]))[:6]
            ) or "none"
            top_classes = ", ".join(
                key
                for key, _ in sorted(
                    classifications.items(), key=lambda item: (-item[1], item[0])
                )[:4]
            ) or "none"
            capsule_text = (
                f"Repository: {repo_id}\n"
                f"Repeated work classes: {top_classes}\n"
                f"Frequently reloaded files: {top_files}\n"
                "Review this capsule before reconstructing the same context."
            )
            raw_tokens = sum(row["total_tokens"] for row in group)
            estimated_saved = max(0, raw_tokens - max(1, len(capsule_text) // 4))
            capsule_id = stable_hash(repo_id + capsule_text, 24)
            self.conn.execute(
                """
                INSERT OR REPLACE INTO context_capsules (
                    capsule_id, repo_id, capsule_text, source_count,
                    estimated_tokens_saved, created_at
                ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (capsule_id, repo_id, capsule_text, len(group), estimated_saved),
            )
            capsule_count += 1

        self.conn.commit()
        return {
            "duplicate_pairs": duplicate_pairs,
            "avoidable_tokens": avoidable_tokens,
            "avoidable_cost_usd": round(avoidable_cost, 6),
            "capsules": capsule_count,
        }

    def status(self) -> dict[str, int | float]:
        interaction = self.conn.execute(
            """
            SELECT COUNT(*) AS count,
                   COALESCE(SUM(total_tokens), 0) AS tokens,
                   COALESCE(SUM(cost_usd), 0) AS cost
            FROM interactions
            """
        ).fetchone()
        duplicate = self.conn.execute(
            """
            SELECT COUNT(*) AS count,
                   COALESCE(SUM(avoidable_tokens), 0) AS tokens,
                   COALESCE(SUM(avoidable_cost_usd), 0) AS cost
            FROM duplicate_pairs
            """
        ).fetchone()
        capsule = self.conn.execute(
            """
            SELECT COUNT(*) AS count,
                   COALESCE(SUM(estimated_tokens_saved), 0) AS saved
            FROM context_capsules
            """
        ).fetchone()
        return {
            "interactions": int(interaction["count"]),
            "tokens_spent": int(interaction["tokens"]),
            "llm_spend_usd": round(float(interaction["cost"]), 6),
            "duplicate_pairs": int(duplicate["count"]),
            "avoidable_tokens": int(duplicate["tokens"]),
            "avoidable_cost_usd": round(float(duplicate["cost"]), 6),
            "context_capsules": int(capsule["count"]),
            "estimated_capsule_tokens_saved": int(capsule["saved"]),
        }


    def purge(self, *, before: str | None = None, repo_id: str | None = None) -> dict[str, int]:
        clauses: list[str] = []
        params: list[object] = []
        if before:
            try:
                datetime.fromisoformat(before.replace("Z", "+00:00"))
            except ValueError as error:
                raise ValueError("before must be an ISO-8601 timestamp") from error
            clauses.append("timestamp < ?")
            params.append(before)
        if repo_id:
            clauses.append("repo_id = ?")
            params.append(repo_id)
        if not clauses:
            raise ValueError("purge requires --before and/or --repo")
        where = " AND ".join(clauses)
        count = self.conn.execute(f"SELECT COUNT(*) FROM interactions WHERE {where}", params).fetchone()[0]
        with self.conn:
            self.conn.execute(f"DELETE FROM interactions WHERE {where}", params)
            self.conn.execute("DELETE FROM duplicate_pairs")
            self.conn.execute("DELETE FROM context_capsules")
        return {"interactions_deleted": int(count), "analysis_invalidated": 1}

    def repositories(self) -> list[dict]:
        return [
            dict(row)
            for row in self.conn.execute(
                """
                SELECT repo_id, COUNT(*) interactions, SUM(total_tokens) tokens,
                       ROUND(SUM(cost_usd), 6) cost_usd,
                       MIN(timestamp) first_timestamp, MAX(timestamp) last_timestamp
                FROM interactions GROUP BY repo_id ORDER BY repo_id
                """
            )
        ]

    def query(self, text: str, limit: int = 8) -> list[QueryHit]:
        if limit < 1 or limit > 100:
            raise ValueError("limit must be between 1 and 100")
        hits: list[QueryHit] = []
        for row in self.rows():
            score = similarity(
                text,
                " ".join(
                    [row["prompt"], row["response"], row["classification"], row["repo_id"]]
                ),
            )
            if score:
                hits.append(
                    QueryHit(
                        row["event_id"],
                        score,
                        row["repo_id"],
                        row["classification"],
                        row["prompt"][:240],
                        row["response"][:320],
                    )
                )
        return sorted(hits, key=lambda hit: (-hit.score, hit.event_id))[:limit]

    def export_rows(self) -> list[dict]:
        output: list[dict] = []
        for row in self.rows():
            item = dict(row)
            item["files_read"] = json.loads(item.pop("files_read_json"))
            item["files_modified"] = json.loads(item.pop("files_modified_json"))
            item["metadata"] = json.loads(item.pop("metadata_json"))
            output.append(item)
        return output

    def capsules(self) -> list[dict]:
        return [
            dict(row)
            for row in self.conn.execute(
                "SELECT * FROM context_capsules ORDER BY repo_id, capsule_id"
            )
        ]
