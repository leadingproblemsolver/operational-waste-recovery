# OpenAI Integration Gate

MODE: MANUAL
BRAAT BLOCK: API key integration
MISSION: Explain exactly where `OPENAI_API_KEY` belongs without making it required.

Current local proof path does not call OpenAI.

The key is read by:

```text
src/owrp/core/config.py
```

The check is visible through:

```bash
python -m owrp.cli config
```

Integrate OpenAI only in:

```text
src/owrp/execution_context/capsules.py
```

Allowed use:

- compress repeated repo context into shorter capsules
- summarize incident reasoning paths
- extract hypothesis/test/result nodes from raw Slack text

Forbidden use before measurement proof:

- chat UI
- dashboard explanations
- generic prompt optimization
- autonomous agents

The first OpenAI-backed feature must report tokens saved against the deterministic capsule baseline.
