from __future__ import annotations

from goat_desktop.bridge import validate_flat_marker_contract


def test_flat_marker_contract_accepts_read_only_marker() -> None:
    result = validate_flat_marker_contract(
        {
            "ok": True,
            "command": "wo ist speichern",
            "targetHint": "speichern",
            "marker": {
                "available": True,
                "label": "Speichern",
                "region": {"x": 10, "y": 20, "width": 80, "height": 30},
                "confidence": 0.7,
                "source": "goat_flat_contract",
            },
            "safety": {
                "readOnly": True,
                "noClick": True,
                "noKeyboard": True,
                "noDesktopAction": True,
                "requiresGate": True,
            },
        }
    )

    assert result["ok"] is True
    assert result["status"] == "accept"
    assert result["marker"]["region"] == {"x": 10.0, "y": 20.0, "width": 80.0, "height": 30.0}
    assert result["effects"]["mouseActionsExecuted"] is False
    assert result["effects"]["keyboardActionsExecuted"] is False
    assert result["effects"]["mayExecuteRealAction"] is False


def test_flat_marker_contract_refuses_if_safety_not_read_only() -> None:
    result = validate_flat_marker_contract(
        {
            "ok": True,
            "marker": {
                "available": True,
                "label": "Speichern",
                "region": {"x": 10, "y": 20, "width": 80, "height": 30},
            },
            "safety": {
                "readOnly": True,
                "noClick": False,
                "noKeyboard": True,
                "noDesktopAction": True,
                "requiresGate": True,
            },
        }
    )

    assert result["ok"] is False
    assert result["status"] == "stop"
    assert "read-only" in result["reason"]
    assert result["marker"]["region"] is None
