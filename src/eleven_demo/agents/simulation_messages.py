"""Load user turn strings from a JSON file for agent conversation simulation."""

from __future__ import annotations

import json
from pathlib import Path


def load_user_messages_from_json_file(path: Path) -> list[str]:
    """Parse a JSON file into an ordered list of simulated user messages.

    The file must contain a JSON array of strings, for example:
    ``["First user turn.", "Second turn."]``.

    Args:
        path: UTF-8 JSON file path.

    Returns:
        Non-empty list of user message strings.

    Raises:
        ValueError: If the JSON is not an array of non-empty trimmed strings.
        OSError: If the file cannot be read.
    """
    raw = path.read_text(encoding="utf-8")
    return parse_user_messages_json(raw)


def parse_user_messages_json(raw: str) -> list[str]:
    """Parse JSON text into user messages (used by tests without touching disk).

    Args:
        raw: JSON document body.

    Returns:
        Non-empty list of trimmed, non-empty user strings.

    Raises:
        ValueError: If the structure is invalid.
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {exc}") from exc

    if not isinstance(data, list):
        raise ValueError("JSON root must be an array of strings")

    messages: list[str] = []
    for i, item in enumerate(data):
        if not isinstance(item, str):
            raise ValueError(f"Item at index {i} must be a string, got {type(item).__name__}")
        text = item.strip()
        if not text:
            raise ValueError(f"Item at index {i} must be a non-empty string after strip()")
        messages.append(text)

    if not messages:
        raise ValueError("JSON array must contain at least one user message")

    return messages
