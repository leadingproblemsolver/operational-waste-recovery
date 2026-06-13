$ErrorActionPreference='Stop'; New-Item -ItemType Directory -Force retrieval,tests\fixtures,docs,data | Out-Null; @'
from typing import Any

def make_hit(kind: str, content: str, source_path: str | None, doc_id: str | None, signal_type: str | None = None, score: float | None = None) -> dict[str, Any]:
    return {"kind": kind, "signal_type": signal_type, "content": content or "", "source_path": source_path, "doc_id": doc_id, "relevance_score": score or 0.0}

def dedupe_hits(hits: list[dict]) -> list[dict]:
    seen = set(); out = []
    for h in hits:
        key = (h.get("kind"), h.get("signal_type"), (h.get("content") or "").strip(), h.get("source_path"), h.get("doc_id"))
        if key in seen: continue
        seen.add(key); out.append(h)
    return out
'@ | Set-Content retrieval\contracts.py; @'
from pathlib import Path

class RetrievalConfig:
    def __init__(self, state_db: str = ".cce/living_context.db", index_dir: str = ".cce/indexes", keyword_backend: str = "sqlite_like", semantic_backend: str = "disabled", default_limit: int = 20):
        self.state_db = Path(state_db); self.index_dir = Path(index_dir); self.keyword_backend = keyword_backend; self.semantic_backend = semantic_backend; self.default_limit = default_limit
'@ | Set-Content retrieval\config.py; @'
import sqlite3
from pathlib import Path

def connect(db_path: str | Path):
    conn = sqlite3.connect(str(db_path)); conn.row_factory = sqlite3.Row; return conn

def fetch_documents(conn):
    return [dict(r) for r in conn.execute("SELECT * FROM documents")]

def fetch_retrieval_units(conn):
    return [dict(r) for r in conn.execute("SELECT ru.*, d.source_path FROM retrieval_units ru LEFT JOIN documents d ON d.doc_id=ru.doc_id")]

def fetch_signals(conn):
    return [dict(r) for r in conn.execute("SELECT s.*, d.source_path FROM signals s LEFT JOIN documents d ON d.doc_id=s.doc_id")]
'@ | Set-Content retrieval\sqlite_access.py; @'
from retrieval.contracts import make_hit

def retrieve(topic: str, rows: list[dict], kind: str, limit: int = 20) -> list[dict]:
    terms = [t.lower() for t in topic.split() if len(t) > 1]
    scored = []
    for row in rows:
        content = (row.get("content") or "").lower()
        score = sum(content.count(t) for t in terms)
        if score: scored.append((score, row))
    scored.sort(key=lambda x: x[0], reverse=True)
    out = []
    for score, row in scored[:limit]:
        out.append(make_hit(kind=kind, content=row.get("content",""), source_path=row.get("source_path"), doc_id=row.get("doc_id"), signal_type=row.get("signal_type"), score=float(score)))
    return out
'@ | Set-Content retrieval\keyword_retriever.py; @'
def retrieve(topic: str, limit: int = 20) -> list[dict]:
    return []
'@ | Set-Content retrieval\semantic_retriever.py; @'
def merge_hits(keyword_hits: list[dict], semantic_hits: list[dict]) -> list[dict]:
    seen = set(); out = []
    for hit in keyword_hits + semantic_hits:
        key = (hit.get("kind"), hit.get("signal_type"), (hit.get("content") or "").strip(), hit.get("source_path"), hit.get("doc_id"))
        if key in seen: continue
        seen.add(key); out.append(hit)
    out.sort(key=lambda h: (-float(h.get("relevance_score") or 0.0), h.get("source_path") or ""))
    return out
'@ | Set-Content retrieval\result_aggregator.py; @'
from retrieval.sqlite_access import connect, fetch_retrieval_units, fetch_signals
from retrieval.keyword_retriever import retrieve as keyword_retrieve
from retrieval.semantic_retriever import retrieve as semantic_retrieve
from retrieval.result_aggregator import merge_hits

def run(topic: str, db_path: str, limit: int = 20) -> dict:
    conn = connect(db_path)
    try:
        signal_rows = fetch_signals(conn); ru_rows = fetch_retrieval_units(conn)
    finally:
        conn.close()
    keyword_hits = keyword_retrieve(topic, signal_rows, kind="signal", limit=limit) + keyword_retrieve(topic, ru_rows, kind="retrieval_unit", limit=limit)
    semantic_hits = semantic_retrieve(topic, limit=limit)
    hits = merge_hits(keyword_hits, semantic_hits)[:limit]
    return {"topic": topic, "hits": hits, "signals": [h for h in hits if h.get("kind") == "signal"], "retrieval_units": [h for h in hits if h.get("kind") == "retrieval_unit"], "source_paths": sorted({h.get("source_path") for h in hits if h.get("source_path")})}
'@ | Set-Content retrieval\orchestrator.py; @'
from retrieval.config import RetrievalConfig
from retrieval.orchestrator import run

def search(topic: str, config: RetrievalConfig | None = None, limit: int | None = None) -> dict:
    config = config or RetrievalConfig()
    return run(topic=topic, db_path=str(config.state_db), limit=limit or config.default_limit)
'@ | Set-Content retrieval\service.py; @'
from retrieval.service import search

if __name__ == "__main__":
    import json, sys
    if len(sys.argv) < 2:
        raise SystemExit("usage: python -m retrieval.service '<topic>'")
    print(json.dumps(search(sys.argv[1]), indent=2, ensure_ascii=False))
'@ | Set-Content retrieval\__main__.py; @'
import sqlite3
from pathlib import Path

def build_fixture(path: str = "tests/fixtures/retrieval_fixture.db"):
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p))
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS documents(doc_id TEXT PRIMARY KEY, source_path TEXT, content TEXT);
    CREATE TABLE IF NOT EXISTS retrieval_units(ru_id TEXT PRIMARY KEY, doc_id TEXT, content TEXT);
    CREATE TABLE IF NOT EXISTS signals(signal_id TEXT PRIMARY KEY, ru_id TEXT, doc_id TEXT, signal_type TEXT, content TEXT);
    DELETE FROM documents; DELETE FROM retrieval_units; DELETE FROM signals;
    INSERT INTO documents VALUES ('d1','data/sample_project.md','payments rollout delayed');
    INSERT INTO retrieval_units VALUES ('r1','d1','Blocker: payment flow unstable');
    INSERT INTO retrieval_units VALUES ('r2','d1','Decision: stability over release deadline');
    INSERT INTO signals VALUES ('s1','r1','d1','blocker','Blocker: payment flow unstable');
    INSERT INTO signals VALUES ('s2','r2','d1','decision','Decision: stability over release deadline');
    """)
    conn.commit(); conn.close()

if __name__ == "__main__":
    build_fixture()
'@ | Set-Content tests\fixtures\sqlite_fixture_builder.py; @'
# Retrieval phase 1 file update map

## New files to create
- `retrieval/contracts.py`
- `retrieval/config.py`
- `retrieval/sqlite_access.py`
- `retrieval/keyword_retriever.py`
- `retrieval/semantic_retriever.py`
- `retrieval/result_aggregator.py`
- `retrieval/orchestrator.py`
- `retrieval/service.py`
- `retrieval/__main__.py`
- `tests/fixtures/sqlite_fixture_builder.py`

## Existing files to update manually
- `lce/main.py`
  - add `compile` command later, after retrieval phase proves out
  - do not wire semantic retrieval before keyword retrieval proves out
- `docs/operations/RUNBOOK.md`
  - add retrieval proof path after phase 1 passes

## Do not touch in phase 1
- `lce/storage/sqlite_store.py`
- `lce/pipeline/*`
- `lce/execution_context.py`

## Proof commands after file creation
```powershell
py tests\fixtures\sqlite_fixture_builder.py
py -m retrieval.service "payment"
```
'@ | Set-Content docs\RETRIEVAL_FILE_UPDATE_MAP.md; @'
# Retrieval Phase 1 reasoning log

## Purpose
Create the smallest inspectable retrieval scaffold that can query existing SQLite state without introducing new infrastructure.

## Why these files
- `sqlite_access.py`: isolates SQLite reads from retrieval logic
- `keyword_retriever.py`: gives immediate usable retrieval without semantic dependency risk
- `semantic_retriever.py`: reserved adapter seam, returns empty for now
- `result_aggregator.py`: merges keyword and semantic hits deterministically
- `orchestrator.py`: one callable retrieval path
- `service.py` / `__main__.py`: gives immediate CLI proof path
- `sqlite_fixture_builder.py`: proves retrieval pipeline without touching production state

## Boundaries
- no schema invention
- no FAISS or Pyserini hard dependency in phase 1
- no mutation of existing lce pipeline
- no LLM dependency
- no compile/dossier generation yet

## Phase 1 success condition
- can query a SQLite fixture and get structured hits
- response includes signals, retrieval units, and source paths
- no external service required

## Follow-on work after proof
- swap `keyword_retriever.py` backend to SQLite FTS5 or Pyserini
- implement semantic backend in `semantic_retriever.py`
- wire into `lce.main` only after retrieval proof is stable
'@ | Set-Content data\RETRIEVAL_PHASE1_REASONING_LOG.md