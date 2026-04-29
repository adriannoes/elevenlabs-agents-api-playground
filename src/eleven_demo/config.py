"""Typed application settings loaded from environment variables and optional `.env` file."""

from functools import lru_cache
from typing import Self

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for ElevenLabs demos."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    elevenlabs_api_key: SecretStr = Field(
        ...,
        description="ElevenLabs API key (never log this value).",
    )
    default_pt_voice_id: str | None = None
    default_en_voice_id: str | None = None
    demo_agent_id_telecom: str | None = None
    demo_agent_id_banking: str | None = None
    demo_agent_id_healthcare: str | None = None
    tts_model_id: str = "eleven_flash_v2_5"
    tts_output_format: str = "mp3_22050_32"
    stt_model_id: str = "scribe_v1"
    stt_realtime_model_id: str = "scribe_v2_realtime"
    log_level: str = "INFO"

    @field_validator(
        "default_pt_voice_id",
        "default_en_voice_id",
        "demo_agent_id_telecom",
        "demo_agent_id_banking",
        "demo_agent_id_healthcare",
        mode="before",
    )
    @classmethod
    def empty_optional_str_to_none(cls, value: object) -> str | None:
        if value == "":
            return None
        return value  # type: ignore[return-value]

    @model_validator(mode="after")
    def api_key_must_be_non_empty(self) -> Self:
        raw = self.elevenlabs_api_key.get_secret_value().strip()
        if not raw:
            msg = "ELEVENLABS_API_KEY is required"
            raise ValueError(msg)
        return self


@lru_cache
def get_settings() -> Settings:
    """Return cached settings (singleton per process)."""
    return Settings()
