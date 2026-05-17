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

run_a_started_2026_05_17:
"Run A gestartet am 2026-05-17. Scope: native PyQt6-Tray-App mit verschiebbarem Mini-Popup, ohne Overlay, Bridge, Vision, UIA oder Aktionen."

run_a_code_ready_2026_05_17:
"Run A Code-Stand angelegt am 2026-05-17. Erstes natives PyQt6-Projekt mit src/goat_desktop, Tray-Icon, Rechtsklick-Menue mit Beenden, Linksklick/DoubleClick oeffnet Popup, verschiebbares Status-Popup mit offline-Verbindung, leerem Screen-Kontext, Pause/Stop-Button und LiveTalk-Platzhalter. Compile-Check bestanden. Acceptance-Screenshot wurde nicht committed, weil im Desktop-Hintergrund ein sensibles .env-Notepad sichtbar war. Run A ist erst nach sauberem Screenshot vollstaendig completed."

run_a_completed_2026_05_17:
"Run A abgeschlossen am 2026-05-17. Sauberer Acceptance-Screenshot committed unter docs/screenshots/run-a-acceptance-2026-05-17.png. Screenshot zeigt native GOAT-Popup-Schale mit Statusfeldern, Pause/Stop, LiveTalk-Platzhalter und Windows-Taskleiste mit aktiver App. Keine sensitiven Fensterinhalte im Acceptance-Artefakt."

run_b_started_2026_05_17:
"Run B gestartet am 2026-05-17. Pflichtreferenz err-dev-002 gelesen. Scope: PyQt6 Overlay/gelber Ball, click-through, Popup-Steuerung, globaler Kill-Switch. Kein Bridge, UIA, OCR, Vision oder Action-Layer."

run_b_code_ready_2026_05_17:
"Run B Code-Stand angelegt am 2026-05-17. Fullscreen-Overlay-Ansatz wurde verworfen, weil er schwarz renderte und damit err-dev-002-Risiko zeigte. Implementiert ist stattdessen ein kleines click-through Topmost-Cue-Window mit gelbem Ball, Popup-Buttons zum Bewegen/Verbergen und globalem Ctrl+Alt+Esc-Hotkey. Runtime-Checks: overlay_click_through=True, hotkey_registered=True. Visual Check: docs/screenshots/run-b-code-ready-visual-check-2026-05-17.png. Run B ist noch nicht completed, weil Screencast und manueller Click-through-Test ueber zwei externe Apps fehlen."

run_b_completed_2026_05_17:
"Run B abgeschlossen am 2026-05-17. Acceptance-Evidenz committed unter docs/run-b-acceptance-report-2026-05-17.md sowie docs/screenshots/run-b-acceptance-context-1.png und docs/screenshots/run-b-acceptance-context-2.png. Verifiziert: gelber Ball sichtbar ueber externer Chrome/Render-UI in zwei Positionen, WS_EX_TRANSPARENT=True, WS_EX_LAYERED=True, Hit-Tests resolve nicht auf das Overlay, Ctrl+Alt+Esc versteckt Overlay und Popup. Der sicherere kleine Cue-Window-Ansatz bleibt bewusst gesetzt; kein Fullscreen-Overlay."

## Current State

Repo initialized from GOAT Desktop Vision v1.1. Run A native tray shell is completed. Run B overlay/cue-ball safety layer is completed.

## Verified

- Documentation-only repository scaffold exists.
- Canonical spec v1.1 is stored at `docs/GOAT-DESKTOP-VISION.md`.
- AICOS references are listed at `docs/AICOS-REFERENCES.md`.
- Run A native PyQt6 tray app and mini-popup code compile successfully.
- Run A acceptance screenshot is committed at `docs/screenshots/run-a-acceptance-2026-05-17.png`.
- Run B overlay code compiles and runtime checks confirm click-through style plus global hotkey registration.
- Run B acceptance evidence is committed at `docs/run-b-acceptance-report-2026-05-17.md` with two visual screenshots.

## Not Yet Verified

- OCR and Vision-LLM provider defaults are not selected yet.
- Bridge, LiveTalk implementation, and action gating do not exist yet.
