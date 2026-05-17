from __future__ import annotations

from pathlib import Path

import pytest

from goat_desktop.action_gate import ActionStage, classify_action_with_reason, evaluate_action_gate, ActionRequest
from goat_desktop.audit_log import read_audit_events


ACCEPTED = {"status": "accept", "final_bbox": [10, 10, 50, 50], "fusion_path": "test"}


@pytest.mark.parametrize(
    ("action_type", "label", "expected_stage"),
    [
        ("scroll", "scroll page", ActionStage.FREE_NAVIGATION),
        ("hover", "hover tooltip", ActionStage.FREE_NAVIGATION),
        ("move pointer", "move pointer over info icon", ActionStage.FREE_NAVIGATION),
        ("type", "enter text in search field", ActionStage.LIGHT_APPROVAL),
        ("select", "select dropdown value", ActionStage.LIGHT_APPROVAL),
        ("paste", "paste into safe test field", ActionStage.LIGHT_APPROVAL),
        ("click", "Save changes", ActionStage.HARD_APPROVAL),
        ("click", "Manual Deploy", ActionStage.HARD_APPROVAL),
        ("click", "Delete record", ActionStage.HARD_APPROVAL),
        ("click", "Bezahlen", ActionStage.HARD_APPROVAL),
        ("click", "Kuendigen", ActionStage.HARD_APPROVAL),
        ("type", "password field", ActionStage.TECHNICAL_LOCK),
        ("type", "API token", ActionStage.TECHNICAL_LOCK),
        ("type", "2FA code", ActionStage.TECHNICAL_LOCK),
    ],
)
def test_classification_matrix(action_type: str, label: str, expected_stage: ActionStage) -> None:
    decision = classify_action_with_reason(action_type, label)
    assert decision.stage_enum == expected_stage
    assert decision.reason


def test_stage4_overrides_lower_stage_terms() -> None:
    decision = classify_action_with_reason("type", "save password")
    assert decision.stage_enum == ActionStage.TECHNICAL_LOCK
    assert decision.matched_term == "password"


def test_unknown_defaults_to_stage3() -> None:
    decision = classify_action_with_reason("mystery", "unrecognized operation")
    assert decision.stage_enum == ActionStage.HARD_APPROVAL
    assert decision.matched_term is None
    assert decision.reason == "unknown action defaults to stage 3"


def test_context_terms_participate_in_classification() -> None:
    decision = classify_action_with_reason(
        "focus",
        "masked field",
        {"input_type": "password", "control_type": "Edit"},
    )
    assert decision.stage_enum == ActionStage.TECHNICAL_LOCK
    assert decision.matched_term == "password"


def test_audit_contains_classification_reason(monkeypatch, tmp_path: Path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    monkeypatch.setenv("GOAT_AUDIT_LOG_PATH", str(audit_path))

    evaluate_action_gate(ActionRequest("click", "Manual Deploy", ACCEPTED))

    events = read_audit_events(audit_path)
    assert events[0]["payload"]["classification"]["stage"] == 3
    assert events[0]["payload"]["classification"]["matched_term"] == "manual deploy"
    assert events[0]["payload"]["classification"]["reason"] == "consequential-action term matched"
