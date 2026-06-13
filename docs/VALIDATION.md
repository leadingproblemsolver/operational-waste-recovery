# Validation

MODE: MANUAL
BRAAT BLOCK: Executability standard
MISSION: Prevent fake progress.

`python -m owrp.cli validate` checks:

- real directories exist
- required config files exist
- required Python modules import
- SQLite DB exists after ingestion
- required tables exist

It does not check imaginary future systems.

## Passing output

```text
VALIDATE OK
```

Warnings are allowed for missing logs/report only before the first proof run.
