from __future__ import annotations

from strands.vended_interventions.hitl import HumanInTheLoop

from recovery_agent import strands_app


def test_strands_tools_and_hitl_policy_are_declared() -> None:
    assert callable(strands_app.build_agent)
    assert isinstance(strands_app.SYSTEM_PROMPT, str)
    assert "Human approval is authoritative" in strands_app.SYSTEM_PROMPT
    assert strands_app.MUTATING_TOOL_NAME == "execute_approved_recovery_action"
    assert HumanInTheLoop.__name__ == "HumanInTheLoop"


def test_only_mutating_tool_is_excluded_from_safe_allow_list() -> None:
    assert strands_app.MUTATING_TOOL_NAME not in strands_app.SAFE_TOOL_NAMES
    assert strands_app.SAFE_TOOL_NAMES == (
        "inspect_coding_history",
        "inspect_repository",
        "get_recovery_evidence",
        "run_recovery_preflight",
        "propose_bounded_recovery_action",
    )
