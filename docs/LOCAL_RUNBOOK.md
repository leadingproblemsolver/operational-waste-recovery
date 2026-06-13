# Local Runbook

MODE: MANUAL
BRAAT BLOCK: Operator proof path
MISSION: Run locally without asking anyone what to do next.

## 1. Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
```

## 2. Run proof path

```bash
python -m owrp.cli ingest
python -m owrp.cli status
python -m owrp.cli validate
python -m owrp.cli query "redis timeout"
```

## 3. Inspect proof

```bash
python -m owrp.cli inspect-db
cat reports/weekly_recovery.json
cat logs/owrp.log
```

SQLite inspection:

```bash
sqlite3 data/owrp.sqlite ".tables"
sqlite3 data/owrp.sqlite "select * from recovery_ledger;"
```

## Stop condition

Stop only when all four proof commands pass and the DB/log/report files exist.
