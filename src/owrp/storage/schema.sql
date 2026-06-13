-- MODE: VIBECODABLE
-- BRAAT BLOCK: SQLite persistence schema
-- MISSION: Keep measurement proof inspectable with a local DB.

CREATE TABLE IF NOT EXISTS llm_interactions (
    interaction_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    user_id TEXT NOT NULL,
    repo_id TEXT NOT NULL,
    branch TEXT NOT NULL,
    prompt TEXT NOT NULL,
    response TEXT NOT NULL,
    tokens_spent INTEGER NOT NULL,
    cost_usd REAL NOT NULL,
    files_read_json TEXT NOT NULL,
    files_modified_json TEXT NOT NULL,
    prompt_hash TEXT NOT NULL,
    semantic_hash TEXT NOT NULL,
    context_hash TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_llm_repo ON llm_interactions(repo_id);
CREATE INDEX IF NOT EXISTS idx_llm_prompt_hash ON llm_interactions(prompt_hash);
CREATE INDEX IF NOT EXISTS idx_llm_context_hash ON llm_interactions(context_hash);

CREATE TABLE IF NOT EXISTS duplicate_prompt_pairs (
    pair_id TEXT PRIMARY KEY,
    left_interaction_id TEXT NOT NULL,
    right_interaction_id TEXT NOT NULL,
    similarity REAL NOT NULL,
    avoidable_tokens INTEGER NOT NULL,
    avoidable_cost_usd REAL NOT NULL,
    detected_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS context_reconstruction_events (
    context_event_id TEXT PRIMARY KEY,
    context_hash TEXT NOT NULL,
    repo_id TEXT NOT NULL,
    repeated_loads INTEGER NOT NULL,
    avoidable_context_tokens INTEGER NOT NULL,
    avoidable_context_cost_usd REAL NOT NULL,
    detected_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS recovery_ledger (
    ledger_id TEXT PRIMARY KEY,
    metric_name TEXT NOT NULL,
    resource_lost REAL NOT NULL,
    resource_measured REAL NOT NULL,
    resource_recovered REAL NOT NULL,
    unit TEXT NOT NULL,
    source TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS incident_events (
    node_id TEXT PRIMARY KEY,
    incident_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    service TEXT NOT NULL,
    actor TEXT NOT NULL,
    node_type TEXT NOT NULL,
    text TEXT NOT NULL,
    confidence REAL NOT NULL,
    metadata_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_incident_service ON incident_events(service);
CREATE INDEX IF NOT EXISTS idx_incident_type ON incident_events(node_type);

CREATE TABLE IF NOT EXISTS incident_edges (
    edge_id TEXT PRIMARY KEY,
    incident_id TEXT NOT NULL,
    source_node_id TEXT NOT NULL,
    target_node_id TEXT NOT NULL,
    relation TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS context_capsules (
    capsule_id TEXT PRIMARY KEY,
    repo_id TEXT NOT NULL,
    service TEXT NOT NULL,
    capsule_text TEXT NOT NULL,
    source_count INTEGER NOT NULL,
    estimated_tokens_saved INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
