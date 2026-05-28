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
