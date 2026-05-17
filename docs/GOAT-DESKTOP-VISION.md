# GOAT Desktop Vision v1.1

Datum: 2026-05-17
Status: kanonische Master-Spec, Evidence-First-Update nach Run 0a/0b/0c
Ablage: `goat-desktop/docs/GOAT-DESKTOP-VISION.md`
Vorgaenger: v1.0 (durch v1.1 ersetzt), v0.1 (in Soulmatch, bleibt fuer Nutzer-Modi gueltig)

---

## 0. Kernsatz

**Builder ist Hirn. Desktop ist Augen, Stimme, Overlay und gestufte Haende. Maya ist die sichtbare Vermittlerin. Slim Stack ist der Motor. Coordinate Broker mit Local Verifier ist die Geometrie-Autoritaet. CNC-Anker sichern jede Aktion. Das Ziel gibst du. Das letzte Ja gibst du. Der Notausknopf gehoert dir.**

---

## 1. Was sich gegenueber v1.0 geaendert hat

Drei Aenderungen, alle Evidence-getrieben:

**Aenderung 1: UFO² raus, Slim Stack rein.** Run 0b (Spike-Report db387f8) hat gezeigt: UFO² als Library fuehrt in dieser Umgebung zu Python-Pin-Konflikten (`faiss-cpu`, `pandas`) und 2.27 s Screen-Sensor-Latenz. Wir verlieren UFO²s Speculative-Multi-Action, gewinnen aber einen kontrollierbaren Stack und einen plausiblen Pfad zu sub-second Latenz.

**Aenderung 2: Coordinate Broker mit Local Verifier als Geometrie-Autoritaet.** Run 0c (Spike-Report a79bb8a) hat gezeigt: ein zweistufiger Broker (Candidate Builder + Verifier) liefert pixelgenaue Koordinaten (IoU 0.97 auf Chrome HTML-Test). Wichtiger Befund: ohne Verifier waere `Search tabs` als Input-Feld falsch akzeptiert worden. Verifier ist nicht Optional, sondern Pflicht.

**Aenderung 3: Vision-LLM ist semantischer Helfer, nicht Koordinaten-Quelle.** Klare Autoritaetsgrenze: Vision-LLM darf Kandidaten und Semantik vorschlagen, aber **niemals allein `accept` erzeugen**. Maximal `uncertain`. Finale Pixel-Koordinaten kommen ausschliesslich aus lokalen Geometrie-Quellen (UIA, OCR).

---

## 2. Rollen

**Builder (Render-hosted Soulmatch-Backend):** Hirn und Orchestrator. Maya als Persoenlichkeit. Council, Worker-Swarm, Master-Piece, Task-Planner, Async-Jobs. Plant Schritte, beurteilt Zwischenstand, eskaliert bei Unklarheit.

**GOAT Desktop (lokale Windows-App):** Augen, Stimme, Overlay, gestufte Haende. Tray, Popup, Overlay, lokale Bridge, Coordinate Broker, Verifier, Stufen-Klassifikator, LiveTalk. Eigenstaendige `.exe`, kein Render-Service.

**Maya:** Sichtbare Vermittlerin im Popup. Spricht mit dir, plant strategisch. Lebt im Builder, ist im Desktop nur als Stimme und Text sichtbar.

**Slim Stack (lokal):** `mss` fuer Screenshot, `pywinauto` fuer UIA, optional leichte OCR (WinRT/Tesseract/RapidOCR), optional Vision-LLM via API.

**Vision-/LLM-Provider (direkt vom Desktop):** Ein konfigurierbarer schneller Vision-LLM fuer semantische Hilfe, plus optionaler Heavy-Fallback. Konkrete Provider- und Modellnamen werden erst nach separater Provider-Verifikation festgeschrieben. Latenzkritische Calls gehen direkt, ohne Umweg ueber Builder.

**Lokale KI gibt es nicht.** Desktop ist Mechanik, Intelligenz kommt remote. Ohne Internet ist Maya stumm.

---

## 3. Architektur in einem Bild

```
+---------------------------------------+
|  Soulmatch Builder (Render)           |
|  Maya, Council, Worker-Swarm,         |
|  Task-Planner, Approval-Logik         |
+---------------------------------------+
                  ^
                  | WebSocket, vom Desktop initiiert
                  | Auth-Token, signierte Cues
                  |
+---------------------------------------+
|  GOAT Desktop (lokal, .exe)           |
|                                       |
|  +-- Tray + Popup (PyQt6)             |
|  +-- Overlay + gelber Ball (PyQt6)    |
|  +-- LiveTalk (Mikrofon, STT, TTS)    |
|  +-- Lokale Bridge (FastAPI, 127.0.0.1)|
|  +-- Stufen-Klassifikator             |
|  +-- Coordinate Broker:               |
|       Candidate Builder               |
|       Local Verifier                  |
|       Fusion-Regeln                   |
|  +-- CNC Anchor Protocol Layer        |
|  +-- Slim Stack:                      |
|       mss, pywinauto, optional OCR    |
+---------------------------------------+
                  |
                  | direkter HTTPS (optional, semantisch)
                  v
+---------------------------------------+
|  Vision-/LLM-Provider                 |
|  konfigurierbarer Vision-LLM          |
|  (nur Semantik, niemals Koordinaten)  |
+---------------------------------------+
```

---

## 4. Was GOAT NICHT ist

- keine React-Komponente im Soulmatch-Builder
- kein Web-Popup auf `/builder`
- kein DOM-Selector-Marker auf bekannte Builder-Buttons
- kein Browser-Feature
- kein Render-Service
- keine Komponente, die Builder erlaubt, frei in den Desktop hineinzugreifen
- keine lokale KI mit eigenem Verstand
- **kein UFO²-Agent-Loop und keine UFO²-Library** (durch Run 0b widerlegt)
- **kein Vision-LLM als Koordinaten-Quelle** (Vision allein darf nie `accept`)

---

## 5. Mayas vier Bedienstufen

Klassifikation passiert **im Desktop**, nicht in Builder. Im Zweifel: Stufe nach oben, nie nach unten.

**Stufe 1 — Maya darf frei steuern (keine Absprache):**
Scrollen, Tab-Wechsel, Untermenue oeffnen, Akkordeon-Felder, "Mehr anzeigen", Pagination, Hover-Tooltips, Filter sichtbar machen ohne sie zu setzen.

**Stufe 2 — Maya schlaegt vor, du nickst (leichte Absprache):**
Text in Feld tippen, Dropdown waehlen, Checkbox, Radio-Button, Datum, Datei-Upload-Dialog oeffnen (nicht hochladen).

**Stufe 3 — Maya haelt an, du sagst aktiv Ja (harte Absprache):**
"Absenden", "Bezahlen", "Bestellen", "Buchen", "Speichern" wenn Datensaetze geschrieben werden, "Loeschen", "Stornieren", Termin buchen, Vertrag abschicken, E-Mail abschicken, Datei hochladen.

**Stufe 4 — Maya schaut weg, du tippst selbst (technische Sperre):**
Passwoerter, 2FA-Codes, TANs, OTPs, Kreditkartennummern, CVV, Bankgeheimwoerter, Wiederherstellungs-Codes, private Schluessel, API-Keys, Signatur-PINs.

---

## 6. Coordinate Broker mit Local Verifier (zentraler Mechanismus, neu in v1.1)

Bezug: AICOS-Card `sol-cross-063` (folgt nach diesem Push).

Jede geplante Aktion durchlaeuft einen zweistufigen Broker. Stage 1 sammelt Kandidaten aus mehreren Quellen. Stage 2 verifiziert lokal, deterministisch, ohne LLM-Beteiligung. Nur der Verifier darf final `accept`, `uncertain` oder `stop` zurueckgeben.

### 6.1 Candidate Builder

Quellen, gestaffelt nach Verlaesslichkeit:

**Quelle A — UIA via pywinauto (primaer):**
Liefert Element-Name, automation_id, control_type, bounds, visible, enabled. Pixel-genaue Bounding Boxes. Gemessen in Run 0c: 142 ms auf Chrome, 444 ms auf Notepad.

**Sonderregel fuer Chrome und andere Chromium-Browser:** muss mit `--force-renderer-accessibility`-Flag laufen, sonst exponiert UIA nur die Browser-Chrome (Adressleiste, Tabs), nicht den Seiteninhalt. Ohne diese Flagge wurde im Spike `Search tabs` faelschlich als primaeres Input-Feld akzeptiert. Dokumentiere das in der GOAT-User-UX als Setup-Schritt fuer Browser-Begleitung.

**Quelle B — OCR (Fallback, gestaffelt):**
- Erste Wahl: UIA-eigene Text-Inhalte (`name`, `automation_id`) — kostenlos
- Zweite Wahl: Windows-native OCR via WinRT (`winsdk` oder `winrt-python`) — leichtgewichtig
- Dritte Wahl: Tesseract via `pytesseract` ODER RapidOCR — wenn schnell installierbar
- **Niemals:** EasyOCR oder PaddleOCR im MVP (zieht PyTorch/Paddle rein, gleiche Dependency-Hoelle wie UFO²)

**Quelle C — Vision-LLM (semantisch, optional):**
Konfigurierbarer Vision-LLM ueber API. Liefert Element-Beschreibung und ungefaehre Position (links/rechts/oben/unten), **keine pixelgenauen Koordinaten**. Optional aktivierbar. Spike laeuft auch ohne. Konkrete Provider werden erst nach eigenem Provider-Spike als Default gesetzt.

Pro Quelle Kandidat-JSON: `{source, bbox, label, confidence, time_ms, raw_evidence}`.

### 6.2 Local Verifier (Authority)

Pruefe pro Kandidat ohne LLM-Beteiligung:

- bounds finite und nicht 0×0
- bbox.center innerhalb aktivem Window-Rect
- Bei UIA-Quelle: `visible=true` UND `enabled=true` UND `onscreen=true`
- Bei OCR-Quelle: Text-Inhalt matcht semantischen Kontext
- DPI-Faktor angewendet (`GetDpiForWindow` oder Aequivalent)
- Fokus-Check: Window ist im Vordergrund

### 6.3 Fusion-Regeln

**`accept`:**
- mindestens eine lokale Geometriequelle (UIA oder OCR) valide
- UND Semantik passt (Vision-LLM-Hint oder Heuristik aus UIA-name)
- UND bbox besteht alle Verifier-Checks

**`uncertain`:**
- nur Vision-LLM hat Kandidat geliefert
- ODER lokale Quellen schwach aber plausibel
- ODER ein Verifier-Check unsicher (z. B. Window-Fokus unklar)

**`stop`:**
- Quellen widersprechen stark (siehe Toleranz-Regel)
- ODER bbox-/Fokus-/DPI-/Window-Check failt
- ODER alle Quellen leer

**Vision-LLM allein darf niemals `accept` erzeugen.** Maximal `uncertain`.

### 6.4 Toleranz-Regel (statt naivem px-Radius)

- Element-Diameter < 50 px: Center-Abstand ≤ 5 px zum erwarteten Punkt = match
- Element-Diameter ≥ 50 px: IoU ≥ 0.7 zur erwarteten Bounding Box = match
- High-DPI / Multi-Monitor: Toleranz proportional zur effektiven Element-Groesse

### 6.5 Performance-Optimierungen (verbindlich)

Aus Run-0c-Spike abgeleitet:

- **Window-only Screenshot** statt full-desktop. Spart ca. 350 ms gegenueber 405 ms full-desktop-Capture mit PNG-Disk-Write.
- **In-memory Screenshot** ohne PNG-Disk-Write.
- **Gezielter UIA-Lookup** statt full UIA-Tree-Collection, wenn Ziel-Element semantisch eingegrenzt werden kann.
- **UIA-Cache** pro Window-Handle: wenn Fenster unveraendert, nicht neu lookupen.
- **Parallel-Query** mit `asyncio.gather()`: UIA + OCR + Vision-Hint parallel statt sequentiell.

Ziel-Latenz mit Optimierungen: Stufe 1 = 100–250 ms, Stufe 2 = 300–700 ms, Stufe 3 = 600–1500 ms. Diese Werte sind Zielbudget, nicht abschliessend gemessene Produktwerte.

---

## 7. CNC Anchor Protocol

Bezug: AICOS-Card `sol-cross-062`.

Jede Action auf Stufe 3 (verbindlich) plus optional Stufe 2 (Feldeingabe) laeuft durch ein Anker-basiertes Verifikations-Protokoll **on top of** dem Coordinate Broker:

1. **Origin setzen:** Window-Rect des aktiven Fensters via pywinauto UIA, pixelgenau.
2. **3–5 Anker definieren:** stabile UI-Elemente (Titelleiste, Logo, fester Menue-Eintrag, Tab-Reiter, Statusleiste). Position relativ zum Origin gespeichert.
3. **Zielkoordinate berechnen:** relativ zum Origin und zum Anker-Set, nicht als absolute Bildschirm-Pixel-Koordinate.
4. **Pre-Action-Verifikation:** alle Anker erneut suchen, Drift gegen erwartete Position pruefen. Toleranz pro App-Klasse kalibrieren. Bei Ueberschreitung: Stop und Rekalibrierung.
5. **Coordinate Broker liefert finale Bounding Box** (siehe Abschnitt 6).
6. **Action ausfuehren** ueber pywinauto, nicht Pixel-Schaetzung.
7. **Post-Action-Verifikation:** erwarteter Bildschirm- oder Zustandswechsel pruefen. Bei unerwartetem Zustand: Stop, Maya meldet.
8. **Audit-Log:** Origin, Anker-Set, Coordinate-Broker-Entscheidung, Pre-/Post-Verifikations-Ergebnisse je Aktion persistieren.

**Stufen-Wirkung:**
- Stufe 1: Coordinate Broker, kein voller CNC-Anker
- Stufe 2: Coordinate Broker + leichte Anker-Verifikation
- Stufe 3: Coordinate Broker + voller CNC-Anker + User-Bestaetigung mit Anker-Vorschau
- Stufe 4: keine Action, nur Feld-Erkennung via UIA `type=password`-Hint

---

## 8. Zielorientierung, Notausknopf, Sicherheit

Unveraendert gegenueber v1.0:
- Maya arbeitet auf ein User-Ziel hin, meldet Fortschritt, stoppt bei Unerwartetem.
- Globaler Hotkey (Strg+Alt+Esc) stoppt sofort, hoechste Prioritaet.
- Desktop ist die lokale Autoritaetsgrenze. Builder schlaegt vor, Desktop entscheidet, du gibst das letzte Ja.
- Outbound-Bruecke nur vom Desktop initiiert. Keine offenen Ports nach aussen.

---

## 9. Was streng verboten ist

1. Keine weitere Builder-GOAT-UI-Arbeit im Soulmatch-Repo, solange GOAT Desktop nicht Run C abgenommen.
2. Keine DOM-Selector-Marker auf bekannte Builder-Buttons.
3. Keine Behauptung "Desktop-Navigation fertig", solange das Overlay nicht ueber fremden Apps lebt.
4. Keine Stufe-3- oder Stufe-4-Action ohne explizites User-Ja.
5. Kein STATE/RADAR-Drift ueber mehr als einen Push-Zyklus.
6. Kein `unverified_local_claim` — lokal ungepushter Code zaehlt nicht.
7. Keine direkte Builder-zu-Desktop-Push-Verbindung. Nur Desktop-initiiert Outbound.
8. Keine Stufen-Herabstufung im Zweifelsfall. Unsicher = naechsthoehere Stufe.
9. Keine Action ohne Coordinate-Broker-`accept` plus CNC-Anker-Verifikation in Run G.
10. Kein Overlay ohne `WS_EX_TRANSPARENT` (click-through). Bezug: AICOS-Card `err-dev-002`.
11. **Kein Vision-LLM als alleinige Koordinaten-Quelle.** Vision-only kann nur `uncertain` erzeugen, niemals `accept`.
12. **Kein EasyOCR, kein PaddleOCR im MVP.** Dependency-Hoelle wie UFO².
13. Kein UFO²-Code in unserem Repo, weder als Library noch als Agent-Loop.

---

## 10. Stack-Entscheidung (Evidence-First, durch Run 0a/0b/0c bestaetigt)

- **Sprache:** Python 3.12 (gemessen funktionierend in Run 0c), 3.11 oder 3.10 falls verfuegbar
- **UI:** PyQt6 (Tray, Popup, Overlay)
- **Screenshot:** `mss`, Window-only, in-memory
- **UIA:** `pywinauto` (Backend `uia`)
- **OCR:** Windows-native WinRT zuerst, dann Tesseract/RapidOCR. Kein EasyOCR/PaddleOCR.
- **Vision-Provider (optional, semantisch):** konfigurierbarer schneller Vision-LLM, Default erst nach Provider-Verifikation
- **Lokale Bridge:** FastAPI auf 127.0.0.1
- **Builder-Bruecke:** `websockets` outbound zu Render
- **Mikrofon/STT/TTS:** zu entscheiden in Run F (Grok Voice, OpenAI Realtime, oder lokale Whisper+Piper)
- **Build:** PyInstaller fuer `.exe`-Paketierung
- **Spaeter (Phase 2):** Code-Signing-Zertifikat gegen Defender-Quarantaene

---

## 11. Run-Plan (aktualisiert nach Phase 0)

**Phase 0 — abgeschlossen:**
- Run 0a: ✅ done. `79ec22b` als phantom_claim verifiziert.
- Run 0b: ✅ done. UFO² als Library nicht praktikabel, 2.27 s Latenz.
- Run 0c: ✅ done. Coordinate Broker mit Verifier validiert, IoU 0.97 auf Chrome HTML.

**Phase 1 — MVP-Build:**
- Run 1: ✅ done. Repo `goat-desktop` lebt, v1.1-Spec hier.
- Run A: ✅ done. Tray-App + Mini-Popup. PyQt6. Tray-Icon, verschiebbares Popup, drei Statusfelder, LiveTalk-Platzhalter.
- Run B: ✅ done. Globales Overlay + statischer gelber Ball. Always-on-top, `WS_EX_TRANSPARENT`, click-through, vom Popup verschiebbar. Pflicht: Kill-Switch in derselben Iteration testen.
- Run C: ✅ done. Lokale Bridge + Slim Stack + Coordinate Broker + Verifier. FastAPI auf 127.0.0.1. Endpoints `/healthz`, `/screen-cue`, `/screen-capture`, `/active-window`. Cue-Schema enthaelt `safety_state`, `anchors[]`, `broker_decision`.
- Run D: ✅ done. Builder-Bruecke. WebSocket Outbound, Token-Auth, Reconnect.
- Run E: ✅ done. Vision-LLM-Konfiguration via Builder-Proxy. Provider-Spike fuer gemini_flash_lite, gemini_flash und grok_4_3 abgeschlossen. Nur als semantischer Helfer, niemals als Koordinaten-Quelle.
- **Run F:** LiveTalk. Mikrofon, STT, TTS. Half-Duplex. Mock-Schale ist code-ready. Windows-Audio-Probe fuer Aufnahme + SAPI-Ausgabe ist erledigt, aber echter STT-Pfad fehlt weiter; deshalb nicht `completed`.
- **Run G1–G5:** Action Layer in fuenf Sub-Phasen, Stufen 1 bis 4 plus Klassifikator-Pipeline. G1-Skeleton ist code-ready. G2 Stage-1-Executor ist completed fuer Scroll und Hover/Pointer-Move in einem harmlosen Testfenster. G3 Stage-2-Texteingabe ist completed fuer einzeilige Safe-Context-Eingabe nach Preview-Approval. G4 Stage-3-Hard-Approval ist completed als Review-Layer ohne OS-Ausfuehrung. G5 Klassifikator-Haertung ist completed mit Audit-Reasoning und Matrix-Tests. G1-G5 Integrationskette ist completed. Stage 4 bleibt technische Sperre.

**Phase 2 — optional, evidenzbasiert:**
- **Run 0d (OmniParser-Spike):** nur, wenn Run B oder C zeigt, dass UIA + OCR fuer Electron-Apps (VS Code, Slack, Discord) nicht reicht.

---

## 12. Acceptance-Tests pro Run

- **Run A:** Screenshot mit Tray-Icon und Popup ueber Desktop (nicht in Browser).
- **Run B:** Screencast mit gelbem Ball ueber zwei verschiedenen externen Apps, Koordinatenwechsel live, click-through verifiziert.
- **Run C:** Screencast: Popup-Klick → Bridge antwortet → Broker `accept` → Ball springt zur Cue-Koordinate. Plus Logging des Verifier-Pfads (welche Quelle akzeptiert, welche abgelehnt).
- **Run D:** Screencast: Desktop verbindet sich zu Builder, Builder schickt Test-Cue, Desktop zeigt Vorschau, User approved, Ball rendert.
- **Run E:** Screencast: Maya findet Action-Buttons auf drei verschiedenen externen Apps korrekt; Vision-LLM-Hint sichtbar im Log; finale Koordinate kommt aus UIA, nicht aus Vision.
- **Run F:** Audio-Aufnahme + Screencast: gesprochener Roundtrip "zeig mir das Suchfeld" → gesprochene Antwort → Ball.
- **Run G1–G5:** je eigene Screencast-Acceptance pro Stufe.

---

## 13. Repo-Disziplin

- `goat-desktop` hat eigene `STATE.md`, `RADAR.md`, `SESSION-LOG.md`, `CLAUDE-CONTEXT.md`.
- Jeder Push, der GOAT-Code aendert, aktualisiert STATE.md im selben oder direkt folgenden Commit.
- Diese Spec ist Pflicht-Anker fuer jeden Codex-Run, gelesen vor STATE/RADAR.
- AICOS-Referenzen (`docs/AICOS-REFERENCES.md`) muessen vor Run-Start gelesen werden.
- Lokale, ungepushte Staende sind kein Arbeitsstand.

---

## 14. AICOS-Referenzen (Pflichtlektuere vor Coding)

- **`err-dev-002` — Desktop-Overlay blockiert alle UI-Elemente.** Pflicht vor Run B.
- **`sol-cross-062` — CNC Anchor Protocol for Screen Actions.** Pflicht vor Run C und Run G.
- **`sol-cross-063` — Multi-Source Coordinate Broker for Screen Actions.** Pflicht vor Run C. (Neu in v1.1, folgt nach diesem Push.)
- **`sol-cross-042` — UI-Aware Self-Correcting Agent.** Pflicht vor Run G.
- **`sol-cross-038` — Agent Capability Assumptions.** Pflicht vor Run G.
- **`sol-cross-014` — Agent Self-Correction Protocol.** Pflicht vor Run G.
- **`sol-cross-034` — UI-Agent Transparency Stack.** Pflicht vor Run G.
- **`sol-cross-032` / `sol-cross-044` — Timeout-Protected Resource Wrapper.** Pflicht vor Run D.
- **`sol-cross-016` — Agent Registry Protocol.** Pflicht vor Run 1.
- **`sol-ux-002` — Demo-First.** Empfohlen vor Run A.

---

## 15. Was wir NICHT selbst bauen, was wir selbst bauen

**Nicht selbst:**
- Screenshot-Mechanik (mss liefert).
- UIA/Win32-Integration (pywinauto liefert).
- OCR-Engines (Tesseract/RapidOCR/WinRT liefern).
- Vision-Modelle (Provider liefern, oder OmniParser falls Run 0d positiv ausfaellt).

**Selbst gebaut:**
- Tray, Popup, Overlay, gelber Ball (PyQt6).
- Coordinate Broker mit Candidate Builder.
- **Local Verifier** (zentrale eigene Logik, ohne LLM).
- Fusion-Regeln (accept/uncertain/stop).
- CNC Anchor Protocol-Layer.
- Stufen-Klassifikator (Heuristik + spaeter optional CatBoost-Modell mit gesammelten Daten).
- Builder-Bruecke (WebSocket-Client mit Reconnect).
- Maya-Persoenlichkeits-Schicht im Popup.
- LiveTalk-Integration.
- Audit-Log fuer alle Aktionen.

---

## 16. Abbruchkriterien

- Run A liefert keine native Tray-App, sondern wieder Web-Demo.
- Run B: gelber Ball nur im Browser sichtbar, nicht ueber externen Apps.
- Run C: Broker liefert in mehr als 20 % der Test-Apps `stop`, ohne dass dies legitim ist.
- Run D: Desktop rendert Vorschlaege ohne User-Approval.
- Run G: Anker-Drift wird ignoriert statt zu stoppen.
- Wenn jemand vorschlaegt, Vision-LLM solle final klicken-duerfen ohne Verifier-Akzeptanz, wird abgelehnt.

---

## 17. Kernsatz nochmal

**Slim Stack ist der Motor. Coordinate Broker mit Local Verifier ist die Geometrie-Autoritaet. CNC-Anker sichern die Aktion. Maya gibt die Stimme, Builder gibt den Plan, du gibst das Ziel und das letzte Ja.**
