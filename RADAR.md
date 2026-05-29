# RADAR

## 2026-05-29: Recovery reset after governance drift

Next:

- GOAT-RECOVERY-001: keep one current control surface for the next agent run. `RADAR.md` is the tactical next-work file; `.specify/.app-goal.md` is the product boundary; `STATE.md` and `SESSION-LOG.md` are append-only history.
- GOAT-LIVE-001: prove Builder -> Desktop -> visible popup with a live or controlled local bridge check. Required evidence: checked commit, command list, `/healthz` result when available, cue payload class, popup-visible result, and explicit no-effects flags before approval.
- GOAT-PACKAGE-001: add a normal user startup/package path after GOAT-LIVE-001 passes.
- GOAT-CAPABILITY-001: choose exactly one next capability after the live proof, preferably connection status in Builder or a controlled harmless Stage-1 click design review.

Risks:

- The repo has been drifting into copy, redaction, and contract-hardening loops. Further wording/redaction work needs a concrete bug or failing test.
- The latest visible screenshots and acceptance artifacts are old relative to recent commits. Every product run now needs a visible acceptance artifact or a clear reason why it is intentionally governance-only.
- Stage 3 is still review-only and has no OS execution path. Do not describe it as product action capability.
- Builder connection can be inert without `GOAT_BUILDER_WS_URL` and `GOAT_BUILDER_TOKEN`; the next live proof must make that state visible instead of silently passing unit tests.
