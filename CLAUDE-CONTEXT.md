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
- Screenshot hygiene before every commit: close `.env` files, editor windows with tokens/keys/passwords, login pages, and chats or logs that may show secrets before taking acceptance screenshots.
- Multi-monitor screenshots must include only clean screens. Exclude or clear any screen not needed for the acceptance artifact.
- After every screenshot, visually inspect it before committing. If any suspicious content is visible, discard the image and retake it.
- Codex and Claude may independently discard a suspicious screenshot and stop instead of committing it. This is expected behavior, not a failure.
- Source: Run A acceptance on 2026-05-17, where a screenshot was discarded because a visible `.env` Notepad window appeared in the background.

## Required References

- `docs/AICOS-REFERENCES.md`
- AICOS `sol-cross-062` before Run C and Run G.
- AICOS `err-dev-002` before Run B.
