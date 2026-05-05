"""Unit tests for batch STT ``transcribe``."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from eleven_demo.stt.batch import transcribe


def test_transcribe_opens_file_and_calls_convert(tmp_path: Path) -> None:
    audio_path = tmp_path / "sample.mp3"
    audio_path.write_bytes(b"fake-mp3")
    transcript = MagicMock()

    mock_client = MagicMock()
    mock_client.speech_to_text.convert.return_value = transcript

    with patch("eleven_demo.stt.batch.get_client", return_value=mock_client):
        out = transcribe(
            audio_path,
            language="por",
            model_id="scribe_v2",
            diarize=False,
            tag_audio_events=False,
        )

    assert out is transcript
    mock_client.speech_to_text.convert.assert_called_once()
    kwargs = mock_client.speech_to_text.convert.call_args.kwargs
    assert kwargs["model_id"] == "scribe_v2"
    assert kwargs["language_code"] == "por"
    assert kwargs["diarize"] is False
    assert kwargs["tag_audio_events"] is False
    sent = kwargs["file"]
    assert hasattr(sent, "read")
