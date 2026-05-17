# Run G Integration Completion Report - G1 to G5 Decision Chain

Date: 2026-05-17

## Result

The G1-G5 action layer is integrated and verified as a decision chain.

Executed real OS actions:

- none

Executed through recording backends:

- Stage 1 scroll
- Stage 2 safe text input

Reviewed without execution:

- Stage 3 hard approval
- Stage 4 technical lock
- Unknown action defaulting to Stage 3

## Verified Chain

Expected statuses:

- Stage 1 scroll: `executed`
- Stage 2 without approval: `preview`
- Stage 2 with approval and safe context: `executed`
- Stage 3 with exact approval phrase: `approved_not_executed`
- Stage 4 sensitive field: `locked`
- Unknown action: `needs_approval`

Evidence artifacts:

- `docs/run-g-integration-results-2026-05-17.json`
- `docs/run-g-integration-audit-sample.jsonl`

## Verification

Commands:

```powershell
python -m compileall src tests
python -m pytest tests/test_action_gate.py tests/test_action_classification_matrix.py tests/test_action_layer_integration.py tests/test_stage1_executor.py tests/test_stage2_executor.py tests/test_stage3_approval.py tests/test_vision_hint_multi_provider.py -q
```

Result:

```text
61 passed
```

## Safety Notes

This run adds no new capability. It verifies that the existing action layer composes correctly:

- Broker `accept` remains the prerequisite for gate progress.
- Stage 2 requires preview approval and safe text context.
- Stage 3 approval still does not execute an OS action.
- Stage 4 remains non-overridable.
- Unknown actions remain Stage 3.
