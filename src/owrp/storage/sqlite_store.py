# MODE: VIBECODABLE
# BRAAT BLOCK: Storage adapter
# MISSION: Implement only the persistence operations used by the CLI proof path.

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from owrp.core.hashing import context_hash, jaccard, stable_hash, token_fingerprint
from owrp.core.paths import db_path, ensure_runtime_dirs
from owrp.core.types import IncidentEvent, LLMInteraction, QueryHit, RecoveryMetric

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


class SQLiteStore:
    def __init__(self, root: Path | None = None):
        self.root = root or Path.cwd()
        ensure_runtime_dirs(self.root)
        self.path = db_path(self.root)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.init_schema()

    def close(self) -> None:
        self.conn.close()

    def init_schema(self) -> None:
        self.conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.conn.commit()

    def insert_llm_interaction(self, event: LLMInteraction) -> None:
        prompt_hash = stable_hash(event.prompt)
        semantic_hash = stable_hash(" ".join(sorted(token_fingerprint(event.prompt))), length=20)
        ctx_hash = event.context_hash or context_hash(event.files_read, event.prompt)
        self.conn.execute(
            """
            INSERT OR REPLACE INTO llm_interactions
            (interaction_id, timestamp, user_id, repo_id, branch, prompt, response,
             tokens_spent, cost_usd, files_read_json, files_modified_json,
             prompt_hash, semantic_hash, context_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.interaction_id,
                event.timestamp,
                event.user_id,
                event.repo_id,
                event.branch,
                event.prompt,
                event.response,
                event.tokens_spent,
                event.cost_usd,
                json.dumps(list(event.files_read)),
                json.dumps(list(event.files_modified)),
                prompt_hash,
                semantic_hash,
                ctx_hash,
            ),
        )
        self.conn.commit()

    def insert_incident_event(self, event: IncidentEvent) -> str:
        node_id = stable_hash(f"{event.incident_id}:{event.timestamp}:{event.node_type}:{event.text}", length=24)
        self.conn.execute(
            """
            INSERT OR REPLACE INTO incident_events
            (node_id, incident_id, timestamp, service, actor, node_type, text, confidence, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                node_id,
                event.incident_id,
                event.timestamp,
                event.service,
                event.actor,
                event.node_type,
                event.text,
                event.confidence,
                json.dumps(event.metadata, sort_keys=True),
            ),
        )
        if event.related_to:
            edge_id = stable_hash(f"{event.related_to}->{node_id}", length=24)
            self.conn.execute(
                """
                INSERT OR REPLACE INTO incident_edges
                (edge_id, incident_id, source_node_id, target_node_id, relation)
                VALUES (?, ?, ?, ?, ?)
                """,
                (edge_id, event.incident_id, event.related_to, node_id, "related_to"),
            )
        self.conn.commit()
        return node_id

    def fetch_llm_rows(self) -> list[sqlite3.Row]:
        return list(self.conn.execute("SELECT * FROM llm_interactions ORDER BY timestamp"))

    def fetch_incident_rows(self) -> list[sqlite3.Row]:
        return list(self.conn.execute("SELECT * FROM incident_events ORDER BY timestamp"))

    def clear_detected_metrics(self) -> None:
        self.conn.execute("DELETE FROM duplicate_prompt_pairs")
        self.conn.execute("DELETE FROM context_reconstruction_events")
        self.conn.execute("DELETE FROM recovery_ledger")
        self.conn.execute("DELETE FROM context_capsules")
        self.conn.commit()

    def insert_duplicate_pair(
        self,
        left_id: str,
        right_id: str,
        similarity: float,
        avoidable_tokens: int,
        avoidable_cost_usd: float,
    ) -> None:
        pair_id = stable_hash(f"{left_id}:{right_id}", length=24)
        self.conn.execute(
            """
            INSERT OR REPLACE INTO duplicate_prompt_pairs
            (pair_id, left_interaction_id, right_interaction_id, similarity,
             avoidable_tokens, avoidable_cost_usd, detected_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                pair_id,
                left_id,
                right_id,
                similarity,
                avoidable_tokens,
                avoidable_cost_usd,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.conn.commit()

    def insert_context_reconstruction(
        self,
        ctx_hash: str,
        repo_id: str,
        repeated_loads: int,
        avoidable_context_tokens: int,
        avoidable_context_cost_usd: float,
    ) -> None:
        context_event_id = stable_hash(f"{repo_id}:{ctx_hash}:{repeated_loads}", length=24)
        self.conn.execute(
            """
            INSERT OR REPLACE INTO context_reconstruction_events
            (context_event_id, context_hash, repo_id, repeated_loads,
             avoidable_context_tokens, avoidable_context_cost_usd, detected_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                context_event_id,
                ctx_hash,
                repo_id,
                repeated_loads,
                avoidable_context_tokens,
                avoidable_context_cost_usd,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.conn.commit()

    def insert_recovery_metric(self, metric: RecoveryMetric) -> None:
        ledger_id = stable_hash(f"{metric.metric_name}:{metric.source}:{metric.resource_recovered}", length=24)
        self.conn.execute(
            """
            INSERT OR REPLACE INTO recovery_ledger
            (ledger_id, metric_name, resource_lost, resource_measured,
             resource_recovered, unit, source, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ledger_id,
                metric.metric_name,
                metric.resource_lost,
                metric.resource_measured,
                metric.resource_recovered,
                metric.unit,
                metric.source,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.conn.commit()

    def insert_capsule(self, repo_id: str, service: str, capsule_text: str, source_count: int, estimated_tokens_saved: int) -> None:
        capsule_id = stable_hash(f"{repo_id}:{service}:{capsule_text[:100]}", length=24)
        self.conn.execute(
            """
            INSERT OR REPLACE INTO context_capsules
            (capsule_id, repo_id, service, capsule_text, source_count, estimated_tokens_saved, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                capsule_id,
                repo_id,
                service,
                capsule_text,
                source_count,
                estimated_tokens_saved,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.conn.commit()

    def status(self) -> dict[str, float | int]:
        row = self.conn.execute(
            """
            SELECT
              COUNT(*) AS interactions,
              COALESCE(SUM(tokens_spent), 0) AS tokens_spent,
              COALESCE(SUM(cost_usd), 0.0) AS llm_spend
            FROM llm_interactions
            """
        ).fetchone()
        dup = self.conn.execute(
            """
            SELECT
              COUNT(*) AS duplicate_pairs,
              COALESCE(SUM(avoidable_tokens), 0) AS duplicate_tokens,
              COALESCE(SUM(avoidable_cost_usd), 0.0) AS duplicate_cost
            FROM duplicate_prompt_pairs
            """
        ).fetchone()
        ctx = self.conn.execute(
            """
            SELECT
              COUNT(*) AS repeated_context_events,
              COALESCE(SUM(avoidable_context_tokens), 0) AS avoidable_context_tokens,
              COALESCE(SUM(avoidable_context_cost_usd), 0.0) AS avoidable_context_cost
            FROM context_reconstruction_events
            """
        ).fetchone()
        inc = self.conn.execute("SELECT COUNT(*) AS incident_nodes FROM incident_events").fetchone()
        caps = self.conn.execute("SELECT COUNT(*) AS context_capsules FROM context_capsules").fetchone()
        return {
            "interactions": int(row["interactions"]),
            "tokens_spent": int(row["tokens_spent"]),
            "llm_spend": round(float(row["llm_spend"]), 6),
            "duplicate_pairs": int(dup["duplicate_pairs"]),
            "duplicate_tokens": int(dup["duplicate_tokens"]),
            "duplicate_cost": round(float(dup["duplicate_cost"]), 6),
            "repeated_context_events": int(ctx["repeated_context_events"]),
            "avoidable_context_tokens": int(ctx["avoidable_context_tokens"]),
            "avoidable_context_cost": round(float(ctx["avoidable_context_cost"]), 6),
            "incident_nodes": int(inc["incident_nodes"]),
            "context_capsules": int(caps["context_capsules"]),
        }

    def query(self, text: str, limit: int = 8) -> list[QueryHit]:
        query_terms = token_fingerprint(text)
        hits: list[QueryHit] = []
        for row in self.fetch_llm_rows():
            blob = f"{row['prompt']} {row['response']} {' '.join(json.loads(row['files_read_json']))}"
            score = jaccard(query_terms, token_fingerprint(blob))
            if score > 0:
                hits.append(QueryHit("llm_interaction", row["interaction_id"], score, row["prompt"][:80], row["response"][:220]))
        for row in self.fetch_incident_rows():
            blob = f"{row['service']} {row['node_type']} {row['text']}"
            score = jaccard(query_terms, token_fingerprint(blob))
            if score > 0:
                title = f"{row['incident_id']} / {row['service']} / {row['node_type']}"
                hits.append(QueryHit("incident_event", row["node_id"], score, title, row["text"][:220]))
        return sorted(hits, key=lambda hit: hit.score, reverse=True)[:limit]
