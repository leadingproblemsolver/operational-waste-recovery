from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

from .core import inspect_repo_state
from .judge_runs import _seed_owr, _setup_repo
from .strands_app import build_agent, build_openai_model


def _approval_callback(mode: str, prompts: list[str]):
    if mode == "stdio":
        return "stdio"

    def ask(prompt: str) -> str:
        prompts.append(prompt)
        return "yes" if mode == "yes" else "no"

    return ask


def run_live_smoke(*, model_id: str | None, approval_mode: str) -> dict[str, object]:
    approval_prompts: list[str] = []
    with tempfile.TemporaryDirectory(prefix="recovery-agent-live-") as tmp:
        base = Path(tmp)
        owr_root = base / "owr"
        repo = base / "repo"
        _setup_repo(repo)
        finding_id = _seed_owr(owr_root)

        model = build_openai_model(model_id=model_id)
        ask = _approval_callback(approval_mode, approval_prompts)
        agent = build_agent(model=model, ask=ask)
        prompt = (
            f"OWR root: {owr_root}\n"
            f"Repository: {repo}\n"
            "Recover the strongest repeated-work finding. Inspect evidence and repository state, "
            "run deterministic preflight, propose at most one bounded action, and if approval is "
            "granted execute it and report the exact receipt."
        )

        result = agent(prompt)
        recovery_notes = sorted((repo / ".recovery").glob("*.md")) if (repo / ".recovery").exists() else []
        repo_state = inspect_repo_state(str(repo))

        if approval_mode == "yes":
            passed = (
                len(recovery_notes) == 1
                and approval_prompts
                and repo_state["changed_paths"] == [str(recovery_notes[0].relative_to(repo))]
            )
        elif approval_mode == "deny":
            passed = len(recovery_notes) == 0 and bool(approval_prompts)
        else:
            # Stdio is for an operator-recorded demo. The receipt records outcome, but the
            # operator decides whether a created note is expected based on their response.
            passed = len(recovery_notes) <= 1

        note_receipt: dict[str, object] | None = None
        if recovery_notes:
            body = recovery_notes[0].read_bytes()
            note_receipt = {
                "path": str(recovery_notes[0].relative_to(repo)),
                "sha256": hashlib.sha256(body).hexdigest(),
                "bytes": len(body),
            }

        return {
            "receipt_version": 1,
            "agent": "Recovery Agent",
            "framework": "Strands Agents SDK",
            "model_provider": "OpenAI via Strands",
            "model_id": model_id or "OPENAI_MODEL_ID/default",
            "fixture": "synthetic_sanitized_repeated_work",
            "finding_id": finding_id,
            "approval_mode": approval_mode,
            "approval_prompt_count": len(approval_prompts),
            "recovery_note": note_receipt,
            "repo_changed_paths": repo_state["changed_paths"],
            "agent_result_excerpt": str(result)[:1200],
            "passed": passed,
            "claim_boundary": {
                "proves": [
                    "credentialed model invocation through the Strands model provider",
                    "Strands tool orchestration over the real OWR/repository tools",
                    "the mutating tool is subject to the configured HITL intervention",
                    "bounded repository outcome is externally hashable when approved",
                ],
                "does_not_prove": [
                    "real customer history",
                    "production deployment",
                    "realized savings",
                    "hackathon placement",
                ],
            },
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run credentialed Strands Recovery Agent smoke")
    parser.add_argument("--model", help="OpenAI model id; defaults to OPENAI_MODEL_ID or gpt-4o-mini")
    parser.add_argument(
        "--approval",
        choices=("stdio", "yes", "deny"),
        default="stdio",
        help="stdio for recorded human approval; yes/deny for explicit automated smoke branches",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    receipt = run_live_smoke(model_id=args.model, approval_mode=args.approval)
    rendered = json.dumps(receipt, indent=2, sort_keys=True)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
