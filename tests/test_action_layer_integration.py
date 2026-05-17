from __future__ import annotations

from pathlib import Path

from goat_desktop.audit_log import read_audit_events
from goat_desktop.stage1_executor import Stage1ExecutionRequest, execute_stage1_action
from goat_desktop.stage2_executor import Stage2ExecutionRequest, execute_stage2_text_input
from goat_desktop.stage3_approval import APPROVAL_PHRASE, Stage3ApprovalRequest, review_stage3_action


ACCEPTED = {"status": "accept", "final_bbox": [100, 200, 180, 240], "fusion_path": "integration"}


class RecordingMouseBackend:
    def __init__(self) -> None:
        self.moves: list[tuple[int, int]] = []
        self.scrolls: list[int] = []

    def move_to(self, x: int, y: int) -> None:
        self.moves.append((x, y))

    def scroll(self, amount: int) -> None:
        self.scrolls.append(amount)


class RecordingTextBackend:
    def __init__(self) -> None:
        self.moves: list[tuple[int, int]] = []
        self.clicks = 0
        self.typed: list[str] = []

    def move_to(self, x: int, y: int) -> None:
        self.moves.append((x, y))

    def click_left(self) -> None:
        self.clicks += 1

    def type_text(self, text: str) -> None:
        self.typed.append(text)


def test_action_layer_end_to_end_decision_chain(monkeypatch, tmp_path: Path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    monkeypatch.setenv("GOAT_AUDIT_LOG_PATH", str(audit_path))

    mouse = RecordingMouseBackend()
    text = RecordingTextBackend()

    stage1 = execute_stage1_action(
        Stage1ExecutionRequest("scroll", "scroll page", ACCEPTED, dry_run=False, scroll_amount=-120),
        backend=mouse,
    )
    stage2_preview = execute_stage2_text_input(
        Stage2ExecutionRequest(
            "type",
            "enter text in safe test field",
            ACCEPTED,
            "safe input",
            user_approved=False,
            dry_run=False,
            safe_text_context=True,
        ),
        backend=text,
    )
    stage2_execute = execute_stage2_text_input(
        Stage2ExecutionRequest(
            "type",
            "enter text in safe test field",
            ACCEPTED,
            "safe input",
            user_approved=True,
            dry_run=False,
            safe_text_context=True,
        ),
        backend=text,
    )
    stage3 = review_stage3_action(
        Stage3ApprovalRequest(
            "click",
            "Manual Deploy",
            ACCEPTED,
            "This would trigger a manual deploy.",
            user_approved=True,
            approval_phrase=APPROVAL_PHRASE,
        )
    )
    stage4 = review_stage3_action(
        Stage3ApprovalRequest(
            "type",
            "password field",
            ACCEPTED,
            "This would type into a password field.",
            user_approved=True,
            approval_phrase=APPROVAL_PHRASE,
        )
    )
    unknown = review_stage3_action(
        Stage3ApprovalRequest(
            "mystery",
            "unrecognized operation",
            ACCEPTED,
            "Unknown operations must stay at Stage 3.",
            user_approved=False,
        )
    )

    assert stage1.status == "executed"
    assert stage1.executed is True
    assert mouse.scrolls == [-120]

    assert stage2_preview.status == "preview"
    assert stage2_preview.executed is False
    assert text.typed == ["safe input"]
    assert stage2_execute.status == "executed"
    assert stage2_execute.executed is True

    assert stage3.status == "approved_not_executed"
    assert stage3.executed is False

    assert stage4.status == "locked"
    assert stage4.executed is False

    assert unknown.status == "needs_approval"
    assert unknown.stage == 3
    assert unknown.executed is False

    events = read_audit_events(audit_path)
    statuses = [event["status"] for event in events]
    assert "executed" in statuses
    assert "preview" in statuses
    assert "approved_not_executed" in statuses
    assert "locked" in statuses
    assert "needs_approval" in statuses
    assert all("payload" in event for event in events)
