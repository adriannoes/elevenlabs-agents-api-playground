---
name: elevenlabs-docs
description: Look up real-time, authoritative information about any ElevenLabs product, endpoint, model, SDK, or feature by fetching the live documentation. Use whenever the user asks about ElevenLabs, ElevenAgents, ElevenAPI, ElevenCreative, voice cloning, TTS, STT, dubbing, music, sound effects, agents, telephony (Twilio/SIP/Plivo/Vonage), WebSocket events, pricing, models (Eleven v3, Flash, Multilingual, Scribe), or any term that appears in the ElevenLabs platform.
license: MIT
compatibility: Requires network access to `elevenlabs.io` documentation; API key optional unless testing live endpoints.
---

# ElevenLabs Documentation Lookup

Official Agent Skills bundles from ElevenLabs: [github.com/elevenlabs/skills](https://github.com/elevenlabs/skills).

For runnable code snippets, prefer **`@elevenlabs/elevenlabs-js`** (`npm install @elevenlabs/elevenlabs-js`) in Node/TypeScript; the npm package literally named `elevenlabs` is legacy v1.x.

Authoritative source of truth for anything ElevenLabs. The docs change frequently; always fetch instead of relying on memory.

## Lookup Protocol

Follow this 3-step protocol. Stop as soon as you have the answer.

### Step 1 — Index First (cheap, fast)

Fetch the LLM-optimized index to discover the exact page URL:

```
https://elevenlabs.io/docs/llms.txt
```

Search the returned list for the term (e.g. "Tools", "WebSocket", "Knowledge base", "Twilio"). Each entry is `[Page Title](URL): description`.

If the answer is small and the user just needs a pointer, return the URL + one-line description from the index.

### Step 2 — Fetch the Specific Page

When you need details, fetch the canonical URL from step 1:

```
https://elevenlabs.io/docs/<section>/<page>
```

Strip any `.mdx` suffix; the public URL works without it.

### Step 3 — Fall Back to Full Dump (last resort)

Only if the index is ambiguous and several pages might be relevant:

```
https://elevenlabs.io/docs/llms-full.txt
```

This is large (multi-MB). Prefer Step 2 whenever possible.

## Section Map

The docs are organized in 5 top-level areas. Use this map to jump directly to the right URL prefix.

| Area | URL prefix | Use for |
|---|---|---|
| Overview & capabilities | `/docs/overview/` | Models, capabilities, billing, workspaces, SSO |
| ElevenCreative | `/docs/eleven-creative/` | Studio, audiobooks, dubbing, music, voice cloning UX |
| ElevenAgents | `/docs/eleven-agents/` | Voice agents: build, integrate, operate, telephony |
| ElevenAPI | `/docs/eleven-api/` | Cookbooks, latency concepts, streaming, security |
| API Reference | `/docs/api-reference/` | REST + WebSocket endpoints (request/response schemas) |

## High-Value Entry Points

Memorize these — they answer ~80% of questions.

### Models & Capabilities

- `https://elevenlabs.io/docs/overview/models` — current model lineup, latencies, languages
- `https://elevenlabs.io/docs/eleven-api/concepts/latency` — what contributes to latency, tradeoffs
- `https://elevenlabs.io/docs/eleven-api/guides/how-to/best-practices/latency-optimization` — concrete tips

### ElevenAgents (the Brazil-focused product)

- `https://elevenlabs.io/docs/eleven-agents/overview` — platform overview + capability matrix
- `https://elevenlabs.io/docs/eleven-agents/quickstart` — 5-minute first agent
- `https://elevenlabs.io/docs/eleven-agents/best-practices/prompting-guide` — production prompting
- `https://elevenlabs.io/docs/eleven-agents/customization/tools` — client / server / system / MCP tools
- `https://elevenlabs.io/docs/eleven-agents/customization/knowledge-base` — KB + RAG
- `https://elevenlabs.io/docs/eleven-agents/customization/agent-workflows` — visual graph workflows
- `https://elevenlabs.io/docs/eleven-agents/libraries/web-sockets` — low-level real-time protocol
- `https://elevenlabs.io/docs/eleven-agents/phone-numbers/twilio-integration/native-integration` — telephony
- `https://elevenlabs.io/docs/eleven-agents/customization/agent-testing` — automated agent tests
- `https://elevenlabs.io/docs/eleven-agents/operate/experiments` — A/B testing in production

### ElevenAPI (TTS / STT / Voices)

- `https://elevenlabs.io/docs/api-reference/text-to-speech/convert` — sync TTS
- `https://elevenlabs.io/docs/api-reference/text-to-speech/stream` — HTTP chunked stream
- `https://elevenlabs.io/docs/api-reference/text-to-speech/v-1-text-to-speech-voice-id-stream-input` — TTS WebSocket
- `https://elevenlabs.io/docs/api-reference/text-to-speech/v-1-text-to-speech-voice-id-multi-stream-input` — Multi-Context WebSocket (real-time agents)
- `https://elevenlabs.io/docs/api-reference/speech-to-text/convert` — STT batch
- `https://elevenlabs.io/docs/api-reference/speech-to-text/v-1-speech-to-text-realtime` — STT realtime WebSocket
- `https://elevenlabs.io/docs/api-reference/voices/search` — list voices (filter by language, gender, accent)

### Specs (when you need exact schemas)

- `https://elevenlabs.io/openapi.json` — REST OpenAPI 3.1
- `https://elevenlabs.io/asyncapi.json` — WebSocket AsyncAPI 2.6

## Search Patterns

When the user asks about a specific concept, map it to a URL pattern before fetching.

| User asks about | Look at |
|---|---|
| "how to give my agent tools" | `/docs/eleven-agents/customization/tools` |
| "how to add knowledge / RAG" | `/docs/eleven-agents/customization/knowledge-base` |
| "agent calls phone number" | `/docs/eleven-agents/customization/tools/system-tools/transfer-to-number` |
| "how to test agents" | `/docs/eleven-agents/customization/agent-testing` + `/docs/eleven-agents/operate/experiments` |
| "lowest latency setup" | `/docs/eleven-api/concepts/latency` + `/docs/eleven-api/guides/how-to/best-practices/latency-optimization` |
| "voice cloning" (IVC vs PVC) | `/docs/eleven-api/concepts/voice-cloning` |
| "Twilio / SIP / outbound calls" | `/docs/eleven-agents/phone-numbers/...` |
| "post-call analysis / webhooks" | `/docs/eleven-agents/workflows/post-call-webhooks` + `/docs/eleven-agents/customization/agent-analysis` |
| "reduce LLM cost" | `/docs/eleven-agents/customization/llm/optimizing-costs` |
| "compliance / HIPAA / TCPA / LGPD" | `/docs/eleven-agents/legal/...` + `/docs/eleven-api/resources/zero-retention-mode` |
| "data residency" | `/docs/overview/administration/data-residency` |
| "voice isolation / isolate speech / denoise recording" | search `llms.txt` → audio isolation / Voice Isolator |

## Citation Rule

When answering the user with information from a fetched page, cite the canonical URL inline so they can open and verify it. Format: `(per [docs](https://elevenlabs.io/docs/...))`.

## Anti-Patterns

- Do not invent endpoint paths or parameter names. Fetch first.
- Do not rely on training-data knowledge of model IDs (e.g. `eleven_turbo_v2_5`); confirm against `/docs/overview/models`.
- Do not fetch `llms-full.txt` casually — it costs many tokens. Use the index.
