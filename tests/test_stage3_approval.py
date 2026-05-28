from __future__ import annotations

import json
from pathlib import Path

from goat_desktop.audit_log import read_audit_events
from goat_desktop.stage3_approval import APPROVAL_PHRASE, Stage3ApprovalRequest, review_stage3_action


ACCEPTED = {"status": "accept", "final_bbox": [100, 200, 180, 240], "fusion_path": "test"}


def test_stage3_without_approval_needs_approval(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GOAT_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))

    result = review_stage3_action(
        Stage3ApprovalRequest(
            "click",
            "Save changes",
            ACCEPTED,
            "This would save changes in the current app.",
            user_approved=False,
        )
    )

    assert result.status == "needs_approval"
    assert result.executed is False
    assert result.stage == 3
    assert result.user_message == "Review nicht freigegeben."
    assert result.preview["approval_phrase_required"] == APPROVAL_PHRASE


def test_stage3_wrong_phrase_blocks(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GOAT_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))

    result = review_stage3_action(
        Stage3ApprovalRequest(
            "click",
            "Delete record",
            ACCEPTED,
            "This would delete a record.",
            user_approved=True,
            approval_phrase="yes",
        )
    )

    assert result.status == "approval_phrase_mismatch"
    assert result.executed is False
    assert result.user_message == "Review nicht freigegeben."


def test_stage3_correct_phrase_approves_but_does_not_execute(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GOAT_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))

    result = review_stage3_action(
        Stage3ApprovalRequest(
            "click",
            "Manual Deploy",
            ACCEPTED,
            "This would trigger a manual deploy.",
            user_approved=True,
            approval_phrase=APPROVAL_PHRASE,
            dry_run=False,
        )
    )

    assert result.status == "approved_not_executed"
    assert result.executed is False
    assert result.approval_required is False
    assert result.user_message == "Review verstanden. Keine Aktion ausgefuehrt."
    body = result.to_dict()
    assert body["completion_verified"] is False
    assert body["mayExecuteRealAction"] is False
    assert body["effects"]["desktopActionsExecuted"] is False
    assert body["effects"]["mouseActionsExecuted"] is False
    assert body["effects"]["keyboardActionsExecuted"] is False


def test_stage3_dry_run_approval_does_not_execute(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GOAT_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))

    result = review_stage3_action(
        Stage3ApprovalRequest(
            "click",
            "Pay invoice",
            ACCEPTED,
            "This would pay an invoice.",
            user_approved=True,
            approval_phrase=APPROVAL_PHRASE,
            dry_run=True,
        )
    )

    assert result.status == "approved_dry_run"
    assert result.executed is False
    assert result.user_message == "Review geprueft. Keine Aktion ausgefuehrt."


def test_broker_uncertain_stops(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GOAT_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))

    result = review_stage3_action(
        Stage3ApprovalRequest(
            "click",
            "Save changes",
            {"status": "uncertain"},
            "This would save changes.",
            user_approved=True,
            approval_phrase=APPROVAL_PHRASE,
        )
    )

    assert result.status == "stop"
    assert result.executed is False


def test_stage4_remains_locked(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GOAT_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))

    result = review_stage3_action(
        Stage3ApprovalRequest(
            "type",
            "password field",
            ACCEPTED,
            "This would type into a password field.",
            user_approved=True,
            approval_phrase=APPROVAL_PHRASE,
        )
    )

    assert result.status == "locked"
    assert result.executed is False
    assert result.stage == 4
    assert result.user_message == "Gesperrt. Bitte selbst erledigen."
    assert result.preview["label"] == "sensibles Feld"
    assert result.preview["label_redacted"] is True
    assert result.preview["consequence_summary"] == ""
    assert result.preview["consequence_summary_redacted"] is True


def test_stage4_audit_redacts_sensitive_request(monkeypatch, tmp_path: Path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    monkeypatch.setenv("GOAT_AUDIT_LOG_PATH", str(audit_path))

    review_stage3_action(
        Stage3ApprovalRequest(
            "type",
            "api-token-input",
            ACCEPTED,
            "This would type raw-secret-summary.",
            user_approved=True,
            approval_phrase=APPROVAL_PHRASE,
        )
    )

    events = read_audit_events(audit_path)
    stage3_event = next(event for event in events if event["event_type"] == "stage3_approval")
    assert stage3_event["payload"]["request"]["label"] == "[redacted]"
    assert stage3_event["payload"]["request"]["label_redacted"] is True
    assert stage3_event["payload"]["request"]["consequence_summary"] == ""
    assert stage3_event["payload"]["request"]["consequence_summary_redacted"] is True
    assert stage3_event["payload"]["result"]["preview"]["label"] == "sensibles Feld"
    assert stage3_event["payload"]["result"]["user_message"] == "Gesperrt. Bitte selbst erledigen."
    assert "api-token-input" not in json.dumps(stage3_event)
    assert "raw-secret-summary" not in json.dumps(stage3_event)


def test_stage2_is_blocked_by_stage3_review(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GOAT_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))

    result = review_stage3_action(
        Stage3ApprovalRequest(
            "type",
            "enter text in safe test field",
            ACCEPTED,
            "This would type harmless text.",
            user_approved=True,
            approval_phrase=APPROVAL_PHRASE,
        )
    )

    assert result.status == "blocked"
    assert result.stage == 2
    assert result.executed is False
    assert result.user_message == "Review nicht ausgefuehrt."


def test_stage3_audit_contains_scope(monkeypatch, tmp_path: Path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    monkeypatch.setenv("GOAT_AUDIT_LOG_PATH", str(audit_path))

    review_stage3_action(
        Stage3ApprovalRequest(
            "click",
            "Manual Deploy",
            ACCEPTED,
            "This would trigger a manual deploy.",
            user_approved=True,
            approval_phrase=APPROVAL_PHRASE,
        )
    )

    events = read_audit_events(audit_path)
    assert events[-1]["event_type"] == "stage3_approval"
    assert events[-1]["status"] == "approved_not_executed"
    assert events[-1]["payload"]["result"]["executed"] is False
    assert events[-1]["payload"]["result"]["user_message"] == "Review verstanden. Keine Aktion ausgefuehrt."
    assert "run_g4 validates hard approval only and executes no stage 3 OS action" in events[-1]["payload"][
        "assumptions"
    ]
