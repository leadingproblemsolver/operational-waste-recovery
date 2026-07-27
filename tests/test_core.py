import json
import os
import subprocess
import sys
from pathlib import Path

from owrp.adapters import adapt
from owrp.core.hashing import similarity
from owrp.pipeline.ingest import ingest_jsonl
from owrp.storage.sqlite_store import SQLiteStore


def sample(event_id="1", prompt="debug redis timeout"):
    return {
        "event_id": event_id,
        "timestamp": "2026-01-01T00:00:00Z",
        "user_id": "u",
        "repo_id": "r",
        "source": "test",
        "model_name": "m",
        "prompt": prompt,
        "response": "fixed",
        "prompt_tokens": 10,
        "completion_tokens": 5,
        "total_tokens": 15,
        "cost_usd": 0.01,
        "classification": "debugging",
        "files_read": ["a.py"],
    }


def test_adapter_and_validation():
    assert adapt(sample()).validate() == []


def test_openai_adapter():
    event = adapt(
        {
            "id": "x",
            "model": "gpt",
            "usage": {"input_tokens": 3, "output_tokens": 2, "total_tokens": 5},
            "repo_id": "r",
            "user_id": "u",
        },
        "openai",
    )
    assert event.total_tokens == 5


def test_similarity():
    assert similarity("redis timeout error", "redis timeout issue") > 0.4


def test_ingest_idempotent(tmp_path):
    path = tmp_path / "events.jsonl"
    path.write_text(json.dumps(sample()) + "\n", encoding="utf-8")
    store = SQLiteStore(tmp_path)
    ingest_jsonl(path, store)
    ingest_jsonl(path, store)
    assert store.status()["interactions"] == 1
    store.close()


def test_duplicate_analysis(tmp_path):
    path = tmp_path / "events.jsonl"
    path.write_text(
        "\n".join(json.dumps(item) for item in [sample("1"), sample("2", "debug redis timeout again")]) + "\n",
        encoding="utf-8",
    )
    store = SQLiteStore(tmp_path)
    ingest_jsonl(path, store)
    result = store.analyze(0.4)
    assert result["duplicate_pairs"] == 1
    store.close()


def test_query(tmp_path):
    path = tmp_path / "events.jsonl"
    path.write_text(json.dumps(sample()) + "\n", encoding="utf-8")
    store = SQLiteStore(tmp_path)
    ingest_jsonl(path, store)
    assert store.query("redis")[0].event_id == "1"
    store.close()


def test_reject_bad_tokens(tmp_path):
    path = tmp_path / "events.jsonl"
    bad = sample()
    bad["total_tokens"] = 99
    path.write_text(json.dumps(bad) + "\n", encoding="utf-8")
    store = SQLiteStore(tmp_path)
    try:
        try:
            ingest_jsonl(path, store)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid token totals must fail")
    finally:
        store.close()


def test_cli_smoke(tmp_path):
    path = tmp_path / "events.jsonl"
    path.write_text(json.dumps(sample()) + "\n", encoding="utf-8")
    env = dict(os.environ)
    env["PYTHONPATH"] = str(Path.cwd() / "src")
    commands = [
        ("ingest", "--input", str(path)),
        ("status",),
        ("query", "redis", "--json"),
        ("report",),
        ("export", "--output", str(tmp_path / "out.json")),
    ]
    for command in commands:
        result = subprocess.run(
            [sys.executable, "-m", "owrp.cli", "--root", str(tmp_path), *command],
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
    assert (tmp_path / "out.json").exists()


def test_public_bind_requires_token(tmp_path, monkeypatch):
    from owrp.server import serve
    monkeypatch.delenv("OWRP_API_TOKEN", raising=False)
    try:
        serve(tmp_path, "0.0.0.0", 0)
    except RuntimeError as error:
        assert "OWRP_API_TOKEN" in str(error)
    else:
        raise AssertionError("public bind should require a token")


def test_strict_ingest_is_atomic(tmp_path):
    import json
    from owrp.pipeline.ingest import ingest_jsonl
    from owrp.storage.sqlite_store import SQLiteStore
    path = tmp_path / "bad.jsonl"
    valid = {"event_id":"one","timestamp":"2026-01-01T00:00:00Z","user_id":"u","repo_id":"r","source":"test","model_name":"m","prompt":"p","response":"r","prompt_tokens":1,"completion_tokens":1,"total_tokens":2,"cost_usd":0}
    path.write_text(json.dumps(valid) + "\nnot-json\n", encoding="utf-8")
    store = SQLiteStore(tmp_path)
    try:
        try:
            ingest_jsonl(path, store, strict=True)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid strict input should fail")
        assert store.status()["interactions"] == 0
    finally:
        store.close()


def test_event_id_is_stable_across_json_key_order():
    from owrp.adapters import canonical
    left = canonical({"repo_id":"r", "prompt":"p", "response":"x"})
    right = canonical({"response":"x", "prompt":"p", "repo_id":"r"})
    assert left.event_id == right.event_id


def test_ingest_rejects_possible_secrets_by_default(tmp_path):
    path = tmp_path / "secret.jsonl"
    value = sample()
    value["prompt"] = "api_key=supersecretcredential"
    path.write_text(json.dumps(value) + "\n", encoding="utf-8")
    store = SQLiteStore(tmp_path)
    try:
        try:
            ingest_jsonl(path, store)
        except ValueError as error:
            assert "possible secret" in str(error)
        else:
            raise AssertionError("secret-like content should be rejected")
        assert store.status()["interactions"] == 0
    finally:
        store.close()


def test_sensitive_redaction_before_storage(tmp_path):
    path = tmp_path / "sensitive.jsonl"
    value = sample()
    value["prompt"] = "email dev@example.com api_key=supersecretcredential"
    path.write_text(json.dumps(value) + "\n", encoding="utf-8")
    store = SQLiteStore(tmp_path)
    try:
        ingest_jsonl(path, store, redact_sensitive=True)
        stored = store.export_rows()[0]["prompt"]
        assert "dev@example.com" not in stored
        assert "supersecretcredential" not in stored
        assert "REDACTED" in stored
    finally:
        store.close()


def test_purge_is_scoped_and_invalidates_analysis(tmp_path):
    path = tmp_path / "events.jsonl"
    old = sample("old")
    recent = sample("recent")
    recent["timestamp"] = "2026-03-01T00:00:00Z"
    recent["repo_id"] = "other"
    path.write_text("\n".join([json.dumps(old), json.dumps(recent)]) + "\n", encoding="utf-8")
    store = SQLiteStore(tmp_path)
    try:
        ingest_jsonl(path, store)
        result = store.purge(before="2026-02-01T00:00:00Z")
        assert result["interactions_deleted"] == 1
        assert [item["repo_id"] for item in store.repositories()] == ["other"]
    finally:
        store.close()

def test_bundled_sample_demonstrates_duplicate_detection(tmp_path):
    source = Path(__file__).resolve().parents[1] / "data" / "sample_events.jsonl"
    store = SQLiteStore(tmp_path)
    try:
        ingest_jsonl(source, store)
        result = store.analyze()
        assert result["duplicate_pairs"] >= 1
        assert result["avoidable_tokens"] > 0
        assert result["capsules"] >= 1
    finally:
        store.close()

