# Run F Live Microphone Attempt Report

Date: 2026-05-17

## Result

Run F live microphone acceptance was attempted, but not accepted.

Technical path:

- audio recorded: true
- Builder STT returned transcript: true
- SAPI response played: true
- raw audio committed: false

Acceptance result:

- expected transcript: `zeige das suchfeld`
- observed transcript: `GOAT Desktop`
- accepted: false

## TTS Language Correction

The first audible response used the Windows default SAPI voice, which sounded English. The app now prefers a German SAPI voice when available, matching descriptions containing:

- `German`
- `Deutsch`
- `Hedda`

This should make the local spoken response German on this machine, where `Microsoft Hedda Desktop - German` is installed.

## Evidence

- Metadata: `docs/run-f-live-microphone-acceptance-2026-05-17.json`

No WAV/audio artifact is committed.

## Decision

Do not set `run_f_completed`.

The STT/TTS path is technically connected, but the spoken German acceptance phrase was not recognized correctly enough.
