# Run G3 Completion Report - Stage-2 Text Input With Preview Approval

Date: 2026-05-17

## Result

Run G3 is completed for controlled Stage-2 one-line text input.

Executed action:

- one-line dummy text input into a dedicated safe Tk test field

Not executed:

- Stage-3 consequential action
- Stage-4 sensitive-field action
- file dialog
- save / submit / delete / pay / order action
- multi-line text input

## Acceptance Setup

The acceptance run used a dedicated Tk test window titled `GOAT G3 Safe Text Acceptance Window`.

The input field started empty. The only text entered was:

```text
GOAT safe input
```

The capture scope was the Tk window rectangle only. No unrelated desktop background was captured.

## Evidence

- Before screenshot: `docs/screenshots/run-g3-stage2-before-2026-05-17.png`
- After screenshot: `docs/screenshots/run-g3-stage2-after-2026-05-17.png`
- Result JSON: `docs/run-g3-real-acceptance-results.json`
- Audit log: `docs/run-g3-real-acceptance-audit.jsonl`

Observed results:

- `preview_result.status = preview`
- `preview_result.executed = false`
- `approved_result.status = executed`
- `approved_result.executed = true`
- `observed_entry_value = GOAT safe input`
- `safety.no_file_dialog = true`
- `safety.no_stage3_stage4_execution = true`

## Implementation Note

The first real acceptance attempt failed closed: the approval path returned `executed`, but the field stayed empty because the Win32 `SendInput` structure used an incomplete union. The backend was corrected to use the full Windows `INPUT` union size and to raise an explicit `OSError` if `SendInput` fails.

## Safety Check

Both committed screenshots were visually inspected before commit. They show only the dedicated Tk test window, an empty field before execution, and the dummy text after execution. No secrets, `.env` contents, chat logs, browser tabs, or unrelated desktop background are visible.

## Scope Boundary

Run G3 completes only one-line Stage-2 text input after preview approval in a known safe context. It does not authorize Stage-3 or Stage-4 execution.
