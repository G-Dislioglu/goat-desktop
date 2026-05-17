# Run G2 Code-Ready Report - Controlled Stage-1 Navigation

Date: 2026-05-17

## Scope

Run G2 adds a narrow execution path for Stage-1 free-navigation actions only.

Allowed in this run:

- scroll through the configured mouse backend
- hover / pointer move to the Coordinate-Broker-verified bbox center

Explicitly not allowed in this run:

- click
- text input
- file dialogs
- save / submit / delete / pay / order actions
- password-like or secret-like fields
- Stage 2, Stage 3, or Stage 4 execution

## Implementation

- `src/goat_desktop/stage1_executor.py`
  - wraps `evaluate_action_gate`
  - requires Broker `accept` through the existing gate
  - independently blocks anything outside Stage 1
  - independently blocks Stage-1 labels that are not in the G2 executor allowlist
  - writes JSONL audit events for executed and blocked paths
- `src/goat_desktop/bridge.py`
  - adds `POST /action/stage1`
  - defaults to `dry_run=true` for bridge calls unless the caller explicitly sets `dry_run=false`
  - bridge runtime smoke is deferred to desktop acceptance because this test shell does not have PyQt6 installed
- `pytest.ini`
  - makes `python -m pytest` reproducible without a manual `PYTHONPATH`

## Verification

Commands:

```powershell
python -m compileall src tests
python -m pytest tests/test_action_gate.py tests/test_stage1_executor.py tests/test_vision_hint_multi_provider.py -q
```

Result:

```text
24 passed
```

Evidence artifacts:

- `docs/run-g2-stage1-executor-results.json`
- `docs/run-g2-stage1-audit-sample.jsonl`

The evidence sample uses a `RecordingMouseBackend`, so no real desktop OS action was executed during report generation.

## Safety Notes

- Stage 2 can become `ready` in the gate after user approval, but the Stage-1 executor still blocks it.
- Stage 3 can become `ready` in the gate after user approval, but the Stage-1 executor still blocks it.
- Stage 4 is locked by the gate and also cannot be executed through the Stage-1 executor.
- `open menu` remains classified as Stage 1, but is intentionally blocked in G2 because opening menus may require a click path. It can be reconsidered in a later run with explicit UIA-backed targeting and a visual preview.

## Status

Run G2 is `code_ready`, not `completed`.

Completion still requires a controlled manual acceptance run on a harmless test window, with visible before/after evidence and no sensitive content on screen.
