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
