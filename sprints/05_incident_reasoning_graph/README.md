# Incident Reasoning Graph

MODE: MANUAL
BRAAT BLOCK: Incident Reasoning Graph
MISSION: Store incident observations, hypotheses, failed tests, fixes, and outcomes.

## Next action

Follow the local proof path. Do not branch into dashboards or external services.

## Proof required

```text
incident_events and incident_edges exist and query returns incident matches.
```

## Stop condition

Stop when the proof is visible through CLI output and inspectable in `data/owrp.sqlite`, `logs/owrp.log`, or `reports/weekly_recovery.json`.

## Forbidden

- adding a dashboard before measurement proof
- adding external tools before local JSONL proof
- adding abstractions not used by a command
- claiming a path or function exists before it is implemented
