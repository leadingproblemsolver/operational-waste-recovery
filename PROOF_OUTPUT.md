# Reproducible Local Proof

This file contains commands, not fabricated outcome claims.

```bash
rm -f data/owrp.sqlite
python -m pip install .
owrp --root . ingest --input data/sample_events.jsonl
owrp --root . status
owrp --root . analyze
owrp --root . query "redis timeout" --json
owrp --root . report
owrp --root . export --format json --output reports/interactions.json
```

Expected proof surfaces:

- ingestion exits successfully and prints accepted/rejected counts;
- `status` reports the exact records present in the local database;
- the bundled synthetic sample produces one lexical repeated-work pair at the default threshold;
- query results preserve event IDs and repository classification;
- `reports/recovery_report.json` and `.md` are generated;
- exported records can be inspected independently;
- rerunning ingestion is idempotent by event ID.

The numeric results depend entirely on the imported event set. They must not be represented as realized savings without separate workflow evidence.
