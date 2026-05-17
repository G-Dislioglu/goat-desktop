# Run G5 Completion Report - Action Classification Hardening

Date: 2026-05-17

## Result

Run G5 is completed for action-classification hardening.

Executed OS actions:

- none

## Scope

Run G5 improves the classifier that maps proposed actions to the four Maya stages.

Key rules:

- Stage 4 terms are evaluated before all lower stages.
- Unknown actions default to Stage 3.
- Classification now records `matched_term`, `reason`, and `normalized_text` in the audit payload.
- Context fields such as `control_type`, `automation_id`, `role`, `aria_label`, and `input_type` can participate in classification.

## Added Coverage

The matrix now covers:

- Stage 1: scroll, hover, pointer movement
- Stage 2: text input, dropdown/select, paste
- Stage 3: save, deploy, delete, pay, cancel/subscription-like actions, upload/share/invite/transfer
- Stage 4: password, token, 2FA, API key, security-code-like fields
- Override behavior: `save password` becomes Stage 4, not Stage 3
- Unknown behavior: unrecognized operation becomes Stage 3
- Context behavior: `input_type=password` becomes Stage 4

## Verification

Commands:

```powershell
python -m compileall src tests
python -m pytest tests/test_action_gate.py tests/test_action_classification_matrix.py tests/test_stage1_executor.py tests/test_stage2_executor.py tests/test_stage3_approval.py tests/test_vision_hint_multi_provider.py -q
```

Result:

```text
60 passed
```

Evidence artifacts:

- `docs/run-g5-classification-matrix-results.json`

## Safety Notes

Run G5 intentionally adds no new execution path. It only makes the classification layer more conservative, more explainable, and better tested.
