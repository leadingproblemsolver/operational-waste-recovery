from recovery_agent.judge_runs import run_judge_scenarios


def test_judge_scenarios_all_pass() -> None:
    receipt = run_judge_scenarios()

    assert receipt["passed"] is True
    scenarios = {item["scenario"]: item for item in receipt["scenarios"]}

    assert scenarios["approved_positive"]["receipt_status"] == "EXECUTED"
    assert scenarios["approved_positive"]["replay_status"] == "ALREADY_EXISTS"

    assert scenarios["human_denied"]["mutation_attempted"] is False
    assert scenarios["human_denied"]["target_exists"] is False

    assert scenarios["stale_evidence_after_approval"]["repository_unchanged"] is True
    assert scenarios["stale_evidence_after_approval"]["target_exists"] is False
    assert (
        scenarios["stale_evidence_after_approval"]["error"]
        == "action evidence does not match persisted evidence"
    )
