# Deployability and Distribution

The primary distribution form is a dependency-free Python wheel and `owrp` CLI for local machines, CI jobs, and internal batch runners. The optional HTTP service is read-only.

## Build and install

```bash
python -m pip wheel . --no-deps --no-build-isolation --wheel-dir dist
python -m pip install --no-index --no-deps dist/operational_waste_recovery-*.whl
owrp --root /var/lib/owrp validate
```

## Service deployment

```bash
cp .env.example .env
# replace OWRP_API_TOKEN
docker compose up --build
```

Persist `/app/data`, `/app/reports`, and `/app/logs`. Binding beyond loopback requires `OWRP_API_TOKEN`; configure one exact `OWRP_CORS_ORIGIN` only when required. Set `OWRP_DB_PATH`, `OWRP_REPORT_DIR`, and `OWRP_DUPLICATE_THRESHOLD` where defaults are unsuitable.

## Privacy and retention

Use `--redact-sensitive` when telemetry can contain personal data or credentials. Obvious secret-like content is rejected by default. Define a retention schedule and use the explicit, confirmation-gated `purge` command. Back up the SQLite database before upgrades or deletion.

## Activation event

A user has activated the system when one real event set is imported and `owrp report` produces an inspectable duplicate/recovery report that can be traced back to source events.

## Remaining external proof

Production load, provider-field drift, security integration, backup restoration, realized time savings, and organizational behavior change require live deployment and user evidence.
