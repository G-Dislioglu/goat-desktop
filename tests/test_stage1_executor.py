from __future__ import annotations

from pathlib import Path

from goat_desktop.audit_log import read_audit_events
from goat_desktop.stage1_executor import Stage1ExecutionRequest, execute_stage1_action


ACCEPTED = {"status": "accept", "final_bbox": [100, 200, 140, 240], "fusion_path": "test"}


class RecordingMouseBackend:
    def __init__(self) -> None:
        self.moves: list[tuple[int, int]] = []
        self.scrolls: list[int] = []

    def move_to(self, x: int, y: int) -> None:
        self.moves.append((x, y))

    def scroll(self, amount: int) -> None:
        self.scrolls.append(amount)


class FailingMouseBackend(RecordingMouseBackend):
    def __init__(self, *, fail_on: str) -> None:
        super().__init__()
        self.fail_on = fail_on

    def move_to(self, x: int, y: int) -> None:
        if self.fail_on == "move":
            raise OSError("test move failure")
        super().move_to(x, y)

    def scroll(self, amount: int) -> None:
        if self.fail_on == "scroll":
            raise OSError("test scroll failure")
        super().scroll(amount)


def test_stage1_scroll_executes_when_gate_allows(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GOAT_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))
    backend = RecordingMouseBackend()

    result = execute_stage1_action(
        Stage1ExecutionRequest("scroll", "scroll page", ACCEPTED, dry_run=False, scroll_amount=-240),
        backend=backend,
    )

    assert result.status == "executed"
    assert result.executed is True
    assert result.stage == 1
    assert backend.scrolls == [-240]
    assert backend.moves == []


def test_stage1_hover_moves_to_broker_bbox_center(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GOAT_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))
    backend = RecordingMouseBackend()

    result = execute_stage1_action(
        Stage1ExecutionRequest("hover", "hover tooltip", ACCEPTED, dry_run=False),
        backend=backend,
    )

    assert result.status == "executed"
    assert result.target == {"x": 120, "y": 220}
    assert backend.moves == [(120, 220)]
    assert backend.scrolls == []


def test_stage1_scroll_backend_failure_is_not_reported_as_executed(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GOAT_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))
    backend = FailingMouseBackend(fail_on="scroll")

    result = execute_stage1_action(
        Stage1ExecutionRequest("scroll", "scroll page", ACCEPTED, dry_run=False, scroll_amount=-240),
        backend=backend,
    )

    assert result.status == "failed"
    assert result.executed is False
    assert result.action_type == "scroll"
    assert "mouse backend failed" in result.reason


def test_stage1_move_backend_failure_is_not_reported_as_executed(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GOAT_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))
    backend = FailingMouseBackend(fail_on="move")

    result = execute_stage1_action(
        Stage1ExecutionRequest("hover", "hover tooltip", ACCEPTED, dry_run=False),
        backend=backend,
    )

    assert result.status == "failed"
    assert result.executed is False
    assert result.target == {"x": 120, "y": 220}
    assert "mouse backend failed" in result.reason


def test_stage1_dry_run_blocks_execution(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GOAT_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))
    backend = RecordingMouseBackend()

    result = execute_stage1_action(
        Stage1ExecutionRequest("scroll", "scroll page", ACCEPTED, dry_run=True),
        backend=backend,
    )

    assert result.status == "blocked"
    assert result.executed is False
    assert "dry_run_ready" in result.reason
    assert backend.scrolls == []


def test_stage2_is_blocked_even_when_approved(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GOAT_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))
    backend = RecordingMouseBackend()

    result = execute_stage1_action(
        Stage1ExecutionRequest("type", "enter text in search field", ACCEPTED, user_approved=True, dry_run=False),
        backend=backend,
    )

    assert result.status == "blocked"
    assert result.stage == 2
    assert result.executed is False
    assert backend.moves == []
    assert backend.scrolls == []


def test_stage3_is_blocked_even_when_approved(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GOAT_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))
    result = execute_stage1_action(
        Stage1ExecutionRequest("click", "Save changes", ACCEPTED, user_approved=True, dry_run=False),
        backend=RecordingMouseBackend(),
    )

    assert result.status == "blocked"
    assert result.stage == 3
    assert result.executed is False


def test_stage4_is_blocked(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GOAT_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))
    result = execute_stage1_action(
        Stage1ExecutionRequest("type", "password field", ACCEPTED, user_approved=True, dry_run=False),
        backend=RecordingMouseBackend(),
    )

    assert result.status == "blocked"
    assert result.stage == 4
    assert result.executed is False


def test_open_menu_stage1_is_not_in_g2_executor_allowlist(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GOAT_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))
    result = execute_stage1_action(
        Stage1ExecutionRequest("open menu", "open menu", ACCEPTED, dry_run=False),
        backend=RecordingMouseBackend(),
    )

    assert result.status == "blocked"
    assert result.stage == 1
    assert "not in the G2 executor allowlist" in result.reason


def test_broker_uncertain_blocks_before_executor(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GOAT_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))
    backend = RecordingMouseBackend()

    result = execute_stage1_action(
        Stage1ExecutionRequest("scroll", "scroll page", {"status": "uncertain"}, dry_run=False),
        backend=backend,
    )

    assert result.status == "blocked"
    assert result.executed is False
    assert backend.scrolls == []


def test_execution_audit_contains_stage1_scope(monkeypatch, tmp_path: Path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    monkeypatch.setenv("GOAT_AUDIT_LOG_PATH", str(audit_path))

    execute_stage1_action(
        Stage1ExecutionRequest("scroll", "scroll page", ACCEPTED, dry_run=False),
        backend=RecordingMouseBackend(),
    )

    events = read_audit_events(audit_path)
    assert events[-1]["event_type"] == "stage1_execution"
    assert events[-1]["status"] == "executed"
    assert "run_g2 only executes stage 1 free-navigation actions" in events[-1]["payload"]["assumptions"]
