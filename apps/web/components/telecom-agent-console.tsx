"use client"

import { ConversationProvider } from "@elevenlabs/react"
import { AlertCircle, CheckCircle2, LockKeyhole, Radio } from "lucide-react"
import { useCallback, useEffect, useMemo, useState } from "react"

import {
  ConversationBar,
  type ConversationBarStatus,
} from "@/components/ui/conversation-bar"
import { LiveWaveform } from "@/components/ui/live-waveform"
import { Orb, type AgentState } from "@/components/ui/orb"
import { cn } from "@/lib/utils"

type TelecomAgentConsoleProps = {
  apiKeyConfigured: boolean
  agentConfigured: boolean
}

type SignedUrlPayload = {
  signedUrl?: string
  error?: string
}

const STATUS_LABELS: Record<ConversationBarStatus, string> = {
  disconnected: "Ready",
  connecting: "Connecting",
  connected: "Live",
  disconnecting: "Disconnecting",
  error: "Needs setup",
}

function mapOrbState(
  status: ConversationBarStatus,
  mode: "speaking" | "listening"
): AgentState {
  if (status === "connecting") {
    return "thinking"
  }

  if (status !== "connected") {
    return null
  }

  return mode === "speaking" ? "talking" : "listening"
}

export function TelecomAgentConsole({
  apiKeyConfigured,
  agentConfigured,
}: TelecomAgentConsoleProps) {
  const [status, setStatus] =
    useState<ConversationBarStatus>("disconnected")
  const [mode, setMode] = useState<"speaking" | "listening">("listening")
  const [error, setError] = useState<string | null>(null)
  const [lastMessage, setLastMessage] = useState<string | null>(null)

  const ready = apiKeyConfigured && agentConfigured
  const orbState = useMemo(() => mapOrbState(status, mode), [status, mode])

  const getSignedUrl = useCallback(async (): Promise<string> => {
    setError(null)

    const response = await fetch("/api/signed-url", {
      cache: "no-store",
      headers: {
        Accept: "application/json",
      },
    })
    const payload = (await response.json()) as SignedUrlPayload

    if (!response.ok || !payload.signedUrl) {
      throw new Error(payload.error ?? "Unable to start the signed session.")
    }

    return payload.signedUrl
  }, [])

  return (
    <ConversationProvider>
      <section className="grid gap-6 lg:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
        <div className="rounded-[2rem] border bg-card/80 p-6 shadow-sm backdrop-blur">
          <div className="mb-6 flex items-center justify-between gap-3">
            <div>
              <p className="text-sm font-medium text-muted-foreground">
                Telecom voice agent
              </p>
              <h2 className="text-3xl font-semibold tracking-tight">
                Telecom Customer Care
              </h2>
            </div>
            <StatusBadge status={status} ready={ready} />
          </div>

          <div className="relative mx-auto aspect-square max-w-[360px] overflow-hidden rounded-full bg-[radial-gradient(circle_at_50%_45%,rgba(47,109,246,0.18),rgba(255,255,255,0)_64%)]">
            <SafeOrb
              agentState={orbState}
              colors={["#2f6df6", "#8fb4ff"]}
              className="absolute inset-0"
              seed={67}
            />
          </div>

          <div className="mt-6 grid gap-3 rounded-2xl border bg-background/70 p-4 text-sm text-muted-foreground">
            <div className="flex items-center gap-2 text-foreground">
              {ready ? (
                <CheckCircle2 className="h-4 w-4 text-[var(--success)]" />
              ) : (
                <AlertCircle className="h-4 w-4 text-[var(--warning)]" />
              )}
              <span className="font-medium">
                {ready
                  ? "Server-side signed URL flow is ready."
                  : "Add ELEVENLABS_API_KEY and DEMO_AGENT_ID_TELECOM."}
              </span>
            </div>
            <p>
              The browser requests only <code>/api/signed-url</code>; the raw
              ElevenLabs API key stays in the Next.js route handler.
            </p>
          </div>
        </div>

        <div className="flex min-h-[560px] flex-col justify-between rounded-[2rem] border bg-card p-6 shadow-sm">
          <div className="space-y-5">
            <div className="flex items-start gap-3 rounded-2xl border bg-muted/40 p-4">
              <LockKeyhole className="mt-0.5 h-5 w-5 text-[var(--agents-accent)]" />
              <div>
                <h3 className="font-medium">Private conversation session</h3>
                <p className="mt-1 text-sm text-muted-foreground">
                  Press the phone button below to request microphone access and
                  start the same Telecom agent used by the Gradio demo.
                </p>
              </div>
            </div>

            <div className="rounded-2xl border bg-background/70 p-4">
              <div className="mb-3 flex items-center justify-between gap-3 text-sm">
                <span className="font-medium">Microphone level</span>
                <span className="text-muted-foreground">
                  {STATUS_LABELS[status]}
                </span>
              </div>
              <LiveWaveform
                active={status === "connected"}
                processing={status === "connecting"}
                barColor="#2f6df6"
                className="rounded-xl bg-[var(--agents-accent-soft)]"
                height={72}
                mode="static"
              />
              <p className="mt-2 text-xs text-muted-foreground">
                Waveform animates while connecting; after Live, bars follow your
                mic (separate from the control bar below). The orb only moves
                during an active session.
              </p>
            </div>

            {lastMessage ? (
              <div className="rounded-2xl border bg-background/70 p-4 text-sm">
                <div className="mb-2 flex items-center gap-2 font-medium">
                  <Radio className="h-4 w-4 text-[var(--agents-accent)]" />
                  Latest message
                </div>
                <p className="text-muted-foreground">{lastMessage}</p>
              </div>
            ) : null}

            {error ? (
              <div className="rounded-2xl border border-[var(--danger)]/30 bg-[var(--danger)]/10 p-4 text-sm text-[var(--danger)]">
                {error}
              </div>
            ) : null}
          </div>

          <div
            className={cn(
              "mt-8 rounded-2xl border bg-background/80",
              !ready && "pointer-events-none opacity-50"
            )}
          >
            <ConversationBar
              getSignedUrl={getSignedUrl}
              onConnect={() => setError(null)}
              onError={(nextError) => setError(nextError.message)}
              onMessage={(message) => setLastMessage(message.message)}
              onModeChange={setMode}
              onStatusChange={setStatus}
              waveformClassName="bg-[var(--agents-accent-soft)]"
            />
          </div>
        </div>
      </section>
    </ConversationProvider>
  )
}

function SafeOrb({
  agentState,
  colors,
  className,
  seed,
}: {
  agentState: AgentState
  colors: [string, string]
  className?: string
  seed: number
}) {
  const [webglSupported, setWebglSupported] = useState(false)

  useEffect(() => {
    const canvas = document.createElement("canvas")
    const context =
      canvas.getContext("webgl") ?? canvas.getContext("experimental-webgl")

    setWebglSupported(Boolean(context))
  }, [])

  if (!webglSupported) {
    return (
      <div
        className={cn(
          "grid place-items-center bg-[radial-gradient(circle,rgba(47,109,246,0.55)_0%,rgba(143,180,255,0.32)_42%,rgba(255,255,255,0)_70%)]",
          className
        )}
      >
        <div
          className={cn(
            "h-40 w-40 rounded-full bg-[linear-gradient(135deg,#2f6df6,#8fb4ff)] opacity-80 blur-sm transition-transform",
            agentState === "talking" && "scale-110",
            agentState === "listening" && "scale-105",
            agentState === "thinking" && "scale-95"
          )}
        />
      </div>
    )
  }

  return (
    <Orb
      agentState={agentState}
      colors={colors}
      className={className}
      seed={seed}
    />
  )
}

function StatusBadge({
  status,
  ready,
}: {
  status: ConversationBarStatus
  ready: boolean
}) {
  return (
    <div
      className={cn(
        "rounded-full border px-3 py-1 text-xs font-medium",
        ready
          ? "border-[var(--agents-accent)]/20 bg-[var(--agents-accent-soft)] text-[var(--agents-accent)]"
          : "border-[var(--warning)]/30 bg-[var(--warning)]/10 text-[var(--warning)]"
      )}
    >
      {ready ? STATUS_LABELS[status] : "Setup required"}
    </div>
  )
}
