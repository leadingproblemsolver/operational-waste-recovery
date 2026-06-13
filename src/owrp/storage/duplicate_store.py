# ============================================================
# MODE: HYBRID
# BRAAT BLOCK: 02 Deduplication Engine
# FILE: storage/duplicate_store.py
# ============================================================
#
# MISSION:
#   Persist duplicate evidence in SQLite.
#
# WHY THIS FILE EXISTS:
#   Detection without stored proof is not inspectable.
#
# INPUT:
#   DuplicateEvidence
#
# OUTPUT:
#   duplicate_events table
#
# NON-NEGOTIABLE:
#   No recovery math here.
#   No reporting here.
# ============================================================

import sqlite3

from pipeline.deduplicate import DuplicateEvidence


def initialize_duplicate_table(conn: sqlite3.Connection) -> None:
    """
    Create duplicate evidence table.

    This table proves repeated work was detected.
    """

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS duplicate_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            current_event_id TEXT NOT NULL,
            matched_event_id TEXT NOT NULL,
            duplicate_type TEXT NOT NULL,
            duplicate_score REAL NOT NULL,
            reason TEXT NOT NULL
        )
        """
    )

    conn.commit()


def insert_duplicate_evidence(
    conn: sqlite3.Connection,
    evidence: list[DuplicateEvidence],
) -> int:
    """
    Store duplicate evidence records.

    Returns number of inserted rows.
    """

    for item in evidence:
        conn.execute(
            """
            INSERT INTO duplicate_events (
                current_event_id,
                matched_event_id,
                duplicate_type,
                duplicate_score,
                reason
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                item.current_event_id,
                item.matched_event_id,
                item.duplicate_type,
                item.duplicate_score,
                item.reason,
            ),
        )

    conn.commit()

    return len(evidence)