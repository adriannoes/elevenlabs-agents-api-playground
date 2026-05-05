"""Tests for deterministic Convai tool webhook dispatch."""

from __future__ import annotations

import pytest

from eleven_demo.agents.tool_webhook import dispatch_convai_demo_tool


def test_dispatch_lookup_telecom_account_flat_body() -> None:
    payload = dispatch_convai_demo_tool({"cpf": "12345678900"})
    assert payload["account_ref_masked"] == "***8900"
    assert isinstance(payload["balance_brl_major"], float)
    assert payload["plan_summary"] in (
        "prepaid_standard",
        "postpaid_standard",
        "corporate_managed",
    )


def test_dispatch_lookup_telecom_account_parameters_nested() -> None:
    payload = dispatch_convai_demo_tool({"parameters": {"cpf": "12345678900"}})
    assert payload["account_ref_masked"].endswith("8900")


def test_dispatch_transfer_when_tool_named() -> None:
    payload = dispatch_convai_demo_tool(
        {
            "tool_name": "transfer_to_human",
            "reason_code": "customer_request",
        }
    )
    assert isinstance(payload["queue_position"], int)
    assert payload["callback_reference"].startswith("TCK-")


def test_dispatch_raises_for_unknown_explicit_tool() -> None:
    with pytest.raises(ValueError, match="unknown tool_name"):
        dispatch_convai_demo_tool({"tool_name": "not_registered", "x": "1"})


def test_dispatch_rejects_duplicate_keys_between_levels() -> None:
    with pytest.raises(ValueError, match="ambiguous"):
        dispatch_convai_demo_tool({"cpf": "11111111111", "parameters": {"cpf": "12345678900"}})


def test_dispatch_empty_payload_no_tool_matches() -> None:
    with pytest.raises(ValueError, match="no registered demo tool"):
        dispatch_convai_demo_tool({})
