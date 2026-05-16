# GOAT Desktop Vision v1.0

Datum: 2026-05-16
Status: kanonische Master-Spec
Ablage: `goat-desktop/docs/GOAT-DESKTOP-VISION.md`
Vorgaenger: v0.1 (in Soulmatch), v0.2, v0.3, v0.4 (alle abgeloest)

---

## 0. Kernsatz

**Builder ist Hirn. Desktop ist Augen, Stimme, Overlay und gestufte Haende. Maya ist die sichtbare Vermittlerin. UFO² ist der Motor. CNC-Anker sichern jede Aktion. Das Ziel gibst du. Das letzte Ja gibst du. Der Notausknopf gehoert dir.**

---

## 1. Produktziel

GOAT ist ein lokaler Windows-Desktop-Agent mit Taskleisten-Icon, nativem Mini-Popup, globalem Bildschirm-Overlay und LiveTalk. Maya fuehrt dich zielorientiert durch beliebige Apps und Webseiten. Eingriffsrechte sind in vier Stufen geregelt, von freier Navigation bis hart gegateten Aktionen. Microsoft UFO² liefert die Windows-Mechanik. Das CNC Anchor Protocol stellt sicher, dass jede Aktion auf einem verifizierten, deterministischen Bezugssystem aufsetzt.

---

## 2. Rollen

**Builder (Render-hosted Soulmatch-Backend):** Hirn und Orchestrator. Maya als Persoenlichkeit. Council, Worker-Swarm, Master-Piece, Task-Planner, Async-Jobs. Plant Schritte, beurteilt Zwischenstand, eskaliert bei Unklarheit.

**GOAT Desktop (lokale Windows-App):** Augen, Stimme, Overlay, gestufte Haende. Tray, Popup, Overlay, lokale Bridge, Screen-Sensor, LiveTalk, Anchor-Protokoll, Stufen-Klassifikator. Eigenstaendige `.exe`, kein Render-Service.

**Maya:** Sichtbare Vermittlerin im Popup. Spricht mit dir, plant strategisch. Lebt im Builder, ist im Desktop nur als Stimme und Text sichtbar.

**UFO² (Microsoft, MIT-Lizenz):** Motor fuer Windows-Mechanik. UI Automation, Win32, WinCOM. Hybrid GUI+API. Visual + UIA Detection. Speculative Multi-Action.

**OmniParser (Microsoft, AGPL/MIT):** Vision-Schicht fuer Apps, in denen UIA versagt. Bekommt Screenshots, liefert strukturierte Element-Listen mit Bounding-Boxes.

**Vision-/LLM-Provider (direkt vom Desktop):** Grok 4.3 oder Claude Sonnet 4.6 fuer Screen-Vision. Grok Voice oder vergleichbar fuer LiveTalk. Latenzkritische Calls gehen direkt, ohne Umweg ueber Builder.

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
|  +-- Stufen-Klassifikator (G1–G5)     |
|  +-- CNC Anchor Protocol Layer        |
|  +-- UFO² als Library:                |
|       UIA + Win32 + WinCOM + Hybrid   |
|       + OmniParser-Anbindung          |
+---------------------------------------+
                  |
                  | direkter HTTPS
                  v
+---------------------------------------+
|  Vision-/LLM-Provider                 |
|  Grok 4.3 / Claude Sonnet 4.6 (Vision)|
|  Grok Voice (LiveTalk)                |
+---------------------------------------+
```

**Wichtig:** UFO² wird als **Library** eingebunden (nicht als Agent-Loop). Maya bleibt die einzige Persoenlichkeits-Schicht. UFO² liefert die Mechanik, der Stufen-Klassifikator klassifiziert jede UFO²-Action vor Ausfuehrung, das Anker-Protokoll verifiziert vor und nach jeder Action. Es gibt **keine** doppelte LLM-Schicht.

---

## 4. Was GOAT NICHT ist

- keine React-Komponente im Soulmatch-Builder
- kein Web-Popup auf `/builder`
- kein DOM-Selector-Marker auf bekannte Builder-Buttons
- kein Browser-Feature
- kein Render-Service
- keine Komponente, die Builder erlaubt, frei in den Desktop hineinzugreifen
- keine lokale KI mit eigenem Verstand
- kein UFO²-Agent-Loop (UFO² wird nur als Library benutzt, nicht als selbstaendige Agent-Schicht)

---

## 5. Mayas vier Bedienstufen

Klassifikation passiert **im Desktop**, nicht in Builder. Im Zweifel: Stufe nach oben, nie nach unten.

**Stufe 1 — Maya darf frei steuern (keine Absprache):**
Scrollen, Tab-Wechsel, Untermenue oeffnen, Akkordeon-Felder, "Mehr anzeigen", Pagination, Hover-Tooltips, Filter sichtbar machen ohne sie zu setzen.
Stil: Maya kommentiert nebenbei, wartet nicht.

**Stufe 2 — Maya schlaegt vor, du nickst (leichte Absprache):**
Text in Feld tippen, Dropdown waehlen, Checkbox, Radio-Button, Datum, Datei-Upload-Dialog oeffnen (nicht hochladen).
Stil: Maya zeigt Vorschau im Popup, du nickst per Klick, Sprache oder Enter. Mehrere logisch zusammenhaengende Felder koennen gebuendelt werden.

**Stufe 3 — Maya haelt an, du sagst aktiv Ja (harte Absprache):**
"Absenden", "Bezahlen", "Bestellen", "Buchen", "Speichern" wenn Datensaetze geschrieben werden, "Loeschen", "Stornieren", Termin buchen, Vertrag abschicken, E-Mail abschicken, Datei hochladen.
Stil: Maya stoppt, zeigt Vorschau mit Anker-Verifikation, eine Aktion eine Bestaetigung, niemals automatisch.

**Stufe 4 — Maya schaut weg, du tippst selbst (technische Sperre):**
Passwoerter, 2FA-Codes, TANs, OTPs, Kreditkartennummern, CVV, Bankgeheimwoerter, Wiederherstellungs-Codes, private Schluessel, API-Keys, Signatur-PINs.
Stil: Maya markiert nur das Feld mit dem gelben Ball. Die Tastatur ist fuer Maya in diesem Feld **technisch** gesperrt — der Desktop blockiert eigenstaendig jeden Tipp-Versuch von Maya in als Stufe-4 erkannte Felder.

**Klassifikator-Quellen (in dieser Prioritaet):**
1. Heuristische Regeln (Button-Text-Liste, `type=password`, ARIA-Hinweise) — sofort, billig.
2. Vision-KI-Einschaetzung wenn Heuristik unklar.
3. User-Override pro App oder Webseite — verbindlich, liegt lokal.

---

## 6. CNC Anchor Protocol — die Sicherheits-Disziplin unter dem KI-Layer

Bezug: AICOS-Card `sol-cross-062` (CNC Anchor Protocol for Screen Actions).

Jede Action — egal welcher Stufe — laeuft durch ein Anker-basiertes Verifikations-Protokoll. Inspiriert von CNC-Laser-Cuttern: Nullpunkt, Bezugspunkte, relative Zielkoordinaten, Pre- und Post-Verifikation.

**Anker-Setzung vor jeder Action:**
- Origin = linke obere Ecke des aktiven Fensters, pixelgenau aus Windows UIA.
- 3–5 stabile Anker-Elemente: Titelleiste, Logo, fester Menue-Eintrag, Tab-Reiter, Statusleiste. Position relativ zum Origin gespeichert.

**Zielkoordinate immer relativ zum Anker-Set**, nicht absolute Bildschirm-Pixel. Beispiel: Bezahlen-Button bei Origin + (320, 580), zwischen Tab-Anker A und Logo-Anker B.

**Pre-Action-Verifikation in zwei Phasen:**
- Phase 1 (Anker-Check): alle Anker erneut suchen, Drift gegen erwartete Position pruefen. Toleranz ≤ 5 px fuer Desktop-Apps, ≤ 20 px fuer responsive Web-Apps. Ueberschreitung → Stop und Rekalibrierung.
- Phase 2 (Ziel-Check): UIA- oder Vision-Lookup an der berechneten Zielkoordinate, pruefen ob das erwartete Element wirklich da ist. Mismatch → Stop und User-Eskalation.

**Action ausfuehren** ueber deterministische OS-API (UFO²-Hybrid), nicht Pixel-Schaetzung.

**Post-Action-Verifikation:** erwarteter Bildschirm-Change eingetreten? Bei unerwartetem Zustand → Stop, Maya meldet.

**Audit-Log:** Origin, Anker-Set, erwartete und gemessene Zielkoordinate, Pre-/Post-Verifikations-Ergebnisse persistieren je Action.

**Wirkung pro Stufe:**
- Stufe 1: Anker-Setzung passiert, Pre-Verifikation light, keine Post-Verifikation noetig.
- Stufe 2: volle Pre-Verifikation, Post-Verifikation prueft Feld-Wert.
- Stufe 3: volle CNC-Disziplin plus User-Bestaetigung mit Anker-Vorschau ("ich klicke hier, das ist Button X, gepruefte Position").
- Stufe 4: keine Action ueberhaupt, aber Anker dienen zur Feld-Erkennung.

---

## 7. Zielorientierung

Maya arbeitet nicht ohne Ziel. Bevor sie aktiv wird, formulierst du ein Ziel ueber Popup-Text oder LiveTalk.

Maya bekommt das Ziel als Strukturdaten, schickt es an Builder, Builder zerlegt es in Schritte und schickt sie zurueck. Maya arbeitet das ab mit den Stufen-Regeln aus Abschnitt 5 und dem Anker-Protokoll aus Abschnitt 6.

Mayas Verpflichtungen waehrend einer Zielarbeit:
- Ziel im Popup sichtbar halten.
- Fortschritt in Klartext melden ("Schritt 3 von 7").
- Bei Unerwartetem stoppen und fragen.
- Bei Unloesbarkeit ehrlich zurueckgeben.
- Bei Erfolg "Ziel erreicht" sagen und aktiv stoppen.

---

## 8. Notaus / Kill-Switch

Globaler Hotkey (Strg+Alt+Esc oder konfigurierbar) stoppt Maya sofort:
- alle laufenden Klicks/Tipps werden abgebrochen
- Overlay-Ball verschwindet
- Maus wird wieder freigegeben
- Mikrofon aus
- Popup-Status: "Maya gestoppt"
- Builder bekommt Event `user_killswitch`

Hoechste Prioritaet, ueberschreibt alles, auch mitten in einer Stufe-3-Action.

---

## 9. Sicherheitsgrenzen

**Bis einschliesslich Run F (vor Action-Layer):**
- kein Maus-Klick durch GOAT
- keine Tastatur-Eingabe durch GOAT
- keine Hotkey-Registrierung
- keine Desktop-Schreib-Aktion
- kein Trading-Call
- kein Internet-Egress ausser Vision-/LiveTalk-Provider-Calls und Builder-Bruecke
- Mikrofon nur aktiv wenn LiveTalk-Button gedrueckt
- Screenshot nur on-demand

**Ab Run G (Action-Layer) zusaetzlich:**
- jede Action durch CNC Anchor Protocol (Abschnitt 6)
- jede Action mit Stufen-Klassifikation (Abschnitt 5)
- Stufe-4-Felder technisch gesperrt
- Notausknopf jederzeit verfuegbar

**Desktop ist die lokale Autoritaetsgrenze.** Builder schlaegt vor, Desktop entscheidet, du gibst das letzte Ja bei Stufen 3 und 4.

---

## 10. Was streng verboten ist

1. Keine weitere Builder-GOAT-UI-Arbeit im Soulmatch-Repo, solange GOAT Desktop nicht Run C abgenommen.
2. Keine DOM-Selector-Marker auf bekannte Builder-Buttons.
3. Keine Behauptung "Desktop-Navigation fertig", solange das Overlay nicht ueber fremden Apps lebt.
4. Keine Stufe-3- oder Stufe-4-Action ohne explizites User-Ja.
5. Kein STATE/RADAR-Drift ueber mehr als einen Push-Zyklus.
6. Kein `unverified_local_claim` — lokal ungepushter Code zaehlt nicht.
7. Keine direkte Builder-zu-Desktop-Push-Verbindung. Nur Desktop-initiiert Outbound.
8. Keine Stufen-Herabstufung im Zweifelsfall. Unsicher = naechsthoehere Stufe.
9. Keine Action ohne CNC-Anker-Verifikation in Run G.
10. Kein Overlay ohne `pointer-events`-Aequivalent (Windows: `WS_EX_TRANSPARENT`). Bezug: AICOS-Card `err-dev-002` (Lessons-Learned aus GhostOS).
11. Kein UFO²-Agent-Loop in unserem Code — UFO² ausschliesslich als Library.

---

## 11. Stack-Entscheidung

Steht fest durch Library-Wahl:

- **Sprache:** Python 3.11
- **UI:** PyQt6 (Tray, Popup, Overlay)
- **Windows-Mechanik:** UFO² (Microsoft, MIT) als Library
- **Vision-Backup:** OmniParser (Microsoft) ueber UFO² eingebunden
- **Lokale Bridge:** FastAPI auf 127.0.0.1
- **Builder-Bruecke:** `websockets` (Python-Lib) outbound zu Render
- **Mikrofon/STT/TTS:** zu entscheiden in Run F (Optionen: Grok Voice, OpenAI Realtime, lokale Whisper+Piper)
- **Vision-Provider:** Grok 4.3 (primary), Claude Sonnet 4.6 (fallback)
- **Build:** PyInstaller fuer `.exe`-Paketierung
- **Spaeter (Phase 2 nach MVP):** Code-Signing-Zertifikat gegen Defender-Quarantaene

---

## 12. Run-Plan: Run 0a bis Run G5

Jeder Run hat eine harte Acceptance per Screenshot oder Screencast.

**Run 0a — Wahrheitsklaerung `79ec22b`.** Codex prueft, ob der frueher behauptete GOAT Control Adapter lokal existiert. Kein Code. Bericht reicht.

**Run 0b — UFO²-Spike.** Codex installiert UFO² in einer Sandbox, startet ein Hello-World das den aktiven Bildschirm liest und einen Screenshot speichert. Beantwortet: laeuft UFO² in deiner Umgebung? Performance? Library-vs-CLI-Frage (kann UFO² als reine Python-Lib genutzt werden?). Kein Produkt-Code.

**Run 1 — Neues Repo `goat-desktop`.** Codex (oder du) legt das Repo an, mit Anker-Dateien (`STATE.md`, `RADAR.md`, `SESSION-LOG.md`, `CLAUDE-CONTEXT.md`), `README.md`, `docs/GOAT-DESKTOP-VISION.md` (diese Datei), `docs/AICOS-REFERENCES.md` (Liste der relevanten AICOS-Cards). Stack-Entscheidung im README dokumentiert. Kein Anwendungscode.

**Run A — Tray-App + Mini-Popup.** PyQt6. System-Tray-Icon, Linksklick oeffnet verschiebbares Popup, drei Statusfelder, LiveTalk-Platzhalter. Keine Bridge, kein Overlay, kein UFO², keine Vision, kein Mikrofon. Acceptance: Programm startet ausserhalb Browser, Tray-Icon sichtbar, Popup ueber dem Desktop verschiebbar.

**Run B — Globales Overlay + statischer gelber Ball.** Transparentes Always-on-top Vollbild-Fenster, Ball an Hardcoded-Koordinate, vom Popup verschiebbar, click-through (`WS_EX_TRANSPARENT`). **Pflicht-Guardrail aus `err-dev-002`:** Kill-Switch (Escape) muss in derselben Iteration getestet werden, in der der Ball implementiert wird. Acceptance: Ball ueber zwei verschiedenen externen Apps sichtbar, click-through funktioniert, Escape stoppt sofort.

**Run C — Lokale Bridge + UFO²-Integration.** FastAPI auf 127.0.0.1. UFO² als Library eingebunden. Endpoints `/healthz`, `/screen-cue`, `/screen-capture`, `/active-window`. Cue-Schema mit `safety_state`, `anchors[]`-Feld. Popup-Klick "Test-Cue holen" laesst UFO² den aktiven Bildschirm lesen, liefert echten Window-Rect, setzt Ball an reale Position eines erkannten UI-Elements. Erstmaliger Anker-Setzung im Code, aber noch keine Pre-/Post-Verifikation. Acceptance: Ball springt an erkannte reale Position eines Buttons in einer externen App.

**Run D — Builder-Bruecke.** WebSocket vom Desktop zu Soulmatch-Backend (neuer Endpoint `wss://soulmatch-1.onrender.com/api/goat/connect`). Token-Auth, Heartbeat, Reconnect. Builder sendet Test-Plan-Vorschlag, Desktop zeigt im Popup als Vorschau, User approved per Klick, Ball rendert. Promise.race + Timeout-Wrapper aus `sol-cross-044`. Acceptance: vollstaendiger Roundtrip Builder → Desktop → User → Ball.

**Run E — Vision-Provider-Konfiguration.** UFO² mit Grok-4.3-Vision (primary) und Claude-Sonnet-4.6 (fallback) konfigurieren. OmniParser-Anbindung aktivieren. User formuliert Ziel ("zeig mir das Suchfeld"), UFO²-Vision findet das Suchfeld in einer externen App, Ball rendert dort. Acceptance: drei externe Apps, korrekte Suchfeld-Lokalisierung in mindestens zwei davon.

**Run F — LiveTalk.** Mikrofon ueber LiveTalk-Button. STT, LLM-Dialog (Maya ueber Builder-Bruecke), TTS. Half-Duplex (Tap-to-talk) im MVP. Acceptance: gesprochener Roundtrip, "zeig mir das Suchfeld" → gesprochene Antwort → Ball.

**Run G — Action Layer in fuenf Sub-Phasen:**
- **G1:** Stufe 1 (freie Navigation). Maya darf scrollen, Tabs wechseln, Menues oeffnen ohne Approval. Anker-Setzung passiert, Pre-Verifikation light. Notausknopf wirkt.
- **G2:** Stufe 2 (Feld-Eingabe mit Nick). Vorschau-Popup vor Tippen. Volle Pre-Verifikation, Post-Verifikation prueft Feld-Wert.
- **G3:** Stufe 3 (harte Bestaetigung). Maya darf wirksame Buttons klicken nach aktivem Ja. Volle CNC-Disziplin mit Anker-Vorschau in der User-Bestaetigung.
- **G4:** Stufe 4 (Tastatursperre). Technische Sperre fuer als sensibel erkannte Felder.
- **G5:** Klassifikator-Pipeline zusammenfuehren (Heuristik + Vision + Override mit Default-nach-oben bei Unsicherheit).

Jede Sub-Phase eigene Acceptance per Screencast.

---

## 13. Repo-Disziplin

- `goat-desktop` bekommt eigene `STATE.md`, `RADAR.md`, `SESSION-LOG.md`, `CLAUDE-CONTEXT.md`. Gleiche Konvention wie Soulmatch.
- Jeder Push, der GOAT-Code aendert, aktualisiert STATE.md im selben oder direkt folgenden Commit.
- Diese Spec ist Pflicht-Anker fuer jeden Codex-Run, gelesen vor STATE/RADAR.
- AICOS-Referenzen (`docs/AICOS-REFERENCES.md`) muessen vor Run-Start gelesen werden.
- Lokale, ungepushte Staende sind kein Arbeitsstand.
- Soulmatch-Repo bekommt nur eine Quer-Referenz auf `goat-desktop`, kein Spec-Spiegel.

---

## 14. AICOS-Referenzen (Pflichtlektuere vor Coding)

Diese Cards aus `aicos-registry/cards/` muessen vor jedem Codex-Run gelesen werden, der den jeweiligen Run beruehrt:

- **`err-dev-002` — Desktop-Overlay blockiert alle UI-Elemente.** Lessons-Learned aus GhostOS. Pflicht vor Run B. Guardrails: pointer-events-Aequivalent, Kill-Switch sofort, Desktop von Anfang an statt Browser-Umweg.
- **`sol-cross-062` — CNC Anchor Protocol for Screen Actions.** Pflicht vor Run C und Run G. Definition des Anker-Protokolls.
- **`sol-cross-042` — UI-Aware Self-Correcting Agent.** Pflicht vor Run G. Maya korrigiert sich bei UI-Struggle.
- **`sol-cross-038` — Agent Capability Assumptions.** Pflicht vor Run G. Annahmen-Registry im Manifest.
- **`sol-cross-014` — Agent Self-Correction Protocol.** Pflicht vor Run G. Split-Role, Regime Exit.
- **`sol-cross-034` — UI-Agent Transparency Stack.** Pflicht vor Run G. Audit-Trail.
- **`sol-cross-032` / `sol-cross-044` — Timeout-Protected Resource Wrapper.** Pflicht vor Run D. Bridge-Reconnect mit Promise.race.
- **`sol-cross-016` — Agent Registry Protocol.** Pflicht vor Run 1. Manifest-Format.
- **`sol-ux-002` — Demo-First.** Empfohlen vor Run A. HTML-Mockup oder Skizze vor Code.

---

## 15. Was wir NICHT selbst bauen

- **Windows UIA / Win32 / WinCOM-Integration:** UFO² liefert.
- **Hybrid GUI+API-Action-Strategie:** UFO² liefert.
- **Speculative Multi-Action (51% weniger LLM-Calls):** UFO² liefert.
- **UI-Element-Detection mit Vision:** OmniParser ueber UFO² liefert.
- **Vision-Provider-Wrapper:** UFO² unterstuetzt schon OpenAI, Claude, Qwen, Gemini, DeepSeek.
- **MCP-Integration:** UFO² hat sie eingebaut.
- **Knowledge Substrate / RAG:** UFO² liefert, falls spaeter gewuenscht.

**Wir bauen selbst:** Tray, Popup, Overlay, gelber Ball, Stufen-Klassifikator, Anker-Protokoll-Schicht, Builder-Bruecke, LiveTalk, Maya-Persoenlichkeits-Schicht.

---

## 16. Abbruchkriterien

Diese Spec ist abgebrochen oder muss ueberarbeitet werden, wenn:

- Run 0b zeigt: UFO² laeuft in deiner Umgebung nicht oder ist zu langsam (> 3 s pro Screen-Sensor-Aufruf). Fallback: zurueck zu Eigenbau auf `pywinauto`.
- Run A liefert keine native Tray-App, sondern wieder Web-Demo.
- Run B zeigt: gelber Ball nur im Browser sichtbar, nicht ueber externen Apps.
- Run C: Anker-Setzung schlaegt in mehr als 20% der Test-Apps fehl. Klassifikator-Heuristik braucht Erweiterung.
- Run D: Desktop rendert Vorschlaege ohne User-Approval. Sicherheits-Bruch.
- Run G: Anker-Drift > 5 px wird ignoriert statt zu stoppen. CNC-Disziplin verletzt.
- Wenn jemand vorschlaegt, Builder solle den Desktop fernsteuern ohne Desktop-Approval, wird abgelehnt.
- Wenn UFO²-Agent-Loop versehentlich in unseren Code wandert (statt nur als Library), wird zurueckgeschnitten.

---

## 17. Verhaeltnis zu Vorgaengern

- **v0.1** (`docs/GOAT-USER-NAVIGATOR-VISION-v0.1.md` in Soulmatch): bleibt fuer Modi `Erklaeren`, `Zeigen`, `Fuehren`, `Selber machen` als allgemeines Konzept gueltig. v1.0 schaerft `Selber machen` zu den vier Stufen aus Abschnitt 5.
- **v0.2, v0.3, v0.4:** vollstaendig ersetzt durch v1.0. v1.0 konsolidiert Diagnose-Erkenntnisse, AICOS-Recherche, externe Recherche, UFO²-Foundation und das CNC Anchor Protocol in eine kohaerente Master-Spec.

---

## 18. Was sich gegenueber v0.4 konkret geaendert hat

1. **Microsoft UFO² als Library** ersetzt grossen Teil des Eigenbaus bei Run C, E, G. Geschaetzte Code-Reduktion: 60–80% in diesen Runs.
2. **Stack-Entscheidung steht fest** (Python + PyQt6 + UFO² + FastAPI + websockets). Keine Open-Choice-Diskussion mehr.
3. **CNC Anchor Protocol** als eigener Abschnitt 6, nicht als Nebenbemerkung. Pflicht-Standard fuer Stufe 3, optional Stufe 2, Light fuer Stufe 1.
4. **Run 0b (UFO²-Spike)** als neuer Vorab-Schritt vor Run 1. Beantwortet die Library-vs-CLI-Frage frueh.
5. **Klare AICOS-Referenz-Liste** in Abschnitt 14 mit Pflichtlektuere pro Run.
6. **Verbot Nr. 11** explizit gegen UFO²-Agent-Loop in unserem Code.
7. **Guardrail aus `err-dev-002`** als verbindlich fuer Run B.
8. **Abbruchkriterium fuer UFO²-Probleme** in Run 0b — wenn UFO² nicht laeuft, faellt der Stack zurueck auf Eigenbau, ohne Drama.

---

## 19. Naechste konkrete Schritte

In dieser Reihenfolge:

1. **Drift-Marker-Commit in Soulmatch** (aus dem Run-0-Package). Ehrliche Markierung der GOAT-Web-Demo-Drift, Verweis auf neue kanonische Spec.
2. **Run 0a starten** (Codex-Auftrag zur Wahrheitsklaerung `79ec22b`).
3. **AICOS-Card `sol-cross-062` einchecken** in `aicos-registry/cards/solutions/`.
4. **Run 0b starten** (UFO²-Spike) sobald Run 0a beantwortet ist.
5. **Run 1** (Repo `goat-desktop` anlegen mit dieser Spec) sobald 0a + 0b geklaert sind.
6. **Run A** beginnen.

Bis Schritt 5 wird kein Anwendungscode geschrieben. Nur Doku, Wahrheit, Spike.
