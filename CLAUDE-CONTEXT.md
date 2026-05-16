# CLAUDE CONTEXT

## Operating Rules

- Read `docs/GOAT-DESKTOP-VISION.md` before proposing or editing implementation work.
- Treat Claude, Codex, and user text as hypotheses until checked against files, tests, runtime behavior, or primary sources.
- Reuse first: prefer existing libraries, platform APIs, and AICOS cards over rebuilding known infrastructure.
- Keep work goal-focused. Every run needs a concrete acceptance artifact: screenshot, screencast, log, test, or committed file.
- Respect dependencies. Do not implement a layer until its prerequisite spike or gate has passed.
- Clean up after temporary probes, scratch scripts, and generated artifacts unless they are intentionally committed.
- No `unverified_local_claim`: local unpushed code is not a project state.
- Desktop is the local authority boundary. Builder proposes; Desktop verifies; the user gives final approval for hard or sensitive actions.

## Required References

- `docs/AICOS-REFERENCES.md`
- AICOS `sol-cross-062` before Run C and Run G.
- AICOS `err-dev-002` before Run B.
