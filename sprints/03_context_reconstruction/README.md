# Context Reconstruction Detector

MODE: MANUAL
BRAAT BLOCK: Context Reconstruction Detector
MISSION: Measure repeated loading of repo/service context.

## Next action

Follow the local proof path. Do not branch into dashboards or external services.

## Proof required

```text
context_reconstruction_events has rows after sample ingest.
```

## Stop condition

Stop when the proof is visible through CLI output and inspectable in `data/owrp.sqlite`, `logs/owrp.log`, or `reports/weekly_recovery.json`.

## Forbidden

- adding a dashboard before measurement proof
- adding external tools before local JSONL proof
- adding abstractions not used by a command
- claiming a path or function exists before it is implemented
