import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js"
import { NextResponse } from "next/server"

export const runtime = "nodejs"
export const dynamic = "force-dynamic"

type SignedUrlResponse = {
  signedUrl: string
}

type ErrorResponse = {
  error: string
}

export async function GET(): Promise<
  NextResponse<SignedUrlResponse | ErrorResponse>
> {
  const apiKey = process.env.ELEVENLABS_API_KEY
  const agentId = process.env.DEMO_AGENT_ID_TELECOM

  if (!apiKey || !agentId) {
    return NextResponse.json(
      {
        error:
          "Missing ELEVENLABS_API_KEY or DEMO_AGENT_ID_TELECOM in apps/web/.env.local.",
      },
      { status: 503 }
    )
  }

  try {
    const client = new ElevenLabsClient({ apiKey })
    const response =
      await client.conversationalAi.conversations.getSignedUrl({
        agentId,
      })

    return NextResponse.json({ signedUrl: response.signedUrl })
  } catch (error) {
    console.error("ElevenLabs API Error:", error)
    return NextResponse.json(
      { error: "Unable to create a signed ElevenLabs conversation URL." },
      { status: 502 }
    )
  }
}
