---
name: elevenlabs-api-cookbook
description: Production-ready Python snippets for ElevenLabs core APIs (Text-to-Speech, Speech-to-Text, Voices, Voice Cloning, Sound Effects, Music, Voice Isolator audio isolation, Dubbing). Use when the user wants to build a quick demo, prototype a feature, measure latency, stream audio, list or filter voices, clone a voice, transcribe audio, clean/isolate vocals from noisy audio, or test any ElevenAPI endpoint outside of ElevenAgents.
license: MIT
compatibility: Requires the `elevenlabs` Python SDK, network access to `api.elevenlabs.io`, and `ELEVENLABS_API_KEY`.
metadata:
  openclaw:
    requires:
      env:
        - ELEVENLABS_API_KEY
    primaryEnv: ELEVENLABS_API_KEY
---

# ElevenAPI Cookbook

Granular upstream skills maintained by ElevenLabs (installation via `npx skills add`): [github.com/elevenlabs/skills](https://github.com/elevenlabs/skills) (follows [Agent Skills](https://agentskills.io/specification)).

Snippets below use the official Python SDK. **Inside this repository**, prefer `get_client()` from `eleven_demo.client` (`src/eleven_demo/client.py`; retries on 429/5xx); use a bare `ElevenLabs(api_key=...)` only for standalone snippets without project imports.

Non-Python integrations: prefer `@elevenlabs/elevenlabs-js` (`npm install @elevenlabs/elevenlabs-js`). The legacy npm package named `elevenlabs` is an outdated client — do not use.

For uncertainty about model IDs, parameter shapes, or new endpoints, invoke the `elevenlabs-docs` skill first.

## API key setup

1. Create or copy an API key in the [dashboard](https://elevenlabs.io/app/settings/api-keys).
2. In this repo, copy `.env.example` to `.env` and set `ELEVENLABS_API_KEY=` (never commit `.env`).
3. Use `python-dotenv` or load env in your shell before running snippets.

## Setup

```bash
pip install elevenlabs python-dotenv
```

```python
from dotenv import load_dotenv

load_dotenv()

# Preferred in this repository:
from eleven_demo.client import get_client

client = get_client()
```

Standalone (REPL / script outside this repo, no retry wrapper):

```python
import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

load_dotenv()
client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])
```

## Model Quick Reference

Model IDs change. **Always reconfirm** via `client.models.list()` or [`/docs/overview/models`](https://elevenlabs.io/docs/overview/models) before pinning a value in code. Snapshot at time of writing:

| Goal | Model ID | Notes |
|---|---|---|
| Lowest TTS latency | `eleven_flash_v2_5` | ~75ms TTFB, 32 languages, also recommended for Agents |
| Multilingual high quality | `eleven_multilingual_v2` | 29 languages, normalizes numbers/dates well |
| Highest expressivity | `eleven_v3` | 70+ languages, tags, emotions, dialogue (5k char limit) |
| STT batch | `scribe_v2` | 90+ languages, diarization up to 32 speakers, keyterm prompting |
| STT realtime | `scribe_v2_realtime` | ~150ms partial, streaming WebSocket |
| Sound effects | `eleven_text_to_sound_v2` | Current sound-effects model |

> Deprecated / outclassed (per docs): `eleven_turbo_v2_5`, `eleven_turbo_v2` (use Flash equivalents); `scribe_v1` (use `scribe_v2`); `eleven_monolingual_v1`, `eleven_multilingual_v1`.

## Text-to-Speech

### Sync convert (file output)

```python
audio = client.text_to_speech.convert(
    voice_id="JBFqnCBsd6RMkjVDRZzb",
    text="Hello! This is an ElevenLabs multilingual demo.",
    model_id="eleven_multilingual_v2",
    output_format="mp3_44100_128",
)
with open("out.mp3", "wb") as f:
    for chunk in audio:
        f.write(chunk)
```

### Capture cost + request ID from headers

```python
resp = client.text_to_speech.with_raw_response.convert(
    voice_id="JBFqnCBsd6RMkjVDRZzb",
    text="Hello, world!",
    model_id="eleven_flash_v2_5",
)
print("characters:", resp.headers.get("x-character-count"))
print("request_id:", resp.headers.get("request-id"))
```

### HTTP streaming (chunked) — measure TTFB

```python
import time

t0 = time.perf_counter()
ttfb = None
total_bytes = 0
stream = client.text_to_speech.stream(
    voice_id="JBFqnCBsd6RMkjVDRZzb",
    text="Streaming text to speech for low-latency demos.",
    model_id="eleven_flash_v2_5",
    output_format="mp3_22050_32",
)
for chunk in stream:
    if ttfb is None:
        ttfb = time.perf_counter() - t0
    total_bytes += len(chunk)
print(f"TTFB={ttfb*1000:.0f}ms  total={total_bytes}B")
```

### WebSocket TTS (input streaming, true real-time)

Use when you have streaming text from an LLM and want first audio out before the LLM finishes.

```python
import asyncio, json, base64, os, websockets

async def stream_tts():
    voice_id = "JBFqnCBsd6RMkjVDRZzb"
    uri = (
        f"wss://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream-input"
        f"?model_id=eleven_flash_v2_5&output_format=mp3_22050_32"
    )
    async with websockets.connect(uri, additional_headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"]}) as ws:
        await ws.send(json.dumps({"text": " "}))
        for word in "This is a websocket TTS demo for low-latency streaming.".split():
            await ws.send(json.dumps({"text": word + " ", "try_trigger_generation": True}))
        await ws.send(json.dumps({"text": ""}))
        with open("ws_out.mp3", "wb") as f:
            async for raw in ws:
                msg = json.loads(raw)
                if msg.get("audio"):
                    f.write(base64.b64decode(msg["audio"]))
                if msg.get("isFinal"):
                    break

asyncio.run(stream_tts())
```

### Convert with timestamps (for subtitles / lipsync)

```python
result = client.text_to_speech.convert_with_timestamps(
    voice_id="JBFqnCBsd6RMkjVDRZzb",
    text="Hello world.",
    model_id="eleven_multilingual_v2",
)
print(result.alignment.characters[:10], result.alignment.character_start_times_seconds[:10])
```

## Speech-to-Text

### Batch transcription

```python
with open("input.mp3", "rb") as audio_file:
    transcript = client.speech_to_text.convert(
        file=audio_file,
        model_id="scribe_v2",
        language_code="por",
        diarize=True,
        tag_audio_events=True,
    )
print(transcript.text)
for word in transcript.words[:5]:
    print(word.speaker_id, word.text, word.start, word.end)
```

### Realtime STT (microphone-style streaming)

Use for live captions or feeding a custom voice agent.

```python
import asyncio, json, os, websockets

async def stream_stt(audio_chunks_iter):
    uri = "wss://api.elevenlabs.io/v1/speech-to-text/realtime?model_id=scribe_v2_realtime&language_code=por"
    async with websockets.connect(uri, additional_headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"]}) as ws:
        async def sender():
            async for chunk in audio_chunks_iter:
                await ws.send(chunk)
            await ws.send(json.dumps({"type": "EndOfStream"}))

        async def receiver():
            async for raw in ws:
                ev = json.loads(raw)
                if ev.get("type") == "Transcript":
                    print("partial" if ev.get("is_partial") else "final", ev.get("text"))

        await asyncio.gather(sender(), receiver())
```

## Voices

### List voices, filter by language

```python
voices = client.voices.search(page_size=50)
pt_voices = [v for v in voices.voices if "pt" in (v.labels or {}).get("language", "").lower()
             or "portuguese" in (v.labels or {}).get("accent", "").lower()]
for v in pt_voices[:5]:
    print(v.voice_id, v.name, v.labels)
```

### Default settings + per-call override

```python
default = client.voices.settings.get_default()
print(default.stability, default.similarity_boost, default.style)

audio = client.text_to_speech.convert(
    voice_id="JBFqnCBsd6RMkjVDRZzb",
    text="Esta voz está com mais estilo.",
    model_id="eleven_multilingual_v2",
    voice_settings={"stability": 0.4, "similarity_boost": 0.85, "style": 0.6, "use_speaker_boost": True},
)
```

## Voice Cloning

### Instant Voice Cloning (IVC) — seconds, lower fidelity

```python
voice = client.voices.ivc.create(
    name="Demo customer — Demo",
    description="Voz clonada para demo de SAC. Consentimento LGPD coletado.",
    files=[open("sample1.wav", "rb"), open("sample2.wav", "rb")],
)
print("cloned voice_id:", voice.voice_id)
```

Always confirm consent before cloning a real person's voice. ElevenLabs ToS requires it.

### Professional Voice Cloning (PVC) — hours of audio, training pipeline

Reference: `/docs/eleven-api/guides/how-to/voices/professional-voice-cloning`. PVC is multi-step (create → upload samples → train → wait → use).

## Sound Effects

```python
audio = client.text_to_sound_effects.convert(
    text="Heavy rain on a tin roof, thunder rumbling in the distance",
    duration_seconds=8.0,
    prompt_influence=0.4,
)
with open("rain.mp3", "wb") as f:
    for chunk in audio:
        f.write(chunk)
```

## Music

```python
result = client.music.compose(
    prompt="Upbeat bossa nova with light percussion, 90 bpm, 30 seconds",
    music_length_ms=30_000,
)
with open("bossa.mp3", "wb") as f:
    for chunk in result:
        f.write(chunk)
```

## Voice Isolator (audio isolation)

Removes noise and emphasizes speech/vocals from a mixed recording—useful before STT on noisy clips or after field recording.

Supports common containers (MP3, WAV, M4A, FLAC, MP4, etc.). Response streams as MP3 chunks. Optional `file_format="pcm_s16le_16"` for raw 16-bit PCM mono @ 16 kHz (often lower latency). Confirm parameters with the `elevenlabs-docs` skill (`llms.txt` → audio isolation).

```python
with open("noisy.mp3", "rb") as audio_file:
    stream = client.audio_isolation.convert(audio=audio_file)

with open("clean.mp3", "wb") as f:
    for chunk in stream:
        f.write(chunk)
```

Optional PCM path (already-decoded microphone capture):

```python
stream = client.audio_isolation.convert(audio=pcm_bytes, file_format="pcm_s16le_16")
```

Prep for transcription in one flow: run isolation, then feed `clean.mp3` to `speech_to_text.convert(...)`.

## Dubbing (audio/video → other language)

```python
with open("clip_en.mp4", "rb") as f:
    job = client.dubbing.create(
        file=f,
        target_lang="pt",
        source_lang="en",
        watermark=False,
        num_speakers=2,
    )
print("dubbing_id:", job.dubbing_id)

import time
while True:
    status = client.dubbing.get(dubbing_id=job.dubbing_id)
    if status.status == "dubbed":
        break
    if status.status == "failed":
        raise RuntimeError(status.error_message)
    time.sleep(5)

audio = client.dubbing.audio.get(dubbing_id=job.dubbing_id, language_code="pt")
with open("clip_pt.mp4", "wb") as f:
    for chunk in audio:
        f.write(chunk)
```

## Latency Optimization Quick Wins

In order of impact:

1. **Use Flash models** (`eleven_flash_v2_5`) for TTS in latency-sensitive paths
2. **Stream, do not buffer** — use `text_to_speech.stream()` or WebSocket
3. **Lower output format bitrate** — `mp3_22050_32` instead of `mp3_44100_128`
4. **Co-locate** your backend with the ElevenLabs region (US East default)
5. **Pre-warm voices** by hitting `/voices/{id}` once at boot
6. **Avoid SSML / heavy punctuation parsing** for shortest paths
7. **Reuse HTTPS connection** (the SDK does this automatically)

Always benchmark with the TTFB snippet above, do not eyeball.

## Error Handling Pattern

```python
from elevenlabs.core import ApiError

try:
    audio = client.text_to_speech.convert(voice_id="bad", text="x", model_id="eleven_flash_v2_5")
except ApiError as e:
    print("status:", e.status_code, "body:", e.body)
```

Common codes:

- `401` — bad / missing API key
- `402` — quota exhausted (check `client.user.subscription.get()`)
- `422` — validation error (check `body["detail"]`)
- `429` — rate limit (back off, then retry)
