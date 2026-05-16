# Run 0c - Coordinate Broker Core Spike

Date: 2026-05-17
Scope: architecture spike only, no product code
Sandbox: `run-0c-coordinate-broker-work` (contents cleaned; empty directory removal blocked by a Windows file handle)

## Summary

The two-stage Coordinate Broker pattern is viable, but only when at least one local geometry source exposes the target element. On the controlled Chrome HTML test page, `mss` + `pywinauto`/UIA + local verifier produced pixel-accurate results against DOM ground truth. On Notepad, the broker correctly stopped when the desired deeper menu item was not exposed by the current UIA collection path.

Key conclusion: use `mss` + `pywinauto`/UIA as the primary MVP path. Keep OCR and Vision as optional fallback sources, not blockers for Run A. OmniParser remains a separate Run 0d candidate for apps where UIA does not expose enough structure.

## Setup

- Python requested: 3.11/3.10 if available.
- Python available: 3.14, 3.13, 3.12 only.
- Python used: 3.12.10.
- Dependencies installed: `mss`, `pywinauto`, `pillow`, `pywin32`, `requests`, `websocket-client`, `pytesseract`.
- Heavy OCR avoided: no EasyOCR, no PaddleOCR, no Torch/Paddle.
- Vision LLM: skipped in this core spike by design.
- Chrome launched with `--force-renderer-accessibility`, isolated profile, and DevTools port for DOM ground truth.

## A. Latency Breakdown

Final measured run:

| Source | Latency |
|---|---:|
| `mss` screenshot | 404.90 ms |
| `pywinauto` UIA candidate collection on Chrome | 142.16 ms |
| OCR probe | 17.40 ms, failed fast because Tesseract binary is not installed |
| Vision semantic hint | 0.01 ms, skipped |
| Broker decisions for two HTML targets | 0.22 ms total |
| Notepad UIA candidate collection | 444.25 ms |

Notes:

- `mss` was slower than the expected 5-50 ms in this run, likely because it captured the full virtual desktop and wrote PNG to disk.
- UIA was fast enough for MVP when Chrome renderer accessibility was enabled.
- Notepad UIA traversal stayed below 500 ms.

## B. Trefferquote

HTML test page, DOM ground truth:

| Target | Broker status | Fusion path | Match |
|---|---|---|---|
| Primary action button `Senden` | accept | `uia_local_semantic_match` | true |
| Primary input `Search Query` | accept | `uia_local_semantic_match` | true |

Notepad:

| Target | Broker status | Fusion path | Match |
|---|---|---|---|
| `Save As` / `Speichern unter` menu item | stop | `no_save_as_candidate` | no ground truth |

The Notepad result is a useful stop case: the script found top-level menu controls but did not expose the desired submenu item through the simple `Alt+F` + descendant collection path.

## C. False Positives

Final corrected run:

- HTML false positives: 0/2.
- Notepad false positives: 0/1, because the verifier stopped instead of accepting an ungrounded target.

Important intermediate finding: before `--force-renderer-accessibility`, Chrome UIA exposed only browser chrome. A naive semantic match accepted `Search tabs` as the primary input. That false positive was eliminated by exposing page accessibility and by verifying against DOM ground truth.

## D. False Negatives

- HTML false negatives: 0/2.
- Notepad: 1 stop for the desired `Save As` item. This is not counted as a product failure; it shows the current minimal UIA path is not enough for every native-app menu state.

## E. Total Latency

For the successful HTML path:

- Screenshot + UIA + broker decision: about 547 ms without OCR/Vision.
- Screenshot + UIA + OCR probe + broker decision: about 565 ms.

This is acceptable for Stufe 2 and very good for Stufe 3 preview flows. For Stufe 1, GOAT should avoid full-screen screenshot unless needed and rely on cached UIA/window state where possible.

## F. OCR Engine

`pytesseract` Python package installed, but the Tesseract executable is not installed or not in `PATH`.

Result: OCR source disabled cleanly. No Torch/Paddle OCR dependencies were introduced.

Recommendation: do not block Run A on OCR. For Run C or 0d, evaluate Windows-native OCR or a lightweight OCR binary separately.

## G. Vision LLM

Vision LLM was not activated. This was intentional: Run 0c tested the broker and verifier core, not provider integration.

Rule confirmed: Vision alone must never produce `accept`; it can only provide semantic hints or `uncertain`.

## H. Recommendation

The Coordinate Broker should be adopted in v1.1 with this authority split:

- Candidate Builder: UIA, OCR, optional Vision.
- Local Verifier: finite bounds, onscreen, enabled, visible, foreground window, DPI/window mapping, semantic match.
- Fusion: `accept`, `uncertain`, or `stop`; Vision-only can never accept.

Run 0d is still useful, but narrower than before:

- Test OmniParser or another UI parser only for cases where UIA does not expose enough page/app structure.
- Include Electron apps and native menu/submenu states.

Run A can start before Run 0d because tray + popup are independent of the coordinate broker implementation.

## Broker Source Summary

The spike source was kept out of product code. Sandbox contents were removed after the run; the now-empty sandbox directory could not be removed because Windows still held a file handle. The operative source shape was:

```python
# Core structure used in the sandbox:
# - launch Chrome with --force-renderer-accessibility and DevTools
# - gather DOM ground truth through Runtime.evaluate
# - capture screenshot through mss
# - gather UIA candidates through pywinauto Desktop(backend="uia")
# - optionally probe pytesseract, but fail closed if binary missing
# - skip Vision LLM in this core spike
# - verify candidates locally before accept
# - compare final bbox to DOM ground truth with IoU/center-distance rules
#
# Critical verifier rule:
#   accept requires a valid local geometry source plus semantic match.
#   vision-only may only return uncertain.
```
