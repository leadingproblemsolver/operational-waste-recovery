python -m pip install -r requirements.txt
python -m pip install -e .

python -m owrp.cli ingest --input data/sample_events.jsonl
python -m owrp.cli status
python -m owrp.cli validate
python -m owrp.cli report
python -m owrp.cli query "debugging" --limit 10
python -m pytest