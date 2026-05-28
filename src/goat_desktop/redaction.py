from __future__ import annotations

from typing import Any


REDACTED_VALUE = "[redacted]"
SENSITIVE_FIELD_LABEL = "sensibles Feld"
SENSITIVE_TARGET_LABEL = "sensibles Ziel"


def redact_context(context: dict[str, Any]) -> dict[str, str]:
    return {key: REDACTED_VALUE for key in context}


def redact_locked_request_payload(payload: dict[str, Any], *, redact_text: bool = False) -> dict[str, Any]:
    redacted = dict(payload)
    redacted["label"] = REDACTED_VALUE
    redacted["label_redacted"] = True
    if redact_text and "text" in redacted:
        redacted["text"] = ""
        redacted["text_redacted"] = True
    if redacted.get("context"):
        redacted["context"] = redact_context(dict(redacted["context"]))
        redacted["context_redacted"] = True
    return redacted


def redact_locked_stage3_payload(payload: dict[str, Any]) -> dict[str, Any]:
    redacted = redact_locked_request_payload(payload)
    if "consequence_summary" in redacted:
        redacted["consequence_summary"] = ""
        redacted["consequence_summary_redacted"] = True
    return redacted


def redact_locked_classification_payload(payload: dict[str, Any]) -> dict[str, Any]:
    redacted = dict(payload)
    redacted["normalized_text"] = REDACTED_VALUE
    redacted["normalized_text_redacted"] = True
    return redacted


def redact_nested_context_values(value: Any) -> Any:
    if isinstance(value, dict):
        redacted = {}
        for key, item in value.items():
            if key == "context" and isinstance(item, dict):
                redacted[key] = redact_context(item)
                redacted["context_redacted"] = True
            else:
                redacted[key] = redact_nested_context_values(item)
        return redacted
    if isinstance(value, list):
        return [redact_nested_context_values(item) for item in value]
    return value
