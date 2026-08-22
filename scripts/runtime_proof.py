from __future__ import annotations

import json
import os
import shutil
import socket
import statistics
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOKEN = "runtime-proof-token"


def run(*args: str, check: bool = True, capture: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args),
        cwd=ROOT,
        check=check,
        text=True,
        capture_output=capture,
    )


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def request_json(url: str, *, token: str | None = TOKEN, timeout: float = 2.0) -> tuple[int, dict]:
    request = urllib.request.Request(url)
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


def wait_ready(base_url: str, deadline_seconds: float = 20.0) -> dict:
    deadline = time.monotonic() + deadline_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            status, payload = request_json(f"{base_url}/health/ready")
            if status == 200:
                return payload
        except Exception as error:  # transient container startup failures
            last_error = error
        time.sleep(0.25)
    raise RuntimeError(f"service did not become ready: {last_error}")


def docker_run_cli(image: str, volume: str, *args: str, mount: tuple[Path, str] | None = None) -> subprocess.CompletedProcess[str]:
    command = ["docker", "run", "--rm", "-v", f"{volume}:/app/data"]
    if mount:
        host, target = mount
        command.extend(["-v", f"{host.resolve()}:{target}:ro"])
    command.extend([image, "owrp", "--root", "/app", *args])
    return run(*command, check=False)


def make_strict_failure_fixture(path: Path) -> None:
    records = [
        {
            "event_id": "runtime-new-before-failure",
            "timestamp": "2026-08-22T18:20:00Z",
            "user_id": "runtime-proof",
            "repo_id": "runtime-proof-repo",
            "source": "runtime-proof",
            "model_name": "runtime-model",
            "prompt": "valid event before strict failure",
            "response": "must never persist when later record fails",
            "prompt_tokens": 2,
            "completion_tokens": 1,
            "total_tokens": 3,
            "cost_usd": 0.001,
            "classification": "proof",
            "files_read": [],
            "files_modified": [],
            "metadata": {"proof": True},
        },
        {
            "event_id": "runtime-invalid",
            "timestamp": "2026-08-22T18:21:00Z",
            "user_id": "runtime-proof",
            "repo_id": "runtime-proof-repo",
            "source": "runtime-proof",
            "model_name": "runtime-model",
            "prompt": "domain-invalid token totals",
            "response": "syntactically valid JSON",
            "prompt_tokens": 2,
            "completion_tokens": 2,
            "total_tokens": 99,
            "cost_usd": 0.001,
            "classification": "proof",
            "files_read": [],
            "files_modified": [],
            "metadata": {"proof": True},
        },
    ]
    path.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")


def main() -> int:
    if shutil.which("docker") is None:
        raise RuntimeError("docker is required for runtime proof")

    suffix = f"{os.getpid()}-{int(time.time())}"
    image = f"owrp-runtime-proof:{suffix}"
    volume = f"owrp-runtime-proof-data-{suffix}"
    container = f"owrp-runtime-proof-{suffix}"
    port = free_port()
    base_url = f"http://127.0.0.1:{port}"
    receipt: dict[str, object] = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "claim_boundary": {
            "proves": "bounded container/runtime behavior in one isolated CI run",
            "does_not_prove": ["production scale", "customer traffic", "multi-tenant isolation"],
        },
        "checks": {},
    }

    def start_container() -> None:
        run(
            "docker",
            "run",
            "-d",
            "--name",
            container,
            "-e",
            f"OWRP_API_TOKEN={TOKEN}",
            "-p",
            f"127.0.0.1:{port}:8787",
            "-v",
            f"{volume}:/app/data",
            image,
        )

    try:
        run("docker", "build", "-t", image, ".")
        run("docker", "volume", "create", volume)
        image_id = run("docker", "image", "inspect", image, "--format", "{{.Id}}").stdout.strip()
        receipt["image_id"] = image_id

        start_container()
        initial = wait_ready(base_url)
        receipt["checks"]["clean_boot"] = {
            "passed": initial.get("interactions") == 0,
            "ready": initial,
        }

        unauth_status, unauth_payload = request_json(f"{base_url}/api/status", token=None)
        receipt["checks"]["unauthorized_boundary"] = {
            "passed": unauth_status == 401 and unauth_payload == {"error": "unauthorized"},
            "status": unauth_status,
        }

        sample = ROOT / "data" / "sample_events.jsonl"
        first_ingest = docker_run_cli(
            image,
            volume,
            "ingest",
            "--input",
            "/tmp/sample.jsonl",
            mount=(sample, "/tmp/sample.jsonl"),
        )
        if first_ingest.returncode != 0:
            raise RuntimeError(f"first ingest failed: {first_ingest.stderr}")
        after_first = request_json(f"{base_url}/api/status")[1]
        receipt["checks"]["first_ingest"] = {
            "passed": after_first.get("interactions") == 3,
            "status": after_first,
        }

        replay = docker_run_cli(
            image,
            volume,
            "ingest",
            "--input",
            "/tmp/sample.jsonl",
            mount=(sample, "/tmp/sample.jsonl"),
        )
        if replay.returncode != 0:
            raise RuntimeError(f"replay ingest failed: {replay.stderr}")
        after_replay = request_json(f"{base_url}/api/status")[1]
        receipt["checks"]["duplicate_idempotency"] = {
            "passed": after_replay.get("interactions") == 3,
            "before": after_first.get("interactions"),
            "after": after_replay.get("interactions"),
        }

        with tempfile.TemporaryDirectory(prefix="owrp-runtime-proof-") as tmp:
            malformed = Path(tmp) / "strict_failure.jsonl"
            make_strict_failure_fixture(malformed)
            strict_failure = docker_run_cli(
                image,
                volume,
                "ingest",
                "--input",
                "/tmp/strict_failure.jsonl",
                mount=(malformed, "/tmp/strict_failure.jsonl"),
            )
        after_failure = request_json(f"{base_url}/api/status")[1]
        receipt["checks"]["strict_failure_atomicity"] = {
            "passed": strict_failure.returncode != 0 and after_failure.get("interactions") == 3,
            "command_exit_code": strict_failure.returncode,
            "interactions_after_failure": after_failure.get("interactions"),
        }

        report = docker_run_cli(image, volume, "report")
        report_payload = json.loads(report.stdout) if report.returncode == 0 else None
        receipt["checks"]["report_generation"] = {
            "passed": report.returncode == 0 and isinstance(report_payload, dict),
            "exit_code": report.returncode,
        }

        durations_ms: list[float] = []
        request_errors = 0
        for _ in range(30):
            started = time.perf_counter()
            try:
                status, _ = request_json(f"{base_url}/api/status")
                if status != 200:
                    request_errors += 1
            except Exception:
                request_errors += 1
            durations_ms.append((time.perf_counter() - started) * 1000)
        sorted_ms = sorted(durations_ms)
        p95_index = max(0, min(len(sorted_ms) - 1, int(len(sorted_ms) * 0.95) - 1))
        receipt["checks"]["bounded_status_probe"] = {
            "passed": request_errors == 0,
            "requests": len(durations_ms),
            "errors": request_errors,
            "error_rate": request_errors / len(durations_ms),
            "p50_ms": round(statistics.median(durations_ms), 3),
            "p95_ms": round(sorted_ms[p95_index], 3),
            "max_ms": round(max(durations_ms), 3),
        }

        run("docker", "rm", "-f", container)
        start_container()
        recreated = wait_ready(base_url)
        receipt["checks"]["container_recreation_persistence"] = {
            "passed": recreated.get("interactions") == 3,
            "ready": recreated,
        }

        run("docker", "stop", container)
        outage_observed = False
        try:
            request_json(f"{base_url}/api/status", timeout=1.0)
        except Exception:
            outage_observed = True
        run("docker", "start", container)
        recovered = wait_ready(base_url)
        receipt["checks"]["outage_recovery"] = {
            "passed": outage_observed and recovered.get("interactions") == 3,
            "outage_observed": outage_observed,
            "recovered": recovered,
        }

        checks = receipt["checks"]
        assert isinstance(checks, dict)
        receipt["passed"] = all(
            isinstance(value, dict) and value.get("passed") is True for value in checks.values()
        )
        print(json.dumps(receipt, indent=2, sort_keys=True))
        return 0 if receipt["passed"] else 1
    finally:
        run("docker", "rm", "-f", container, check=False)
        run("docker", "volume", "rm", "-f", volume, check=False)
        run("docker", "image", "rm", "-f", image, check=False)


if __name__ == "__main__":
    raise SystemExit(main())
