from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_scan_001_eligible_context_paths_exist() -> None:
    contract = json.loads((ROOT / "contracts" / "SCAN-001.json").read_text(encoding="utf-8"))

    missing = [
        path
        for path in contract["eligible_context"]
        if any(ch in path for ch in "*?") is False and not (ROOT / path).exists()
    ]

    assert missing == []


def test_goat_vision_path_is_canonical_in_governance_docs() -> None:
    for relative_path in ["AGENTS.md", ".specify/.recovery-scan.md", "contracts/SCAN-001.json"]:
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        assert "docs/GOAT-DESKTOP-VISION.md" in text
        assert "`GOAT-DESKTOP-VISION.md`" not in text


def test_recovery_001_product_progress_gate_is_canonical() -> None:
    contract = json.loads((ROOT / "contracts" / "GOAT-RECOVERY-001.json").read_text(encoding="utf-8"))
    assert contract["next_contract"] == "GOAT-LIVE-001"

    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    app_goal = (ROOT / ".specify" / ".app-goal.md").read_text(encoding="utf-8")
    radar = (ROOT / "RADAR.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    for text in [agents, app_goal]:
        assert "Product Progress Gate" in text
        assert "GOAT-LIVE-001" in text
        assert "copy, redaction, or wording" in text

    assert "GOAT-RECOVERY-001" in radar
    assert "GOAT-LIVE-001" in radar
    assert "Run 0a" not in radar
    assert "UFO2 library usage is still an assumption" not in radar
    assert "Python 3.12 or newer" in readme
    assert "UFO2 is not the application foundation" in readme


def test_live_001_contract_requires_visible_no_effects_proof() -> None:
    contract = json.loads((ROOT / "contracts" / "GOAT-LIVE-001.json").read_text(encoding="utf-8"))
    evidence = "\n".join(contract["required_evidence"])
    forbidden = "\n".join(contract["forbidden_during_proof"])

    assert "popup-visible result" in evidence
    assert "desktopActions=false" in evidence
    assert "mouseActions=false" in evidence
    assert "keyboardActions=false" in evidence
    assert "mayExecute=false" in evidence
    assert "secrets in logs" in forbidden
    assert "unapproved mouse or keyboard effects" in forbidden


def test_live_002_contract_keeps_builder_status_visible_and_safe() -> None:
    contract = json.loads((ROOT / "contracts" / "GOAT-LIVE-002.json").read_text(encoding="utf-8"))
    claims = "\n".join(contract["claims"])

    assert contract["next_contract"] == "GOAT-CAPABILITY-001"
    assert "Missing GOAT_BUILDER_WS_URL and/or GOAT_BUILDER_TOKEN shows a visible waiting status" in claims
    assert "No secret values are displayed" in claims
    assert "No Builder cue, Stage 1, Stage 2, Stage 3, or Stage 4 permission is expanded" in claims
