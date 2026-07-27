# Local Runbook

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install .
make smoke
```

Direct commands:

```bash
owrp --root . ingest --input data/sample_events.jsonl
owrp --root . status
owrp --root . analyze
owrp --root . query "redis timeout" --json
owrp --root . report
owrp --root . export --format json --output reports/interactions.json
```

Reset generated local state:

```bash
make clean
```

Do not run `purge` without a database backup when the imported corpus matters.
