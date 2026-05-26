from __future__ import annotations

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
    assert result.stage == 2
    assert result.target == {"x": 140, "y": 220}
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
    assert result.target == {"x": 140, "y": 220}
    assert "text input backend failed" in result.reason
    assert backend.moves == [(140, 220)]
    assert backend.clicks == 1
    assert backend.typed == []


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
    assert "dry_run_ready" in result.reason
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
            "secret",
            user_approved=True,
            dry_run=False,
            safe_text_context=True,
        ),
        backend=RecordingTextBackend(),
    )

    assert result.status == "blocked"
    assert result.stage == 4
    assert result.executed is False


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
    assert "run_g3 only executes stage 2 text input after explicit preview approval" in events[-1]["payload"][
        "assumptions"
    ]
