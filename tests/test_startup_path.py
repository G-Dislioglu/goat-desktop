from __future__ import annotations

import json
import subprocess
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_pyproject_exposes_goat_desktop_entry_point() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert pyproject["project"]["scripts"]["goat-desktop"] == "goat_desktop.__main__:main"


def test_start_script_has_non_gui_check_mode() -> None:
    script = ROOT / "scripts" / "start-goat-desktop.ps1"
    text = script.read_text(encoding="utf-8")

    assert "param(" in text
    assert "[switch]$Check" in text
    assert "pythonPathStartsWithSrc" in text
    assert "-m goat_desktop" in text


def test_start_script_check_mode_resolves_local_startup_path() -> None:
    script = ROOT / "scripts" / "start-goat-desktop.ps1"
    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script),
            "-Check",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    )
    payload = json.loads(result.stdout)

    assert payload["ok"] is True
    assert Path(payload["repoRoot"]).resolve() == ROOT
    assert payload["pythonPathStartsWithSrc"] is True
    assert payload["module"] == "goat_desktop"
    assert payload["entry"] == "goat_desktop.__main__:main"


def test_package_001_contract_points_to_next_live_visibility_work() -> None:
    contract = json.loads((ROOT / "contracts" / "GOAT-PACKAGE-001.json").read_text(encoding="utf-8"))

    assert contract["next_contract"] == "GOAT-LIVE-002"
    assert "No Stage 1, Stage 2, Stage 3, or Stage 4 permission is expanded" in contract["claims"]
