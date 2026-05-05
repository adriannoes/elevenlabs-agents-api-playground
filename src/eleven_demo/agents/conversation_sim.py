"""Typed wrapper around Conversational AI conversation simulation."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Literal, cast

from elevenlabs.conversational_ai.agents.client import AgentsClient
from pydantic import BaseModel, ConfigDict

from eleven_demo.client import get_client

if TYPE_CHECKING:
    from elevenlabs import ElevenLabs

from elevenlabs.types import (
    AgentConfig,
    ConversationSimulationSpecification,
    PromptAgentApiModelOutput,
)
from elevenlabs.types import ConversationHistoryAnalysisCommonModel as SdkAnalysis
from elevenlabs.types import ConversationHistoryTranscriptCommonModelInput as SdkHistoryInputTurn
from elevenlabs.types import ConversationHistoryTranscriptResponseModel as SdkTranscriptTurn
from elevenlabs.types import ConversationHistoryTranscriptToolCallCommonModelOutput as SdkToolCall

# HTTP read timeout per ``simulate`` call (LLM + tools can exceed one minute).
SIMULATION_TIMEOUT_SECONDS = 120
SIMULATED_USER_PROMPT = (
    "Você é um cliente brasileiro realista em uma ligação de suporte. Responda em português do "
    "Brasil, de forma natural e breve, com dúvidas e informações plausíveis do cenário. Não diga "
    "que é uma IA, assistente, modelo de linguagem ou sistema automatizado."
)


class Turn(BaseModel):
    """Single transcript line mirrored from simulated conversation."""

    role: Literal["user", "agent"]
    message: str | None = None

    model_config = ConfigDict(extra="forbid")


class ToolCall(BaseModel):
    tool_name: str
    request_id: str
    params_as_json: str

    model_config = ConfigDict(extra="forbid")

    @classmethod
    def from_sdk(cls, item: SdkToolCall) -> ToolCall:
        return cls(
            tool_name=item.tool_name,
            request_id=item.request_id,
            params_as_json=item.params_as_json,
        )


class Analysis(BaseModel):
    call_successful: str
    transcript_summary: str
    call_summary_title: str | None = None

    model_config = ConfigDict(extra="forbid")

    @classmethod
    def from_sdk(cls, item: SdkAnalysis) -> Analysis:
        return cls(
            call_successful=str(item.call_successful),
            transcript_summary=item.transcript_summary,
            call_summary_title=item.call_summary_title,
        )


class SimulationResult(BaseModel):
    conversation_id: str | None
    transcript: list[Turn]
    tool_calls: list[ToolCall]
    analysis: Analysis

    model_config = ConfigDict(extra="forbid")


def _agents_side(client: ElevenLabs | None = None) -> AgentsClient:
    cli = get_client() if client is None else client
    return cast(AgentsClient, cli.conversational_ai.agents)


def _turn_to_partial_history_item(turn: SdkTranscriptTurn) -> SdkHistoryInputTurn:
    raw = json.loads(turn.model_dump_json(exclude_none=True))
    try:
        return SdkHistoryInputTurn.model_validate(raw)
    except Exception:
        role = turn.role if turn.role in ("user", "agent") else "agent"
        return SdkHistoryInputTurn(
            role=role,
            message=turn.message,
            time_in_call_secs=turn.time_in_call_secs,
        )


def simulate(
    agent_id: str,
    user_messages: list[str],
    language: str = "en",
    *,
    client: ElevenLabs | None = None,
) -> SimulationResult:
    """Run scripted user turns sequentially by chaining partial conversation histories."""
    agents = _agents_side(client)
    if not user_messages:
        msg = "user_messages must contain at least one message"
        raise ValueError(msg)

    partial_turns: list[SdkHistoryInputTurn] = []
    merged_transcript: list[Turn] = []
    merged_tools: list[ToolCall] = []
    analysis: SdkAnalysis | None = None

    for utterance in user_messages:
        spec = ConversationSimulationSpecification(
            simulated_user_config=AgentConfig(
                first_message=utterance,
                language=language,
                prompt=PromptAgentApiModelOutput(prompt=SIMULATED_USER_PROMPT),
            ),
            partial_conversation_history=list(partial_turns),
        )
        run = agents.simulate_conversation(
            agent_id=agent_id,
            simulation_specification=spec,
            request_options={"timeout_in_seconds": SIMULATION_TIMEOUT_SECONDS},
        )
        analysis = run.analysis
        for line in run.simulated_conversation:
            if line.role in ("user", "agent"):
                role: Literal["user", "agent"] = line.role
                merged_transcript.append(Turn(role=role, message=line.message))
            if line.tool_calls:
                merged_tools.extend(ToolCall.from_sdk(t) for t in line.tool_calls)
            partial_turns.append(_turn_to_partial_history_item(line))

    assert analysis is not None
    return SimulationResult(
        conversation_id=None,
        transcript=merged_transcript,
        tool_calls=merged_tools,
        analysis=Analysis.from_sdk(analysis),
    )
