from pathlib import Path

from owrp.reel_proof import build_reel_proof


def test_reel_proof_is_deterministic_over_sample(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[1]
    result = build_reel_proof(repo_root / "data" / "sample_events.jsonl", tmp_path)

    assert result["status"] == "proof_generated"
    assert result["source"] == "synthetic_sample_data"
    assert result["input_events"] == 3
    assert result["rejected_events"] == 0
    assert result["duplicate_pairs"] == 1
    assert result["avoidable_tokens"] == 1500
    assert result["avoidable_cost_usd"] == 0.015
    assert result["context_capsules"] == 1
    assert result["top_capsule"]["repo_id"] == "payments-api"
    assert result["top_capsule"]["source_count"] == 2
    assert "Repeated work classes: debugging" in result["top_capsule"]["capsule_text"]
    assert "not proof of realized labor/time savings" in result["claim_boundary"]
