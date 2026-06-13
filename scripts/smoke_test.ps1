$ErrorActionPreference = "Stop"
python -m owrp.cli ingest
python -m owrp.cli status
python -m owrp.cli validate
python -m owrp.cli query "redis timeout"
