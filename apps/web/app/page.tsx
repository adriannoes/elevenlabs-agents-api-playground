import { TelecomAgentConsole } from "@/components/telecom-agent-console"

export default function Home() {
  const apiKeyConfigured = Boolean(process.env.ELEVENLABS_API_KEY)
  const agentConfigured = Boolean(process.env.DEMO_AGENT_ID_TELECOM)

  return (
    <main className="min-h-screen bg-[var(--demo-bg)] px-6 py-8 text-foreground sm:px-10 lg:px-16">
      <div className="mx-auto flex max-w-6xl flex-col gap-8">
        <header className="rounded-[2rem] border bg-card/90 p-8 shadow-sm">
          <p className="text-sm font-medium uppercase tracking-[0.24em] text-[var(--agents-accent)]">
            ElevenLabs Vertical Exploration
          </p>
          <div className="mt-4 grid gap-6 lg:grid-cols-[1.2fr_0.8fr] lg:items-end">
            <div>
              <h1 className="text-4xl font-semibold tracking-tight sm:text-6xl">
                Next.js reference surface for ElevenAgents
              </h1>
              <p className="mt-5 max-w-2xl text-base leading-7 text-muted-foreground">
                A minimal App Router demo that connects the shared Telecom
                agent through the official ElevenLabs UI registry and
                server-minted signed URLs.
              </p>
            </div>
            <div className="rounded-2xl border bg-muted/40 p-4 text-sm text-muted-foreground">
              <p className="font-medium text-foreground">Environment status</p>
              <ul className="mt-3 space-y-2">
                <li>
                  ELEVENLABS_API_KEY:{" "}
                  <strong className="text-foreground">
                    {apiKeyConfigured ? "configured" : "missing"}
                  </strong>
                </li>
                <li>
                  DEMO_AGENT_ID_TELECOM:{" "}
                  <strong className="text-foreground">
                    {agentConfigured ? "configured" : "missing"}
                  </strong>
                </li>
              </ul>
            </div>
          </div>
        </header>

        <TelecomAgentConsole
          agentConfigured={agentConfigured}
          apiKeyConfigured={apiKeyConfigured}
        />

        <footer className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border bg-card/80 px-5 py-4 text-sm text-muted-foreground">
          <span>
            Brand-inspired local demo, not an official ElevenLabs product.
          </span>
          <span>
            Same agent contract as <code>apps/gradio_app.py</code>.
          </span>
        </footer>
      </div>
    </main>
  )
}
