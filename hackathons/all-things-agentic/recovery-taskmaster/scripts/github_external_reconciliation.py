from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

CRASH_EXIT = 86
RUN_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
BRANCH_PREFIX = "proof/taskmaster-external-"


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def _api(method: str, path: str, *, payload: dict[str, object] | None = None, allow_404: bool = False):
    token = _required("GITHUB_TOKEN")
    api_url = os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(
        f"{api_url}{path}",
        data=body,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "recovery-taskmaster-external-reconciliation",
            **({"Content-Type": "application/json"} if body is not None else {}),
        },
    )
    try:
        with urlopen(request, timeout=30) as response:
            raw = response.read()
            parsed = json.loads(raw) if raw else None
            return response.status, parsed
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        if allow_404 and exc.code == 404:
            return 404, None
        raise RuntimeError(f"GitHub API {method} {path} failed: HTTP {exc.code}: {raw[:500]}") from exc


def _repo_parts() -> tuple[str, str]:
    repository = _required("GITHUB_REPOSITORY")
    try:
        owner, repo = repository.split("/", 1)
    except ValueError as exc:
        raise RuntimeError("GITHUB_REPOSITORY must be owner/repo") from exc
    return owner, repo


def _paths(run_id: str) -> tuple[str, str]:
    if not RUN_ID_RE.fullmatch(run_id):
        raise ValueError("run_id must contain only letters, numbers, _ or - and be <=64 chars")
    branch = f"{BRANCH_PREFIX}{run_id}"
    target = f".taskmaster-proof/{run_id}.json"
    return branch, target


def _proof_payload(run_id: str, source_sha: str) -> bytes:
    body = {
        "proof_version": 1,
        "run_id": run_id,
        "source_sha": source_sha,
        "external_system": "github-contents-api",
        "invariant": "ACTION_PENDING -> external reread -> VERIFIED; no blind retry",
    }
    return (json.dumps(body, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _delete_branch(owner: str, repo: str, branch: str) -> None:
    if not branch.startswith(BRANCH_PREFIX):
        raise RuntimeError("refusing to delete a branch outside the proof prefix")
    ref = quote(f"heads/{branch}", safe="/")
    status, _ = _api("DELETE", f"/repos/{owner}/{repo}/git/refs/{ref}", allow_404=True)
    if status not in {204, 404}:
        raise RuntimeError(f"unexpected branch cleanup status: {status}")


def execute_crash(run_id: str, state_path: Path) -> None:
    owner, repo = _repo_parts()
    source_sha = _required("GITHUB_SHA")
    branch, target = _paths(run_id)
    payload = _proof_payload(run_id, source_sha)
    expected_sha256 = hashlib.sha256(payload).hexdigest()

    # A rerun may inherit a proof branch from a previously interrupted job.
    _delete_branch(owner, repo, branch)
    status, _ = _api(
        "POST",
        f"/repos/{owner}/{repo}/git/refs",
        payload={"ref": f"refs/heads/{branch}", "sha": source_sha},
    )
    if status != 201:
        raise RuntimeError(f"proof branch creation returned HTTP {status}")

    # Durable intent is persisted before the remote mutation.
    state = {
        "proof_version": 1,
        "run_id": run_id,
        "repository": f"{owner}/{repo}",
        "source_sha": source_sha,
        "branch": branch,
        "target_path": target,
        "state": "ACTION_PENDING",
        "expected_sha256": expected_sha256,
        "action_dispatch_count": 1,
    }
    _write_json(state_path, state)

    encoded_target = quote(target, safe="/")
    status, response = _api(
        "PUT",
        f"/repos/{owner}/{repo}/contents/{encoded_target}",
        payload={
            "message": f"proof: external reconciliation {run_id}",
            "content": base64.b64encode(payload).decode("ascii"),
            "branch": branch,
        },
    )
    if status not in {200, 201}:
        raise RuntimeError(f"remote content mutation returned HTTP {status}")
    remote_commit = ((response or {}).get("commit") or {}).get("sha")
    print(f"REMOTE_MUTATION_ACCEPTED branch={branch} target={target} commit={remote_commit}")
    print("SIMULATED_CRASH local state intentionally remains ACTION_PENDING")
    raise SystemExit(CRASH_EXIT)


def resume(run_id: str, state_path: Path, receipt_path: Path) -> None:
    owner, repo = _repo_parts()
    state = _read_json(state_path)
    branch, target = _paths(run_id)
    if state.get("run_id") != run_id or state.get("branch") != branch or state.get("target_path") != target:
        raise RuntimeError("persisted state does not match requested run")
    if state.get("state") != "ACTION_PENDING":
        raise RuntimeError(f"resume requires ACTION_PENDING, got {state.get('state')}")

    # Fresh process reconciles external state before any retry.
    encoded_target = quote(target, safe="/")
    query = urlencode({"ref": branch})
    status, remote = _api("GET", f"/repos/{owner}/{repo}/contents/{encoded_target}?{query}")
    if status != 200 or not isinstance(remote, dict):
        raise RuntimeError(f"external reread returned HTTP {status}")
    remote_bytes = base64.b64decode(str(remote["content"]).replace("\n", ""))
    observed_sha256 = hashlib.sha256(remote_bytes).hexdigest()
    expected_sha256 = str(state["expected_sha256"])

    commits_query = urlencode({"sha": branch, "path": target, "per_page": 100})
    status, commits = _api("GET", f"/repos/{owner}/{repo}/commits?{commits_query}")
    if status != 200 or not isinstance(commits, list):
        raise RuntimeError(f"commit-count query returned HTTP {status}")
    remote_mutation_commit_count = len(commits)

    executed = {
        **state,
        "state": "EXECUTED",
        "observed_sha256": observed_sha256,
        "remote_blob_sha": remote.get("sha"),
        "remote_mutation_commit_count": remote_mutation_commit_count,
        "reconciled_after_ambiguous_execution": True,
    }
    _write_json(state_path, executed)

    verified = observed_sha256 == expected_sha256 and remote_mutation_commit_count == 1
    terminal = "VERIFIED" if verified else "FAILED"
    final_state = {**executed, "state": terminal}
    _write_json(state_path, final_state)

    receipt = {
        "receipt_version": 1,
        "run_id": run_id,
        "source_sha": state["source_sha"],
        "external_system": "GitHub Contents API",
        "external_repository": state["repository"],
        "ephemeral_branch": branch,
        "target_path": target,
        "recovered_from_state": "ACTION_PENDING",
        "terminal_state": terminal,
        "expected_sha256": expected_sha256,
        "observed_sha256": observed_sha256,
        "remote_blob_sha": remote.get("sha"),
        "remote_mutation_commit_count": remote_mutation_commit_count,
        "action_dispatch_count": int(state.get("action_dispatch_count", 0)),
        "blind_retry_performed": False,
        "duplicate_remote_mutation_detected": remote_mutation_commit_count != 1,
        "fresh_process_reconciliation": True,
        "claim_boundary": {
            "proves": [
                "a real GitHub API mutation occurred on an isolated ephemeral branch",
                "the local process boundary ended while durable state remained ACTION_PENDING",
                "a fresh Python process reread GitHub before any retry",
                "the remote payload matched the pre-action SHA-256 expectation",
                "the target path had exactly one mutation commit before cleanup",
            ],
            "does_not_prove": [
                "exactly-once semantics for arbitrary external systems",
                "distributed locking across concurrent workers",
                "customer adoption",
                "production-scale reliability",
            ],
        },
    }
    _write_json(receipt_path, receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    if not verified:
        raise RuntimeError("external reconciliation receipt did not verify")


def cleanup(run_id: str) -> None:
    owner, repo = _repo_parts()
    branch, _ = _paths(run_id)
    _delete_branch(owner, repo, branch)
    print(f"CLEANUP branch={branch}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["execute-crash", "resume", "cleanup"])
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--state", type=Path, default=Path("artifacts/external-reconcile/state.json"))
    parser.add_argument("--receipt", type=Path, default=Path("artifacts/external-reconcile/receipt.json"))
    args = parser.parse_args()

    if args.mode == "execute-crash":
        execute_crash(args.run_id, args.state)
    elif args.mode == "resume":
        resume(args.run_id, args.state, args.receipt)
    else:
        cleanup(args.run_id)


if __name__ == "__main__":
    main()
