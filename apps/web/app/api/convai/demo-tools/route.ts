import { NextResponse } from "next/server"

export const runtime = "nodejs"
export const dynamic = "force-dynamic"

const DEFAULT_BRIDGE_TOOLS_URL =
  "http://127.0.0.1:8788/convai/demo-tools"

type ErrorBody = {
  error: string
}

/**
 * Proxies Convai webhook tool POSTs from a public HTTPS origin (tunnel → Next.js)
 * to the local uvicorn ws_bridge (`/convai/demo-tools`).
 */
export async function POST(
  req: Request
): Promise<NextResponse<unknown | ErrorBody>> {
  const bridgeUrl =
    process.env.INTERNAL_WS_BRIDGE_TOOLS_URL ?? DEFAULT_BRIDGE_TOOLS_URL

  const payload = await req.arrayBuffer()
  const headers: Record<string, string> = {
    Accept: "application/json",
  }
  const contentType = req.headers.get("Content-Type")
  if (contentType) {
    headers["Content-Type"] = contentType
  } else if (payload.byteLength > 0) {
    headers["Content-Type"] = "application/json"
  }

  let upstream: Response
  try {
    upstream = await fetch(bridgeUrl, {
      method: "POST",
      headers,
      body: payload.byteLength === 0 ? undefined : payload,
    })
  } catch (error) {
    console.error("Convai demo-tools proxy upstream error:", error)
    return NextResponse.json(
      {
        error:
          "Tool bridge unreachable. Start the stack (`pnpm --dir apps/web run demo` or scripts/demo_stack.py) or set INTERNAL_WS_BRIDGE_TOOLS_URL.",
      },
      { status: 503 }
    )
  }

  const text = await upstream.text()

  try {
    const parsed = JSON.parse(text) as unknown
    return NextResponse.json(parsed, { status: upstream.status })
  } catch {
    return new NextResponse(text, {
      status: upstream.status,
      headers: {
        "Content-Type":
          upstream.headers.get("Content-Type") ?? "text/plain; charset=utf-8",
      },
    })
  }
}
