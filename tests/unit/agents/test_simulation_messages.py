"""Tests for JSON simulation message loading."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from eleven_demo.agents.simulation_messages import (
    load_user_messages_from_json_file,
    parse_user_messages_json,
)


def test_parse_accepted_array(tmp_path: Path) -> None:
    path = tmp_path / "m.json"
    path.write_text(
        json.dumps(["  first  ", "second"]),
        encoding="utf-8",
    )
    assert load_user_messages_from_json_file(path) == ["first", "second"]


def test_parse_invalid_json() -> None:
    with pytest.raises(ValueError, match="Invalid JSON"):
        parse_user_messages_json("{ not json")


def test_parse_not_array() -> None:
    with pytest.raises(ValueError, match="array"):
        parse_user_messages_json('{"messages": ["a"]}')


def test_parse_empty_array() -> None:
    with pytest.raises(ValueError, match="at least one"):
        parse_user_messages_json("[]")


def test_parse_non_string_element() -> None:
    with pytest.raises(ValueError, match="index 1"):
        parse_user_messages_json('["ok", 3]')


def test_parse_empty_string_element() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        parse_user_messages_json('["ok", "   "]')
