"""Idempotent Conversational AI agent provisioning helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from elevenlabs.conversational_ai.agents.client import AgentsClient

from eleven_demo.client import get_client

if TYPE_CHECKING:
    from elevenlabs import ElevenLabs

from elevenlabs.types import AgentPlatformSettingsRequestModel, ConversationalConfig
from elevenlabs.types import AgentSummaryResponseModel as AgentSummary
from elevenlabs.types import GetAgentResponseModel as Agent


def _agents(client: ElevenLabs | None = None) -> ElevenLabs:
    if client is None:
        return get_client()
    return client


def _convai_agents(client: ElevenLabs | None = None) -> AgentsClient:
    return cast(AgentsClient, _agents(client).conversational_ai.agents)


def find_agent_by_name(name: str, *, client: ElevenLabs | None = None) -> AgentSummary | None:
    """Return the agent whose name matches exactly, or ``None`` if absent."""
    agents = _convai_agents(client)
    cursor: str | None = None
    while True:
        page = agents.list(page_size=100, search=name, cursor=cursor)
        for summary in page.agents:
            if summary.name == name:
                return summary
        if not page.has_more or page.next_cursor is None:
            return None
        cursor = page.next_cursor


def create_agent(
    name: str,
    conversation_config: ConversationalConfig,
    tags: list[str] | None = None,
    *,
    platform_settings: AgentPlatformSettingsRequestModel | None = None,
    client: ElevenLabs | None = None,
) -> Agent:
    agents = _convai_agents(client)
    create_kwargs: dict[str, Any] = {
        "name": name,
        "conversation_config": conversation_config,
        "tags": tags or [],
    }
    if platform_settings is not None:
        create_kwargs["platform_settings"] = platform_settings
    created = agents.create(**create_kwargs)
    return agents.get(agent_id=created.agent_id)


def update_agent(
    agent_id: str,
    *,
    name: str | None = None,
    conversation_config: ConversationalConfig | None = None,
    platform_settings: AgentPlatformSettingsRequestModel | None = None,
    tags: list[str] | None = None,
    client: ElevenLabs | None = None,
) -> Agent:
    agents = _convai_agents(client)
    patch: dict[str, Any] = {
        "agent_id": agent_id,
        "name": name,
        "conversation_config": conversation_config,
        "tags": tags,
    }
    if platform_settings is not None:
        patch["platform_settings"] = platform_settings
    return agents.update(**patch)


def delete_agent(agent_id: str, *, client: ElevenLabs | None = None) -> None:
    _convai_agents(client).delete(agent_id=agent_id)


def list_agents(*, client: ElevenLabs | None = None) -> list[AgentSummary]:
    """Paginate through all accessible agents and return their summaries."""
    agents = _convai_agents(client)
    out: list[AgentSummary] = []
    cursor: str | None = None
    while True:
        page = agents.list(page_size=100, cursor=cursor)
        out.extend(page.agents)
        if not page.has_more or page.next_cursor is None:
            break
        cursor = page.next_cursor
    return out


def upsert_agent(
    name: str,
    conversation_config: ConversationalConfig,
    *,
    platform_settings: AgentPlatformSettingsRequestModel | None = None,
    client: ElevenLabs | None = None,
) -> Agent:
    """Create the agent if missing, otherwise update configuration in place."""
    existing = find_agent_by_name(name, client=client)
    if existing is None:
        return create_agent(
            name,
            conversation_config,
            platform_settings=platform_settings,
            client=client,
        )
    return update_agent(
        existing.agent_id,
        conversation_config=conversation_config,
        platform_settings=platform_settings,
        client=client,
    )
