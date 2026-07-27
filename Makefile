.PHONY: install test validate ingest status analyze query report export smoke clean wheel

install:
	python -m pip install .

test:
	python -m pytest -q

validate:
	owrp --root . validate

ingest:
	owrp --root . ingest --input data/sample_events.jsonl

status:
	owrp --root . status

analyze:
	owrp --root . analyze

query:
	owrp --root . query "redis timeout" --json

report:
	owrp --root . report

export:
	owrp --root . export --format json --output reports/interactions.json

smoke: clean ingest status analyze query report export

wheel:
	python -m pip wheel . --no-deps --no-build-isolation --wheel-dir dist

clean:
	rm -f data/owrp.sqlite data/owrp.sqlite-shm data/owrp.sqlite-wal reports/recovery_report.json reports/recovery_report.md reports/interactions.json
