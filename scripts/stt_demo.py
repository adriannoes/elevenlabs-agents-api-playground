#!/usr/bin/env python3
"""CLI: batch transcribe an audio file and print words (diarization table)."""

from __future__ import annotations

import argparse
from pathlib import Path

from elevenlabs.types.multichannel_speech_to_text_response_model import (
    MultichannelSpeechToTextResponseModel,
)
from elevenlabs.types.speech_to_text_chunk_response_model import SpeechToTextChunkResponseModel
from rich.console import Console
from rich.table import Table

from eleven_demo.stt.batch import transcribe


def _extract_words(result: object) -> list[object]:
    if isinstance(result, SpeechToTextChunkResponseModel):
        return list(result.words)
    if isinstance(result, MultichannelSpeechToTextResponseModel):
        words: list[object] = []
        for chunk in result.transcripts:
            words.extend(chunk.words)
        return words
    return []


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch STT demo (ElevenLabs).")
    parser.add_argument("audio_path", type=Path)
    args = parser.parse_args()

    path: Path = args.audio_path
    if not path.is_file():
        msg = f"Audio not found: {path}"
        raise SystemExit(msg)

    result = transcribe(path)
    text = getattr(result, "text", "") or ""
    if not text and isinstance(result, MultichannelSpeechToTextResponseModel):
        text = " ".join(t.text for t in result.transcripts)

    words = _extract_words(result)

    console = Console()
    console.print(text)

    table = Table(title="Words (first 20)", show_lines=False)
    table.add_column("speaker_id")
    table.add_column("start", justify="right")
    table.add_column("end", justify="right")
    table.add_column("word")

    for w in words[:20]:
        table.add_row(
            str(getattr(w, "speaker_id", "") or ""),
            f"{getattr(w, 'start', None) or 0:.3f}",
            f"{getattr(w, 'end', None) or 0:.3f}",
            str(getattr(w, "text", "")),
        )
    console.print(table)


if __name__ == "__main__":
    main()
