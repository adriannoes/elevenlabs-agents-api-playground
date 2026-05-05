# ElevenLabs UI Reference App

This small Next.js app shows the same Telecom ElevenAgents scenario used by
`apps/gradio_app.py`, but through the official `elevenlabs/ui` registry and
`@elevenlabs/react`.

It is a brand-inspired reference surface, not an official ElevenLabs product.

## Prerequisites

- Node 20+ and pnpm.
- An ElevenLabs API key.
- A Telecom agent created with `uv run python scripts/agent_create.py telecom`.

## Setup

```bash
cp .env.example .env.local
pnpm install
pnpm dev
```

Open <http://localhost:3000>.

## Environment

Use the same variable names as the Python demo so values can be copied without
renaming:

- `ELEVENLABS_API_KEY`
- `DEMO_AGENT_ID_TELECOM`

## Security Notes

`ELEVENLABS_API_KEY` is read only by `app/api/signed-url/route.ts`. The browser
receives `{ "signedUrl": "..." }` and never receives the raw API key.

Keep real values in `.env.local`, which is ignored by Git. Use HTTPS/TLS for any
deployment beyond local development so signed session URLs and microphone traffic
are protected in transit.
