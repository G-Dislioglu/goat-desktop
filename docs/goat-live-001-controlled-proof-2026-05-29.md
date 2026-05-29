# GOAT-LIVE-001 Controlled Proof

Date: 2026-05-29
Commit checked before proof: 3b794ba
Mode: controlled local bridge proof

## Commands

- `Invoke-RestMethod -Uri http://127.0.0.1:8765/healthz -TimeoutSec 5`
- `Invoke-RestMethod -Uri http://127.0.0.1:8765/active-window -TimeoutSec 5`
- `Invoke-RestMethod -Uri http://127.0.0.1:8765/builder-cue -Method Post -ContentType application/json`

## Result

The local bridge was running and reported `Bildschirm bereit`.

Controlled cue:

- `source`: `test_cue`
- `action_type`: `hover`
- `label`: `GOAT-LIVE-001 kontrolliertes Testziel`
- `bbox`: inside the active foreground window

Bridge response:

- `ok`: true
- `scope`: `local_builder_cue_proposal`
- `safety_state`: `accept`
- `requiresPopupApproval`: true
- `mayExecute`: false
- `dispatch.popupProposalEmitted`: true

Effects before user approval:

- `effects.desktopActionsExecuted`: false
- `effects.mouseActionsExecuted`: false
- `effects.keyboardActionsExecuted`: false
- `effects.tradingActionsExecuted`: false
- `effects.mayExecuteRealAction`: false

## Notes

The first proof attempt assumed `/active-window` returned `window.bbox`. The actual local API returns `rect`, so the controlled cue builder was corrected before the passing proof.

No secrets were read or printed. No microphone capture was started. No real user field was used. No Stage 3 or Stage 4 execution was attempted.
