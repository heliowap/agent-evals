import { appendFileSync, chmodSync } from "node:fs"

const hooks = ["http.request", "http.response", "experimental.ws.handshake", "experimental.ws.send", "experimental.ws.receive"]
const usageFields = new Set([
  "input_tokens", "output_tokens", "total_tokens", "prompt_tokens", "completion_tokens", "reasoning_tokens",
  "cache_read_input_tokens", "cache_creation_input_tokens", "cached_tokens", "input_tokens_details",
  "output_tokens_details", "prompt_tokens_details", "completion_tokens_details", "cache_creation",
  "ephemeral_5m_input_tokens", "ephemeral_1h_input_tokens", "accepted_prediction_tokens", "rejected_prediction_tokens",
  "audio_tokens", "text_tokens", "image_tokens",
])

function strings(value, fields) {
  return Object.fromEntries(fields.filter((key) => typeof value?.[key] === "string").map((key) => [key, value[key]]))
}

function usage(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return undefined
  const result = {}
  for (const [key, item] of Object.entries(value)) {
    if (!usageFields.has(key)) continue
    if (typeof item === "number" && Number.isFinite(item)) result[key] = item
    else if (item && typeof item === "object") {
      const nested = usage(item)
      if (nested && Object.keys(nested).length) result[key] = nested
    }
  }
  return Object.keys(result).length ? result : undefined
}

function requestMetadata(body) {
  const result = strings(body, ["model", "service_tier"])
  const effort = body?.reasoning_effort ?? body?.reasoning?.effort ?? body?.output_config?.effort
  if (typeof effort === "string") result.reasoning_effort = effort
  if (typeof body?.thinking?.type === "string") result.thinking_type = body.thinking.type
  for (const key of ["max_tokens", "max_output_tokens", "max_completion_tokens"]) {
    if (typeof body?.[key] === "number" && Number.isFinite(body[key])) result[key] = body[key]
  }
  if (typeof body?.thinking?.budget_tokens === "number" && Number.isFinite(body.thinking.budget_tokens)) {
    result.thinking_budget_tokens = body.thinking.budget_tokens
  }
  return result
}

function parse(text) {
  try { return JSON.parse(text) } catch { return undefined }
}

function location(url) {
  try {
    const parsed = new URL(url)
    return `${parsed.protocol}//${parsed.host}${parsed.pathname}`
  } catch { return undefined }
}

export default {
  id: "implementation-observer",
  async setup(ctx) {
    const file = process.env.OPENCODE_OBSERVATION_FILE
    if (!file) throw new Error("Observation file is required")
    const requests = new WeakMap()
    const sockets = new Map()
    let sequence = 0
    function write(event) {
      appendFileSync(file, JSON.stringify({ ...event, at_ms: performance.now() }) + "\n", { mode: 0o600 })
    }
    function call(evt, transport, url) {
      return {
        call_id: `${process.pid}-${++sequence}`, session_id: evt.sessionID, agent: evt.agent, kind: evt.kind,
        identity: strings(evt.model, ["id", "providerID", "variant"]), transport, url: location(url),
      }
    }
    function fail(info, code, status, detail = {}) {
      write({ ...info, event: "error", error: code, ...detail, ...(status ? { status } : {}) })
    }
    function observe(info, body, eventType, status) {
      if (!body || typeof body !== "object") return
      const type = typeof body.type === "string" ? body.type : eventType
      const nested = body.response ?? body.message ?? body
      const response = strings(nested, ["model", "service_tier"])
      const tokens = usage(nested.usage ?? body.usage)
      if (tokens) response.usage = tokens
      if ((Object.keys(response).length || ["response.completed", "response.failed", "response.incomplete", "error"].includes(type)) && typeof type === "string") response.event_type = type
      if (Object.keys(response).length) write({ ...info, event: "response", response, ...(status ? { status } : {}) })
      if (body.error || ["error", "response.failed", "response.incomplete"].includes(type)) {
        const error = body.error ?? body.response?.error ?? body.message?.error ?? {}
        fail(info, "provider_failure", status, {
          provider_code: typeof error.code === "string" || typeof error.code === "number" ? error.code : undefined,
          provider_type: typeof error.type === "string" ? error.type : undefined,
        })
      }
      return type
    }
    function wrap(info, response) {
      const isSSE = (response.headers.get("content-type") ?? "").includes("text/event-stream")
      const decoder = new TextDecoder()
      let line = "", data = [], dataSize = 0, eventType, json = "", afterCR = false, limited = false, ended = false, cancelled = false
      function end() {
        if (ended) return
        ended = true
        write({ ...info, event: "end", status: response.status })
      }
      function dispatch() {
        if (data.length) observe(info, parse(data.join("\n")), eventType, response.status)
        data = []
        dataSize = 0
        eventType = undefined
      }
      function onLine() {
        if (line === "") dispatch()
        else if (!line.startsWith(":")) {
          const colon = line.indexOf(":")
          const key = colon < 0 ? line : line.slice(0, colon)
          let value = colon < 0 ? "" : line.slice(colon + 1)
          if (value.startsWith(" ")) value = value.slice(1)
          if (key === "data") { data.push(value); dataSize += value.length }
          if (key === "event") eventType = value
        }
        line = ""
      }
      function text(chunk) {
        if (limited) return
        if (!isSSE) {
          json += chunk
          if (json.length > 2_097_152) { limited = true; json = ""; fail(info, "metadata_limit", response.status) }
          return
        }
        for (const char of chunk) {
          if (afterCR) {
            afterCR = false
            if (char === "\n") continue
          }
          if (char === "\r" || char === "\n") { onLine(); afterCR = char === "\r" }
          else line += char
          if (line.length + dataSize > 2_097_152) {
            limited = true; line = ""; data = []; fail(info, "metadata_limit", response.status); return
          }
        }
      }
      if (!response.body) { end(); return response }
      const observed = response.body.pipeThrough(new TransformStream({
        transform(chunk, controller) { text(decoder.decode(chunk, { stream: true })); controller.enqueue(chunk) },
        flush() {
          text(decoder.decode())
          if (isSSE) { if (line) onLine(); dispatch() }
          else observe(info, parse(json), undefined, response.status)
          end()
        },
      }))
      const reader = observed.getReader()
      const stream = new ReadableStream({
        async pull(controller) {
          try {
            const result = await reader.read()
            if (cancelled) return
            if (result.done) controller.close()
            else controller.enqueue(result.value)
          } catch (error) {
            if (cancelled) return
            fail(info, "stream_failure", response.status, { transport_code: typeof error?.code === "string" ? error.code : undefined })
            end()
            controller.error(error)
          }
        },
        async cancel(reason) {
          cancelled = true
          fail(info, "stream_cancelled", response.status)
          try {
            await reader.cancel(reason)
          } catch (error) {
            fail(info, "stream_cancel_failure", response.status, { transport_code: typeof error?.code === "string" ? error.code : undefined })
            throw error
          } finally { end() }
        },
      })
      return new Response(stream, { status: response.status, statusText: response.statusText, headers: response.headers })
    }
    const callbacks = {
      async "http.request"(evt) {
        const info = call(evt, "http", evt.request.url)
        requests.set(evt.request, info)
        const body = parse(await evt.request.clone().text())
        write({ ...info, event: "request", request: requestMetadata(body) })
      },
      "http.response"(evt) {
        const info = requests.get(evt.request)
        if (!info) throw new Error("Unobserved HTTP request")
        write({ ...info, event: "response", status: evt.response.status })
        evt.response = wrap(info, evt.response)
      },
      "experimental.ws.handshake"(evt) {
        const previous = sockets.get(evt.sessionID)
        sockets.set(evt.sessionID, { url: evt.url, info: previous?.info })
        write({ ...call(evt, "websocket", evt.url), event: "handshake" })
      },
      "experimental.ws.send"(evt) {
        const body = parse(evt.frame)
        if (body?.type !== "response.create") return
        const socket = sockets.get(evt.sessionID) ?? {}
        const info = call(evt, "websocket", socket.url)
        sockets.set(evt.sessionID, { ...socket, info })
        write({ ...info, event: "request", request: requestMetadata(body.response ?? body) })
      },
      "experimental.ws.receive"(evt) {
        const body = parse(evt.frame)
        const info = sockets.get(evt.sessionID)?.info
        if (!info) {
          if (body?.type === "error" || (typeof body?.type === "string" && body.type.startsWith("response."))) throw new Error("Unobserved WebSocket request")
          return
        }
        const type = observe(info, body)
        if (["response.completed", "response.failed", "response.incomplete", "error"].includes(type)) {
          write({ ...info, event: "end", status: type === "response.completed" ? 200 : 502 })
        }
      },
    }
    const registrations = []
    for (const name of hooks) registrations.push(await ctx.session.hook(name, callbacks[name]))
    write({ event: "ready", observerVersion: 1, hooks })
    chmodSync(file, 0o600)
    return async () => { for (const registration of registrations) await registration.dispose() }
  },
}
