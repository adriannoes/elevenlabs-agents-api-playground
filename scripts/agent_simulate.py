#!/usr/bin/env python3
"""CLI: run ElevenAgents conversation simulation against a demo agent id from settings."""

from __future__ import annotations

import argparse

from rich.console import Console
from rich.panel import Panel

from eleven_demo.agents import simulate
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


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Simulate one user turn against a demo agent (reads DEMO_AGENT_ID_*).",
    )
    parser.add_argument(
        "scenario",
        choices=("telecom", "banking", "healthcare"),
        help="Which DEMO_AGENT_ID_* env var to use.",
    )
    parser.add_argument(
        "message",
        help="Single simulated user utterance (quote if it contains spaces).",
    )
    parser.add_argument(
        "--language",
        default="en",
        help="Simulated user language tag (default: en).",
    )
    args = parser.parse_args()

    settings = get_settings()
    agent_id = _resolve_agent_id(settings, args.scenario)

    result = simulate(agent_id, [args.message], language=args.language)

    lines: list[str] = [
        f"[bold]agent_id[/bold]  {agent_id}",
        "",
        f"[bold]call_successful[/bold]  {result.analysis.call_successful}",
    ]
    if result.analysis.call_summary_title:
        lines.extend(("", f"[bold]title[/bold]  {result.analysis.call_summary_title}"))
    lines.extend(
        (
            "",
            "[bold]transcript_summary[/bold]",
            result.analysis.transcript_summary,
        ),
    )
    if result.transcript:
        lines.append("")
        lines.append("[bold]transcript[/bold]")
        for i, turn in enumerate(result.transcript, start=1):
            role = turn.role.upper()
            text = turn.message if turn.message is not None else ""
            lines.append(f"  {i}. [{role}] {text}")
    if result.tool_calls:
        lines.append("")
        lines.append("[bold]tool_calls[/bold]")
        for tc in result.tool_calls:
            lines.append(f"  • {tc.tool_name}  ({tc.request_id})")
    body = "\n".join(lines)
    Console().print(Panel(body, title="Simulate", expand=False))


if __name__ == "__main__":
    main()
