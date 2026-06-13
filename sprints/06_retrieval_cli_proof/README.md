# Retrieval and CLI Proof

MODE: MANUAL
BRAAT BLOCK: Retrieval and CLI Proof
MISSION: Make query return prior LLM work and incident cognition.

## Next action

Follow the local proof path. Do not branch into dashboards or external services.

## Proof required

```text
python -m owrp.cli query "redis timeout" returns hits.
```

## Stop condition

Stop when the proof is visible through CLI output and inspectable in `data/owrp.sqlite`, `logs/owrp.log`, or `reports/weekly_recovery.json`.

## Forbidden

- adding a dashboard before measurement proof
- adding external tools before local JSONL proof
- adding abstractions not used by a command
- claiming a path or function exists before it is implemented
