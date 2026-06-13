# MODE: HYBRID
# BRAAT BLOCK: Context recovery layer
# MISSION: Replace repeated high-token context loads with compact, local capsules.

from __future__ import annotations

import json
from collections import Counter, defaultdict

from owrp.core.hashing import estimate_tokens
from owrp.storage.sqlite_store import SQLiteStore


def build_context_capsules(store: SQLiteStore) -> int:
    rows = store.fetch_llm_rows()
    grouped: dict[str, list] = defaultdict(list)
    for row in rows:
        grouped[row["repo_id"]].append(row)

    created = 0
    for repo_id, group in grouped.items():
        if not group:
            continue
        file_counter: Counter[str] = Counter()
        prompt_terms: Counter[str] = Counter()
        for row in group:
            file_counter.update(json.loads(row["files_read_json"]))
            prompt_terms.update(row["prompt"].lower().split())
        top_files = [path for path, _ in file_counter.most_common(6)]
        top_terms = [term.strip(".,:;()[]{}") for term, _ in prompt_terms.most_common(12) if len(term) > 3]
        service = top_files[0].split("/")[0] if top_files else "repo"
        capsule = (
            f"Repository: {repo_id}\n"
            f"Likely service/folder: {service}\n"
            f"Repeatedly loaded files: {', '.join(top_files) if top_files else 'none'}\n"
            f"Repeated investigation terms: {', '.join(top_terms[:10]) if top_terms else 'none'}\n"
            "Use this capsule before reloading the same repo context."
        )
        raw_tokens = sum(int(row["tokens_spent"]) for row in group)
        saved = max(0, raw_tokens - estimate_tokens(capsule))
        store.insert_capsule(repo_id, service, capsule, len(group), saved)
        created += 1
    return created
