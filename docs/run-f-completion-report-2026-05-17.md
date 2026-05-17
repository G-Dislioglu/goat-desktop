# Run F Completion Report

Date: 2026-05-17

## Result

Run F final live acceptance passed through the visible GOAT Desktop UI.

Observed in the acceptance screenshot:

- Audio status: `STT Builder aktiv / TTS Builder aktiv`
- Screen context: `Zeige mir das Suchfeld.`
- Maya response: `Gehoert: Zeige mir das Suchfeld.. Ich handle nur nach Freigabe.`
- The yellow overlay ball is visible.

The accepted path is:

```text
visible GOAT Desktop UI -> microphone -> Builder STT -> Builder TTS -> local playback
```

## Fixes Required Before Acceptance

The final acceptance required several practical fixes:

- A visible recording cue and longer 5-second capture window.
- Builder STT/TTS auto-mode when Builder URL and token are configured.
- Windows User environment fallback for Builder audio configuration.
- Visible Audio status in the popup.
- Clearer Builder-STT error text.
- `GOAT_BUILDER_RESOLVE_IP=216.24.57.7` for local DNS failure against `soulmatch-1.onrender.com`.

## Evidence

- Screenshot: `docs/screenshots/run-f-final-acceptance-2026-05-17.png`

No microphone WAV and no generated TTS WAV are committed.

## Decision

Run F is completed.
