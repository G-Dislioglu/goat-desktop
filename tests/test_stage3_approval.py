from __future__ import annotations

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
    assert "run_g4 validates hard approval only and executes no stage 3 OS action" in events[-1]["payload"][
        "assumptions"
    ]
