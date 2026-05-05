"""Dispatch ElevenAgents server-tool webhook payloads to deterministic demo mocks."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import ValidationError

from eleven_demo.agents.tools import TOOLS_REGISTRY


def _flatten_tool_payload(body: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize platform-specific envelopes into a single parameter mapping."""
    if not isinstance(body, Mapping):
        msg = "webhook payload must be a JSON object"
        raise TypeError(msg)

    data: dict[str, Any] = dict(body)

    nested = data.pop("parameters", None)
    if nested is None:
        nested = data.pop("params", None)
    if isinstance(nested, dict):
        overlapping = sorted(set(data) & set(nested))
        if overlapping:
            msg = f"ambiguous keys at top level and in parameters: {overlapping}"
            raise ValueError(msg)
        data.update(nested)

    meta_keys = {
        "tool_call_id",
        "conversation_id",
        "conversationId",
        "agent_id",
        "request_id",
        "timestamp",
        "signature",
        "sig",
    }
    for key in meta_keys:
        data.pop(key, None)

    return data


def _tool_hint_from_flat(data: dict[str, Any]) -> tuple[str | None, dict[str, Any]]:
    """Optional explicit tool name (strip from params for pydantic-only bodies)."""
    hint: str | None = None
    for key in ("tool_name", "name"):
        raw = data.pop(key, None)
        if raw is None:
            continue
        if isinstance(raw, str) and raw.strip():
            hint = raw.strip()
        break
    return hint, data


def dispatch_convai_demo_tool(body: Mapping[str, Any]) -> dict[str, Any]:
    """Run the first demo tool whose input schema validates against the flattened body."""
    flat = _flatten_tool_payload(body)
    hint, params = _tool_hint_from_flat(flat)

    if hint:
        registration = TOOLS_REGISTRY.get(hint)
        if registration is None:
            msg = f"unknown tool_name: {hint}"
            raise ValueError(msg)
        inp_model, _out_model, fn = registration
        try:
            inp = inp_model.model_validate(params)
        except ValidationError as exc:
            msg = f"invalid parameters for {hint}: {exc.error_count()} validation errors"
            raise ValueError(msg) from exc
        out = fn(inp)
        return out.model_dump(mode="json")

    last_error: ValidationError | None = None
    for _name, (inp_model, _out_model, fn) in TOOLS_REGISTRY.items():
        try:
            inp = inp_model.model_validate(params)
        except ValidationError as exc:
            last_error = exc
            continue
        out = fn(inp)
        return out.model_dump(mode="json")

    if last_error is not None:
        msg = (
            "no registered demo tool matched the webhook body; "
            f"last validation error ({last_error.error_count()} issues)"
        )
        raise ValueError(msg) from last_error

    msg = "no registered demo tools"
    raise ValueError(msg)


__all__ = ["dispatch_convai_demo_tool"]
