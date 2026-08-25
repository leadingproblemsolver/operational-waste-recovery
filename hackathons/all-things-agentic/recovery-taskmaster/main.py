from __future__ import annotations

import hashlib
import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from google.adk.cli.fast_api import get_fast_api_app

from recovery_taskmaster import tools


APP_ROOT = os.path.dirname(os.path.abspath(__file__))
_PHASES = ["OBSERVED", "EVIDENCE_READY", "ACTION_PENDING", "EXECUTED", "VERIFIED"]
_TERMINAL_FAILURES = {"BLOCKED", "FAILED"}

app: FastAPI = get_fast_api_app(
    agents_dir=APP_ROOT,
    allow_origins=["*"],
    web=True,
)


def _timeline(current_state: str, from_state: str | None = None) -> list[dict[str, str]]:
    cursor = current_state if current_state in _PHASES else from_state if from_state in _PHASES else None
    cursor_index = _PHASES.index(cursor) if cursor in _PHASES else -1
    timeline: list[dict[str, str]] = []
    for index, phase in enumerate(_PHASES):
        if index < cursor_index:
            status = "complete"
        elif index == cursor_index:
            status = "current"
        else:
            status = "pending"
        timeline.append({"phase": phase, "status": status})
    return timeline


def _safe_target_snapshot(run_id: str, target_path: object) -> dict[str, object]:
    if not isinstance(target_path, str) or not target_path:
        return {"path": None, "exists": False, "sha256": None}

    _, repo = tools._paths(run_id)
    repo_root = repo.resolve()
    target = (repo_root / Path(target_path)).resolve()
    try:
        target.relative_to(repo_root)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail="persisted target path escaped the run workspace") from exc

    if not target.is_file():
        return {"path": target_path, "exists": False, "sha256": None}
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    return {"path": target_path, "exists": True, "sha256": digest}


def _snapshot(run_id: str) -> dict[str, object]:
    try:
        state = tools._read_run_state(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if state is None:
        raise HTTPException(status_code=404, detail="run not found")

    current_state = str(state.get("state", "UNKNOWN"))
    from_state = state.get("from_state")
    from_state_str = str(from_state) if isinstance(from_state, str) else None
    artifact = _safe_target_snapshot(run_id, state.get("target_path"))

    expected = state.get("expected_sha256") or state.get("sha256")
    observed = state.get("actual_sha256") or artifact.get("sha256")
    expected_str = str(expected) if isinstance(expected, str) else None
    observed_str = str(observed) if isinstance(observed, str) else None
    hash_match = expected_str == observed_str if expected_str and observed_str else None

    return {
        "run": {
            "run_id": run_id,
            "state": current_state,
            "terminal_failure": current_state in _TERMINAL_FAILURES,
            "action_count": int(state.get("action_count", 0)),
            "finding_id": state.get("finding_id"),
            "reason": state.get("reason"),
        },
        "timeline": _timeline(current_state, from_state_str),
        "artifact": artifact,
        "verification": {
            "expected_sha256": expected_str,
            "observed_sha256": observed_str,
            "match": hash_match,
            "settled": current_state == "VERIFIED" and hash_match is True,
        },
        "raw_state": state,
        "claim_boundary": {
            "proves": "what this service can reconstruct from the persisted run state and bounded action artifact",
            "does_not_prove": "customer adoption, distributed exactly-once execution, or external systems that cannot be reconciled",
        },
    }


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {
        "status": "ok",
        "agent": "recovery_taskmaster",
        "runtime": "google-adk-cloud-run",
    }


@app.get("/api/runs/{run_id}")
def inspect_run(run_id: str) -> dict[str, object]:
    """Return a read-only view reconstructed from persisted Taskmaster run state."""
    return _snapshot(run_id)


INSPECTOR_HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Recovery Taskmaster · Run Inspector</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #090b10;
      --panel: #11151d;
      --panel-2: #171c26;
      --border: #293142;
      --text: #eef2f7;
      --muted: #9aa6b7;
      --accent: #89a8ff;
      --ok: #78d6a3;
      --warn: #f2c879;
      --bad: #ff8f8f;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: radial-gradient(circle at 20% 0%, #151b29 0, var(--bg) 36rem);
      color: var(--text);
      font: 15px/1.5 ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    a { color: var(--accent); text-decoration: none; }
    .shell { max-width: 1120px; margin: 0 auto; padding: 40px 24px 72px; }
    .eyebrow { color: var(--accent); font-size: 12px; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; }
    h1 { margin: 7px 0 8px; font-size: clamp(32px, 5vw, 54px); line-height: 1.02; letter-spacing: -.035em; }
    .lede { max-width: 760px; margin: 0 0 26px; color: var(--muted); font-size: 17px; }
    .notice { border: 1px solid var(--border); background: rgba(17,21,29,.86); padding: 12px 14px; border-radius: 12px; color: var(--muted); }
    .controls { display: flex; gap: 10px; margin: 22px 0; }
    input, button {
      border: 1px solid var(--border); border-radius: 10px; padding: 11px 13px; font: inherit;
    }
    input { min-width: 280px; flex: 1; color: var(--text); background: #0d1118; outline: none; }
    input:focus { border-color: var(--accent); }
    button { cursor: pointer; color: #07111f; background: #b8c9ff; font-weight: 750; }
    .grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
    .card, .section { border: 1px solid var(--border); background: rgba(17,21,29,.9); border-radius: 14px; }
    .card { padding: 15px; min-height: 100px; }
    .label { color: var(--muted); font-size: 12px; letter-spacing: .08em; text-transform: uppercase; }
    .value { margin-top: 7px; font-size: 18px; font-weight: 720; overflow-wrap: anywhere; }
    .badge { display: inline-flex; align-items: center; gap: 7px; padding: 5px 9px; border-radius: 999px; border: 1px solid var(--border); font-size: 13px; font-weight: 800; }
    .badge.ok { color: var(--ok); border-color: color-mix(in srgb, var(--ok) 45%, transparent); }
    .badge.warn { color: var(--warn); border-color: color-mix(in srgb, var(--warn) 45%, transparent); }
    .badge.bad { color: var(--bad); border-color: color-mix(in srgb, var(--bad) 45%, transparent); }
    .section { margin-top: 14px; padding: 18px; }
    .section h2 { margin: 0 0 14px; font-size: 18px; }
    .timeline { display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; }
    .phase { border: 1px solid var(--border); background: var(--panel-2); padding: 12px; border-radius: 10px; min-height: 78px; }
    .phase.complete { border-color: color-mix(in srgb, var(--ok) 38%, var(--border)); }
    .phase.current { border-color: var(--accent); box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--accent) 45%, transparent); }
    .phase.pending { opacity: .45; }
    .phase .phase-state { margin-top: 6px; color: var(--muted); font-size: 12px; }
    .verification { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    .hash { padding: 12px; border-radius: 10px; background: #0a0e14; border: 1px solid var(--border); overflow-wrap: anywhere; font: 12px/1.6 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
    details { margin-top: 14px; }
    summary { cursor: pointer; color: var(--muted); }
    pre { overflow: auto; padding: 14px; border-radius: 10px; background: #080b10; border: 1px solid var(--border); font-size: 12px; }
    .empty { color: var(--muted); padding: 24px 0 8px; }
    .error { color: var(--bad); }
    .footer { display: flex; justify-content: space-between; gap: 12px; margin-top: 20px; color: var(--muted); font-size: 13px; }
    @media (max-width: 760px) {
      .grid { grid-template-columns: 1fr 1fr; }
      .timeline { grid-template-columns: 1fr; }
      .verification { grid-template-columns: 1fr; }
      .controls { flex-direction: column; }
      input { min-width: 0; width: 100%; }
    }
  </style>
</head>
<body>
  <main class="shell">
    <div class="eyebrow">Execution verification sidecar</div>
    <h1>Recovery Taskmaster</h1>
    <p class="lede">An agent can perform a side effect and still not know whether the external state actually changed. This inspector shows the persisted evidence, bounded execution state, and independent verification receipt for one real run.</p>
    <div class="notice">Read-only inspector. Nothing on this page executes or retries work. Every displayed run value is reconstructed from persisted Taskmaster state.</div>

    <form class="controls" id="run-form">
      <input id="run-id" name="run_id" autocomplete="off" placeholder="Run ID, e.g. judge-demo-01" aria-label="Run ID" />
      <button type="submit">Inspect run</button>
    </form>

    <div id="message" class="empty">Enter a run ID to inspect its actual persisted state.</div>
    <div id="content" hidden>
      <section class="grid">
        <div class="card"><div class="label">State</div><div class="value" id="state"></div></div>
        <div class="card"><div class="label">Run ID</div><div class="value" id="run"></div></div>
        <div class="card"><div class="label">Action count</div><div class="value" id="actions"></div></div>
        <div class="card"><div class="label">Finding</div><div class="value" id="finding"></div></div>
      </section>

      <section class="section">
        <h2>Execution timeline</h2>
        <div class="timeline" id="timeline"></div>
      </section>

      <section class="section">
        <h2>Bounded action</h2>
        <div class="grid">
          <div class="card"><div class="label">Target</div><div class="value" id="target"></div></div>
          <div class="card"><div class="label">Artifact exists</div><div class="value" id="exists"></div></div>
          <div class="card"><div class="label">Failure / block reason</div><div class="value" id="reason"></div></div>
          <div class="card"><div class="label">Settlement</div><div class="value" id="settled"></div></div>
        </div>
      </section>

      <section class="section">
        <h2>Independent verification</h2>
        <div class="verification">
          <div><div class="label">Expected SHA-256</div><div class="hash" id="expected"></div></div>
          <div><div class="label">Observed reread SHA-256</div><div class="hash" id="observed"></div></div>
        </div>
        <details>
          <summary>Raw persisted runtime state</summary>
          <pre id="raw"></pre>
        </details>
      </section>
    </div>

    <div class="footer">
      <span>Evidence → bounded action → external reread → settlement</span>
      <span><a href="/">Agent UI</a> · <a href="/healthz">Health</a></span>
    </div>
  </main>

  <script>
    const form = document.getElementById('run-form');
    const input = document.getElementById('run-id');
    const message = document.getElementById('message');
    const content = document.getElementById('content');

    function text(id, value, fallback = '—') {
      document.getElementById(id).textContent = value === null || value === undefined || value === '' ? fallback : String(value);
    }

    function renderState(state) {
      const el = document.getElementById('state');
      const cls = state === 'VERIFIED' ? 'ok' : (state === 'FAILED' || state === 'BLOCKED' ? 'bad' : 'warn');
      el.textContent = '';
      const badge = document.createElement('span');
      badge.className = `badge ${cls}`;
      badge.textContent = state;
      el.appendChild(badge);
    }

    function renderTimeline(items) {
      const root = document.getElementById('timeline');
      root.textContent = '';
      items.forEach((item) => {
        const card = document.createElement('div');
        card.className = `phase ${item.status}`;
        const title = document.createElement('strong');
        title.textContent = item.phase;
        const status = document.createElement('div');
        status.className = 'phase-state';
        status.textContent = item.status;
        card.append(title, status);
        root.appendChild(card);
      });
    }

    async function loadRun(runId) {
      message.textContent = 'Loading persisted run state…';
      message.className = 'empty';
      content.hidden = true;
      try {
        const response = await fetch(`/api/runs/${encodeURIComponent(runId)}`, { headers: { 'Accept': 'application/json' } });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || `HTTP ${response.status}`);

        renderState(data.run.state);
        text('run', data.run.run_id);
        text('actions', data.run.action_count);
        text('finding', data.run.finding_id);
        text('target', data.artifact.path);
        text('exists', data.artifact.exists ? 'YES' : 'NO');
        text('reason', data.run.reason);
        text('settled', data.verification.settled ? 'VERIFIED' : 'NOT SETTLED');
        text('expected', data.verification.expected_sha256);
        text('observed', data.verification.observed_sha256);
        document.getElementById('raw').textContent = JSON.stringify(data.raw_state, null, 2);
        renderTimeline(data.timeline);

        message.textContent = data.verification.match === true
          ? 'Independent reread matches the expected receipt.'
          : 'Showing current persisted state; verification is not yet settled.';
        message.className = 'empty';
        content.hidden = false;
      } catch (error) {
        message.textContent = `Unable to inspect run: ${error.message}`;
        message.className = 'empty error';
      }
    }

    form.addEventListener('submit', (event) => {
      event.preventDefault();
      const runId = input.value.trim();
      if (!runId) return;
      const url = new URL(window.location.href);
      url.searchParams.set('run_id', runId);
      history.replaceState({}, '', url);
      loadRun(runId);
    });

    const initial = new URL(window.location.href).searchParams.get('run_id');
    if (initial) {
      input.value = initial;
      loadRun(initial);
    }
  </script>
</body>
</html>
"""


@app.get("/inspector", response_class=HTMLResponse)
def inspector() -> str:
    """Serve the minimal read-only run inspector; it never executes agent actions."""
    return INSPECTOR_HTML


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
