# Validation

```bash
python -m pytest -q
python -m compileall -q src
python -m pip wheel . --no-deps --no-build-isolation --wheel-dir dist
PYTHONPATH=src python -m owrp.cli --root . validate
```

Validation establishes deterministic local contracts, not realized savings, production scale, or live provider compatibility.
