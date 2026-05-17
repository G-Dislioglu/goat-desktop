from __future__ import annotations

from pathlib import Path

from goat_desktop.action_gate import ActionRequest, classify_action, evaluate_action_gate
from goat_desktop.audit_log import read_audit_events


ACCEPTED = {"status": "accept", "final_bbox": [10, 10, 50, 50], "fusion_path": "test"}


def test_stage_1_navigation_dry_run(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GOAT_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))
    decision = evaluate_action_gate(ActionRequest("scroll", "scroll page", ACCEPTED))
    assert decision.status == "dry_run_ready"
    assert decision.stage == 1
    assert decision.allowed_to_execute is False


def test_stage_2_requires_preview_approval(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GOAT_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))
    decision = evaluate_action_gate(ActionRequest("type", "enter text in search field", ACCEPTED))
    assert decision.status == "preview"
    assert decision.stage == 2
    assert decision.requires_user_approval is True


def test_stage_3_requires_explicit_approval(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GOAT_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))
    decision = evaluate_action_gate(ActionRequest("click", "Manual Deploy", ACCEPTED))
    assert decision.status == "needs_approval"
    assert decision.stage == 3
    assert decision.allowed_to_execute is False


def test_stage_4_locks_sensitive_fields(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GOAT_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))
    decision = evaluate_action_gate(ActionRequest("type", "password field", ACCEPTED, user_approved=True))
    assert decision.status == "locked"
    assert decision.stage == 4
    assert decision.allowed_to_execute is False


def test_broker_uncertain_stops(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GOAT_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))
    decision = evaluate_action_gate(ActionRequest("scroll", "scroll page", {"status": "uncertain"}))
    assert decision.status == "stop"
    assert decision.allowed_to_execute is False


def test_unknown_action_escalates_to_stage_3() -> None:
    assert classify_action("mystery", "unknown operation") == 3


def test_audit_log_contains_lineage(monkeypatch, tmp_path: Path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    monkeypatch.setenv("GOAT_AUDIT_LOG_PATH", str(audit_path))
    evaluate_action_gate(ActionRequest("click", "Delete record", ACCEPTED))
    events = read_audit_events(audit_path)
    assert len(events) == 1
    assert events[0]["event_type"] == "action_gate_needs_approval"
    assert "assumptions" in events[0]["payload"]
    assert events[0]["payload"]["request"]["broker_decision"]["status"] == "accept"
