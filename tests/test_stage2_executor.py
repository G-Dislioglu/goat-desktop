from __future__ import annotations

import json
from pathlib import Path

from goat_desktop.audit_log import read_audit_events
from goat_desktop.stage2_executor import Stage2ExecutionRequest, execute_stage2_text_input


ACCEPTED = {"status": "accept", "final_bbox": [100, 200, 180, 240], "fusion_path": "test"}


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

    def typed_text_matches(self, text: str) -> bool:
        return bool(self.typed) and self.typed[-1] == text


class FailingTextBackend(RecordingTextBackend):
    def __init__(self, *, fail_on: str) -> None:
        super().__init__()
        self.fail_on = fail_on

    def move_to(self, x: int, y: int) -> None:
        if self.fail_on == "move":
            raise OSError("test move failure")
        super().move_to(x, y)

    def click_left(self) -> None:
        if self.fail_on == "click":
            raise OSError("test click failure")
        super().click_left()

    def type_text(self, text: str) -> None:
        if self.fail_on == "type":
            raise OSError("test type failure")
        super().type_text(text)


def test_stage2_without_approval_returns_preview(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GOAT_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))
    backend = RecordingTextBackend()

    result = execute_stage2_text_input(
        Stage2ExecutionRequest(
            "type",
            "enter text in safe test field",
            ACCEPTED,
            "hello",
            user_approved=False,
            dry_run=False,
            safe_text_context=True,
        ),
        backend=backend,
    )

    assert result.status == "preview"
    assert result.executed is False
    assert result.completion_verified is False
    assert result.user_message == "Eingabe nicht freigegeben."
    assert result.to_dict()["effects"]["keyboardActionsExecuted"] is False
    assert result.preview["text"] == "hello"
    assert backend.typed == []


def test_stage2_without_safe_context_returns_preview(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GOAT_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))
    result = execute_stage2_text_input(
        Stage2ExecutionRequest(
            "type",
            "enter text in safe test field",
            ACCEPTED,
            "hello",
            user_approved=True,
            dry_run=False,
            safe_text_context=False,
        ),
        backend=RecordingTextBackend(),
    )

    assert result.status == "preview"
    assert result.executed is False
    assert "safe_text_context" in result.reason
    assert result.user_message == "Eingabe nicht freigegeben."


def test_stage2_executes_after_approval_and_safe_context(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GOAT_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))
    backend = RecordingTextBackend()

    result = execute_stage2_text_input(
        Stage2ExecutionRequest(
            "type",
            "enter text in safe test field",
            ACCEPTED,
            "GOAT safe input",
            user_approved=True,
            dry_run=False,
            safe_text_context=True,
        ),
        backend=backend,
    )

    assert result.status == "executed"
    assert result.executed is True
    assert result.completion_verified is True
    assert result.user_message == "Text eingetragen."
    assert result.stage == 2
    assert result.target == {"x": 140, "y": 220}
    body = result.to_dict()
    assert body["effects"]["desktopActionsExecuted"] is True
    assert body["effects"]["mouseActionsExecuted"] is True
    assert body["effects"]["keyboardActionsExecuted"] is True
    assert backend.moves == [(140, 220)]
    assert backend.clicks == 1
    assert backend.typed == ["GOAT safe input"]


def test_stage2_backend_failure_is_not_reported_as_executed(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GOAT_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))
    backend = FailingTextBackend(fail_on="type")

    result = execute_stage2_text_input(
        Stage2ExecutionRequest(
            "type",
            "enter text in safe test field",
            ACCEPTED,
            "GOAT safe input",
            user_approved=True,
            dry_run=False,
            safe_text_context=True,
        ),
        backend=backend,
    )

    assert result.status == "failed"
    assert result.executed is False
    assert result.user_message == "Text nicht eingetragen."
    assert result.completion_verified is False
    assert result.target == {"x": 140, "y": 220}
    assert "text input backend failed" in result.reason
    assert backend.moves == [(140, 220)]
    assert backend.clicks == 1
    assert backend.typed == []


def test_stage2_failed_verification_is_not_reported_as_executed(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GOAT_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))

    class MismatchTextBackend(RecordingTextBackend):
        def typed_text_matches(self, text: str) -> bool:
            return False

    backend = MismatchTextBackend()

    result = execute_stage2_text_input(
        Stage2ExecutionRequest(
            "type",
            "enter text in safe test field",
            ACCEPTED,
            "GOAT safe input",
            user_approved=True,
            dry_run=False,
            safe_text_context=True,
        ),
        backend=backend,
    )

    assert result.status == "failed"
    assert result.executed is False
    assert result.completion_verified is False
    assert result.target == {"x": 140, "y": 220}
    assert "text input verification failed" in result.reason
    assert backend.typed == ["GOAT safe input"]


def test_stage2_dry_run_blocks_execution(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GOAT_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))
    backend = RecordingTextBackend()

    result = execute_stage2_text_input(
        Stage2ExecutionRequest(
            "type",
            "enter text in safe test field",
            ACCEPTED,
            "hello",
            user_approved=True,
            dry_run=True,
            safe_text_context=True,
        ),
        backend=backend,
    )

    assert result.status == "preview"
    assert result.executed is False
    assert result.reason == "Erst Eingabe pruefen, dann freigeben."
    assert backend.typed == []


def test_stage3_is_blocked_even_when_approved(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GOAT_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))
    result = execute_stage2_text_input(
        Stage2ExecutionRequest(
            "click",
            "Save changes",
            ACCEPTED,
            "hello",
            user_approved=True,
            dry_run=False,
            safe_text_context=True,
        ),
        backend=RecordingTextBackend(),
    )

    assert result.status == "blocked"
    assert result.stage == 3
    assert result.executed is False


def test_stage4_is_blocked(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GOAT_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))
    result = execute_stage2_text_input(
        Stage2ExecutionRequest(
            "type",
            "password field",
            ACCEPTED,
            "ultra-private-value",
            user_approved=True,
            dry_run=False,
            safe_text_context=True,
        ),
        backend=RecordingTextBackend(),
    )

    assert result.status == "blocked"
    assert result.stage == 4
    assert result.executed is False
    assert result.preview["text"] == ""
    assert result.preview["text_length"] == 0
    assert result.preview["text_redacted"] is True
    assert result.preview["label"] == "sensibles Feld"
    assert result.preview["label_redacted"] is True

    events = read_audit_events(tmp_path / "audit.jsonl")
    stage2_event = next(event for event in events if event["event_type"] == "stage2_execution")
    assert stage2_event["payload"]["request"]["label"] == "[redacted]"
    assert stage2_event["payload"]["request"]["label_redacted"] is True
    assert stage2_event["payload"]["request"]["text"] == ""
    assert stage2_event["payload"]["request"]["text_redacted"] is True
    assert "ultra-private-value" not in json.dumps(events)


def test_stage4_context_is_blocked_and_redacted(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GOAT_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))
    result = execute_stage2_text_input(
        Stage2ExecutionRequest(
            "type",
            "Login Feld",
            ACCEPTED,
            "context-private-value",
            user_approved=True,
            dry_run=False,
            safe_text_context=True,
            context={"automation_id": "api-token-input", "control_type": "Edit"},
        ),
        backend=RecordingTextBackend(),
    )

    assert result.status == "blocked"
    assert result.stage == 4
    assert result.executed is False
    assert result.preview["text"] == ""
    assert result.preview["text_redacted"] is True
    assert result.preview["label"] == "sensibles Feld"
    assert result.preview["label_redacted"] is True

    events = read_audit_events(tmp_path / "audit.jsonl")
    stage2_event = next(event for event in events if event["event_type"] == "stage2_execution")
    assert stage2_event["payload"]["request"]["text"] == ""
    assert stage2_event["payload"]["request"]["text_redacted"] is True
    assert stage2_event["payload"]["request"]["context"] == {"automation_id": "[redacted]", "control_type": "[redacted]"}
    assert stage2_event["payload"]["request"]["context_redacted"] is True
    assert "context-private-value" not in json.dumps(events)
    assert "api-token-input" not in json.dumps(events)


def test_multiline_text_is_blocked(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GOAT_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))
    result = execute_stage2_text_input(
        Stage2ExecutionRequest(
            "type",
            "enter text in safe test field",
            ACCEPTED,
            "line one\nline two",
            user_approved=True,
            dry_run=False,
            safe_text_context=True,
        ),
        backend=RecordingTextBackend(),
    )

    assert result.status == "blocked"
    assert "multi-line" in result.reason
    assert result.user_message == "Text nicht eingetragen."


def test_whitespace_only_text_is_blocked(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GOAT_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))
    backend = RecordingTextBackend()

    result = execute_stage2_text_input(
        Stage2ExecutionRequest(
            "type",
            "enter text in safe test field",
            ACCEPTED,
            "   ",
            user_approved=True,
            dry_run=False,
            safe_text_context=True,
        ),
        backend=backend,
    )

    assert result.status == "blocked"
    assert result.executed is False
    assert "empty" in result.reason
    assert backend.typed == []


def test_long_text_is_blocked(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GOAT_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))
    result = execute_stage2_text_input(
        Stage2ExecutionRequest(
            "type",
            "enter text in safe test field",
            ACCEPTED,
            "x" * 121,
            user_approved=True,
            dry_run=False,
            safe_text_context=True,
        ),
        backend=RecordingTextBackend(),
    )

    assert result.status == "blocked"
    assert "exceeds" in result.reason


def test_broker_uncertain_blocks(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GOAT_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))
    backend = RecordingTextBackend()

    result = execute_stage2_text_input(
        Stage2ExecutionRequest(
            "type",
            "enter text in safe test field",
            {"status": "uncertain"},
            "hello",
            user_approved=True,
            dry_run=False,
            safe_text_context=True,
        ),
        backend=backend,
    )

    assert result.status == "preview"
    assert result.executed is False
    assert backend.typed == []


def test_stage2_audit_contains_scope(monkeypatch, tmp_path: Path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    monkeypatch.setenv("GOAT_AUDIT_LOG_PATH", str(audit_path))

    execute_stage2_text_input(
        Stage2ExecutionRequest(
            "type",
            "enter text in safe test field",
            ACCEPTED,
            "hello",
            user_approved=True,
            dry_run=False,
            safe_text_context=True,
        ),
        backend=RecordingTextBackend(),
    )

    events = read_audit_events(audit_path)
    assert events[-1]["event_type"] == "stage2_execution"
    assert events[-1]["status"] == "executed"
    assert events[-1]["payload"]["result"]["completion_verified"] is True
    assert events[-1]["payload"]["result"]["user_message"] == "Text eingetragen."
    assert events[-1]["payload"]["result"]["effects"]["keyboardActionsExecuted"] is True
    assert "run_g3 only executes stage 2 text input after explicit preview approval" in events[-1]["payload"][
        "assumptions"
    ]
