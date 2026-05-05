#!/usr/bin/env python3
"""CLI: synthesize speech and print billing metadata (rich panel)."""

from __future__ import annotations

import argparse
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from eleven_demo.config import get_settings
from eleven_demo.tts.sync import synthesize


def main() -> None:
    parser = argparse.ArgumentParser(description="ElevenLabs TTS demo (sync HTTP).")
    parser.add_argument("text", help="Text to synthesize")
    parser.add_argument("--voice-id", dest="voice_id", default=None, help="Override voice_id")
    parser.add_argument("--out", default="out.mp3", help="Output audio path")
    args = parser.parse_args()

    settings = get_settings()
    voice_id = args.voice_id or settings.default_pt_voice_id
    if not voice_id:
        msg = "Pass --voice-id or set DEFAULT_PT_VOICE_ID in the environment."
        raise SystemExit(msg)

    audio, meta = synthesize(
        args.text,
        voice_id=voice_id,
        model_id=settings.tts_model_id,
        output_format=settings.tts_output_format,
    )

    outp = Path(args.out)
    outp.write_bytes(audio)

    console = Console()
    body = (
        f"[bold]request_id[/bold]  {meta.get('request_id', '')}\n"
        f"[bold]character_count[/bold]  {meta.get('character_count', 0)}\n"
        f"[bold]voice_id[/bold]  {voice_id}\n"
        f"[bold]model_id[/bold]  {meta.get('model_id', settings.tts_model_id)}\n"
        f"[bold]output[/bold]  {outp.resolve()}"
    )
    console.print(Panel(body, title="TTS", expand=False))


if __name__ == "__main__":
    main()
