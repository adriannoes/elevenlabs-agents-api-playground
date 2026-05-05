#!/usr/bin/env python3
"""CLI: list Voice Library entries filtered for Portuguese / Brazil."""

from __future__ import annotations

import argparse

from rich.console import Console
from rich.table import Table

from eleven_demo.voices.catalog import list_pt_br_voices, list_voices


def main() -> None:
    parser = argparse.ArgumentParser(
        description="List Voice Library voices filtered for Portuguese / Brazil.",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=100,
        help="Page size for voices.search (default: 100).",
    )
    args = parser.parse_args()

    voices = sorted(list_pt_br_voices(page_size=args.page_size), key=lambda v: v.name.lower())
    fallback_used = False
    if not voices:
        fallback_used = True
        voices = sorted(
            list_voices(page_size=min(args.page_size, 10)),
            key=lambda v: v.name.lower(),
        )
    table = Table(title="PT-BR-friendly voices (Voice Library)")
    table.add_column("voice_id")
    table.add_column("name")
    table.add_column("accent")
    table.add_column("gender")
    table.add_column("age")
    table.add_column("preview_url")

    for v in voices:
        table.add_row(
            v.voice_id,
            v.name,
            v.accent,
            v.gender,
            v.age,
            v.preview_url,
        )

    console = Console()
    if fallback_used:
        console.print(
            "[yellow]No PT-BR-labelled voices found. Showing a small Voice Library sample; "
            "set DEFAULT_PT_VOICE_ID manually or pass --voice-id in scripts.[/yellow]"
        )
    console.print(table)


if __name__ == "__main__":
    main()
