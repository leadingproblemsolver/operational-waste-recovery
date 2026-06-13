# Proof Output

MODE: MANUAL
BRAAT BLOCK: Expected local proof
MISSION: Provide a known-good target without requiring external guidance.

After running:

```bash
python -m owrp.cli ingest
python -m owrp.cli status
python -m owrp.cli validate
python -m owrp.cli query "redis timeout"
```

Expected high-level proof:

```text
INGEST OK
llm_interaction: 4
incident_event: 6
duplicate_prompt_pairs: 3
context_reconstruction_events: 1
context_capsules_created: 2
VALIDATE OK
query returns Redis LLM interactions and incident reasoning nodes
```

Expected inspectable files:

```text
data/owrp.sqlite
logs/owrp.log
reports/weekly_recovery.json
```




LLM Spend: $0.15
Duplicate Spend: $0.07
Recovered: 46%

Repeated Context Loads: 7
Avoidable Tokens: 10,500

Top Waste:
- duplicated_prompt
- context_reconstruction