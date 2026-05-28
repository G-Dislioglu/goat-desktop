# GOAT Desktop Agent Rules

## Mission

GOAT Desktop is a local Windows assistant for normal users. Builder may propose, but GOAT Desktop verifies locally and the user gives the final approval. Keep the product simple, clear, and safe.

## Current Focus

- Prioritize safe mouse and keyboard assistance for normal users.
- Keep LiveTalk in the background unless the user explicitly asks for it.
- Prefer small, verifiable changes that preserve the current safety gates.

## Required Start Checks

Before implementation work, check the live repo state instead of trusting handoffs:

```powershell
git status --short
git rev-parse --short HEAD
git branch --show-current
```

If local runtime behavior matters, also check:

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8765/healthz -TimeoutSec 5
```

## Safety Invariants

- Do not read or print secrets.
- Do not leave audio, screenshot, or smoke-test artifacts behind.
- Do not test on real user fields.
- Use controlled Tk test windows for live Stage 1/2 E2E checks.
- `/builder-cue` is proposal-only: it must not execute mouse, keyboard, desktop, trading, or provider actions.
- Vision-only geometry must not create a trusted target.
- Builder-provided geometry must pass local verification in `broker.py`.
- Stage 1 permits only hover, move, and scroll after user approval. No click. No typing.
- Stage 2 permits only one-line text input after popup approval and `safe_text_context=true`.
- Stage 3 is review-only. It may be shown in the popup but must not execute OS actions.
- Stage 4 is locked. Sensitive fields and secret-like targets are handled by the user.

## Critical Files

- `src/goat_desktop/bridge.py`
- `src/goat_desktop/tray.py`
- `src/goat_desktop/popup.py`
- `src/goat_desktop/broker.py`
- `src/goat_desktop/action_gate.py`
- `src/goat_desktop/action_preview.py`
- `src/goat_desktop/stage1_executor.py`
- `src/goat_desktop/stage2_executor.py`
- `src/goat_desktop/stage3_approval.py`
- `STATE.md`
- `RADAR.md`
- `CLAUDE-CONTEXT.md`
- `docs/GOAT-DESKTOP-VISION.md`

## Do Not Overwrite

- `STATE.md`
- `RADAR.md`
- `CLAUDE-CONTEXT.md`
- `SESSION-LOG.md`
- `docs/GOAT-DESKTOP-VISION.md`
- existing run reports under `docs/`

Append or add narrowly scoped files instead.

## Verification

Standard verification:

```powershell
.\.venv\Scripts\python.exe -m compileall src tests
.\.venv\Scripts\python.exe -m pytest -q
Invoke-RestMethod -Uri http://127.0.0.1:8765/healthz -TimeoutSec 5
```

After live checks, clean up:

```powershell
Remove-Item -LiteralPath docs\livetalk-audio -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path docs,tests,src -Recurse -File -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -match 'goat-vision-label-smoke|goat-vision-error-smoke|goat-marker-smoke|goat-ux-screen-smoke|goat-live-text-smoke|goat-chat-screen|visible-desktop|audio-smoke|stage2.*smoke|popup.*e2e' } |
  Select-Object -ExpandProperty FullName
```

## Run Style

- Do not stop after each BP minitask.
- Bundle 2-4 connected BP blocks per run.
- Keep WLP-style scope discipline for each block.
- Small commits are fine.
- Give the final report at the end of the run.

## User Report Format

Use this shape:

- Gemacht
- Verifiziert
- Commit
- Naechster Block
