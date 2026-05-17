# Run G2 Completion Report - Controlled Stage-1 Navigation

Date: 2026-05-17

## Result

Run G2 is completed for controlled Stage-1 navigation.

Executed actions:

- hover / pointer move to Broker-accepted bbox center
- scroll in a harmless generated test window

Not executed:

- click
- text input
- file dialog
- save / submit / delete / pay / order actions
- Stage 2, Stage 3, or Stage 4 actions

## Acceptance Setup

The acceptance run used a dedicated Tk test window titled `GOAT G2 Safe Acceptance Window`.

The window contained only generated dummy text:

```text
Safe scroll line NN: no secrets, no tokens, no external data.
```

The first attempted Notepad-based screenshot was discarded before commit because Windows reused a tabbed Notepad instance that exposed `.env` tab names. The final acceptance used a dedicated Tk window and window-rect-only screenshots.

## Evidence

- Before screenshot: `docs/screenshots/run-g2-stage1-before-2026-05-17.png`
- After screenshot: `docs/screenshots/run-g2-stage1-after-2026-05-17.png`
- Result JSON: `docs/run-g2-real-acceptance-results.json`
- Audit log: `docs/run-g2-real-acceptance-audit.jsonl`

Observed results:

- `hover_result.status = executed`
- `scroll_result.status = executed`
- `broker_decision.status = accept`
- `safety.no_text_input = true`
- `safety.no_click = true`
- `safety.no_stage2_stage3_stage4_execution = true`

## Safety Check

Both committed screenshots were visually inspected before commit. They show only the dedicated Tk test window and generated safe text. No tokens, `.env` contents, chat logs, browser tabs, or unrelated desktop background are visible.

## Scope Boundary

Run G2 completes only Stage-1 free-navigation execution for scroll and hover/pointer move. It does not authorize Stage-2 input, Stage-3 consequential actions, or Stage-4 sensitive-field handling.
