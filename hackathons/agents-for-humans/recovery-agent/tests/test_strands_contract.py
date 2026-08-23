from __future__ import annotations

from strands.vended_interventions.hitl import HumanInTheLoop

from recovery_agent import strands_app


def test_strands_tools_and_hitl_policy_are_declared() -> None:
    assert callable(strands_app.build_agent)
    assert isinstance(strands_app.SYSTEM_PROMPT, str)
    assert "Human approval is authoritative" in strands_app.SYSTEM_PROMPT
    assert "execute_approved_recovery_action" in strands_app.SYSTEM_PROMPT
    assert HumanInTheLoop.__name__ == "HumanInTheLoop"


def test_only_one_tool_is_described_as_side_effecting() -> None:
    docstrings = {
        "inspect_coding_history": strands_app.inspect_coding_history.__doc__ or "",
        "inspect_repository": strands_app.inspect_repository.__doc__ or "",
        "get_recovery_evidence": strands_app.get_recovery_evidence.__doc__ or "",
        "propose_bounded_recovery_action": strands_app.propose_bounded_recovery_action.__doc__ or "",
        "execute_approved_recovery_action": strands_app.execute_approved_recovery_action.__doc__ or "",
    }
    side_effecting = [name for name, text in docstrings.items() if "mutat" in text.lower()]
    assert side_effecting == ["execute_approved_recovery_action"]
