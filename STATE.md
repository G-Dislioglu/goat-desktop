# STATE

last_verified_against_code: 2026-05-16

run_0a_completed_2026_05_16:
"Wahrheitsklaerung GOAT Control Adapter 79ec22b durchgefuehrt am 2026-05-16. Ergebnis: phantom_claim. Hash existiert in keinem der vier Repos (Big-Bro, Maya, aicos-registry, soulmatch), weder lokal noch remote. GOAT Desktop startet ohne Vorgaenger-Code. Detail-Bericht: docs/run-0a-truth-report-2026-05-16.md."

run_0b_completed_2026_05_16:
"UFO2 Library-Spike durchgefuehrt am 2026-05-16. Ergebnis: low-level Module potentiell wiederverwendbar, aber UFO2 als Library-Fundament nicht ueberzeugend. Full Install scheitert wegen Python-Pins (faiss-cpu, pandas). ControlPhotographer-Messung: 2.27s Mittelwert pro Screen-Sensor-Aufruf - zu langsam fuer CNC-Anchor-Protokoll ohne Optimierung. Codex-Empfehlung: kein UFO-Agent-Loop, nur schmal gewrappte Low-Level-Module. Architektur-Frage offen: UFO2 vs Slim Stack (mss + pywinauto + OmniParser direkt). Detail-Bericht: docs/run-0b-ufo2-spike-2026-05-16.md."

run_0c_completed_2026_05_17:
"Coordinate Broker Core Spike durchgefuehrt am 2026-05-17. Ergebnis: zweistufiger Broker (Candidate Builder + Local Verifier) ist als Architektur tragfaehig, wenn mindestens eine lokale Geometriequelle valide Bounds liefert. Chrome-Testseite mit --force-renderer-accessibility: UIA traf Senden-Button und Search-Input gegen DOM-Ground-Truth mit IoU 0.9714/0.98 bei ca. 547 ms Screenshot+UIA+Broker. OCR war nicht verfuegbar (Tesseract-Binary fehlt), Vision-LLM wurde bewusst uebersprungen. Notepad-Menue zeigte einen sauberen Stop-Fall, weil Save-As nicht exponiert wurde. Empfehlung: v1.1 auf Slim Stack + Coordinate Broker schreiben; OmniParser nur als separater Run 0d fuer UIA-Luecken testen. Detail-Bericht: docs/run-0c-coordinate-broker-spike-2026-05-17.md."

v1_1_published_2026_05_17:
"GOAT Desktop Vision v1.1 ist die neue kanonische Master-Spec. Aenderungen gegenueber v1.0: UFO2 raus (Run 0b: 2.27 s Latenz und Python-Pin-Konflikte in dieser Umgebung), Slim Stack rein (mss + pywinauto + optionale OCR/Vision-LLM), Coordinate Broker mit Local Verifier als Geometrie-Autoritaet (Run 0c: IoU 0.9714/0.98 auf Chrome HTML-Test), Authority-Split: Vision-LLM kann niemals allein accept. Provider-Versionen werden erst nach separater Verifikation als Default festgeschrieben. Phase 1 startet mit Run A."

## Current State

Repo initialized from GOAT Desktop Vision v1.1. No application code exists yet.

## Verified

- Documentation-only repository scaffold exists.
- Canonical spec v1.1 is stored at `docs/GOAT-DESKTOP-VISION.md`.
- AICOS references are listed at `docs/AICOS-REFERENCES.md`.

## Not Yet Verified

- OCR and Vision-LLM provider defaults are not selected yet.
- Overlay, tray, popup, LiveTalk, and action gating do not exist yet.
