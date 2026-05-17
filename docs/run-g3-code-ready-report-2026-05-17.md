# Run G3 Code-Ready Report - Stage-2 Text Input With Preview Approval

Date: 2026-05-17

## Scope

Run G3 adds a narrow Stage-2 text-input executor. It is limited to one-line text input after explicit preview approval.

Allowed in this run:

- one-line text input
- maximum 120 characters
- only after Broker `accept`
- only after `user_approved=true`
- only when `safe_text_context=true`

Explicitly not allowed in this run:

- Stage-3 consequential actions
- Stage-4 sensitive fields
- multi-line input
- file dialogs
- submit / save / delete / pay / order actions

## Implementation

- `src/goat_desktop/stage2_executor.py`
  - wraps `evaluate_action_gate`
  - requires Stage 2 from the gate
  - returns `preview` unless the user has approved
  - requires `safe_text_context=true`
  - blocks Stage 3 and Stage 4 even if the caller reaches the module directly
  - writes JSONL audit events for preview, executed, and blocked paths
- `src/goat_desktop/bridge.py`
  - adds `POST /action/stage2/text`
  - defaults to `dry_run=true` unless explicitly overridden

## Verification

Commands:

```powershell
python -m compileall src tests
python -m pytest tests/test_action_gate.py tests/test_stage1_executor.py tests/test_stage2_executor.py tests/test_vision_hint_multi_provider.py -q
```

Result:

```text
34 passed
```

Evidence artifacts:

- `docs/run-g3-stage2-executor-results.json`
- `docs/run-g3-stage2-audit-sample.jsonl`

The evidence sample uses a `RecordingTextBackend`, so no real desktop OS text input was executed during code-ready evidence generation.

## Status

Run G3 is `code_ready`, not `completed`.

Completion requires a controlled real acceptance run on a harmless dedicated test window, with before/after screenshots and visual confirmation that only dummy text was entered.
