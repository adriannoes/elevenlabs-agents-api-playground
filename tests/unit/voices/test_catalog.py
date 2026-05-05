"""Unit tests for Voice Library catalog (mocked SDK)."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from eleven_demo.voices.catalog import VoiceCard, list_pt_br_voices, list_voices

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch


def test_list_voices_maps_sdk_voice_to_voice_card(monkeypatch: MonkeyPatch) -> None:
    v = MagicMock()
    v.voice_id = "vid-1"
    v.name = "Test Voice"
    v.preview_url = "https://example.com/p.mp3"
    v.labels = {"language": "pt", "accent": "brazilian", "gender": "female", "age": "young"}

    mock_resp = MagicMock()
    mock_resp.voices = [v]

    mock_client = MagicMock()
    mock_client.voices.search.return_value = mock_resp
    monkeypatch.setattr("eleven_demo.voices.catalog.get_client", lambda: mock_client)

    cards = list_voices(page_size=50)
    assert len(cards) == 1
    assert cards[0] == VoiceCard(
        voice_id="vid-1",
        name="Test Voice",
        accent="brazilian",
        gender="female",
        age="young",
        language="pt",
        preview_url="https://example.com/p.mp3",
        labels={
            "language": "pt",
            "accent": "brazilian",
            "gender": "female",
            "age": "young",
        },
    )
    mock_client.voices.search.assert_called_once_with(page_size=50)


def test_list_pt_br_voices_filters_by_language_or_accent(monkeypatch: MonkeyPatch) -> None:
    pt = MagicMock()
    pt.voice_id = "a"
    pt.name = "BR"
    pt.preview_url = ""
    pt.labels = {"language": "pt", "accent": "brazilian"}

    en = MagicMock()
    en.voice_id = "b"
    en.name = "US"
    en.preview_url = ""
    en.labels = {"language": "en", "accent": "american"}

    pt_accent_only = MagicMock()
    pt_accent_only.voice_id = "c"
    pt_accent_only.name = "PT accent"
    pt_accent_only.preview_url = ""
    pt_accent_only.labels = {"language": "en", "accent": "portuguese"}

    mock_resp = MagicMock()
    mock_resp.voices = [pt, en, pt_accent_only]

    mock_client = MagicMock()
    mock_client.voices.search.return_value = mock_resp
    monkeypatch.setattr("eleven_demo.voices.catalog.get_client", lambda: mock_client)

    got = list_pt_br_voices(page_size=100)
    assert [c.voice_id for c in got] == ["a", "c"]


def test_list_pt_br_voices_accepts_brazilian_accent_labels(monkeypatch: MonkeyPatch) -> None:
    br = MagicMock()
    br.voice_id = "br"
    br.name = "Brazilian"
    br.preview_url = ""
    br.labels = {"language": "en", "accent": "Brazilian"}

    mock_resp = MagicMock()
    mock_resp.voices = [br]

    mock_client = MagicMock()
    mock_client.voices.search.return_value = mock_resp
    monkeypatch.setattr("eleven_demo.voices.catalog.get_client", lambda: mock_client)

    got = list_pt_br_voices(page_size=100)

    assert [c.voice_id for c in got] == ["br"]
