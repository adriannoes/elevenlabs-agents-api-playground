"""Tests for conversation simulation wrapper."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from elevenlabs.types import AgentSimulatedChatTestResponseModel
from elevenlabs.types import ConversationHistoryAnalysisCommonModel as SdkAnalysis
from elevenlabs.types import ConversationHistoryTranscriptCommonModelInput as SdkHistoryIn
from elevenlabs.types import ConversationHistoryTranscriptResponseModel as SdkTurn
from elevenlabs.types import ConversationHistoryTranscriptToolCallCommonModelOutput as SdkToolCall

import eleven_demo.agents.conversation_sim as simulate_module
from eleven_demo.agents.conversation_sim import ToolCall
from eleven_demo.agents.conversation_sim import simulate as simulate_conv


def test_simulate_empty_messages_raises() -> None:
    with pytest.raises(ValueError, match="at least one"):
        simulate_conv("aid", [], client=MagicMock())


def test_simulate_single_turn() -> None:
    line = MagicMock(spec=SdkTurn)
    line.role = "user"
    line.message = "oi"
    line.time_in_call_secs = 0
    line.tool_calls = None

    analysis = MagicMock(spec=SdkAnalysis)
    analysis.call_successful = "success"
    analysis.transcript_summary = "done"
    analysis.call_summary_title = "t"

    result = AgentSimulatedChatTestResponseModel(simulated_conversation=[line], analysis=analysis)

    agents = MagicMock()
    agents.simulate_conversation.return_value = result

    mock_client = MagicMock()
    mock_client.conversational_ai.agents = agents

    def _minimal_history(turn: SdkTurn) -> SdkHistoryIn:
        role = turn.role if turn.role in ("user", "agent") else "user"
        return SdkHistoryIn(
            role=role,
            message=turn.message or "",
            time_in_call_secs=turn.time_in_call_secs,
        )

    with patch.object(
        simulate_module,
        "_turn_to_partial_history_item",
        side_effect=_minimal_history,
    ):
        out = simulate_conv("agent-1", ["oi"], client=mock_client)

    assert out.transcript[0].role == "user"
    assert out.analysis.transcript_summary == "done"
    agents.simulate_conversation.assert_called_once()
    first_spec = agents.simulate_conversation.call_args.kwargs["simulation_specification"]
    assert first_spec.partial_conversation_history == []
    assert first_spec.simulated_user_config.prompt is not None
    assert "cliente brasileiro" in first_spec.simulated_user_config.prompt.prompt
    request_options = agents.simulate_conversation.call_args.kwargs["request_options"]
    assert request_options["timeout_in_seconds"] == 120


def test_simulate_multiple_user_messages_chains() -> None:
    def _turn(role: str, msg: str | None, *, time_in_call_secs: int = 0) -> SdkTurn:
        t = MagicMock(spec=SdkTurn)
        t.role = role
        t.message = msg
        t.time_in_call_secs = time_in_call_secs
        t.tool_calls = None
        return t

    def _serialize_stub(turn: SdkTurn) -> SdkHistoryIn:
        role = turn.role if turn.role in ("user", "agent") else "user"
        return SdkHistoryIn(
            role=role,
            message=turn.message or "",
            time_in_call_secs=turn.time_in_call_secs,
        )

    analysis = MagicMock(spec=SdkAnalysis)
    analysis.call_successful = "success"
    analysis.transcript_summary = "ok"
    analysis.call_summary_title = None

    r1 = AgentSimulatedChatTestResponseModel(
        simulated_conversation=[_turn("user", "a", time_in_call_secs=0)], analysis=analysis
    )
    r2 = AgentSimulatedChatTestResponseModel(
        simulated_conversation=[_turn("user", "b", time_in_call_secs=1)], analysis=analysis
    )

    agents = MagicMock()
    agents.simulate_conversation.side_effect = [r1, r2]

    mock_client = MagicMock()
    mock_client.conversational_ai.agents = agents

    with patch.object(
        simulate_module,
        "_turn_to_partial_history_item",
        side_effect=_serialize_stub,
    ):
        out = simulate_conv("agent-1", ["a", "b"], client=mock_client)

    assert agents.simulate_conversation.call_count == 2
    assert len(out.transcript) == 2


def test_tool_call_from_sdk_round_trip() -> None:
    sdk = MagicMock(spec=SdkToolCall)
    sdk.tool_name = "lookup_telecom_account"
    sdk.request_id = "rid-1"
    sdk.params_as_json = "{}"
    tc = ToolCall.from_sdk(sdk)
    assert tc.tool_name == "lookup_telecom_account"
    assert tc.request_id == "rid-1"
    assert tc.params_as_json == "{}"


def test_turn_to_partial_history_item_fallback_on_invalid_dump() -> None:
    turn = MagicMock()
    turn.model_dump_json.return_value = '{"not": "a valid history shape for validation"}'
    turn.role = "system"
    turn.message = "x"
    turn.time_in_call_secs = 1
    item = simulate_module._turn_to_partial_history_item(turn)
    assert item.role == "agent"
    assert item.message == "x"


def test_simulate_collects_tool_calls() -> None:
    tool_sdk = MagicMock(spec=SdkToolCall)
    tool_sdk.tool_name = "transfer_to_human"
    tool_sdk.request_id = "r1"
    tool_sdk.params_as_json = '{"reason_code":"off_topic"}'

    line = MagicMock(spec=SdkTurn)
    line.role = "agent"
    line.message = "ok"
    line.time_in_call_secs = 0
    line.tool_calls = [tool_sdk]

    analysis = MagicMock(spec=SdkAnalysis)
    analysis.call_successful = "success"
    analysis.transcript_summary = "done"
    analysis.call_summary_title = None

    result = AgentSimulatedChatTestResponseModel(simulated_conversation=[line], analysis=analysis)

    agents = MagicMock()
    agents.simulate_conversation.return_value = result

    mock_client = MagicMock()
    mock_client.conversational_ai.agents = agents

    with patch.object(
        simulate_module,
        "_turn_to_partial_history_item",
        side_effect=lambda t: SdkHistoryIn(
            role="agent" if t.role == "agent" else "user",
            message=t.message or "",
            time_in_call_secs=int(t.time_in_call_secs or 0),
        ),
    ):
        out = simulate_conv("agent-1", ["hi"], client=mock_client)

    assert len(out.tool_calls) == 1
    assert out.tool_calls[0].tool_name == "transfer_to_human"
