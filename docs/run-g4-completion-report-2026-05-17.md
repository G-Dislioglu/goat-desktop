# Run G4 Completion Report - Stage-3 Hard Approval

Date: 2026-05-17

## Result

Run G4 is completed for Stage-3 hard approval review.

Executed actions:

- none

Validated approval states:

- `needs_approval` without user approval
- `approval_phrase_mismatch` with wrong approval phrase
- `approved_not_executed` with correct phrase
- `locked` for Stage-4 sensitive-field attempts

## Scope

Run G4 intentionally does not execute Stage-3 OS actions. The terminal success state is `approved_not_executed`.

The exact approval phrase is:

```text
I approve this stage 3 action
```

This phrase is deliberately longer than a simple "yes" to reduce accidental approval.

## Implementation

- `src/goat_desktop/stage3_approval.py`
  - wraps `evaluate_action_gate`
  - requires Stage 3 from the gate
  - requires Broker `accept`
  - requires `user_approved=true`
  - requires exact approval phrase
  - never executes the OS action
  - keeps Stage 4 locked
- `src/goat_desktop/bridge.py`
  - adds `POST /action/stage3/review`

## Verification

Commands:

```powershell
python -m compileall src tests
python -m pytest tests/test_action_gate.py tests/test_stage1_executor.py tests/test_stage2_executor.py tests/test_stage3_approval.py tests/test_vision_hint_multi_provider.py -q
```

Result:

```text
42 passed
```

Evidence artifacts:

- `docs/run-g4-stage3-approval-results.json`
- `docs/run-g4-stage3-approval-audit-sample.jsonl`

## Safety Notes

- Stage 3 approval does not imply execution in Run G4.
- Stage 4 technical lock is not overridable by approval phrase.
- Stage 2 actions are blocked by the Stage-3 review module and must use the Stage-2 executor.
- A later run may add a harmless dummy-button execution path, but that must be a separate acceptance run with its own audit and visual proof.
