# ============================================================
# MODE: VIBECODABLE
# BRAAT BLOCK: JSONL Ingestion
# ============================================================

from pipeline.ingest_jsonl import ingest_jsonl


def test_ingest():

    events = ingest_jsonl(
        "data/sample_events.jsonl"
    )

    assert len(events) > 0

    assert events[0].event_id == "evt_001"

    assert events[0].total_tokens == 1500