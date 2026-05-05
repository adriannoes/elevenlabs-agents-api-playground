"""Unit tests for conversational agent factory helpers."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from elevenlabs.types import (
    AgentPlatformSettingsRequestModel,
    ConversationalConfig,
    PrivacyConfigInput,
)

from eleven_demo.agents import factory


def test_find_agent_by_name_returns_exact_match() -> None:
    summary = MagicMock()
    summary.agent_id = "aid1"
    summary.name = "exact-name"
    page = MagicMock()
    page.agents = [summary]
    page.has_more = False
    page.next_cursor = None

    mock_client = MagicMock()
    mock_client.conversational_ai.agents.list.return_value = page

    found = factory.find_agent_by_name("exact-name", client=mock_client)

    assert found is summary


def test_find_agent_by_name_ignores_similar_names() -> None:
    other = MagicMock()
    other.agent_id = "x"
    other.name = "exact-name-staging"
    page = MagicMock()
    page.agents = [other]
    page.has_more = False
    page.next_cursor = None
    mock_client = MagicMock()
    mock_client.conversational_ai.agents.list.return_value = page

    assert factory.find_agent_by_name("exact-name", client=mock_client) is None


def test_create_agent_fetches_full_record() -> None:
    created = MagicMock()
    created.agent_id = "new-id"
    fetched = MagicMock(agent_id="new-id", name="demo")

    agents = MagicMock()
    agents.create.return_value = created
    agents.get.return_value = fetched

    mock_client = MagicMock()
    mock_client.conversational_ai.agents = agents

    cfg = ConversationalConfig()
    out = factory.create_agent("demo", cfg, tags=["x"], client=mock_client)

    assert out is fetched
    agents.get.assert_called_once_with(agent_id="new-id")


def test_upsert_agent_updates_existing() -> None:
    existing = MagicMock(agent_id="exist-id", name="demo-name")
    updated = MagicMock(agent_id="exist-id", name="demo-name")

    agents = MagicMock()
    agents.update.return_value = updated

    mock_client = MagicMock()
    mock_client.conversational_ai.agents = agents

    cfg = ConversationalConfig()
    with patch.object(factory, "find_agent_by_name", return_value=existing):
        out = factory.upsert_agent("demo-name", cfg, client=mock_client)

    assert out is updated
    agents.update.assert_called_once()
    agents.create.assert_not_called()


def test_upsert_agent_creates_when_missing() -> None:
    agents = MagicMock()
    agents.create.return_value = MagicMock(agent_id="fresh")
    agents.get.return_value = MagicMock(agent_id="fresh", name="solo")

    mock_client = MagicMock()
    mock_client.conversational_ai.agents = agents

    cfg = ConversationalConfig()
    with patch.object(factory, "find_agent_by_name", return_value=None):
        factory.upsert_agent("solo", cfg, client=mock_client)

    agents.create.assert_called_once()
    agents.update.assert_not_called()


def test_upsert_agent_passes_platform_settings_to_create() -> None:
    ps = AgentPlatformSettingsRequestModel(privacy=PrivacyConfigInput(zero_retention_mode=True))
    agents = MagicMock()
    agents.create.return_value = MagicMock(agent_id="new-zrm")
    agents.get.return_value = MagicMock(agent_id="new-zrm")

    mock_client = MagicMock()
    mock_client.conversational_ai.agents = agents

    cfg = ConversationalConfig()
    with patch.object(factory, "find_agent_by_name", return_value=None):
        factory.upsert_agent("zrm-demo", cfg, platform_settings=ps, client=mock_client)

    agents.create.assert_called_once()
    assert agents.create.call_args.kwargs["platform_settings"] is ps


def test_upsert_agent_passes_platform_settings_to_update() -> None:
    ps = AgentPlatformSettingsRequestModel(privacy=PrivacyConfigInput(zero_retention_mode=True))
    existing = MagicMock(agent_id="exist-zrm", name="zrm-demo")
    updated = MagicMock(agent_id="exist-zrm")

    agents = MagicMock()
    agents.update.return_value = updated

    mock_client = MagicMock()
    mock_client.conversational_ai.agents = agents

    cfg = ConversationalConfig()
    with patch.object(factory, "find_agent_by_name", return_value=existing):
        factory.upsert_agent("zrm-demo", cfg, platform_settings=ps, client=mock_client)

    agents.update.assert_called_once()
    assert agents.update.call_args.kwargs["platform_settings"] is ps


def test_find_agent_by_name_follows_cursor_until_match() -> None:
    wrong = MagicMock()
    wrong.agent_id = "w"
    wrong.name = "other"
    hit = MagicMock()
    hit.agent_id = "h"
    hit.name = "target"

    page1 = MagicMock(agents=[wrong], has_more=True, next_cursor="c1")
    page2 = MagicMock(agents=[hit], has_more=False, next_cursor=None)

    agents = MagicMock()
    agents.list.side_effect = [page1, page2]

    mock_client = MagicMock()
    mock_client.conversational_ai.agents = agents

    assert factory.find_agent_by_name("target", client=mock_client) is hit
    assert agents.list.call_count == 2


def test_list_agents_collects_multiple_pages() -> None:
    a = MagicMock(agent_id="1")
    b = MagicMock(agent_id="2")
    page1 = MagicMock(agents=[a], has_more=True, next_cursor="next")
    page2 = MagicMock(agents=[b], has_more=False, next_cursor=None)

    agents = MagicMock()
    agents.list.side_effect = [page1, page2]

    mock_client = MagicMock()
    mock_client.conversational_ai.agents = agents

    out = factory.list_agents(client=mock_client)

    assert out == [a, b]
    assert agents.list.call_count == 2


def test_delete_agent_calls_sdk_delete() -> None:
    agents = MagicMock()
    mock_client = MagicMock()
    mock_client.conversational_ai.agents = agents

    factory.delete_agent("to-remove", client=mock_client)

    agents.delete.assert_called_once_with(agent_id="to-remove")


def test_create_agent_omits_platform_settings_when_none() -> None:
    created = MagicMock(agent_id="n1")
    fetched = MagicMock(agent_id="n1", name="n")

    agents = MagicMock()
    agents.create.return_value = created
    agents.get.return_value = fetched

    mock_client = MagicMock()
    mock_client.conversational_ai.agents = agents

    factory.create_agent("n", ConversationalConfig(), client=mock_client)

    assert "platform_settings" not in agents.create.call_args.kwargs
