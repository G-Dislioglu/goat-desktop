from __future__ import annotations

from goat_desktop.tray import GoatTrayApp, _speech_chip_text, _status_chip_text


class FakeLabel:
    def __init__(self, text: str = "") -> None:
        self._text = text
        self.visible = True

    def setText(self, text: str) -> None:
        self._text = text

    def text(self) -> str:
        return self._text

    def setVisible(self, visible: bool) -> None:
        self.visible = visible

    def isHidden(self) -> bool:
        return not self.visible


class FakeButton(FakeLabel):
    def __init__(self, text: str = "") -> None:
        super().__init__(text)
        self.enabled = False

    def setEnabled(self, enabled: bool) -> None:
        self.enabled = enabled


class FakePopup:
    def __init__(self) -> None:
        self.connection_value = FakeLabel()
        self.connection_chip = FakeLabel()
        self.audio_value = FakeLabel()
        self.audio_chip = FakeLabel()
        self.target_value = FakeLabel()
        self.review_status_value = FakeLabel()
        self.review_status_value.setVisible(False)
        self.screen_context_value = FakeLabel()
        self.maya_value = FakeLabel()
        self.cue_approve = FakeButton("Pruefen")
        self.cue_reject = FakeButton("Abbrechen")


class FakeTray:
    def __init__(self) -> None:
        self.popup = FakePopup()
        self.pending_builder_cue = None
        self.pending_stage1_action = None
        self.pending_stage2_action = None
        self.pending_stage3_action = None
        self.shown = False

    def show_popup(self) -> None:
        self.shown = True


def test_builder_stage1_cue_shows_target_check_before_navigation() -> None:
    fake = FakeTray()

    GoatTrayApp.receive_builder_cue(
        fake,
        {
            "action_type": "hover",
            "label": "Senden Button",
            "bbox": [10, 20, 110, 80],
        },
    )

    assert fake.pending_stage1_action == {"action_type": "hover", "label": "Senden Button", "scroll_amount": -360}
    assert fake.popup.target_value.text() == "Zielvorschlag: Senden Button"
    assert fake.popup.screen_context_value.text() == "Schritt 1: Ziel pruefen"
    assert fake.popup.review_status_value.isHidden() is True
    assert fake.popup.maya_value.text() == "Danach kannst du GOAT navigieren lassen."
    assert fake.popup.cue_approve.text() == "Pruefen"
    assert fake.popup.cue_approve.enabled is True
    assert fake.popup.cue_reject.enabled is True
    assert fake.shown is True


def test_status_chips_use_plain_user_states() -> None:
    fake = FakeTray()

    GoatTrayApp._update_connection_status(fake, "builder: connected")

    assert fake.popup.connection_value.text() == "builder: connected"
    assert fake.popup.connection_chip.text() == "Status: Verbunden"
    assert _status_chip_text("builder: reconnecting") == "Status: Verbinde neu"
    assert _status_chip_text("lokal") == "Status: Bereit"
    assert _status_chip_text("already running") == "Status: Schon offen"


def test_bridge_port_in_use_shows_single_instance_message() -> None:
    fake = FakeTray()

    GoatTrayApp._handle_bridge_start_result(fake, {"ok": False, "status": "port_in_use", "port": 8765})

    assert fake.popup.connection_value.text() == "GOAT laeuft schon"
    assert fake.popup.connection_chip.text() == "Status: Schon offen"
    assert fake.popup.screen_context_value.text() == "GOAT ist bereits offen"
    assert fake.popup.maya_value.text() == "Bitte nutze das vorhandene GOAT-Fenster. Diese Instanz fuehrt nichts aus."
    assert fake.popup.cue_approve.enabled is False
    assert fake.popup.cue_reject.enabled is False


def test_speech_chip_uses_plain_user_states() -> None:
    assert _speech_chip_text("Gemini Live aktiv") == "Sprache: Bereit"
    assert _speech_chip_text("Gemini Live 800ms / Aufnahme 1.2s") == "Sprache: Fertig"
    assert _speech_chip_text("Vorlesen fehlgeschlagen: test") == "Sprache: Problem"


def test_accepted_stage1_cue_turns_into_navigation_preview() -> None:
    fake = FakeTray()
    GoatTrayApp.receive_builder_cue(fake, {"action_type": "hover", "label": "Senden Button", "bbox": [10, 20, 110, 80]})

    GoatTrayApp._finish_builder_cue(
        fake,
        {
            "status": "ok",
            "response": {
                "safety_state": "accept",
                "broker_decision": {"status": "accept", "final_bbox": [10, 20, 110, 80]},
            },
        },
    )

    assert fake.pending_stage1_action["broker_decision"] == {"status": "accept", "final_bbox": [10, 20, 110, 80]}
    assert fake.popup.screen_context_value.text() == "Schritt 2: GOAT kann dich navigieren"
    assert fake.popup.review_status_value.isHidden() is True
    assert fake.popup.maya_value.text() == (
        "GOAT will den Mauszeiger auf Senden Button bewegen. Dabei wird nichts geklickt und nichts getippt. "
        "Klicke nur auf Ausfuehren, wenn das markierte Ziel stimmt."
    )
    assert fake.popup.cue_approve.text() == "Ausfuehren"
    assert fake.popup.cue_approve.enabled is True


def test_rejected_builder_cue_uses_plain_user_message() -> None:
    fake = FakeTray()

    GoatTrayApp.receive_builder_cue(
        fake,
        {
            "ok": False,
            "status": "rejected",
            "scope": "local_builder_cue_proposal",
            "reason": "bbox with four numeric values is required; action_type is required",
        },
    )

    assert fake.pending_builder_cue is None
    assert fake.pending_stage1_action is None
    assert fake.pending_stage2_action is None
    assert fake.popup.target_value.text() == "Kein Ziel markiert"
    assert fake.popup.screen_context_value.text() == "Ziel nicht sicher erkannt"
    assert fake.popup.review_status_value.isHidden() is True
    assert fake.popup.maya_value.text() == (
        "Ich konnte das Ziel nicht sicher zuordnen. Bitte zeig mir nochmal, welches Ziel du meinst."
    )
    assert fake.popup.cue_approve.text() == "Pruefen"
    assert fake.popup.cue_approve.enabled is False
    assert fake.popup.cue_reject.enabled is True
    assert fake.shown is True


def test_builder_cue_http_error_uses_plain_user_message() -> None:
    fake = FakeTray()

    GoatTrayApp._finish_builder_cue(fake, {"status": "error", "error": "TimeoutError('timed out')"})

    assert fake.popup.screen_context_value.text() == "Ziel konnte nicht geprueft werden"
    assert fake.popup.maya_value.text() == "Die lokale Pruefung hat gerade nicht geantwortet. Bitte versuch es nochmal."
    assert fake.popup.cue_approve.enabled is False
    assert fake.popup.cue_reject.enabled is True


def test_builder_cue_verifier_reject_uses_plain_user_message() -> None:
    fake = FakeTray()

    GoatTrayApp._finish_builder_cue(
        fake,
        {
            "status": "ok",
            "response": {
                "safety_state": "stop",
                "broker_decision": {
                    "status": "stop",
                    "reason": "bbox center is outside active window",
                },
            },
        },
    )

    assert fake.popup.screen_context_value.text() == "Ziel nicht sicher"
    assert fake.popup.maya_value.text() == (
        "Ich konnte das Ziel nicht sicher zuordnen. Bitte zeig mir nochmal, welches Ziel du meinst."
    )
    assert fake.popup.cue_approve.enabled is False
    assert fake.popup.cue_reject.enabled is True


def test_accepted_scroll_cue_turns_into_scroll_preview() -> None:
    fake = FakeTray()
    GoatTrayApp.receive_builder_cue(
        fake,
        {"action_type": "scroll", "label": "Seite", "bbox": [10, 20, 110, 80], "scroll_amount": 360},
    )

    GoatTrayApp._finish_builder_cue(
        fake,
        {
            "status": "ok",
            "response": {
                "safety_state": "accept",
                "broker_decision": {"status": "accept", "final_bbox": [10, 20, 110, 80]},
            },
        },
    )

    assert fake.pending_stage1_action["scroll_amount"] == 360
    assert fake.popup.screen_context_value.text() == "Schritt 2: GOAT kann dich navigieren"
    assert fake.popup.maya_value.text() == (
        "GOAT will auf der Seite nach oben scrollen. Dabei wird nichts geklickt und nichts getippt. "
        "Klicke nur auf Ausfuehren, wenn das markierte Ziel stimmt."
    )
    assert fake.popup.cue_approve.text() == "Ausfuehren"
    assert fake.popup.cue_approve.enabled is True


def test_stage1_done_resets_pending_navigation() -> None:
    fake = FakeTray()
    fake.pending_builder_cue = {"label": "Senden Button"}
    fake.pending_stage1_action = {"action_type": "hover", "label": "Senden Button"}

    GoatTrayApp._finish_builder_cue(fake, {"status": "stage1_done", "response": {"executed": True, "action_type": "hover"}})

    assert fake.pending_builder_cue is None
    assert fake.pending_stage1_action is None
    assert fake.popup.screen_context_value.text() == "Navigation ausgefuehrt"
    assert fake.popup.maya_value.text() == (
        "Ich habe den Mauszeiger zum Ziel bewegt. Du kannst jetzt weitermachen oder mir den naechsten Schritt sagen."
    )
    assert fake.popup.cue_approve.text() == "Pruefen"
    assert fake.popup.cue_approve.enabled is False
    assert fake.popup.cue_reject.enabled is False


def test_stage1_scroll_done_names_next_step() -> None:
    fake = FakeTray()
    fake.pending_builder_cue = {"label": "Seite"}
    fake.pending_stage1_action = {"action_type": "scroll", "label": "Seite"}

    GoatTrayApp._finish_builder_cue(
        fake,
        {"status": "stage1_done", "response": {"executed": True, "action_type": "scroll", "target": {"scroll_amount": -360}}},
    )

    assert fake.popup.screen_context_value.text() == "Navigation ausgefuehrt"
    assert fake.popup.maya_value.text() == (
        "Ich habe die Seite nach unten gescrollt. Sag mir einfach, was als Naechstes dran ist."
    )


def test_builder_stage2_cue_shows_input_check_before_execution() -> None:
    fake = FakeTray()

    GoatTrayApp.receive_builder_cue(
        fake,
        {
            "action_type": "type",
            "label": "Suchfeld",
            "text": "StepStack",
            "safe_text_context": True,
            "bbox": [10, 20, 110, 80],
        },
    )

    assert fake.pending_stage2_action == {
        "action_type": "type",
        "label": "Suchfeld",
        "text": "StepStack",
        "safe_text_context": True,
    }
    assert fake.popup.target_value.text() == "Eingabefeld: Suchfeld"
    assert fake.popup.screen_context_value.text() == "Schritt 1: Eingabefeld pruefen"
    assert fake.popup.maya_value.text() == "Danach kannst du die Eingabe freigeben."
    assert fake.popup.cue_approve.text() == "Pruefen"


def test_accepted_stage2_cue_turns_into_input_preview() -> None:
    fake = FakeTray()
    GoatTrayApp.receive_builder_cue(
        fake,
        {
            "action_type": "type",
            "label": "Suchfeld",
            "text": "StepStack",
            "safe_text_context": True,
            "bbox": [10, 20, 110, 80],
        },
    )

    GoatTrayApp._finish_builder_cue(
        fake,
        {
            "status": "ok",
            "response": {
                "safety_state": "accept",
                "broker_decision": {"status": "accept", "final_bbox": [10, 20, 110, 80]},
            },
        },
    )

    assert fake.pending_stage2_action["broker_decision"] == {"status": "accept", "final_bbox": [10, 20, 110, 80]}
    assert fake.popup.screen_context_value.text() == "Schritt 2: Freigabe fuer Eingabe"
    assert fake.popup.review_status_value.isHidden() is True
    assert fake.popup.maya_value.text() == (
        'GOAT will Text in Suchfeld eingeben: "StepStack". Bitte pruefe die Eingabe vor dem Ausfuehren. '
        "Klicke nur auf Ausfuehren, wenn Feld und Text stimmen."
    )
    assert fake.popup.cue_approve.text() == "Ausfuehren"
    assert fake.popup.cue_approve.enabled is True


def test_stage2_builder_cue_can_use_prechecked_broker_response() -> None:
    fake = FakeTray()
    GoatTrayApp.receive_builder_cue(
        fake,
        {
            "action_type": "type",
            "label": "Suchfeld",
            "text": "StepStack",
            "safe_text_context": True,
            "bbox": [10, 20, 110, 80],
            "broker_response": {
                "safety_state": "accept",
                "broker_decision": {"status": "accept", "final_bbox": [10, 20, 110, 80]},
            },
        },
    )

    GoatTrayApp._finish_builder_cue(fake, {"status": "ok", "response": fake.pending_builder_cue["broker_response"]})

    assert fake.popup.screen_context_value.text() == "Schritt 2: Freigabe fuer Eingabe"
    assert fake.popup.cue_approve.text() == "Ausfuehren"
    assert fake.popup.cue_approve.enabled is True


def test_stage2_preview_without_safe_context_disables_execute() -> None:
    fake = FakeTray()
    GoatTrayApp.receive_builder_cue(
        fake,
        {"action_type": "type", "label": "Suchfeld", "text": "StepStack", "safe_text_context": False, "bbox": [10, 20, 110, 80]},
    )

    GoatTrayApp._finish_builder_cue(
        fake,
        {
            "status": "ok",
            "response": {
                "safety_state": "accept",
                "broker_decision": {"status": "accept", "final_bbox": [10, 20, 110, 80]},
            },
        },
    )

    assert fake.popup.maya_value.text() == "Ich tippe hier noch nicht. Sag mir genauer, welches Feld das ist, oder zeig es deutlicher."
    assert fake.popup.cue_approve.text() == "Nicht sicher"
    assert fake.popup.cue_approve.enabled is False


def test_stage2_preview_without_text_disables_execute() -> None:
    fake = FakeTray()
    GoatTrayApp.receive_builder_cue(
        fake,
        {"action_type": "type", "label": "Suchfeld", "text": "  ", "safe_text_context": True, "bbox": [10, 20, 110, 80]},
    )

    GoatTrayApp._finish_builder_cue(
        fake,
        {
            "status": "ok",
            "response": {
                "safety_state": "accept",
                "broker_decision": {"status": "accept", "final_bbox": [10, 20, 110, 80]},
            },
        },
    )

    assert fake.popup.maya_value.text() == "Ich tippe hier noch nicht. Mir fehlt noch der Text, den ich eintragen soll."
    assert fake.popup.cue_approve.text() == "Kein Text"
    assert fake.popup.cue_approve.enabled is False
    assert fake.popup.review_status_value.visible is False


def test_builder_stage3_cue_shows_review_before_any_execution() -> None:
    fake = FakeTray()

    GoatTrayApp.receive_builder_cue(
        fake,
        {
            "action_type": "click",
            "label": "Kaufen",
            "bbox": [10, 20, 110, 80],
            "consequence_summary": "Das wuerde einen Kauf ausloesen.",
        },
    )

    assert fake.pending_stage1_action is None
    assert fake.pending_stage2_action is None
    assert fake.pending_stage3_action == {
        "action_type": "click",
        "label": "Kaufen",
        "consequence_summary": "Das wuerde einen Kauf ausloesen.",
    }
    assert fake.popup.target_value.text() == "Zielvorschlag: Kaufen"
    assert fake.popup.screen_context_value.text() == "Schritt 1: Ziel pruefen"
    assert fake.popup.maya_value.text() == "Danach zeigt GOAT dir die wichtige Aktion nur zur Pruefung."
    assert fake.popup.cue_approve.text() == "Pruefen"
    assert fake.popup.cue_approve.enabled is True


def test_accepted_stage3_cue_turns_into_review_only_popup() -> None:
    fake = FakeTray()
    GoatTrayApp.receive_builder_cue(fake, {"action_type": "send", "label": "Senden Button", "bbox": [10, 20, 110, 80]})

    GoatTrayApp._finish_builder_cue(
        fake,
        {
            "status": "ok",
            "response": {
                "safety_state": "accept",
                "broker_decision": {"status": "accept", "final_bbox": [10, 20, 110, 80]},
            },
        },
    )

    assert fake.pending_stage1_action is None
    assert fake.pending_stage2_action is None
    assert fake.pending_stage3_action["broker_decision"] == {"status": "accept", "final_bbox": [10, 20, 110, 80]}
    assert fake.popup.screen_context_value.text() == "Schritt 2: Nur Review - keine Ausfuehrung"
    assert fake.popup.review_status_value.text() == "Nur Review - keine Ausfuehrung"
    assert fake.popup.review_status_value.isHidden() is False
    assert fake.popup.maya_value.text() == (
        "GOAT will etwas ueber Senden Button senden oder teilen. Das kann Folgen haben und braucht deine klare Freigabe. "
        "Pruefe Empfaenger, Inhalt und Sichtbarkeit selbst, bevor du im Programm sendest."
    )
    assert fake.popup.cue_approve.text() == "Verstanden"
    assert fake.popup.cue_approve.enabled is True


def test_accepted_stage3_delete_cue_uses_specific_review_copy() -> None:
    fake = FakeTray()
    GoatTrayApp.receive_builder_cue(fake, {"action_type": "delete", "label": "Loeschen", "bbox": [10, 20, 110, 80]})

    GoatTrayApp._finish_builder_cue(
        fake,
        {
            "status": "ok",
            "response": {
                "safety_state": "accept",
                "broker_decision": {"status": "accept", "final_bbox": [10, 20, 110, 80]},
            },
        },
    )

    assert fake.pending_stage1_action is None
    assert fake.pending_stage2_action is None
    assert fake.popup.screen_context_value.text() == "Schritt 2: Nur Review - keine Ausfuehrung"
    assert fake.popup.review_status_value.text() == "Nur Review - keine Ausfuehrung"
    assert fake.popup.review_status_value.isHidden() is False
    assert fake.popup.maya_value.text() == (
        "GOAT will Loeschen oder Abbrechen ueber Loeschen ausloesen. Das kann Folgen haben und braucht deine klare Freigabe. "
        "Pruefe selbst, ob du das wirklich entfernen, abbrechen oder beenden willst."
    )
    assert fake.popup.cue_approve.text() == "Verstanden"
    assert fake.popup.cue_approve.enabled is True


def test_stage3_review_acknowledge_does_not_start_stage1_or_stage2_execution() -> None:
    fake = FakeTray()
    fake.pending_builder_cue = {"label": "Kaufen"}
    fake.pending_stage3_action = {
        "action_type": "click",
        "label": "Kaufen",
        "broker_decision": {"status": "accept", "final_bbox": [10, 20, 110, 80]},
    }

    GoatTrayApp.approve_pending_cue(fake)

    assert fake.pending_builder_cue is None
    assert fake.pending_stage1_action is None
    assert fake.pending_stage2_action is None
    assert fake.pending_stage3_action is None
    assert fake.popup.screen_context_value.text() == "Review geschlossen"
    assert fake.popup.review_status_value.isHidden() is True
    assert fake.popup.maya_value.text() == (
        "Ich habe nichts ausgefuehrt. Bitte entscheide selbst im Programm, ob du weitermachst."
    )
    assert fake.popup.cue_approve.text() == "Pruefen"
    assert fake.popup.cue_approve.enabled is False


def test_stage2_failed_execution_uses_plain_user_message() -> None:
    fake = FakeTray()
    fake.pending_builder_cue = {"label": "Suchfeld"}
    fake.pending_stage2_action = {"action_type": "type", "label": "Suchfeld", "text": "StepStack"}

    GoatTrayApp._finish_builder_cue(
        fake,
        {
            "status": "stage2_done",
            "response": {
                "executed": False,
                "reason": "safe_text_context must be true before stage 2 text input can execute",
            },
        },
    )

    assert fake.popup.screen_context_value.text() == "Eingabe nicht ausgefuehrt"
    assert fake.popup.maya_value.text() == "Ich tippe hier nicht. Sag mir genauer, welches Feld das ist, oder zeig es deutlicher."
    assert fake.popup.cue_approve.enabled is False


def test_stage2_backend_failure_uses_plain_user_message() -> None:
    fake = FakeTray()

    GoatTrayApp._finish_builder_cue(
        fake,
        {
            "status": "stage2_done",
            "response": {"executed": False, "reason": "text input backend failed before completion"},
        },
    )

    assert fake.popup.screen_context_value.text() == "Eingabe nicht ausgefuehrt"
    assert fake.popup.maya_value.text() == "Die Eingabe hat nicht geklappt. Ich melde sie nicht als erledigt."


def test_stage2_verification_failure_uses_plain_user_message() -> None:
    fake = FakeTray()

    GoatTrayApp._finish_builder_cue(
        fake,
        {
            "status": "stage2_done",
            "response": {"executed": False, "reason": "text input verification failed after typing"},
        },
    )

    assert fake.popup.screen_context_value.text() == "Eingabe nicht ausgefuehrt"
    assert fake.popup.maya_value.text() == "Ich bin nicht sicher, ob die Eingabe angekommen ist. Ich melde sie nicht als erledigt."


def test_stage1_backend_failure_uses_plain_user_message() -> None:
    fake = FakeTray()

    GoatTrayApp._finish_builder_cue(
        fake,
        {
            "status": "stage1_done",
            "response": {"executed": False, "reason": "mouse backend failed before pointer move completed"},
        },
    )

    assert fake.popup.screen_context_value.text() == "Navigation nicht ausgefuehrt"
    assert fake.popup.maya_value.text() == "Die Navigation hat nicht geklappt. Ich melde sie nicht als erledigt."


def test_stage1_verification_failure_uses_plain_user_message() -> None:
    fake = FakeTray()

    GoatTrayApp._finish_builder_cue(
        fake,
        {
            "status": "stage1_done",
            "response": {"executed": False, "reason": "pointer verification failed after move"},
        },
    )

    assert fake.popup.screen_context_value.text() == "Navigation nicht ausgefuehrt"
    assert fake.popup.maya_value.text() == "Ich bin nicht sicher, ob die Navigation angekommen ist. Ich melde sie nicht als erledigt."


def test_stage1_unverified_completion_is_not_reported_as_done() -> None:
    fake = FakeTray()

    GoatTrayApp._finish_builder_cue(
        fake,
        {
            "status": "stage1_done",
            "response": {
                "executed": True,
                "completion_verified": False,
                "reason": "pointer verification failed after move",
            },
        },
    )

    assert fake.popup.screen_context_value.text() == "Navigation nicht ausgefuehrt"
    assert fake.popup.maya_value.text() == "Ich bin nicht sicher, ob die Navigation angekommen ist. Ich melde sie nicht als erledigt."


def test_stage2_unverified_completion_is_not_reported_as_done() -> None:
    fake = FakeTray()

    GoatTrayApp._finish_builder_cue(
        fake,
        {
            "status": "stage2_done",
            "response": {
                "executed": True,
                "completion_verified": False,
                "reason": "text input verification failed after typing",
            },
        },
    )

    assert fake.popup.screen_context_value.text() == "Eingabe nicht ausgefuehrt"
    assert fake.popup.maya_value.text() == "Ich bin nicht sicher, ob die Eingabe angekommen ist. Ich melde sie nicht als erledigt."


def test_stage2_done_resets_pending_input() -> None:
    fake = FakeTray()
    fake.pending_builder_cue = {"label": "Suchfeld"}
    fake.pending_stage2_action = {"action_type": "type", "label": "Suchfeld", "text": "StepStack"}

    GoatTrayApp._finish_builder_cue(
        fake,
        {"status": "stage2_done", "response": {"executed": True, "preview": {"label": "Suchfeld"}}},
    )

    assert fake.pending_builder_cue is None
    assert fake.pending_stage1_action is None
    assert fake.pending_stage2_action is None
    assert fake.popup.screen_context_value.text() == "Eingabe ausgefuehrt"
    assert fake.popup.maya_value.text() == "Ich habe den Text in Suchfeld eingetragen. Bitte pruefe kurz, ob er stimmt."


def test_reject_pending_cue_resets_navigation_state() -> None:
    fake = FakeTray()
    fake.pending_builder_cue = {"label": "Senden Button"}
    fake.pending_stage1_action = {"action_type": "hover", "label": "Senden Button"}
    fake.pending_stage2_action = {"action_type": "type", "label": "Suchfeld", "text": "StepStack"}
    fake.pending_stage3_action = {"action_type": "click", "label": "Kaufen"}

    GoatTrayApp.reject_pending_cue(fake)

    assert fake.pending_builder_cue is None
    assert fake.pending_stage1_action is None
    assert fake.pending_stage2_action is None
    assert fake.pending_stage3_action is None
    assert fake.popup.screen_context_value.text() == "Abgebrochen"
    assert fake.popup.review_status_value.isHidden() is True
    assert fake.popup.cue_approve.text() == "Pruefen"
