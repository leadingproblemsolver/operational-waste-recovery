# MODE: MANUAL
# BRAAT BLOCK: Local proof commands
# MISSION: Keep validation one command away.

.PHONY: ingest status validate query report smoke clean

ingest:
	python -m owrp.cli ingest

status:
	python -m owrp.cli status

validate:
	python -m owrp.cli validate

query:
	python -m owrp.cli query "redis timeout"

report:
	python -m owrp.cli report

smoke:
	python -m owrp.cli ingest
	python -m owrp.cli status
	python -m owrp.cli validate
	python -m owrp.cli query "redis timeout"

clean:
	rm -f data/owrp.sqlite logs/owrp.log reports/weekly_recovery.json
