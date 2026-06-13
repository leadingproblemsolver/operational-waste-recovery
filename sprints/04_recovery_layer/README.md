# Recovery Layer

MODE: MANUAL
BRAAT BLOCK: Recovery Layer
MISSION: Write recovery metrics and build context capsules.

## Next action

Follow the local proof path. Do not branch into dashboards or external services.

## Proof required

```text
recovery_ledger and context_capsules have rows.
```

## Stop condition

Stop when the proof is visible through CLI output and inspectable in `data/owrp.sqlite`, `logs/owrp.log`, or `reports/weekly_recovery.json`.

## Forbidden

- adding a dashboard before measurement proof
- adding external tools before local JSONL proof
- adding abstractions not used by a command
- claiming a path or function exists before it is implemented
