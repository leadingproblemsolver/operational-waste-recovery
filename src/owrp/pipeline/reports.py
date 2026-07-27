from __future__ import annotations

import json
from pathlib import Path

from owrp.core.config import load_config
from owrp.storage.sqlite_store import SQLiteStore


def build_report(store: SQLiteStore, root: Path) -> dict:
    config = load_config(root)
    config.report_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "summary": store.status(),
        "capsules": store.capsules(),
        "limitations": [
            "Duplicate detection is lexical and repo-scoped.",
            "Estimated recovery is potential waste, not realized savings.",
        ],
    }
    json_path = config.report_dir / "recovery_report.json"
    markdown_path = config.report_dir / "recovery_report.md"
    json_path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")

    summary = data["summary"]
    lines = [
        "# Operational Waste Recovery Report",
        "",
        f"- Interactions: {summary['interactions']}",
        f"- Tokens measured: {summary['tokens_spent']}",
        f"- Spend measured: ${summary['llm_spend_usd']:.6f}",
        f"- Duplicate pairs: {summary['duplicate_pairs']}",
        f"- Potentially avoidable tokens: {summary['avoidable_tokens']}",
        f"- Potentially avoidable cost: ${summary['avoidable_cost_usd']:.6f}",
        "",
        "## Context capsules",
    ]
    for capsule in data["capsules"]:
        lines.extend(["", f"### {capsule['repo_id']}", "```", capsule["capsule_text"], "```"])
    lines.extend([
        "",
        "## Evidence boundary",
        "These values are deterministic measurements over the ingested dataset. "
        "They do not prove realized labor savings or production ROI.",
    ])
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"json": str(json_path), "markdown": str(markdown_path), "summary": summary}
