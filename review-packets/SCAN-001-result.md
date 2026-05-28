# SCAN-001 Result - GOAT Desktop Recovery Scan

Date: 2026-05-28
Commit checked: 14461c6
Branch: main
Remote: https://github.com/G-Dislioglu/goat-desktop.git
Mode: read-only scan

## Commands Run

- `git status --short`
- `git rev-parse --short HEAD`
- `git branch --show-current`
- `git remote -v`
- `Get-Content contracts\SCAN-001.json`
- `Get-Content AGENTS.md`
- `Get-Content .specify\.recovery-scan.md`
- `Get-Content STATE.md -Tail 25`
- `Get-Content RADAR.md -Tail 80`
- `Get-Content docs\GOAT-DESKTOP-VISION.md -TotalCount 160`
- `rg -n "Stage 1|Stage 2|Stage 3|Stage 4|stage1|stage2|stage3|TECHNICAL_LOCK|builder-cue|proposal|completion_verified|safe_text_context|Vision|LOCAL_GEOMETRY_SOURCES" src tests AGENTS.md .specify contracts STATE.md`
- `.\.venv\Scripts\python.exe -m compileall src tests`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `Invoke-RestMethod -Uri http://127.0.0.1:8765/healthz -TimeoutSec 5`
- artifact hygiene check for known smoke/audio/screenshot filenames

## Findings

### P2 - New governance references the wrong Vision document path

`docs\GOAT-DESKTOP-VISION.md` exists and declares itself the canonical Master-Spec. The newly added governance files and `contracts/SCAN-001.json` reference `GOAT-DESKTOP-VISION.md` without the `docs/` prefix in several places. This does not break the app, but it can mislead future scan or agent runs.

Recommendation: patch `AGENTS.md`, `.specify/.recovery-scan.md`, `.specify/.app-goal.md` if needed, and `contracts/SCAN-001.json` to use `docs/GOAT-DESKTOP-VISION.md`.

### P3 - Vision v1.1 is stricter than the current broker source list wording

The canonical Vision document says final pixel coordinates come from local geometry sources, especially UIA/OCR, and Vision must never accept alone. Current `broker.py` also allows `active_window` and `test_cue` as local geometry sources. That is acceptable for local bridge/test flows, but future docs should describe this as "local verified geometry" rather than only "UIA/OCR".

Recommendation: keep code unchanged; keep docs precise in future governance edits.

## Confirmed Safety Boundaries

- `/builder-cue` remains proposal-only. Tests cover accepted proposal, missing bbox, missing action type, rejected Vision source, verifier reject, and no popup on reject.
- Stage 1 is restricted to hover/move/scroll after approval. Tests cover dry-run, preview-required, completion verification, and Stage 2/3 blocking in Stage 1 executor.
- Stage 2 requires preview approval and `safe_text_context=true`. Tests cover no approval, unsafe context, dry-run, backend failure, verification failure, and Stage 3/4 blocking.
- Stage 3 is review-only. Tests cover `/action/stage3/review` returning `executed=false`, `completion_verified=false`, `mayExecuteRealAction=false`, and effects all false even with the correct phrase.
- Stage 4 is locked through `ActionStage.TECHNICAL_LOCK` and Stage 4 tests.
- Popup main path now shows Stage 3 as review-only with `Verstanden`, not `Ausfuehren`.

## Verification Result

- `compileall`: green
- Full suite: `233 passed`
- `/healthz`: `localScreen.ready=true`, `statusText=Bildschirm bereit`
- Smoke artifact check: `NO_TEST_ARTIFACTS_FOUND`

## Safety Regressions

No safety regression found in code or tests during this scan.

## Next BP Blocks

1. Fix governance path references to `docs/GOAT-DESKTOP-VISION.md`.
2. Add a tiny contract/doc check so SCAN-001 eligible context paths must exist.
3. Continue Stage-3 Review UX: per-action wording for Senden/Speichern/Kaufen/Loeschen/Deploy, still no OS execution.
4. Optional later: SCAN-001 verifier script, but only if it stays read-only and does not add heavy process overhead.
