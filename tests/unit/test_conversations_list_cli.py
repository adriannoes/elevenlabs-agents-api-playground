"""Unit tests for the conversations listing CLI."""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest
from scripts import conversations_list

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.monkeypatch import MonkeyPatch


def test_redact_sensitive_text() -> None:
    text = (
        "CPF 123.456.789-00, email user@example.com, phone +55 11 91234-5678, card 4111111111111111"
    )

    redacted = conversations_list.redact_sensitive_text(text)

    assert "123.456.789-00" not in redacted
    assert "user@example.com" not in redacted
    assert "91234-5678" not in redacted
    assert "4111111111111111" not in redacted
    assert "[CPF]" in redacted
    assert "[EMAIL]" in redacted
    assert "[PHONE]" in redacted
    assert "[CARD]" in redacted


def test_list_conversations_prints_safe_summary(
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    convo = SimpleNamespace(
        conversation_id="conv-1",
        agent_name="Telecom Customer Care",
        status="done",
        call_successful="success",
        call_duration_secs=42,
        message_count=6,
        start_time_unix_secs=1_700_000_000,
        transcript_summary="Customer CPF 123.456.789-00 asked about billing.",
    )
    page = SimpleNamespace(conversations=[convo], has_more=False, next_cursor=None)
    conversations = SimpleNamespace(list=lambda **kwargs: page)
    client = SimpleNamespace(conversational_ai=SimpleNamespace(conversations=conversations))

    monkeypatch.setattr(conversations_list, "get_client", lambda: client)
    monkeypatch.setattr(
        conversations_list,
        "get_settings",
        lambda: SimpleNamespace(demo_agent_id_telecom="agent-1"),
    )
    monkeypatch.setattr("sys.argv", ["conversations_list.py", "telecom"])

    conversations_list.main()

    printed = capsys.readouterr().out
    assert "conv-1" in printed
    assert "success" in printed
    assert "[CPF]" in printed
    assert "123.456.789-00" not in printed


def test_get_conversation_prints_redacted_details(
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    analysis = SimpleNamespace(
        call_successful="success",
        transcript_summary="Email user@example.com and phone +55 11 91234-5678.",
        call_summary_title="Billing",
    )
    detail = SimpleNamespace(
        conversation_id="conv-2",
        agent_name="Agent",
        status="done",
        analysis=analysis,
    )
    conversations = SimpleNamespace(get=lambda **kwargs: detail)
    client = SimpleNamespace(conversational_ai=SimpleNamespace(conversations=conversations))

    monkeypatch.setattr(conversations_list, "get_client", lambda: client)
    monkeypatch.setattr("sys.argv", ["conversations_list.py", "--id", "conv-2"])

    conversations_list.main()

    printed = capsys.readouterr().out
    assert "conv-2" in printed
    assert "[EMAIL]" in printed
    assert "[PHONE]" in printed
    assert "user@example.com" not in printed


def test_missing_scenario_agent_id_exits(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        conversations_list,
        "get_settings",
        lambda: SimpleNamespace(demo_agent_id_telecom=None),
    )
    monkeypatch.setattr("sys.argv", ["conversations_list.py", "telecom"])

    with pytest.raises(SystemExit, match="Missing DEMO_AGENT_ID_TELECOM"):
        conversations_list.main()
