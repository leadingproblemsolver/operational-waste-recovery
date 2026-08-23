from __future__ import annotations

from recovery_taskmaster.agent import root_agent


def test_root_agent_uses_required_google_model_and_bounded_tools() -> None:
    assert root_agent.name == "recovery_taskmaster"
    assert str(root_agent.model) == "gemini-3.5-flash"

    tool_names = {getattr(tool, "name", getattr(tool, "__name__", "")) for tool in root_agent.tools}
    assert tool_names == {
        "prepare_demo_run",
        "inspect_recovery_evidence",
        "materialize_recovery_capsule",
        "verify_recovery_receipt",
    }

    instruction = str(root_agent.instruction)
    assert "finish only when verification returns VERIFIED" in instruction
    assert "Never invent finding IDs" in instruction
    assert "outside the bounded run workspace" in instruction
