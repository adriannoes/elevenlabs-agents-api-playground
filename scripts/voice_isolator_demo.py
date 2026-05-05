#!/usr/bin/env python3
"""CLI: isolate speech from noisy audio and write a cleaned MP3."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from elevenlabs.core import ApiError
from rich.console import Console
from rich.panel import Panel

from eleven_demo.client import get_client


def main() -> None:
    """Run the Voice Isolator demo CLI."""
    parser = argparse.ArgumentParser(description="ElevenLabs Voice Isolator demo.")
    parser.add_argument("audio_path", type=Path, help="Input noisy audio file")
    parser.add_argument("--out", default="clean.mp3", help="Output cleaned MP3 path")
    parser.add_argument(
        "--file-format",
        choices=["other", "pcm_s16le_16"],
        default="other",
        help="Input audio format hint for the Voice Isolator API",
    )
    args = parser.parse_args()

    input_path: Path = args.audio_path
    if not input_path.is_file():
        msg = f"Audio not found: {input_path}"
        raise SystemExit(msg)

    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    input_bytes = input_path.stat().st_size
    client = get_client()
    started = time.perf_counter()
    output_bytes = 0

    try:
        with input_path.open("rb") as audio_file, output_path.open("wb") as output_file:
            stream = client.audio_isolation.convert(
                audio=audio_file,
                file_format=args.file_format,
            )
            for chunk in stream:
                output_file.write(chunk)
                output_bytes += len(chunk)
    except ApiError as exc:
        if output_path.exists() and output_bytes == 0:
            output_path.unlink()
        msg = f"Voice Isolator failed: {exc.status_code} {exc.body}"
        raise SystemExit(msg) from exc

    elapsed_seconds = time.perf_counter() - started

    body = (
        f"[bold]input[/bold]  {input_path.resolve()}\n"
        f"[bold]output[/bold]  {output_path.resolve()}\n"
        f"[bold]file_format[/bold]  {args.file_format}\n"
        f"[bold]input_bytes[/bold]  {input_bytes}\n"
        f"[bold]output_bytes[/bold]  {output_bytes}\n"
        f"[bold]elapsed_seconds[/bold]  {elapsed_seconds:.2f}\n"
        f"[bold]next_step[/bold]  uv run python scripts/stt_demo.py {output_path}"
    )
    Console().print(Panel(body, title="Voice Isolator", expand=False))


if __name__ == "__main__":
    main()
