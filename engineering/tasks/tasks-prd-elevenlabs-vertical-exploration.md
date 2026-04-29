# Task List — ElevenLabs Vertical Exploration

**Source PRD**: [product/prd/prd-elevenlabs-vertical-exploration.md](../../product/prd/prd-elevenlabs-vertical-exploration.md)

## Relevant Files

- `src/eleven_demo/__init__.py` — Package marker.
- `src/eleven_demo/{tts,stt,voices,agents,metrics,scenarios}/__init__.py` — Package markers (subpackages). (Task 1.1)
- `tests/__init__.py`, `tests/unit/__init__.py`, `tests/integration/__init__.py` — Test package markers. (Task 1.1)
- `src/eleven_demo/client.py` — ElevenLabs factory with `_with_retry` + `httpx.Client` subclass; `timeout=30`. (Tasks 1.3 / 1.6)
- `tests/unit/test_client.py` — Unit tests for `_with_retry`. (Tasks 1.3 / 1.6)
- `src/eleven_demo/config.py` — pydantic-settings loading from `.env`; Task 3.7 extends it with optional OpenAI benchmark settings. (Tasks 1.2 / 1.5 / 3.7)
- `tests/unit/test_config.py` — Unit tests for `Settings` / `get_settings`. (Tasks 1.2 / 1.5)
- `tests/unit/tts/test_sync.py` — Unit tests for `synthesize` / `with_raw_response` metadata. (Task 2.1)
- `tests/unit/tts/test_stream.py` — Unit tests for HTTP `stream()` + TTFB (mocked `perf_counter`). (Task 2.2)
- `tests/unit/tts/test_ws.py` — Unit tests for WebSocket `ws_stream` (mocked connect + async recv). (Task 2.3)
- `src/eleven_demo/tts/{sync,stream,ws}.py` — TTS: HTTP sync, HTTP chunked, WebSocket input-stream (`ws_stream`). `tts/__init__.py` exposes `synthesize` only. (Task 2)
- `src/eleven_demo/stt/{__init__,batch,realtime,types}.py` — STT surfaces: batch and realtime WebSocket; shared transcript/event types. (Task 2)
- `src/eleven_demo/stt/types.py` — Re-exports SDK batch types + `TranscriptEvent` for realtime WebSocket. (Tasks 2.4 / 2.5)
- `src/eleven_demo/stt/batch.py` — `transcribe()` wraps `speech_to_text.convert` with PT-BR-friendly defaults. (Task 2.4)
- `src/eleven_demo/stt/realtime.py` — `realtime_transcribe()` streams PCM chunks over `wss://…/v1/speech-to-text/realtime`. (Task 2.5)
- `tests/unit/stt/test_realtime.py` — Mocked `websockets.connect` tests for realtime STT. (Task 2.5)
- `tests/integration/stt/test_batch.py` — VCR integration test for batch STT on `data/samples/hello-pt-br.mp3`. (Tasks 2.4 / 2.7)
- `tests/integration/tts/test_integration_sync.py` — VCR integration test for synchronous TTS + character billing metadata. (Task 2.6)
- `tests/integration/tts/test_integration_stream.py` — VCR integration test for chunked HTTP streaming TTS + TTFB. (Task 2.6)
- `tests/integration/tts/cassettes/*.yaml` — VCR cassettes for TTS integration tests (sanitized). (Task 2.6)
- `data/samples/hello-pt-br.mp3` — PT-BR phrase audio for batch STT integration (generated via project TTS). (Tasks 2.4 / 2.7)
- `src/eleven_demo/voices/{__init__,catalog}.py` — Voice Library helper with PT-BR filter. (Task 3)
- `src/eleven_demo/metrics/{__init__,latency}.py` — TTFB decorator and `LatencyReport`. (Task 3)
- `scripts/{tts_demo,tts_stream_ttfb,stt_demo,voices_pt_br}.py` — CLI exploration entry points. (Task 3)
- `src/eleven_demo/benchmarks/{__init__,openai_tts,tts_vendor}.py` — Optional vendor benchmark adapters and report models for ElevenLabs vs OpenAI TTS. (Task 3.7–3.11)
- `tests/unit/benchmarks/{test_openai_tts,test_tts_vendor}.py` — Mocked tests for vendor benchmark behavior. (Task 3.7–3.11)
- `scripts/tts_vendor_benchmark.py` — CLI that compares ElevenLabs Flash v2.5 vs OpenAI `gpt-4o-mini-tts` streaming TTFB. (Task 3.10)
- `src/eleven_demo/agents/{__init__,factory,tools,kb,simulate}.py` — ElevenAgents core. (Task 4)
- `src/eleven_demo/scenarios/{__init__,telecom,banking,healthcare}.py` — Vertical configs + `provision()`. (Task 5)
- `scripts/{agent_create,agent_simulate,conversations_list}.py` — CLI for agent provisioning, regression checks, and optional conversation listing (post-call exploration without a webhook receiver). (Task 5 / Task 7)
- `apps/gradio_app.py` — Multi-vertical playground. (Task 6)
- `apps/ws_bridge/{__init__,main}.py` — FastAPI WebSocket proxy (stretch). (Task 6)
- `docs/walkthrough.md` — Guided tour through every demo for anyone exploring the repo. (Task 7)
- `docs/scenarios/{telecom,banking,healthcare}.md` — Per-vertical storytelling. (Task 7)
- `docs/benchmarks/tts-vendor-comparison.md` — Methodology and results template for the ElevenLabs vs OpenAI TTS benchmark. (Task 7.7)
- `docs/reports/technical-exploration-report.md` — Human-readable technical-strategy report for the full exploration. (Task 7.8)
- `scripts/generate_evidence_report.py` — Optional helper that assembles test, coverage, and benchmark artifacts into the report. (Task 8.1)
- `artifacts/reports/` — Generated JUnit, coverage, pre-commit, and report-support artifacts. (Task 8.1)
- `artifacts/benchmarks/tts-vendor-latest.json` — Generated vendor benchmark report. (Task 3.10 / Task 8.1)
- `data/kb/healthcare/*.md` — Knowledge base seed files for the Healthcare scenario. (Task 5)
- `tests/conftest.py` — Shared fixtures: integration skip without API key when no cassette, `mock_eleven_client`, `clear_settings_cache`. (Task 1.4)
- `tests/unit/...` — Mocked unit tests mirroring `src/eleven_demo/`.
- `tests/integration/**/cassettes/*.yaml` — VCR cassettes beside integration test modules (pytest-vcr layout; committed, sanitized).

### Notes

- Unit tests live under `tests/unit/` mirroring `src/eleven_demo/`. Integration tests under `tests/integration/` use VCR cassettes.
- Run a focused unit test: `uv run pytest tests/unit/path/test_xxx.py -v`.
- Run the full fast loop: `uv run pytest -n auto -m "not integration"`.
- Replay integration cassettes: `uv run pytest -m integration`.
- Coverage gate on library code (PRD FR-24): `uv run pytest --cov=src/eleven_demo --cov-report=term --cov-fail-under=80 -m "not integration"` (single invocation without xdist; see `.cursor/rules/testing-standards.mdc`).
- Before declaring the exploration complete, run `uv run pre-commit run --all-files` at repo root (must pass clean).
- **Selective TDD policy**: use test-first for code owned by this repo where behavior is deterministic and design-sensitive: config/settings (Tasks 1.2 / 1.5), client retry (Tasks 1.3 / 1.6), latency metrics (Task 3.2), Pydantic tool schemas + deterministic mocks (Task 4.2), and the scenario base contract (Task 5.1). For thin ElevenLabs SDK wrappers, confirm live docs / SDK signatures first, then cover with unit mocks and VCR-backed integration tests.
- Conventional Commits, one logical change per commit. Soft target: 300 lines per commit.
- Each sub-task should map to one commit when possible; split commits when a cluster would exceed ~300 lines (see suggested commit log below).

## Tasks

### 1.0 Library foundation — Client and Config

**Acceptance criteria:**

- `from eleven_demo.client import get_client` returns a working `ElevenLabs` instance.
- `get_client()` retries 3 times with exponential backoff on HTTP 429 / 5xx.
- `eleven_demo.config.Settings` loads `.env` and fails fast when `ELEVENLABS_API_KEY` is missing.
- Unit tests cover both modules with mocked SDK and `monkeypatch` for env vars.
- `uv run ruff check .` and `uv run ruff format --check .` pass.

- [x] **1.1 Scaffold the Python package directory tree**
  - **File**: `src/eleven_demo/__init__.py`, `src/eleven_demo/{tts,stt,voices,agents,metrics,scenarios}/__init__.py`, `tests/__init__.py`, `tests/unit/__init__.py`, `tests/integration/__init__.py` (create new)
  - **What**: Empty `__init__.py` files (one line each, just `"""Package marker."""`) so Python treats every directory as a package and `pyproject.toml`'s hatch wheel build works.
  - **Why**: Prerequisite for every later import. Without these, `uv run pytest` fails on collection.
  - **Pattern**: Standard layout described in `.cursor/rules/python-best-practices.mdc`.
  - **Verify**: `uv run python -c "import eleven_demo; print(eleven_demo)"` runs without error.

- [x] **1.2 Implement settings module**
  - **File**: `src/eleven_demo/config.py` (create new)
  - **What**: `Settings(BaseSettings)` Pydantic model with fields: `elevenlabs_api_key: SecretStr`, `default_pt_voice_id: str | None`, `default_en_voice_id: str | None`, `demo_agent_id_telecom: str | None`, `demo_agent_id_banking: str | None`, `demo_agent_id_healthcare: str | None`, `tts_model_id: str = "eleven_flash_v2_5"`, `tts_output_format: str = "mp3_22050_32"`, `stt_model_id: str = "scribe_v1"`, `stt_realtime_model_id: str = "scribe_v2_realtime"`, `log_level: str = "INFO"`. `model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")`. Add module-level `get_settings()` function with `lru_cache`.
  - **Why**: Single typed entry point for environment configuration. Fails fast if API key is missing — surfaces misconfiguration before any API call.
  - **TDD**: Start with Task 1.5 tests for env defaults, env overrides, missing `ELEVENLABS_API_KEY`, cache clearing, and `SecretStr` redaction; then implement `config.py` until those tests pass.
  - **Pattern**: Follow `pydantic-settings` v2 idioms; use `SecretStr` for the API key so it never accidentally appears in logs.
  - **Verify**: `uv run python -c "from eleven_demo.config import get_settings; s = get_settings(); print(s.tts_model_id)"` prints `eleven_flash_v2_5` (after `.env` is created with at least the API key).

- [x] **1.3 Implement the SDK client factory with retry**
  - **File**: `src/eleven_demo/client.py` (create new)
  - **What**: `get_client() -> ElevenLabs` returns a configured SDK instance with **effective** retry on HTTP 429 / 5xx for synchronous REST traffic. Pick **one** implementation strategy (document which in module docstring): (a) pass a custom `httpx` client / transport into `ElevenLabs(...)` if the installed SDK supports it, with retries at the HTTP layer; or (b) expose `_with_retry(callable, *, attempts=3, base_delay=1.0)` and ensure **every sync SDK call path** in `eleven_demo/*` invokes wrappers that use `_with_retry` so retries are never accidentally skipped. Include `timeout=30.0`. Cache the client instance with `lru_cache`.
  - **Why**: Centralizes retry / timeout / auth; satisfies `.cursor/rules/elevenlabs-conventions.mdc`. A detached `_with_retry` helper **without** wrapping actual SDK calls would contradict README claims.
  - **TDD**: Start with Task 1.6 tests that prove success without retry, retry on 429 / 5xx, no retry on 400, exponential sleep calls are made, and the last exception is re-raised after 3 failed attempts.
  - **Pattern**: Retry on `httpx.HTTPStatusError` with status in `{429, 500, 502, 503, 504}`; exponential backoff. WebSocket connections remain outside this retry helper (lifecycle differs).
  - **Verify**: `uv run python -c "from eleven_demo.client import get_client; c = get_client(); print(type(c).__name__)"` prints `ElevenLabs`.
  - **Integration**: Imported by every TTS, STT, voices, and agents module.

- [x] **1.4 Add shared test fixtures and conftest**
  - **File**: `tests/conftest.py` (create new)
  - **What**: Autouse fixture `_skip_integration_without_key(request, monkeypatch)` that skips tests marked `@pytest.mark.integration` when both `ELEVENLABS_API_KEY` is unset AND no VCR cassette exists for the test. Also expose `mock_eleven_client` fixture (`MagicMock` spec'd against `ElevenLabs`) and `clear_settings_cache` fixture that calls `get_settings.cache_clear()` between tests.
  - **Why**: Makes integration tests deterministic in CI (replay cassettes) and friendly during local development without a key.
  - **Pattern**: Follow `.cursor/rules/testing-standards.mdc` section "Markers" and "VCR Cassettes Pattern".
  - **Verify**: `uv run pytest --collect-only -q` succeeds (no errors collecting tests).

- [x] **1.5 Unit tests for config**
  - **File**: `tests/unit/test_config.py` (create new)
  - **What**: Tests for `get_settings()`: (a) loads default model id when not set; (b) overrides defaults from env; (c) raises `ValidationError` when `ELEVENLABS_API_KEY` is missing; (d) `SecretStr` does not leak in `repr`. Use `monkeypatch.setenv` and `monkeypatch.delenv`.
  - **Why**: Catches env-loading regressions early. Configuration bugs are the most common cause of demo failures live.
  - **Pattern**: One test function per behavior, descriptive names, type hints on fixtures.
  - **Verify**: `uv run pytest tests/unit/test_config.py -v` is green.

- [x] **1.6 Unit tests for client retry behavior**
  - **File**: `tests/unit/test_client.py` (create new)
  - **What**: Tests for `_with_retry`: (a) returns immediately on success; (b) retries on 429 then succeeds on second attempt; (c) gives up after 3 attempts and re-raises; (d) does not retry on 400. Use `MagicMock` to count calls and a fake `httpx.HTTPStatusError`.
  - **Why**: Retry logic is the kind of subtle code that breaks silently. Lock it in.
  - **Pattern**: Use `mocker.patch` for `time.sleep` to keep tests fast.
  - **Verify**: `uv run pytest tests/unit/test_client.py -v` is green.

---

### 2.0 TTS and STT modules (sync, stream, WebSocket)

**Trigger / entry point:** Imported by Task 3 (CLI scripts) and Task 6 (Gradio app).
**Enables:** Voice playground tab, latency benchmark, STT demo script, scenario testing.
**Depends on:** Task 1 (`client.get_client`).

**Acceptance criteria:**

- `eleven_demo.tts.sync.synthesize(...) -> tuple[bytes, dict]` returns non-empty audio and metadata (`character_count`, `request_id`, …).
- `eleven_demo.tts.stream.stream(...)` yields `(chunk, ttfb_seconds)` tuples (TTFB on first chunk only, or via `measure_ttfb`).
- `eleven_demo.tts.ws.ws_stream(...)` (async) yields audio bytes via the TTS WebSocket.
- `eleven_demo.stt.batch.transcribe(...)` returns a transcript with diarization for a sample MP3.
- `eleven_demo.stt.realtime.realtime_transcribe(...)` defaults to realtime model `scribe_v2_realtime` (confirm against [Models](https://elevenlabs.io/docs/overview/models)).
- VCR-backed integration tests pass for sync TTS and batch STT; WS flows have unit tests with mocked sockets.

- [x] **2.1 Implement synchronous TTS**
  - **File**: `src/eleven_demo/tts/sync.py` (create new)
  - **What**: `synthesize(text: str, *, voice_id: str, model_id: str = "eleven_flash_v2_5", output_format: str = "mp3_22050_32", voice_settings: dict | None = None) -> tuple[bytes, dict]` returns `(audio_bytes, metadata)` where metadata contains `character_count: int`, `request_id: str`, `model_id: str`. Use `client.text_to_speech.with_raw_response.convert(...)` to capture headers; concatenate the iterable response into bytes.
  - **Why**: Foundation for all non-streaming demos. Raw response unlocks cost tracking per `.cursor/rules/elevenlabs-conventions.mdc` rule 3.
  - **Pattern**: Follow snippet "Sync convert (file output)" + "Capture cost + request ID from headers" in `.cursor/skills/elevenlabs-api-cookbook/SKILL.md`.
  - **Verify**: `uv run pytest tests/unit/tts/test_sync.py -v` is green.
  - **Integration**: Used by `scripts/tts_demo.py` and the Gradio TTS Playground tab.

- [x] **2.2 Implement HTTP streaming TTS with TTFB measurement**
  - **File**: `src/eleven_demo/tts/stream.py` (create new)
  - **What**: `stream(text: str, *, voice_id: str, model_id: str = "eleven_flash_v2_5", output_format: str = "mp3_22050_32") -> Iterator[tuple[bytes, float | None]]` yields `(chunk, ttfb_seconds | None)` where `ttfb_seconds` is set only on the first chunk. Internally call `client.text_to_speech.stream(...)`. Use `time.perf_counter()` for measurement.
  - **Why**: Streaming is the latency story. Returning TTFB inline avoids state across calls.
  - **Pattern**: Follow snippet "HTTP streaming (chunked) — measure TTFB" in `.cursor/skills/elevenlabs-api-cookbook/SKILL.md`.
  - **Verify**: `uv run pytest tests/unit/tts/test_stream.py -v` passes (mocked iterator + time control via `monkeypatch`).
  - **Integration**: Used by `scripts/tts_stream_ttfb.py` and the Gradio Latency tab.

- [x] **2.3 Implement WebSocket TTS (input streaming)**
  - **File**: `src/eleven_demo/tts/ws.py` (create new)
  - **What**: `async def ws_stream(text_chunks: AsyncIterable[str], *, voice_id: str, model_id: str = "eleven_flash_v2_5", output_format: str = "mp3_22050_32") -> AsyncIterator[bytes]` connects to `wss://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream-input`, sends `{"text": " "}` first, then iterates over `text_chunks` sending `{"text": chunk + " ", "try_trigger_generation": True}`, then `{"text": ""}` at end. Decodes base64 audio frames and yields bytes.
  - **Why**: Demonstrates the lowest-latency TTS path; needed when an LLM is producing tokens word-by-word.
  - **Pattern**: Follow snippet "WebSocket TTS (input streaming, true real-time)" in `.cursor/skills/elevenlabs-api-cookbook/SKILL.md`. Authenticate via header per `elevenlabs-conventions.mdc` rule 9.
  - **Verify**: `uv run pytest tests/unit/tts/test_ws.py -v` passes (mocked `websockets.connect` via `pytest-asyncio` and `AsyncMock`).
  - **Integration**: Used by `apps/ws_bridge/main.py` (stretch).

- [x] **2.4 Implement batch STT**
  - **File**: `src/eleven_demo/stt/batch.py` (create new)
  - **What**: `transcribe(file_path: Path, *, language: str = "por", model_id: str = "scribe_v1", diarize: bool = True, tag_audio_events: bool = True) -> Transcript` opens the file, calls `client.speech_to_text.convert(...)`, returns the SDK's `SpeechToTextChunkResponseModel`. Re-export the relevant types under `eleven_demo.stt.types`.
  - **Why**: Foundation for transcription-based demos and for verifying agent transcripts post-call.
  - **Pattern**: Follow snippet "Batch transcription" in `.cursor/skills/elevenlabs-api-cookbook/SKILL.md`.
  - **Verify**: `uv run pytest tests/integration/stt/test_batch.py -v` (VCR cassette) passes.
  - **Integration**: Used by `scripts/stt_demo.py`.

- [x] **2.5 Implement realtime STT WebSocket**
  - **File**: `src/eleven_demo/stt/realtime.py` (create new)
  - **What**: `async def realtime_transcribe(audio_chunks: AsyncIterable[bytes], *, model_id: str | None = None, language_code: str = "por") -> AsyncIterator[TranscriptEvent]` — default `model_id` comes from `get_settings().stt_realtime_model_id` (`scribe_v2_realtime`). Connects to `wss://api.elevenlabs.io/v1/speech-to-text/realtime`, runs `sender` and `receiver` coroutines via `asyncio.gather`, yields events with shape `{type, text, is_partial}` mapped from partial / committed payloads ([Realtime WebSocket reference](https://elevenlabs.io/docs/api-reference/speech-to-text/v-1-speech-to-text-realtime)).
  - **Why**: Enables live captioning demos and feeds an LLM as the user speaks.
  - **Pattern**: Follow snippet "Realtime STT (microphone-style streaming)" in `.cursor/skills/elevenlabs-api-cookbook/SKILL.md`.
  - **Verify**: `uv run pytest tests/unit/stt/test_realtime.py -v` (mocked websocket) passes.

- [x] **2.6 Integration tests for TTS sync + stream**
  - **File**: `tests/integration/tts/test_integration_sync.py`, `tests/integration/tts/test_integration_stream.py` (create new; basename must differ from `tests/unit/tts/test_sync.py` to avoid pytest import collisions)
  - **What**: One test each: send a known short text to a known voice id (the public `JBFqnCBsd6RMkjVDRZzb`), assert returned bytes start with the expected MP3 magic header (`b"ID3"` or `b"\xff\xfb"`) and metadata includes a non-zero character count. Mark `@pytest.mark.integration` and `@pytest.mark.vcr(filter_headers=["xi-api-key"], record_mode="once")`.
  - **Why**: Locks in the SDK contract and provides a CI-safe sanity check.
  - **Pattern**: Follow VCR pattern in `.cursor/rules/testing-standards.mdc`.
  - **Verify**: First run with `ELEVENLABS_API_KEY` set records cassettes; subsequent runs with no key replay them.

- [x] **2.7 Integration test for STT batch**
  - **File**: `tests/integration/stt/test_batch.py` (create new), plus `data/samples/hello-pt-br.mp3` (~3 seconds, "olá, esta é uma demonstração")
  - **What**: Generate the sample by recording a short PT-BR phrase or by reusing a TTS output. Test asserts the transcript text contains a known substring.
  - **Why**: STT contracts can drift across model versions; pin via VCR.
  - **Pattern**: Same as 2.6.
  - **Verify**: `uv run pytest tests/integration/stt -v` passes.
  - **Note**: Implemented alongside Task 2.4; audio is TTS-generated PT-BR MP3 (duration varies with synthesis settings).

---

### 3.0 Voice catalog, latency metrics, and CLI exploration scripts

**Trigger / entry point:** Direct invocation by the developer (`uv run python scripts/...`).
**Enables:** Pinning default voice IDs in `.env`, generating TTFB evidence cited in the PRD.
**Depends on:** Task 1 (client) and Task 2 (TTS / STT modules).

**Acceptance criteria:**

- `eleven_demo.voices.catalog.list_pt_br_voices() -> list[VoiceCard]` returns at least one voice.
- `eleven_demo.metrics.latency.measure_ttfb` decorator and `LatencyReport(median, p95, mean, samples)` produce correct numbers on a synthetic series (unit test).
- `scripts/tts_demo.py "<text>"` writes `out.mp3` and prints the character cost from raw response headers.
- `scripts/tts_stream_ttfb.py [--n N] [--model flash|multilingual]` prints a TTFB table.
- `scripts/stt_demo.py <audio>` prints a transcript with speaker labels.
- `scripts/voices_pt_br.py` prints a `rich` table of PT-BR voices.

- [ ] **3.1 Implement Voice Library catalog with PT-BR filter**
  - **File**: `src/eleven_demo/voices/catalog.py` (create new)
  - **What**: `VoiceCard(BaseModel)` with `voice_id, name, accent, gender, age, language, preview_url, labels`. `list_voices(*, page_size: int = 100) -> list[VoiceCard]` calls `client.voices.search(...)`. `list_pt_br_voices(...) -> list[VoiceCard]` filters on `labels.language` containing `"pt"` or `accent` containing `"portuguese"`.
  - **Why**: Voice selection drives the entire perceived quality of every demo. The default voice IDs in `.env` come from this script's output.
  - **Pattern**: Follow snippet "List voices, filter by language" in `.cursor/skills/elevenlabs-api-cookbook/SKILL.md`.
  - **Verify**: `uv run pytest tests/unit/voices/test_catalog.py -v` (mocked SDK) passes.

- [ ] **3.2 Implement latency metrics**
  - **File**: `src/eleven_demo/metrics/latency.py` (create new)
  - **What**: `LatencyReport(BaseModel)` with `samples: list[float]`, computed properties `median`, `p95`, `mean`, `min`, `max`, `count`. `@measure_ttfb(report: LatencyReport)` decorator wraps a function that yields chunks (or returns an iterable) and appends the time-to-first-byte to `report.samples`.
  - **Why**: Without measured numbers, latency talk is hand-waving. The TTFB story in the PRD requires concrete data.
  - **TDD**: Write `tests/unit/metrics/test_latency.py` first for empty samples, one sample, sorted/unsorted sample series, `median`, `p95`, `mean`, `min`, `max`, `count`, and decorator behavior using controlled `time.perf_counter`.
  - **Pattern**: Use `statistics.median` and `numpy.percentile` only if numpy is already present (it is not — implement p95 manually with `sorted(samples)[int(len*0.95)]`). Keep zero numpy dependency.
  - **Verify**: `uv run pytest tests/unit/metrics/test_latency.py -v` (synthetic series with known p95) passes.

- [ ] **3.3 CLI: `scripts/tts_demo.py`**
  - **File**: `scripts/tts_demo.py` (create new)
  - **What**: Accepts `text: str` (positional), optional `--voice-id`, `--out out.mp3`. Calls `synthesize(...)`, writes audio bytes to disk, prints a `rich` panel with `request_id`, `character_count`, `voice_id`, `model_id`, output path. Use `argparse` (no extra dependency) or `typer` if simpler.
  - **Why**: The simplest possible TTS smoke test; also a recurring demo step.
  - **Pattern**: Use `rich.console.Console` for output. Follow the narrative in `.cursor/rules/python-best-practices.mdc` rule 8.
  - **Verify**: `uv run python scripts/tts_demo.py "Olá, esta é uma demonstração."` writes `out.mp3` (>1KB) and prints a panel.

- [ ] **3.4 CLI: `scripts/tts_stream_ttfb.py`**
  - **File**: `scripts/tts_stream_ttfb.py` (create new)
  - **What**: Args: `--n 10`, `--model flash|multilingual` (translates to model id), `--text "..."`, `--voice-id`. Runs N streaming requests, collects TTFB into a `LatencyReport`, prints a `rich` table with rows per call (idx, ttfb_ms, total_bytes) and a footer with median / p95 / mean.
  - **Why**: This is the centerpiece of the latency story. Output of this script is cited in `docs/scenarios/` and the Gradio Latency tab uses the same primitives.
  - **Pattern**: Reuse `eleven_demo.tts.stream.stream()` and `LatencyReport`.
  - **Verify**: `uv run python scripts/tts_stream_ttfb.py --n 3 --text "test"` prints a 3-row table.

- [ ] **3.5 CLI: `scripts/stt_demo.py`**
  - **File**: `scripts/stt_demo.py` (create new)
  - **What**: Positional `audio_path`, prints transcript text and a `rich` table of words with speaker_id, start, end (truncated to first 20 rows).
  - **Why**: Smoke test for STT and a building block for any STT-driven demo.
  - **Pattern**: Reuse `eleven_demo.stt.batch.transcribe()`.
  - **Verify**: `uv run python scripts/stt_demo.py data/samples/hello-pt-br.mp3` prints a transcript.

- [ ] **3.6 CLI: `scripts/voices_pt_br.py`**
  - **File**: `scripts/voices_pt_br.py` (create new)
  - **What**: Prints a `rich` table of PT-BR voices: voice_id, name, accent, gender, age, preview_url. Sorted by name.
  - **Why**: Enables the developer to pick `DEFAULT_PT_VOICE_ID` and `DEFAULT_EN_VOICE_ID` without leaving the terminal.
  - **Pattern**: Reuse `eleven_demo.voices.catalog.list_pt_br_voices()`.
  - **Verify**: `uv run python scripts/voices_pt_br.py` prints a populated table.

- [ ] **3.7 Add optional OpenAI benchmark configuration**
  - **File**: `pyproject.toml`, `.env.example`, `src/eleven_demo/config.py`, `tests/unit/test_config.py` (modify existing)
  - **What**: Add `openai>=1.0.0` as a runtime dependency. Extend settings with `openai_api_key: SecretStr | None = None`, `openai_tts_model_id: str = "gpt-4o-mini-tts"`, `openai_tts_voice: str = "coral"`, `openai_tts_response_format: str = "mp3"`. Add `.env.example` placeholders for `OPENAI_API_KEY`, `OPENAI_TTS_MODEL_ID`, `OPENAI_TTS_VOICE`, `OPENAI_TTS_RESPONSE_FORMAT`. Tests must prove `OPENAI_API_KEY` is optional and redacted when present.
  - **Why**: Keeps the OpenAI dependency scoped to the vendor benchmark. The rest of the repo must still run with only `ELEVENLABS_API_KEY`.
  - **Pattern**: Same `pydantic-settings` + `SecretStr` conventions as Task 1.2. Do not log either API key.
  - **Verify**: `uv run pytest tests/unit/test_config.py -v` passes with and without `OPENAI_API_KEY`.

- [ ] **3.8 Implement OpenAI streaming TTS adapter**
  - **File**: `src/eleven_demo/benchmarks/__init__.py`, `src/eleven_demo/benchmarks/openai_tts.py`, `tests/unit/benchmarks/test_openai_tts.py` (create new)
  - **What**: `stream_openai_tts(text: str, *, model_id: str, voice: str, response_format: str) -> Iterator[tuple[bytes, float | None]]` uses `OpenAI(api_key=...)` and `client.audio.speech.with_streaming_response.create(...)` to stream bytes. Measure TTFB with `time.perf_counter()` on the first chunk. Raise a clear `RuntimeError` if `OPENAI_API_KEY` is missing.
  - **Why**: Provides the comparator path while keeping vendor-specific code isolated from ElevenLabs modules.
  - **Pattern**: Follow OpenAI Speech API streaming docs (`audio.speech.with_streaming_response.create`, `response_format="mp3"` headline baseline; optional `"pcm"` fastest-path control). Unit tests mock the OpenAI client; no live OpenAI calls in unit tests.
  - **Verify**: `uv run pytest tests/unit/benchmarks/test_openai_tts.py -v` passes.

- [ ] **3.9 Implement TTS vendor benchmark report model**
  - **File**: `src/eleven_demo/benchmarks/tts_vendor.py`, `tests/unit/benchmarks/test_tts_vendor.py` (create new)
  - **What**: Pydantic models: `VendorRun(provider, model_id, voice, output_format, text_id, ttfb_ms, total_ms, byte_count, region: str | None)`, `VendorSummary(provider, median_ttfb_ms, p95_ttfb_ms, mean_ttfb_ms, median_total_ms, sample_count)`, `VendorBenchmarkReport(runs, summaries, hypothesis, caveats)`. Add `run_vendor_benchmark(texts: list[str], n: int, randomize_order: bool = True) -> VendorBenchmarkReport` that calls ElevenLabs streaming (Task 2.2) and OpenAI streaming (Task 3.8).
  - **Why**: Ensures the comparison is reproducible, typed, and transparent. The report must show raw numbers even when the result does not favor the expected hypothesis.
  - **Pattern**: Reuse `LatencyReport` logic from Task 3.2 where possible. Randomize provider order per run to reduce warm-cache and ordering bias.
  - **Verify**: `uv run pytest tests/unit/benchmarks/test_tts_vendor.py -v` passes with mocked providers and deterministic timings.

- [ ] **3.10 CLI: `scripts/tts_vendor_benchmark.py`**
  - **File**: `scripts/tts_vendor_benchmark.py` (create new)
  - **What**: Args: `--n 5`, `--text-set short-pt-br`, `--eleven-model eleven_flash_v2_5`, `--openai-model gpt-4o-mini-tts`, `--openai-format mp3`, `--out artifacts/benchmarks/tts-vendor-latest.json`. Use a short PT-BR utterance set (e.g. "Olá, encontrei sua conta. Posso te ajudar com a segunda via?", "Entendi. Vou verificar isso agora.", "Certo, por segurança vou confirmar alguns dados."). Print a `rich` table comparing TTFB median / p95 / mean, total time, and sample count.
  - **Why**: This is the fourth demo's evidence generator. TTFB is the headline metric because it maps directly to perceived responsiveness in voice-agent UX.
  - **Pattern**: Use compressed browser-friendly audio (`ElevenLabs mp3_22050_32` vs OpenAI `mp3`) for the headline comparison. Support `--openai-format pcm` as a secondary control, but do not mix it into the headline row.
  - **Verify**: With both keys set, `uv run python scripts/tts_vendor_benchmark.py --n 3` prints both provider summaries and writes the JSON report. Without `OPENAI_API_KEY`, the script exits with a clear setup message and no stack trace.

- [ ] **3.11 Vendor benchmark tests and VCR policy**
  - **File**: `tests/integration/benchmarks/test_tts_vendor.py` (create new), `tests/conftest.py` (modify if needed)
  - **What**: Add one optional integration test that records/replays the benchmark with `n=1` per provider. Skip when either `ELEVENLABS_API_KEY` or `OPENAI_API_KEY` is missing and no cassette exists. Filter `xi-api-key`, `authorization`, and any vendor request ids from cassettes.
  - **Why**: The benchmark touches two paid APIs; tests must not burn credits unexpectedly or leak secrets.
  - **Pattern**: Same VCR convention as Task 2.6, with OpenAI authorization header redaction added.
  - **Verify**: `uv run pytest tests/integration/benchmarks -v` records once with both keys and replays without keys.

---

### 4.0 ElevenAgents core — factory, tools, knowledge base, simulate

**Trigger / entry point:** Used by Task 5 (scenarios) and Task 6 (Gradio app).
**Enables:** Idempotent agent provisioning, declarative tool wiring, regression testing of prompts via simulate.
**Depends on:** Task 1.

**Acceptance criteria:**

- `agents.factory` exposes idempotent `create_agent`, `update_agent`, `delete_agent`, `list_agents`.
- `agents.tools` defines Pydantic schemas and mock implementations for the six demo tools (telecom, banking ×3, healthcare, transfer-to-human).
- `agents.kb` provides `upload_kb_text`, `upload_kb_file`, `compute_rag(doc_ids)`.
- `agents.simulate.simulate(agent_id, user_messages)` returns a `SimulationResult` (transcript, tool calls, analysis).
- Unit tests cover Pydantic schema validation; integration tests cover one happy-path simulate per scenario via VCR.

- [ ] **4.1 Implement agent CRUD factory**
  - **File**: `src/eleven_demo/agents/factory.py` (create new)
  - **What**: Functions: `create_agent(name, conversation_config, tags=None) -> Agent`, `update_agent(agent_id, **changes) -> Agent`, `delete_agent(agent_id) -> None`, `list_agents() -> list[Agent]`, `find_agent_by_name(name) -> Agent | None`. The high-level helper `upsert_agent(name, conversation_config) -> Agent` calls `find_agent_by_name`, then either creates or updates.
  - **Why**: `provision()` for each scenario needs idempotency (PRD FR-10). Centralizes the agent lifecycle and avoids duplicate agents on re-runs.
  - **Pattern**: Follow snippets in `.cursor/skills/elevenlabs-agents/SKILL.md` ("Create an agent", "List, update, delete").
  - **Verify**: `uv run pytest tests/unit/agents/test_factory.py -v` (mocked client) passes.

- [ ] **4.2 Implement server tools with Pydantic schemas + mocks**
  - **File**: `src/eleven_demo/agents/tools.py` (create new)
  - **What**: Pydantic models for inputs and outputs of: `LookupTelecomAccountInput / Output`, `LookupAccountSummaryInput / Output`, `RequestCardBlockInput / Output`, `RequestCardReplacementInput / Output`, `BookMedicalAppointmentInput / Output`, `TransferToHumanInput / Output`. Each tool has a `mock_<name>(input: Model) -> Model` function returning deterministic but realistic data (e.g. balance derived from a hash of CPF). Also include a `TOOLS_REGISTRY` mapping tool name to (input_model, output_model, mock_callable).
  - **Why**: Demonstrates the four tool types story (server tools here) and lets simulated conversations exercise tool calls without real external systems.
  - **TDD**: Write schema tests first for required fields, invalid inputs, `extra="forbid"`, whitespace stripping, deterministic mock outputs, and no unnecessary raw PII echo in outputs.
  - **Pattern**: `model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)` per `.cursor/rules/security-standards.mdc`.
  - **Verify**: `uv run pytest tests/unit/agents/test_tools.py -v` (schema validation, mock determinism) passes.

- [ ] **4.3 Implement knowledge base helpers**
  - **File**: `src/eleven_demo/agents/kb.py` (create new)
  - **What**: `upload_kb_text(name: str, text: str) -> KbDocument`, `upload_kb_file(path: Path) -> KbDocument`, `list_kb_documents() -> list[KbDocument]`, `compute_rag(document_ids: list[str], wait: bool = True) -> RagIndex`. Use the `client.knowledge_base` namespace.
  - **Why**: Healthcare scenario relies on RAG over symptom protocols.
  - **Pattern**: Look up the exact methods via the `elevenlabs-docs` skill before implementing — the SDK surface for KB has been moving.
  - **Definition of done**: Matches current Agents Platform KB flows ([Knowledge base](https://elevenlabs.io/docs/eleven-agents/customization/knowledge-base), [Compute RAG index](https://elevenlabs.io/docs/eleven-agents/api-reference/knowledge-base/compute-rag-index)); confirm method names against the live SDK before merging.
  - **Verify**: `uv run pytest tests/unit/agents/test_kb.py -v` (mocked) passes.

- [ ] **4.4 Implement simulate wrapper**
  - **File**: `src/eleven_demo/agents/simulate.py` (create new)
  - **What**: `SimulationResult(BaseModel)` with `conversation_id, transcript: list[Turn], tool_calls: list[ToolCall], analysis: Analysis`. `simulate(agent_id: str, user_messages: list[str], language: str = "pt") -> SimulationResult` calls `client.agents.simulate_conversation(...)` for the first message, then loops sending follow-up messages.
  - **Why**: Enables regression tests of prompts and tool wiring without a microphone or a real call.
  - **Pattern**: Follow snippet "Simulate a conversation (offline test)" in `.cursor/skills/elevenlabs-agents/SKILL.md`. Confirm exact SDK signatures via the `elevenlabs-docs` skill since the simulate API surface evolves.
  - **Definition of done**: Wrapper aligns with [Agent Testing](https://elevenlabs.io/docs/eleven-agents/customization/agent-testing) expectations for offline simulation (correct client method(s), typed result shapes).
  - **Verify**: `uv run pytest tests/unit/agents/test_simulate.py -v` passes.

- [ ] **4.5 Unit tests for agents core**
  - **File**: `tests/unit/agents/{test_factory,test_tools,test_kb,test_simulate}.py` (create new)
  - **What**: Per module: 3-5 tests covering happy path, validation error path, and the idempotency case (`upsert_agent` calls `update` not `create` when name exists). Use `mocker` from `pytest-mock` (added to dev deps if missing).
  - **Why**: Lock in the contract before the scenarios depend on it.
  - **Pattern**: Same as 1.5 / 1.6.
  - **Verify**: `uv run pytest tests/unit/agents -v` is green.

---

### 5.0 Vertical scenarios — Telecom, Banking, Healthcare

**Trigger / entry point:** `scripts/agent_create.py <scenario>` invoked by the developer.
**Enables:** Gradio app tabs for each vertical, regression tests, scenario storytelling.
**Depends on:** Task 4 (Agents core), and `data/kb/*.md` seed files for Healthcare.

**Acceptance criteria:**

- Each `scenarios/{telecom,banking,healthcare}.py` exports `SYSTEM_PROMPT`, `FIRST_MESSAGE`, `LANGUAGE`, `VOICE_ID`, `TOOL_NAMES`, `KB_IDS`, `SUCCESS_CRITERIA`, and `provision() -> agent_id` (`TOOL_NAMES` lists server-tool identifiers wired to mocks; `KB_IDS` lists KB document IDs after upload — empty except Healthcare).
- `provision()` is idempotent (creates if missing, updates if present, identifies by name).
- Healthcare scenario uploads at least 5 knowledge base documents and computes a RAG index.
- `scripts/agent_create.py <scenario>` provisions and prints `agent_id`; `scripts/agent_simulate.py <scenario> "<msg>"` returns the analysis output.
- Each scenario has a regression test: simulated 3-turn conversation that asserts on `SUCCESS_CRITERIA`.

- [ ] **5.1 Define a `Scenario` base contract**
  - **File**: `src/eleven_demo/scenarios/base.py` (create new)
  - **What**: `Scenario(BaseModel)` with `name, system_prompt, first_message, language, voice_id, tool_names: list[str], kb_doc_ids: list[str], success_criteria: list[str]`. Abstract method `provision(self) -> str` (returns `agent_id`). Helper `_build_conversation_config(self) -> dict`. Each concrete scenario module exports module-level aliases `TOOL_NAMES` and `KB_IDS` pointing at the same lists as `tool_names` / `kb_doc_ids` for stable imports matching PRD FR-14.
  - **Why**: Removes duplicated `provision` boilerplate from each vertical.
  - **TDD**: Write `tests/unit/scenarios/test_base.py` first for required-field validation, `_build_conversation_config()` shape, voice/language propagation, `tool_names` / `kb_doc_ids` mapping to platform config, and alias expectations for `TOOL_NAMES` / `KB_IDS` in concrete modules.
  - **Pattern**: Prefer `typing.Protocol` or `ABC` if abstract methods on a Pydantic model become awkward — validation stays on `Scenario`; inheritance mechanics are implementation detail.
  - **Verify**: `uv run pytest tests/unit/scenarios/test_base.py -v` passes.

- [ ] **5.2 Implement Telecom scenario**
  - **File**: `src/eleven_demo/scenarios/telecom.py` (create new)
  - **What**: `SCENARIO = Scenario(name="acme-telecom-sac-pt", language="pt", voice_id=settings.default_pt_voice_id, system_prompt=..., first_message="Olá! Aqui é a ACME Telecom. Para sua segurança, qual o seu CPF?", tool_names=["lookup_telecom_account", "transfer_to_human"], kb_doc_ids=[], success_criteria=["account looked up", "human transfer offered when off-topic"])`. Export `TOOL_NAMES` / `KB_IDS` aliases per task 5.1. Real PSTN/SIP escalation uses the platform **transfer_to_number** system tool ([docs](https://elevenlabs.io/docs/eleven-agents/customization/tools/system-tools/transfer-to-number)); this demo stays browser-only and uses the mocked `transfer_to_human` server tool instead. `provision()` calls `agents.factory.upsert_agent`. The `system_prompt` enforces identity, scope, voice-friendly output (no markdown), tool-use guidance.
  - **Why**: First vertical, sets the prompting bar and the storytelling tone.
  - **Pattern**: Apply the 3 rules in `.cursor/skills/elevenlabs-agents/SKILL.md` "Production-Grade Prompting".
  - **Verify**: `uv run python scripts/agent_create.py telecom` prints an agent_id (after Task 5.4 lands).

- [ ] **5.3 Implement Banking scenario**
  - **File**: `src/eleven_demo/scenarios/banking.py` (create new)
  - **What**: Similar shape to 5.2 for "Onyx Pay". Tools: `lookup_account_summary`, `request_card_block`, `request_card_replacement`, `transfer_to_human`. Authentication step in the prompt: ask CPF + last transaction amount before any tool call. Document Zero Retention Mode in the docstring.
  - **Why**: Highest stakes vertical (PII + money). Must show the security-first posture.
  - **Pattern**: Same as 5.2 plus `.cursor/rules/security-standards.mdc` ZRM note.
  - **Verify**: `uv run python scripts/agent_create.py banking` prints an agent_id.

- [ ] **5.4 Implement Healthcare scenario + KB seed files**
  - **File**: `src/eleven_demo/scenarios/healthcare.py`, `data/kb/healthcare/*.md` (5 files: `01-symptom-fever.md`, `02-symptom-headache.md`, `03-symptom-chest-pain.md`, `04-specialties.md`, `05-lgpd-policy.md`) (create new)
  - **What**: Scenario for "Vita Saúde". `provision()` first uploads each KB file via `kb.upload_kb_file`, computes the RAG index, then provisions the agent referencing those `kb_doc_ids`. Enable **Zero Retention Mode** on the agent configuration (same posture as Banking for medical PII) and document in the scenario docstring per PRD §7. KB files are fictional but plausible (~150-300 words each).
  - **Why**: This is the only scenario that exercises Knowledge Base + RAG end to end.
  - **Pattern**: Same as 5.2 plus `agents/kb.py`. Idempotency on KB: skip upload if a document with the same name exists.
  - **Verify**: `uv run python scripts/agent_create.py healthcare` prints an agent_id; the agent answers "tenho febre alta há dois dias" with a specialty suggestion.

- [ ] **5.5 CLI scripts for agent provisioning and simulated checks**
  - **File**: `scripts/agent_create.py`, `scripts/agent_simulate.py` (create new)
  - **What**: `agent_create.py <scenario>` calls `import_module(f"eleven_demo.scenarios.{scenario}").provision()` and prints the `agent_id`. `agent_simulate.py <scenario> "<message>"` resolves the agent id, runs `simulate(agent_id, [message])` and prints the analysis as a `rich` panel.
  - **Why**: Wires the CLI surface to the scenarios. Used by both human exploration and the regression tests in 5.6.
  - **Pattern**: Use `argparse` with `choices=["telecom", "banking", "healthcare"]`.
  - **Verify**: `uv run python scripts/agent_create.py telecom` and `uv run python scripts/agent_simulate.py telecom "qual meu saldo?"` both print expected output.

- [ ] **5.6 Regression tests per scenario**
  - **File**: `tests/integration/scenarios/{test_telecom,test_banking,test_healthcare}.py` (create new)
  - **What**: Each test uses a 3-turn canonical conversation and asserts on stable signals: HTTP/SDK shape, presence of expected tool calls in structured fields where available, language tags — avoid asserting verbatim LLM wording (models drift). Prefer pinning agent LLM/TTS models in scenario config where possible. Marked `@pytest.mark.integration`, recorded via VCR.
  - **Why**: Guards against prompt drift after edits without flaky free-text asserts.
  - **Pattern**: Same VCR convention as 2.6.
  - **Verify**: `uv run pytest tests/integration/scenarios -v` is green.

---

### 6.0 Demo apps — Gradio multi-vertical, vendor benchmark, and FastAPI WebSocket bridge (stretch)

**Trigger / entry point:** `uv run gradio apps/gradio_app.py` and `uv run uvicorn apps.ws_bridge.main:app`.
**Enables:** Live walkthrough of TTS, three voice agents, latency benchmark, and vendor benchmark from a single URL.
**Depends on:** Tasks 2, 3, 4, 5.

**Acceptance criteria:**

- `apps/gradio_app.py` exposes the six tabs from FR-21 / FR-22 / FR-22a; each one responds end-to-end against the live platform or shows setup guidance when optional credentials are missing.
- Voice widgets in agent tabs are loaded via signed URLs (`client.conversations.get_signed_url`).
- Latency tab plots TTFB for 10 runs and shows median + p95.
- Vendor Benchmark tab compares ElevenLabs Flash v2.5 and OpenAI `gpt-4o-mini-tts` TTFB when `OPENAI_API_KEY` is present.
- **Stretch**: `apps/ws_bridge/main.py` exposes `/ws/tts` (proxy) and `/healthz`; smoke test with `wscat` succeeds.

- [ ] **6.1 Gradio app skeleton with 6 tabs and shared theme**
  - **File**: `apps/gradio_app.py` (create new)
  - **What**: Top-level `Blocks(theme=gr.themes.Soft())` with six `gr.Tab`s wired to placeholder functions. Title "ElevenLabs Vertical Exploration". Each tab has a left column (controls) and right column (output + "Why this matters" markdown panel).
  - **Why**: Establishes the layout so subsequent sub-tasks only fill in tab logic.
  - **Pattern**: Use Gradio 5 idioms (function-based tab content). Run with `if __name__ == "__main__": demo.launch()`.
  - **Verify**: `uv run python apps/gradio_app.py` opens at `http://localhost:7860` with six empty tabs.

- [ ] **6.2 Implement TTS Playground tab**
  - **File**: `apps/gradio_app.py` (modify existing)
  - **What**: Inputs: `gr.Textbox(text)`, `gr.Dropdown(voices)` (populated from `list_pt_br_voices()`), `gr.Slider(stability)`, `gr.Slider(style)`. Output: `gr.Audio(autoplay=True)`, `gr.JSON(metadata)`. The handler calls `synthesize(...)` and returns audio bytes + metadata (unpack tuple from sync helper).
  - **Why**: First user-visible demo. Anchors the "build with the SDK" message.
  - **Pattern**: Reuse `eleven_demo.tts.sync` and `eleven_demo.voices.catalog`.
  - **Verify**: Click "Generate", hear audio in <2s, see metadata.

- [ ] **6.3 Implement Telecom and Banking tabs (voice widget embed)**
  - **File**: `apps/gradio_app.py` (modify existing)
  - **What**: For each tab: button "Iniciar atendimento" calls `client.conversations.get_signed_url(agent_id=settings.demo_agent_id_<scenario>)`, then renders `gr.HTML` with a `<elevenlabs-convai>` widget element pointing to the signed URL. Right panel shows the scenario's "Why this matters" markdown sourced from `docs/scenarios/<scenario>.md`.
  - **Why**: Real voice interaction in-browser. The signed URL pattern is enterprise-friendly and worth showing.
  - **Pattern**: ElevenLabs ships a JS widget; embed via `<script>` and a custom element. Confirm exact embed snippet via `elevenlabs-docs` ([Agents integrate overview](https://elevenlabs.io/docs/eleven-agents/integrate/overview)) before implementing.
  - **Definition of done**: Widget loads without console errors; signed URL documented as the private session entry (per security rules). Server-side tool traces are not rendered in Gradio; use dashboard / [Agent Testing](https://elevenlabs.io/docs/eleven-agents/customization/agent-testing) for deep inspection.
  - **Verify**: Click button, talk to the agent, hear it respond in PT-BR.

- [ ] **6.4 Implement Healthcare tab with RAG source highlight**
  - **File**: `apps/gradio_app.py` (modify existing)
  - **What**: Same widget pattern as 6.3, plus a "Source documents" panel that lists the RAG documents the agent had available, sourced from `scenarios.healthcare.SCENARIO.kb_doc_ids`.
  - **Why**: Makes RAG visible. Without this, anyone exploring the demo cannot tell where the answer came from.
  - **Pattern**: Same as 6.3.
  - **Verify**: Same as 6.3, plus the source list renders.

- [ ] **6.5 Implement Latency tab**
  - **File**: `apps/gradio_app.py` (modify existing)
  - **What**: Inputs: `gr.Radio(["flash", "multilingual"])`, `gr.Slider(n, 1, 20, value=10)`, `gr.Textbox(text, value="Esta é uma demonstração de latência.")`, button "Run benchmark". Output: `gr.LinePlot` (TTFB over runs) + `gr.DataFrame` (raw samples) + summary `gr.JSON({median, p95, mean})`.
  - **Why**: Centerpiece of the latency story; shows the platform speed live.
  - **Pattern**: Reuse `eleven_demo.tts.stream.stream` and `eleven_demo.metrics.latency.LatencyReport`.
  - **Verify**: Click "Run", see chart filled in <30s for n=10.

- [ ] **6.6 Implement Vendor Benchmark tab**
  - **File**: `apps/gradio_app.py` (modify existing)
  - **What**: Inputs: `gr.Slider(n, 1, 10, value=3)`, `gr.Dropdown(text_set)`, `gr.Radio(["mp3", "pcm"], value="mp3", label="OpenAI response format")`, button "Run vendor benchmark". Outputs: `gr.DataFrame` with raw runs, `gr.JSON` summary, and a short methodology markdown explaining that TTFB is contextual and measured locally. Handler calls `run_vendor_benchmark(...)`. If `OPENAI_API_KEY` is missing, show setup instructions instead of raising.
  - **Why**: Turns the CLI evidence into a browser-observable fourth demo while keeping the benchmark honest and rerunnable.
  - **Pattern**: Reuse `src/eleven_demo/benchmarks/tts_vendor.py`. Do not hard-code "winner" text; let the measured summary speak.
  - **Verify**: With both keys set, click "Run vendor benchmark" and see rows for both providers in <60s for `n=3`. Without OpenAI key, tab displays a helpful setup message and the rest of the app still works.

- [ ] **6.7 STRETCH: FastAPI WebSocket bridge**
  - **File**: `apps/ws_bridge/__init__.py`, `apps/ws_bridge/main.py` (create new)
  - **What**: FastAPI app with `/healthz` returning `{"status": "ok"}` and `/ws/tts` accepting JSON messages of shape `{"text": "..."}` and forwarding to the ElevenLabs TTS WebSocket, returning binary audio frames to the client.
  - **Why**: Reference implementation for a production-shaped integration. Optional; drop first if Sprint 3 runs over.
  - **Security**: **Local development only.** The bridge is unauthenticated; bind to `localhost`, never expose `/ws/tts` on a public interface without TLS, auth (e.g. API key or mutual TLS), and rate limiting.
  - **Pattern**: Reuse `eleven_demo.tts.ws.ws_stream`. Use `fastapi.WebSocket` lifecycle correctly (accept, loop, close on exception).
  - **Verify**: `uv run uvicorn apps.ws_bridge.main:app --reload`; in another terminal `wscat -c ws://localhost:8000/ws/tts` then send `{"text":"hello"}` and receive binary frames.

---

### 7.0 Documentation — repository walkthrough and scenario storytelling

**Trigger / entry point:** Read by reviewers / collaborators opening the repo.
**Enables:** Self-contained explanation of architecture, decisions, and demo flow.
**Depends on:** Tasks 5 and 6 (the demos must exist before they are documented).

**Acceptance criteria:**

- `docs/walkthrough.md` covers the full repository end-to-end (intro, three scenarios, latency, architecture, next steps).
- `docs/scenarios/{telecom,banking,healthcare}.md` follow a consistent template (persona, problem, demo flow, ROI hypothesis, talking points, risks, references).
- `docs/benchmarks/tts-vendor-comparison.md` documents the ElevenLabs vs OpenAI TTS benchmark methodology and how to rerun it.
- `docs/reports/technical-exploration-report.md` works as a standalone executive/technical entry point before reading code.
- README links to all of the above and stays under 350 lines.
- `pre-commit run --all-files` is clean.

- [ ] **7.1 Per-vertical storytelling: Telecom**
  - **File**: `docs/scenarios/telecom.md` (create new)
  - **What**: Sections: Persona (1-2 paragraphs), Problem space (numbers if known), Demo flow (steps with screenshots placeholder), ROI hypothesis (formula or table), Talking points (3-5 bullets), Risks and mitigations (2-3 bullets), References (links to ElevenLabs docs and tools used).
  - **Why**: Single source of truth for the Telecom story; consumed by the Gradio Telecom tab and by the walkthrough document.
  - **Pattern**: Follow the structure described in PRD section 4.5 FR-30.
  - **Verify**: File exists, all sections populated, no broken markdown.

- [ ] **7.2 Per-vertical storytelling: Banking**
  - **File**: `docs/scenarios/banking.md` (create new)
  - **What**: Same structure as 7.1, adapted for "Onyx Pay". Include explicit notes on BACEN, LGPD, PCI-DSS posture and on Zero Retention Mode.
  - **Why**: Highest-stakes vertical; documentation must reflect the security and compliance angle.
  - **Pattern**: Same as 7.1.
  - **Verify**: File exists, sections populated.

- [ ] **7.3 Per-vertical storytelling: Healthcare**
  - **File**: `docs/scenarios/healthcare.md` (create new)
  - **What**: Same structure as 7.1, adapted for "Vita Saúde". Explain the KB seed files, the RAG flow, and the LGPD posture for medical PII.
  - **Why**: Documents the only RAG-driven scenario and the compliance choices for medical data.
  - **Pattern**: Same as 7.1.
  - **Verify**: File exists, sections populated.

- [ ] **7.4 End-to-end repository walkthrough**
  - **File**: `docs/walkthrough.md` (create new)
  - **What**: Six sections: (1) Opening — what the repo explores and why; (2) Telecom demo; (3) Banking demo; (4) Healthcare + RAG; (5) TTS latency and vendor benchmark; (6) Architecture and next steps. For each demo: short intro, the exact agent prompt or command to type, the expected behavior, a fallback note if a network or platform issue interrupts the run.
  - **Why**: Executable notes, not pure narrative. Lets a reader (including the future me) replay the exploration without rebuilding the context from scratch each time.
  - **Pattern**: Standard documentation: brief intro paragraphs plus fenced code blocks for the exact prompts and commands.
  - **Verify**: Following the document top-to-bottom takes the reader through TTS playground, all three scenarios, the ElevenLabs latency benchmark, and the vendor benchmark without missing inputs or commands.

- [ ] **7.5 Final README polish and link audit**
  - **File**: `README.md` (modify existing)
  - **What**: After Tasks 5/6/7 land: walk the README top-to-bottom, fix any drifted commands, update the project structure tree to reflect actual files, ensure every internal link resolves. Confirm length stays under 350 lines.
  - **Why**: Final guard against documentation drift; the README is the front door of the repo.
  - **Pattern**: Use `grep -RnE '\[.+\]\(\.\./' .` to spot broken relative links.
  - **Verify**: `pre-commit run --all-files` is clean; manual click-through of every README link works.

- [ ] **7.6 Post-call exploration without a webhook receiver**
  - **File**: `scripts/conversations_list.py` (create new), `engineering/architecture/tech-stack-decisions.md` (modify), `docs/walkthrough.md` (cross-link when 7.4 exists)
  - **What**: Small CLI using `client.conversations.list` (and/or get conversation by id) to list recent conversations for a provisioned agent — documents the operational alternative to running a [post-call webhooks](https://elevenlabs.io/docs/eleven-agents/workflows/post-call-webhooks) HTTP receiver. Add an ADR-style paragraph in `tech-stack-decisions.md` stating webhooks are referenced but not implemented in-repo; link from `walkthrough.md`.
  - **Why**: Closes PRD open question #4 without adding a long-lived HTTP service to the demo repo.
  - **Verify**: Script runs with `ELEVENLABS_API_KEY` and prints at least headers/ids (redact PII in output); docs build with no broken links to the new section.

- [ ] **7.7 TTS vendor benchmark methodology**
  - **File**: `docs/benchmarks/tts-vendor-comparison.md` (create new), `README.md` (link only)
  - **What**: Document the benchmark's purpose, hypothesis, exact model IDs, voices, output formats, PT-BR utterance set, local environment fields to capture (date, city/region, network type, machine, Python version), caveats, and rerun command. Include a results section that can paste the JSON summary from `artifacts/benchmarks/tts-vendor-latest.json`.
  - **Why**: The comparison is useful only if readers understand scope. This prevents overclaiming while still showing technical decision-making around TTFB and interactive voice UX.
  - **Pattern**: Cite ElevenLabs model / latency docs and OpenAI Speech API docs. Use clear prose; no vendor-superiority claims beyond the measured run.
  - **Verify**: The doc links to the CLI, Gradio tab, and raw JSON artifact path; all links resolve.

- [ ] **7.8 Technical exploration report**
  - **File**: `docs/reports/technical-exploration-report.md` (create new), `README.md` (link only)
  - **What**: Create a standalone report with sections: Executive Summary, Strategic Framing, Architecture Overview, Demo Portfolio, Benchmark Results, Testing Evidence, Product Insights, Risks and Limitations, and Next Steps. It should link to PRD, task list, scenario docs, benchmark methodology, and generated artifacts under `artifacts/reports/` / `artifacts/benchmarks/`.
  - **Why**: Gives a reader the strategic and technical story before they inspect code. This is the polished artifact that ties product intuition, architecture, evidence, and implementation discipline together.
  - **Pattern**: English, concise, evidence-based. Frame as a hands-on product/engineering exploration; avoid external-evaluation or attention-seeking framing. Use caveats for benchmark and coverage numbers.
  - **Verify**: A reader can understand what was built, why it matters, how it was verified, and where to inspect raw evidence without opening any Python file.

---

### 8.0 Release quality gates (before marking exploration complete)

Run these once Tasks 1–7 are implemented:

| Gate | Command / action |
|---|---|
| Unit/integration evidence | `uv run pytest -n auto --junitxml=artifacts/reports/pytest.xml` |
| Coverage ≥80% on `src/eleven_demo/` | `uv run pytest --cov=src/eleven_demo --cov-report=term --cov-report=xml:artifacts/reports/coverage.xml --cov-report=html:artifacts/reports/htmlcov --cov-fail-under=80 -m "not integration"` |
| Lint + format | `uv run ruff check .` and `uv run ruff format --check .` |
| Pre-commit | `uv run pre-commit run --all-files` (must pass clean at repo root; capture output in `artifacts/reports/pre-commit.txt` if possible) |
| Integration replay | `uv run pytest -m integration --junitxml=artifacts/reports/integration-pytest.xml` (VCR cassettes committed; may skip locally without key per `conftest`) |
| Vendor benchmark smoke | `uv run python scripts/tts_vendor_benchmark.py --n 1 --out artifacts/benchmarks/tts-vendor-latest.json` (requires both API keys; otherwise verify graceful skip/setup message) |
| Final report | Update `docs/reports/technical-exploration-report.md` with the latest coverage, test, benchmark, and caveat summaries |

- [ ] **8.1 Generate evidence artifacts**
  - **File**: `artifacts/reports/pytest.xml`, `artifacts/reports/integration-pytest.xml`, `artifacts/reports/coverage.xml`, `artifacts/reports/htmlcov/`, `artifacts/reports/pre-commit.txt`, `artifacts/benchmarks/tts-vendor-latest.json` (generated), optionally `scripts/generate_evidence_report.py` (create new if manual report assembly becomes repetitive)
  - **What**: Run the release commands above and store outputs in predictable artifact paths. If `scripts/generate_evidence_report.py` is created, it should read the JUnit XML, coverage XML, and vendor benchmark JSON, then print or update the Testing Evidence / Benchmark Results sections of `docs/reports/technical-exploration-report.md`.
  - **Why**: Makes verification portable. A reader can inspect both the curated report and raw machine-readable evidence.
  - **Security**: Do not write API keys, authorization headers, raw CPF, card numbers, emails, phone numbers, or unredacted conversation transcripts into artifacts. Redact or summarize.
  - **Verify**: Artifact paths exist after the release run; opening `docs/reports/technical-exploration-report.md` shows the latest test, coverage, and benchmark summaries.

---

## Suggested commit log (one commit per sub-task or tight cluster)

The following Conventional Commits map cleanly onto the sub-tasks; split rows further if any single commit would exceed ~300 lines.

| Commit | Covers |
|---|---|
| `chore: scaffold python package layout` | 1.1 |
| `feat(config): add typed settings via pydantic-settings` | 1.2 |
| `test(config): unit tests for settings` | 1.5 |
| `feat(client): add elevenlabs sdk factory with retry` | 1.3 |
| `test(client): shared fixtures and client retry tests` | 1.4, 1.6 |
| `feat(tts): add synchronous tts module` | 2.1 |
| `feat(tts): add http streaming tts with ttfb` | 2.2 |
| `feat(tts): add websocket tts streaming` | 2.3 |
| `feat(stt): add batch transcription module` | 2.4 |
| `feat(stt): add realtime websocket transcription` | 2.5 |
| `test(tts,stt): add vcr integration tests` | 2.6, 2.7 |
| `feat(voices): add voice library catalog with pt-br filter` | 3.1 |
| `feat(metrics): add ttfb decorator and latency report` | 3.2 |
| `feat(scripts): add tts_demo cli` | 3.3 |
| `feat(scripts): add tts_stream_ttfb cli` | 3.4 |
| `feat(scripts): add stt_demo cli` | 3.5 |
| `feat(scripts): add voices_pt_br cli` | 3.6 |
| `build: add openai benchmark dependency and settings` | 3.7 |
| `feat(benchmarks): add openai tts streaming adapter` | 3.8 |
| `feat(benchmarks): add tts vendor report model` | 3.9 |
| `feat(scripts): add tts vendor benchmark cli` | 3.10 |
| `test(benchmarks): add vendor benchmark tests` | 3.11 |
| `feat(agents): add factory with idempotent upsert` | 4.1 |
| `feat(agents): add server tools registry` | 4.2 |
| `feat(agents): add knowledge base helpers` | 4.3 |
| `feat(agents): add simulate wrapper` | 4.4 |
| `test(agents): unit tests for agents core` | 4.5 |
| `feat(scenarios): add scenario base contract` | 5.1 |
| `feat(scenarios): add telecom scenario` | 5.2 |
| `feat(scenarios): add banking scenario` | 5.3 |
| `feat(scenarios): add healthcare scenario with kb seed` | 5.4 |
| `feat(scripts): add agent_create and agent_simulate` | 5.5 |
| `test(scenarios): add regression tests via simulate` | 5.6 |
| `feat(apps): add gradio app skeleton` | 6.1 |
| `feat(apps): add tts playground tab` | 6.2 |
| `feat(apps): add telecom and banking tabs with signed urls` | 6.3 |
| `feat(apps): add healthcare tab with rag source panel` | 6.4 |
| `feat(apps): add latency benchmark tab` | 6.5 |
| `feat(apps): add vendor benchmark tab` | 6.6 |
| `feat(apps): add fastapi websocket bridge` | 6.7 (stretch) |
| `docs(scenarios): add telecom storytelling` | 7.1 |
| `docs(scenarios): add banking storytelling` | 7.2 |
| `docs(scenarios): add healthcare storytelling` | 7.3 |
| `docs: add repository walkthrough` | 7.4 |
| `docs(readme): final polish and link audit` | 7.5 |
| `feat(scripts): add conversations list cli` | 7.6 |
| `docs(architecture): document post-call webhook alternative` | 7.6 (same commit as script acceptable if small) |
| `docs(benchmarks): add tts vendor methodology` | 7.7 |
| `docs(reports): add technical exploration report` | 7.8 |
| `chore(release): generate evidence artifacts` | 8.1 |

---

**Execution flow**: open this file, find the next `[ ]` sub-task, implement, run the Verify command, mark `[x]`, and commit. The `.cursor/commands/development.md` workflow will pause between sub-tasks for confirmation. Update the "Relevant Files" section at the top whenever a new file is created.
