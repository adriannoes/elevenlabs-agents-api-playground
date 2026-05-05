"""Voice Library helpers: list voices and filter Portuguese (Brazil) friendly entries."""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eleven_demo.client import get_client


class VoiceCard(BaseModel):
    """Stable view model for Voice Library search results."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    voice_id: str
    name: str
    accent: str = ""
    gender: str = ""
    age: str = ""
    language: str = ""
    preview_url: str = ""
    labels: dict[str, str] = Field(default_factory=dict)


def _normalize_label_dict(raw: dict[str, Any] | None) -> dict[str, str]:
    if not raw:
        return {}
    out: dict[str, str] = {}
    for key, value in raw.items():
        if value is None:
            continue
        out[str(key)] = str(value)
    return out


def _voice_to_card(voice: Any) -> VoiceCard:
    labels_raw = getattr(voice, "labels", None) or {}
    labels = _normalize_label_dict(labels_raw if isinstance(labels_raw, dict) else dict(labels_raw))
    return VoiceCard(
        voice_id=str(getattr(voice, "voice_id", "") or ""),
        name=str(getattr(voice, "name", "") or ""),
        accent=labels.get("accent", ""),
        gender=labels.get("gender", ""),
        age=labels.get("age", ""),
        language=labels.get("language", ""),
        preview_url=str(getattr(voice, "preview_url", "") or ""),
        labels=labels,
    )


def list_voices(*, page_size: int = 100) -> list[VoiceCard]:
    """Return voices from the Voice Library via ``client.voices.search``."""
    client = get_client()
    resp = client.voices.search(page_size=page_size)
    return [_voice_to_card(v) for v in resp.voices]


def _is_pt_br(card: VoiceCard) -> bool:
    lang = card.language.lower()
    accent = card.accent.lower()
    if "pt" in lang:
        return True
    if "portuguese" in lang:
        return True
    if "portuguese" in accent:
        return True
    if "brazil" in accent or "brasil" in accent:
        return True
    return bool(re.search(r"\bpt[-_]?br\b", lang, flags=re.IGNORECASE))


def list_pt_br_voices(*, page_size: int = 100) -> list[VoiceCard]:
    """Return voices whose metadata suggests Brazilian or Portuguese use."""
    return [c for c in list_voices(page_size=page_size) if _is_pt_br(c)]
