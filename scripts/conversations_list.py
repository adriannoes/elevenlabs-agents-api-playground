#!/usr/bin/env python3
"""CLI: list recent ElevenAgents conversations without running a webhook receiver."""

from __future__ import annotations

import argparse
import re

from elevenlabs.core import ApiError
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from eleven_demo.client import get_client
from eleven_demo.config import Settings, get_settings

_AGENT_FIELD: dict[str, str] = {
    "telecom": "demo_agent_id_telecom",
    "banking": "demo_agent_id_banking",
    "healthcare": "demo_agent_id_healthcare",
}

_ENV_HINT: dict[str, str] = {
    "telecom": "DEMO_AGENT_ID_TELECOM",
    "banking": "DEMO_AGENT_ID_BANKING",
    "healthcare": "DEMO_AGENT_ID_HEALTHCARE",
}

_REDACTION_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"), "[CPF]"),
    (re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b"), "[EMAIL]"),
    (re.compile(r"(?<!\+)\b(?:\d[ -]?){13,19}\b"), "[CARD]"),
    (re.compile(r"(?:\+?55\s*)?(?:\(?\d{2}\)?\s*)?9?\d{4}[-\s]?\d{4}"), "[PHONE]"),
)


def redact_sensitive_text(value: str) -> str:
    """Redact common Brazilian PII patterns from display text."""
    out = value
    for pattern, replacement in _REDACTION_PATTERNS:
        out = pattern.sub(replacement, out)
    return out


def _resolve_agent_id(settings: Settings, scenario: str) -> str:
    field = _AGENT_FIELD[scenario]
    raw = getattr(settings, field)
    if raw is None or not str(raw).strip():
        env = _ENV_HINT[scenario]
        msg = (
            f"Missing {env}. Run provisioning and paste the printed id into .env:\n"
            f"  uv run python scripts/agent_create.py {scenario}"
        )
        raise SystemExit(msg)
    return str(raw).strip()


def _safe_text(value: object, *, limit: int = 140) -> str:
    text = "" if value is None else str(value)
    redacted = redact_sensitive_text(text).replace("\n", " ").strip()
    if len(redacted) > limit:
        return f"{redacted[: limit - 1]}…"
    return redacted


def _conversation_attr(item: object, name: str, default: object = "") -> object:
    return getattr(item, name, default)


def _print_conversation_table(conversations: list[object]) -> None:
    table = Table(title="Recent conversations (redacted summary)")
    table.add_column("conversation_id")
    table.add_column("agent")
    table.add_column("status")
    table.add_column("success")
    table.add_column("duration", justify="right")
    table.add_column("messages", justify="right")
    table.add_column("summary")

    for item in conversations:
        table.add_row(
            _safe_text(_conversation_attr(item, "conversation_id")),
            _safe_text(_conversation_attr(item, "agent_name")),
            _safe_text(_conversation_attr(item, "status")),
            _safe_text(_conversation_attr(item, "call_successful")),
            str(_conversation_attr(item, "call_duration_secs", "") or ""),
            str(_conversation_attr(item, "message_count", "") or ""),
            _safe_text(_conversation_attr(item, "transcript_summary")),
        )
    Console().print(table)


def _print_conversation_detail(detail: object) -> None:
    analysis = getattr(detail, "analysis", None)
    lines = [
        f"[bold]conversation_id[/bold]  {_safe_text(getattr(detail, 'conversation_id', ''))}",
        f"[bold]agent[/bold]  {_safe_text(getattr(detail, 'agent_name', ''))}",
        f"[bold]status[/bold]  {_safe_text(getattr(detail, 'status', ''))}",
    ]
    if analysis is not None:
        call_successful = _safe_text(getattr(analysis, "call_successful", ""))
        title = _safe_text(getattr(analysis, "call_summary_title", ""))
        lines.extend(
            [
                "",
                f"[bold]call_successful[/bold]  {call_successful}",
                f"[bold]title[/bold]  {title}",
                "",
                "[bold]transcript_summary[/bold]",
                _safe_text(getattr(analysis, "transcript_summary", ""), limit=500),
            ]
        )
    Console().print(Panel("\n".join(lines), title="Conversation detail", expand=False))


def main() -> None:
    """Run the conversations CLI."""
    parser = argparse.ArgumentParser(
        description="List or inspect recent ElevenAgents conversations with redacted output.",
    )
    parser.add_argument("scenario", nargs="?", choices=sorted(_AGENT_FIELD), help="Demo scenario")
    parser.add_argument("--id", dest="conversation_id", help="Fetch one conversation by id")
    parser.add_argument("--page-size", type=int, default=10, help="Number of conversations to list")
    args = parser.parse_args()

    conversations = get_client().conversational_ai.conversations
    try:
        if args.conversation_id:
            detail = conversations.get(conversation_id=args.conversation_id)
            _print_conversation_detail(detail)
            return

        if args.scenario is None:
            msg = "Pass a scenario (telecom|banking|healthcare) or --id <conversation_id>."
            raise SystemExit(msg)

        agent_id = _resolve_agent_id(get_settings(), args.scenario)
        page = conversations.list(agent_id=agent_id, page_size=args.page_size)
        _print_conversation_table(list(getattr(page, "conversations", [])))
    except ApiError as exc:
        msg = f"Conversations API failed: {exc.status_code} {exc.body}"
        raise SystemExit(msg) from exc


if __name__ == "__main__":
    main()
