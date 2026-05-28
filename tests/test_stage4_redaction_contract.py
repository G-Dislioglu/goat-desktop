from __future__ import annotations

import json
from pathlib import Path

from goat_desktop import bridge
from goat_desktop.action_gate import ActionRequest, evaluate_action_gate
from goat_desktop.audit_log import read_audit_events
from goat_desktop.bridge import create_app
from goat_desktop.screen import WindowInfo
from goat_desktop.stage2_executor import Stage2ExecutionRequest, execute_stage2_text_input


ACCEPTED = {"status": "accept", "final_bbox": [20, 20, 120, 50], "fusion_path": "test"}
RAW_LABEL = "api-token-input"
RAW_TEXT = "raw-secret-text-value"
RAW_CONTEXT = {"automation_id": "api-token-input", "aria_label": "2FA code"}
RAW_VALUES = [RAW_LABEL, RAW_TEXT, "2FA code"]


class FakeSignal:
    def __init__(self) -> None:
        self.payloads: list[dict] = []

    def emit(self, payload: dict) -> None:
        self.payloads.append(payload)


def test_stage4_redaction_contract_blocks_raw_values_across_surfaces(monkeypatch, tmp_path: Path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    monkeypatch.setenv("GOAT_AUDIT_LOG_PATH", str(audit_path))

    gate = evaluate_action_gate(ActionRequest("type", RAW_LABEL, ACCEPTED, user_approved=True, context=RAW_CONTEXT))
    stage2 = execute_stage2_text_input(
        Stage2ExecutionRequest(
            "type",
            RAW_LABEL,
            ACCEPTED,
            RAW_TEXT,
            user_approved=True,
            dry_run=False,
            safe_text_context=True,
            context=RAW_CONTEXT,
        )
    )

    emitted = FakeSignal()
    monkeypatch.setattr(
        bridge,
        "get_active_window",
        lambda: WindowInfo(hwnd=1, title="Test Window", rect=[0, 0, 300, 200], foreground=True),
    )
    builder_cue = _endpoint_for(create_app(dispatch_builder_cue=emitted.emit), "/builder-cue")
    builder_response = builder_cue(
        {
            "source": "test_cue",
            "action_type": "type",
            "label": RAW_LABEL,
            "text": RAW_TEXT,
            "safe_text_context": True,
            "bbox": [20, 20, 120, 50],
            "context": RAW_CONTEXT,
        }
    )

    surfaces = {
        "gate_decision": gate.to_dict(),
        "stage2_response": stage2.to_dict(),
        "audit_events": read_audit_events(audit_path),
        "builder_response": builder_response,
        "popup_payload": emitted.payloads[0],
    }

    assert gate.status == "locked"
    assert stage2.status == "blocked"
    assert emitted.payloads[0]["stage4_lock"] is True
    assert emitted.payloads[0]["label"] == "sensibles Ziel"
    assert emitted.payloads[0]["text"] == ""

    serialized = json.dumps(surfaces, ensure_ascii=False)
    for raw_value in RAW_VALUES:
        assert raw_value not in serialized


def _endpoint_for(app, path: str):
    for route in app.routes:
        if getattr(route, "path", None) == path:
            return route.endpoint
    raise AssertionError(f"route not found: {path}")
