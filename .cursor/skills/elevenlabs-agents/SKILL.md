---
name: elevenlabs-agents
description: Design, build, deploy, and operate ElevenAgents (voice and chat agents). Use when the user wants to create an agent, configure tools, knowledge base, RAG, prompting, conversation flow, voice settings, telephony (Twilio, SIP, Plivo, Vonage, WhatsApp), batch calling, agent testing, A/B experiments, post-call analysis, or anything related to ElevenLabs Conversational AI / Agents Platform / Convai.
license: MIT
compatibility: Requires `elevenlabs` Python SDK or official web/mobile SDKs, network access, and `ELEVENLABS_API_KEY` for programmatic agent management.
metadata:
  openclaw:
    requires:
      env:
        - ELEVENLABS_API_KEY
    primaryEnv: ELEVENLABS_API_KEY
---

# ElevenAgents Engineering

Reference skill pack: [github.com/elevenlabs/skills](https://github.com/elevenlabs/skills/tree/main/agents).

ElevenAgents is the conversational platform: voice or chat agents that combine ASR + LLM + TTS + a proprietary turn-taking model into a single managed product. Optimized for low-latency real-time dialogue.

For any uncertainty about endpoints, model IDs, or current parameter names, invoke the `elevenlabs-docs` skill and fetch the relevant page.

In **this repo**, initialize the REST client via `from eleven_demo.client import get_client` (`get_client()`). For portability, snippets below mirror the generic `ElevenLabs(api_key=...)` constructor.

## The 4 Components

1. **Speech-to-Text (ASR)** — fine-tuned for conversational turns
2. **Language model** — choose from supported LLMs or bring your own (`custom-llm`)
3. **Text-to-Speech (TTS)** — 5k+ voices across 70+ languages, low-latency models
4. **Turn-taking model** — proprietary, handles barge-in, interruptions, silence

This separation matters: customers can swap the LLM (cost / quality / data residency), bring their own TTS voice, or wire ASR confidence into custom logic.

## Mental Model: Build → Integrate → Operate

| Phase | What you decide | Key docs |
|---|---|---|
| Build | system prompt, voice, language(s), KB+RAG, tools, conversation flow | `/docs/eleven-agents/build/overview` |
| Integrate | web widget, React/Swift/Kotlin SDK, WebSocket, Twilio/SIP, WhatsApp | `/docs/eleven-agents/integrate/overview` |
| Operate | testing, A/B experiments, analytics, success evaluation, retention/PII | `/docs/eleven-agents/operate/overview` |

## Tool Types

| Type | Runs where | Use for |
|---|---|---|
| **Client tools** | User's device (browser/mobile) | UI actions, local state, "open this page" |
| **Server tools** | Your backend (HTTP webhook) | CRM lookups, order status, payments — anything with secrets |
| **System tools** | ElevenLabs platform | `end_call`, `language_detection`, `agent_transfer`, `transfer_to_number`, `skip_turn`, `play_keypad_touch_tone`, `voicemail_detection` |
| **MCP** | External MCP server | Plug into any MCP-exposed system (with approval policies) |

Reference: `https://elevenlabs.io/docs/eleven-agents/customization/tools`

## Python SDK Quickstart

Install:

```bash
pip install elevenlabs
```

In this repository:

```python
from eleven_demo.client import get_client

client = get_client()
```

Elsewhere:

```python
import os
from elevenlabs.client import ElevenLabs

client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])
```

### Create an agent

```python
agent = client.agents.create(
    conversation_config={
        "agent": {
            "first_message": "Hello! I'm the support assistant. How can I help?",
            "language": "en",
            "prompt": {
                "prompt": "You are a friendly English-language support agent for the telecom demo. "
                          "Always confirm the customer's identity before sharing account details. "
                          "If asked about anything outside telecom support, politely decline.",
                "llm": "gemini-2.5-flash",
                "temperature": 0.3,
            },
        },
        "tts": {"voice_id": "<voice_id>", "model_id": "eleven_turbo_v2_5"},
    },
    name="demo-telecom-support-pt",
)
```

Confirm current LLM and model IDs via `client.llm.list()` and the docs (model IDs change).

### List, update, delete

```python
agents = client.agents.list()
client.agents.update(agent_id=agent.agent_id, name="demo-telecom-support-pt-v2")
client.agents.delete(agent_id=agent.agent_id)
```

### Get a signed URL for a private session (browser SDK)

```python
signed = client.conversations.get_signed_url(agent_id=agent.agent_id)
print(signed.signed_url)
```

Pass that URL to the React/JS SDK on the client.

### Simulate a conversation (offline test)

```python
sim = client.agents.simulate_conversation(
    agent_id=agent.agent_id,
    simulation_specification={
        "simulated_user_config": {
            "first_message": "I want to cancel my line",
            "language": "en",
        }
    },
)
print(sim.analysis)
```

Use this in CI to regression-test prompt changes.

### List conversations + run analysis

```python
convs = client.conversations.list(agent_id=agent.agent_id, page_size=20)
for c in convs.conversations:
    full = client.conversations.get(conversation_id=c.conversation_id)
    print(c.conversation_id, full.analysis.call_successful, full.analysis.transcript_summary)
```

## Real-Time WebSocket (when SDK is not enough)

Endpoint: `wss://api.elevenlabs.io/v1/convai/conversation?agent_id=<id>` (use signed URL for private agents).

Events you must handle (client side):

- `conversation_initiation_metadata` — first event, contains `conversation_id`
- `audio` — base64 PCM audio chunks to play
- `user_transcript` — what the ASR heard
- `agent_response` — agent's text reply
- `interruption` — user spoke over the agent; stop playback
- `ping` / `pong` — keep-alive

Events you send:

- `user_audio_chunk` (base64) — mic input
- `pong`
- `client_tool_result` — when the agent invokes a client tool

Reference: `https://elevenlabs.io/docs/eleven-agents/customization/events/client-events`

## Latency Numbers

Quote ranges, not absolutes — they shift. For the current stack, expect (warm path, English):

- **TTFB end-to-end**: ~700ms – 1.2s (ASR end-of-turn → first audio byte)
- **TTS-only TTFB (Flash)**: ~75ms – 150ms
- **STT realtime partials**: ~200ms

Always confirm against `/docs/eleven-api/concepts/latency` before quoting in writing. The biggest knobs:

1. Region (data residency adds RTT)
2. LLM choice (Gemini Flash / Groq < GPT-4o < Claude Sonnet)
3. TTS model (Flash < Turbo < Multilingual v2 < v3)
4. KB / RAG cold cache
5. Server tool latency (counted in turn budget)

## Production-Grade Prompting (3 rules)

1. **Identity + scope first**: who you are, what you will and will not do
2. **Output constraints**: response length, formatting (no markdown for voice!), forbidden topics
3. **Tool-use guidance**: when to call which tool, what to do on failure

Full guide: `/docs/eleven-agents/best-practices/prompting-guide`

## Testing & Evaluation Workflow

1. Write **agent tests** (`/docs/eleven-agents/customization/agent-testing`) — assertions on transcript or tool calls
2. Run them via `client.agents.tests.run()` on every prompt/config change
3. Add **success evaluation criteria** (`/docs/eleven-agents/customization/agent-analysis/success-evaluation`) — scored automatically per call
4. Use **experiments** (`/docs/eleven-agents/operate/experiments`) for A/B in prod

## Telephony Decision Tree

| Customer has | Use |
|---|---|
| Twilio account | Native Twilio integration (5-min setup) |
| Owns SIP trunk | SIP trunking |
| Plivo / Vonage / Telnyx | Provider-specific integration pages |
| WhatsApp Business | WhatsApp integration (text or voice) |
| Outbound campaigns | Batch calling API |

All under `/docs/eleven-agents/phone-numbers/`.

## Compliance Talking Points

- **Zero Retention Mode (ZRM)** per-agent — no transcript / audio storage
- **Conversation history redaction** — auto-PII redaction
- **HIPAA**: `/docs/eleven-agents/legal/hipaa`
- **TCPA** (US outbound): `/docs/eleven-agents/legal/tcpa`
- **Data residency**: `/docs/overview/administration/data-residency`
- For LGPD (Brazil), combine ZRM + redaction + EU/regional residency

## Repository anchors (`elevenlabs-agents-api-playground`)

When working in this repository:

- **Visual / Gradio**: `docs/design/visual-system.md`; official logos and symbols under `docs/design/assets/logos/` and `docs/design/assets/symbols/`.
- **Agent provisioning walkthrough (Portuguese)**: `product/guides/demo-agent-setup.md`.

## Common Customer Anti-Patterns

- Asking for "ChatGPT-style" markdown output (sounds awful in TTS — strip it in the prompt)
- Putting secrets in client tools (use server tools)
- Skipping turn-taking config and getting awkward overlaps (tune `interruption_threshold`, `wait_for_user`)
- Forgetting the LLM cost in their unit economics
