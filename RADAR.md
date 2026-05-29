# RADAR

## 2026-05-29: Recovery reset after governance drift

Next:

- GOAT-LIVE-002: make missing Builder websocket configuration visible in the UI/status path instead of letting the Builder connection feel inert.
- GOAT-CAPABILITY-001: choose exactly one next capability after the live proof, preferably connection status in Builder or a controlled harmless Stage-1 click design review.

Completed:

- GOAT-RECOVERY-001: current control surface reset. `RADAR.md` is the tactical next-work file; `.specify/.app-goal.md` is the product boundary; `STATE.md` and `SESSION-LOG.md` are append-only history.
- GOAT-LIVE-001: controlled local proof passed on 2026-05-29. `/builder-cue` emitted a visible popup proposal with `mayExecute=false` and no desktop, mouse, keyboard, or trading effects before approval. Artifact: `docs/goat-live-001-controlled-proof-2026-05-29.md`.
- GOAT-PACKAGE-001: local startup path added. `scripts/start-goat-desktop.ps1` starts from checkout, `-Check` verifies without opening the GUI, and `pyproject.toml` exposes the installable `goat-desktop` entry point.

Risks:

- The repo has been drifting into copy, redaction, and contract-hardening loops. Further wording/redaction work needs a concrete bug or failing test.
- The latest visible screenshots and acceptance artifacts are old relative to recent commits. Every product run now needs a visible acceptance artifact or a clear reason why it is intentionally governance-only.
- Stage 3 is still review-only and has no OS execution path. Do not describe it as product action capability.
- Builder connection can be inert without `GOAT_BUILDER_WS_URL` and `GOAT_BUILDER_TOKEN`; the next live proof must make that state visible instead of silently passing unit tests.
