Good question. This is where the real value is.

These are the **non-negotiables you should internalize at a principles level**—not just for this project, but for any serious system you build.

---

# 🔒 CORE SYSTEM PRINCIPLES (Do not break)

### 1. Measurement before optimization

```text
If you cannot measure it, you are not allowed to improve it.
```

No:

* prompt tuning
* caching
* embeddings
* “efficiency”

Until:

```text
waste is quantified
```

---

### 2. Output proof > internal correctness

```text
A system that “works” internally but produces no inspectable output is useless.
```

Always require:

```text
DB rows
logs
reports
```

Not:

```text
“It should work”
```

---

### 3. Local-first before distributed

```text
If it doesn’t work on your machine, it has no right to exist in the cloud.
```

Sequence:

```text
JSONL → SQLite → CLI → proof
```

Only later:

```text
ClickHouse / Neo4j / Kubernetes
```

---

### 4. One direction architecture

```text
Dependencies flow in one direction only.
```

```text
core ← pipeline ← storage ← retrieval
```

Never:

```text
pipeline → core → pipeline
```

---

### 5. No feature without a resource mapping

Every feature must answer:

```text
What resource does this recover?
```

If not:

```text
Do not build it.
```

---

### 6. Detection ≠ recovery

```text
Detecting waste is not value.

Recovering resources is value.
```

Always separate:

```text
detection
→ classification
→ recovery calculation
```

---

### 7. Schema is truth

```text
The ingest schema defines reality.
```

Not:

* your design doc
* your earlier model
* your assumptions

Reality = what the parser accepts.

---

### 8. Fix inputs before code

```text
80% of pipeline issues are schema/input mismatches.
```

Default move:

```text
Fix JSONL
```

Not:

```text
Rewrite system
```

---

### 9. No abstractions without pressure

```text
Abstraction is earned, not assumed.
```

No:

* factories
* managers
* orchestrators
* pipelines-of-pipelines

Until:

```text
you hit duplication pain
```

---

### 10. Determinism is power

```text
Same input → same output → always
```

If not:

```text
You cannot debug
You cannot trust results
You cannot prove value
```

---

# ⚙️ EXECUTION PRINCIPLES

### 11. One active thread

```text
No parallel deep work.
```

At any moment:

```text
1 file
1 bug
1 command
```

---

### 12. Friction collapse

```text
If stuck for 15 minutes → reduce scope
```

Not:

```text
expand system
add tools
change architecture
```

---

### 13. CLI is the truth layer

```text
If it’s not accessible via CLI, it doesn’t exist.
```

UI is optional.

CLI is mandatory.

---

### 14. Logs are part of the system

```text
If you can’t explain what happened, your system is broken.
```

Always:

```text
log inputs
log outputs
log failures
```

---

### 15. Reports are the product

```text
Your product is not code.

Your product is:
Recovered resources
```

---

# 🧠 THINKING PRINCIPLES

### 16. Build for replayability

```text
Can I rerun everything from raw data?
```

If no:

```text
system is not reliable
```

---

### 17. Optimize for insight, not features

```text
One insight > ten features
```

Example:

```text
“38% of LLM spend is duplicated”
```

is more valuable than:

```text
a dashboard with 20 charts
```

---

### 18. Prefer boring tech early

```text
SQLite > Postgres > ClickHouse
```

```text
JSONL > streaming
```

```text
functions > services
```

---

### 19. Separate signal from noise

```text
More data ≠ more value
```

You want:

```text
data that reveals patterns
```

---

### 20. Build proofs, not promises

```text
Never say:
“This will reduce cost”

Always show:
“This reduced cost by X”
```

---

# 🔥 META PRINCIPLE (most important)

```text
Every line of code must justify itself through recovered resources.
```

If it cannot:

```text
delete it
```

---

# If you internalize only 3 things

Take these:

```text
1. Measurement before everything
2. Local proof before scale
3. No feature without resource recovery
```

---

This is what separates:


people who build systems
vs
people who build projects

