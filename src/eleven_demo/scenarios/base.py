"""Shared contract for vertical demo scenarios (Telecom, Banking, Healthcare)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from eleven_demo.agents.tools import TOOLS_REGISTRY
from eleven_demo.config import get_settings

DEFAULT_AGENT_LLM = "gemini-2.5-flash"
DEFAULT_CONVERSATION_TEMPERATURE = 0.3
DEFAULT_TOOL_WEBHOOK_URL = "https://example.com/eleven-demo-tools"

# ElevenAgents rejects some TTS models when ``agent.language`` is English (platform validation).
_CONVAI_EN_TTS_MODEL_IDS = frozenset({"eleven_flash_v2", "eleven_turbo_v2"})
_DEFAULT_EN_AGENT_TTS_MODEL_ID = "eleven_flash_v2"


def convai_tts_model_id_for_language(language: str, configured_model_id: str) -> str:
    """Return TTS ``model_id`` for Convai: English agents may only use flash v2 or turbo v2."""
    primary = (language or "").strip().lower().split("-", maxsplit=1)[0]
    if primary != "en":
        return configured_model_id
    if configured_model_id in _CONVAI_EN_TTS_MODEL_IDS:
        return configured_model_id
    return _DEFAULT_EN_AGENT_TTS_MODEL_ID


class Scenario(BaseModel, ABC):
    """Declarative agent scenario: prompts, voice, tools, KB ids, and rollout hook."""

    name: str = Field(min_length=1)
    system_prompt: str = Field(min_length=1)
    first_message: str = Field(min_length=1)
    language: str = Field(
        default="en",
        min_length=2,
        description="Convai ASR/TTS locale (ISO 639-1 ``en`` for English-only demos).",
    )
    voice_id: str = Field(min_length=1)
    tool_names: list[str] = Field(default_factory=list)
    kb_doc_ids: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)
    agent_llm: str = Field(default=DEFAULT_AGENT_LLM, min_length=1)
    tool_webhook_url: str | None = Field(
        default=None,
        description=(
            "HTTPS POST endpoint for ElevenAgents server tools (defaults to demo placeholder)."
        ),
    )

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("tool_names")
    @classmethod
    def register_known_tools(cls, names: list[str]) -> list[str]:
        unknown = [n for n in names if n not in TOOLS_REGISTRY]
        if unknown:
            msg = f"unknown tool_names (not in TOOLS_REGISTRY): {unknown}"
            raise ValueError(msg)
        return names

    @abstractmethod
    def provision(self) -> str:
        """Create or update the remote agent and return its ``agent_id``."""

    def _resolve_tool_webhook_url(self) -> str:
        if self.tool_webhook_url:
            return self.tool_webhook_url.strip()
        return DEFAULT_TOOL_WEBHOOK_URL

    def _webhook_tool_dicts(self) -> list[dict[str, Any]]:
        url = self._resolve_tool_webhook_url()
        out: list[dict[str, Any]] = []
        for tool_name in self.tool_names:
            inp_model, _out_model, _fn = TOOLS_REGISTRY[tool_name]
            desc = (inp_model.__doc__ or f"Server tool `{tool_name}`.").strip()
            item = {
                "type": "webhook",
                "name": tool_name,
                "description": desc[:2048],
                "api_schema": {
                    "url": url,
                    "method": "POST",
                    "content_type": "application/json",
                    "request_body_schema": _to_elevenlabs_tool_body_schema(inp_model),
                },
            }
            out.append(item)
        return out

    def _build_conversation_config(self) -> dict[str, Any]:
        """Return a dict compatible with ``ConversationalConfig.model_validate``."""
        settings = get_settings()
        prompt_block: dict[str, Any] = {
            "prompt": self.system_prompt,
            "llm": self.agent_llm,
            "temperature": DEFAULT_CONVERSATION_TEMPERATURE,
        }
        tools_payload = self._webhook_tool_dicts()
        if tools_payload:
            prompt_block["tools"] = tools_payload
        if self.kb_doc_ids:
            prompt_block["knowledge_base"] = [
                {
                    "type": "file",
                    "id": doc_id,
                    "name": doc_id,
                    "usage_mode": "auto",
                }
                for doc_id in self.kb_doc_ids
            ]
        return {
            "agent": {
                "first_message": self.first_message,
                "language": self.language,
                "prompt": prompt_block,
            },
            "tts": {
                "voice_id": self.voice_id,
                "model_id": convai_tts_model_id_for_language(self.language, settings.tts_model_id),
            },
        }


def _to_elevenlabs_tool_body_schema(model: type[BaseModel]) -> dict[str, Any]:
    """Convert a Pydantic model into the Agents webhook schema subset."""
    raw = model.model_json_schema()
    required = list(raw.get("required", []))
    properties: dict[str, Any] = {}
    for name, schema in raw.get("properties", {}).items():
        prop = _literal_tool_property(name, schema)
        if prop is not None:
            properties[name] = prop
    return {
        "type": "object",
        "required": required,
        "properties": properties,
    }


def _literal_tool_property(name: str, schema: dict[str, Any]) -> dict[str, Any] | None:
    """Return a literal property schema accepted by ElevenLabs webhook tools."""
    source = _first_non_null_schema(schema)
    raw_type = source.get("type")
    if raw_type not in {"boolean", "string", "integer", "number"}:
        return None
    description = (
        source.get("description") or schema.get("description") or source.get("title") or name
    )
    prop: dict[str, Any] = {
        "type": raw_type,
        "description": description,
    }
    enum = source.get("enum")
    if isinstance(enum, list):
        prop["enum"] = [str(item) for item in enum]
    return prop


def _first_non_null_schema(schema: dict[str, Any]) -> dict[str, Any]:
    variants = schema.get("anyOf")
    if isinstance(variants, list):
        for item in variants:
            if isinstance(item, dict) and item.get("type") != "null":
                return item
    return schema
