import { test } from "node:test"
import assert from "node:assert/strict"
import { mkdtempSync, readFileSync, rmSync, statSync } from "node:fs"
import { tmpdir } from "node:os"
import { join } from "node:path"

const source = readFileSync(new URL("./observer.js", import.meta.url), "utf8")
const observer = (await import(`data:text/javascript;base64,${Buffer.from(source).toString("base64")}`)).default
const encoder = new TextEncoder()
const scope = { sessionID: "session-a", agent: "navigator", kind: "primary", model: { providerID: "openai", id: "sol", variant: "fast-low" } }

async function harness(fn) {
  const dir = mkdtempSync(join(tmpdir(), "observer-"))
  const file = join(dir, "requests.jsonl")
  const previous = process.env.OPENCODE_OBSERVATION_FILE
  process.env.OPENCODE_OBSERVATION_FILE = file
  const callbacks = new Map()
  const disposed = []
  const cleanup = await observer.setup({ session: { async hook(name, callback) {
    callbacks.set(name, callback)
    return { async dispose() { disposed.push(name) } }
  } } })
  try {
    await fn({
      invoke: (name, evt) => callbacks.get(name)(evt), file,
      rows: () => readFileSync(file, "utf8").trim().split("\n").map((line) => JSON.parse(line)),
    })
    await cleanup()
    assert.equal(disposed.length, 5)
  } finally {
    if (previous === undefined) delete process.env.OPENCODE_OBSERVATION_FILE
    else process.env.OPENCODE_OBSERVATION_FILE = previous
    rmSync(dir, { recursive: true, force: true })
  }
}

function request(body) {
  return new Request("https://example.test/v1/responses?credential=NEVER_LOG_SECRET", {
    method: "POST", headers: { authorization: "Bearer NEVER_LOG_TOKEN", "content-type": "application/json" },
    body: JSON.stringify(body),
  })
}

function bytesStream(bytes, size = 1) {
  let offset = 0
  return new ReadableStream({ pull(controller) {
    if (offset === bytes.length) { controller.close(); return }
    controller.enqueue(bytes.slice(offset, offset + size))
    offset = Math.min(bytes.length, offset + size)
  } })
}

test("HTTP SSE preserves bytes, status, headers and captures split UTF8 multiline metadata", async () => {
  await harness(async ({ invoke, rows, file }) => {
    const req = request({ model: "sol", reasoning: { effort: "low" }, service_tier: "priority", input: "NEVER_LOG_PROMPT" })
    const original = await req.clone().text()
    await invoke("http.request", { ...scope, request: req })
    assert.equal(await req.clone().text(), original)
    const text = ': olá 🍋\r\nevent: response.completed\r\ndata: {"type":"response.completed",\r\ndata: "response":{"model":"sol","service_tier":"priority","usage":{"input_tokens":2,"output_tokens":3,"secret":"NEVER_LOG_USAGE"},"output":"NEVER_LOG_ANSWER"}}\r\n\r\ndata: [DONE]\r\n\r\n'
    const bytes = encoder.encode(text)
    const evt = { ...scope, request: req, response: new Response(bytesStream(bytes), {
      status: 201, statusText: "Created", headers: { "content-type": "text/event-stream", "retry-after": "3", "x-secret": "NEVER_LOG_HEADER" },
    }) }
    await invoke("http.response", evt)
    assert.equal(evt.response.status, 201)
    assert.equal(evt.response.statusText, "Created")
    assert.equal(evt.response.headers.get("retry-after"), "3")
    assert.deepEqual(new Uint8Array(await evt.response.arrayBuffer()), bytes)
    const observed = rows()
    assert.equal(observed[0].event, "ready")
    assert.equal(statSync(file).mode & 0o777, 0o600)
    const sent = observed.find((row) => row.event === "request")
    assert.deepEqual(sent.request, { model: "sol", service_tier: "priority", reasoning_effort: "low" })
    assert.equal(sent.url, "https://example.test/v1/responses")
    assert.equal(sent.identity.variant, "fast-low")
    const received = observed.find((row) => row.response?.event_type === "response.completed")
    assert.deepEqual(received.response, { model: "sol", service_tier: "priority", event_type: "response.completed", usage: { input_tokens: 2, output_tokens: 3 } })
    assert.equal(received.call_id, sent.call_id)
    assert.equal(observed.at(-1).event, "end")
    assert.ok(!readFileSync(file, "utf8").includes("NEVER_LOG"))
    assert.ok(!readFileSync(file, "utf8").includes("password"))
  })
})

test("HTTP hook returns before EOF, cancellation propagates and does not expose reason", async () => {
  await harness(async ({ invoke, rows }) => {
    let cancelled = false
    const req = request({ model: "sol" })
    await invoke("http.request", { ...scope, request: req })
    const evt = { ...scope, request: req, response: new Response(new ReadableStream({
      start(controller) { controller.enqueue(encoder.encode("data: {\"model\":\"sol\"}\n\n")) },
      cancel() { cancelled = true },
    }), { headers: { "content-type": "text/event-stream" } }) }
    await invoke("http.response", evt)
    const reader = evt.response.body.getReader()
    assert.equal((await reader.read()).done, false)
    await reader.cancel("NEVER_LOG_CANCEL")
    assert.equal(cancelled, true)
    assert.ok(rows().some((row) => row.error === "stream_cancelled"))
    assert.equal(rows().at(-1).event, "end")
    assert.ok(!JSON.stringify(rows()).includes("NEVER_LOG"))
  })
})

test("HTTP stream error propagates unchanged with sanitized metadata", async () => {
  await harness(async ({ invoke, rows }) => {
    const req = request({ model: "sol" })
    await invoke("http.request", { ...scope, request: req })
    const failure = new Error("NEVER_LOG_PROVIDER_SECRET")
    const evt = { ...scope, request: req, response: new Response(new ReadableStream({ start(controller) { controller.error(failure) } })) }
    await invoke("http.response", evt)
    await assert.rejects(evt.response.arrayBuffer(), (error) => error === failure)
    assert.ok(rows().some((row) => row.error === "stream_failure"))
    assert.ok(!JSON.stringify(rows()).includes("NEVER_LOG"))
  })
})

test("Anthropic low/medium/high/xhigh and message_start/message_delta capture whitelisted effort and usage", async () => {
  await harness(async ({ invoke, rows }) => {
    for (const effort of ["low", "medium", "high", "xhigh"]) {
      const req = request({ model: "claude-sonnet-5-5", output_config: { effort }, thinking: { type: "adaptive" }, max_tokens: 32768 })
      await invoke("http.request", { ...scope, request: req })
      const text = 'event: message_start\ndata: {"type":"message_start","message":{"model":"claude-sonnet-5-5","usage":{"input_tokens":3,"cache_read_input_tokens":4}}}\n\nevent: content_block_delta\ndata: {"type":"content_block_delta","delta":{"text":"NEVER_LOG_TOKEN"}}\n\nevent: message_delta\ndata: {"type":"message_delta","usage":{"output_tokens":5},"delta":{"text":"NEVER_LOG_DELTA"}}\n\n'
      const evt = { ...scope, request: req, response: new Response(bytesStream(encoder.encode(text), 3), { headers: { "content-type": "text/event-stream" } }) }
      await invoke("http.response", evt)
      await evt.response.arrayBuffer()
    }
    assert.deepEqual(rows().filter((row) => row.event === "request").map((row) => row.request.reasoning_effort), ["low", "medium", "high", "xhigh"])
    assert.equal(new Set(rows().filter((row) => row.event === "request").map((row) => row.call_id)).size, 4)
    assert.equal(rows().filter((row) => row.response?.model === "claude-sonnet-5-5").length, 4)
    assert.equal(rows().filter((row) => row.response?.usage?.output_tokens === 5).length, 4)
    assert.ok(!rows().some((row) => row.response?.event_type === "content_block_delta"))
    assert.ok(!JSON.stringify(rows()).includes("NEVER_LOG"))
  })
})

test("JSON responses parse at EOF and retain HTTP failure status without provider errors", async () => {
  await harness(async ({ invoke, rows }) => {
    const req = request({ model: "deepseek", reasoning_effort: "max" })
    await invoke("http.request", { ...scope, request: req })
    const evt = { ...scope, request: req, response: new Response(bytesStream(encoder.encode(JSON.stringify({
      model: "deepseek", usage: { completion_tokens_details: { reasoning_tokens: 9, private: "NEVER_LOG" } }, error: { message: "NEVER_LOG" },
    }))), { status: 429, headers: { "content-type": "application/json", "retry-after": "7" } }) }
    await invoke("http.response", evt)
    await evt.response.text()
    assert.equal(evt.response.headers.get("retry-after"), "7")
    assert.equal(rows().at(-1).status, 429)
    assert.deepEqual(rows().find((row) => row.response?.usage).response.usage, { completion_tokens_details: { reasoning_tokens: 9 } })
    assert.ok(rows().some((row) => row.error === "provider_failure"))
    assert.ok(!JSON.stringify(rows()).includes("NEVER_LOG"))
  })
})

test("WebSocket frames remain byte-exact, fresh requests correlate new IDs and failed calls cannot pass", async () => {
  await harness(async ({ invoke, rows }) => {
    const handshake = { ...scope, url: "wss://example.test/responses?credential=NEVER_LOG", headers: { authorization: "NEVER_LOG" } }
    await invoke("experimental.ws.handshake", handshake)
    assert.equal(handshake.url, "wss://example.test/responses?credential=NEVER_LOG")
    for (const terminal of ["response.completed", "response.incomplete", "response.failed", "error"]) {
      const outbound = { ...scope, frame: '{ "type":"response.create", "model":"sol", "reasoning":{"effort":"low"}, "service_tier":"priority", "input":"NEVER_LOG" }' }
      const raw = outbound.frame
      await invoke("experimental.ws.send", outbound)
      assert.equal(outbound.frame, raw)
      for (const type of ["response.created", terminal]) {
        const incoming = { ...scope, frame: JSON.stringify({ type, response: { model: "sol", service_tier: "priority", usage: { output_tokens: 2 }, output: "NEVER_LOG" }, error: terminal === "error" ? { message: "NEVER_LOG" } : undefined }) }
        const frame = incoming.frame
        await invoke("experimental.ws.receive", incoming)
        assert.equal(incoming.frame, frame)
      }
    }
    const sent = rows().filter((row) => row.event === "request")
    assert.equal(new Set(sent.map((row) => row.call_id)).size, 4)
    assert.ok(sent.every((row) => row.call_id.startsWith(`${process.pid}-`)))
    for (const row of sent) {
      assert.equal(row.url, "wss://example.test/responses")
      const completed = rows().filter((event) => event.call_id === row.call_id && event.event === "end")
      assert.equal(completed.length, 1)
    }
    assert.deepEqual(rows().filter((row) => row.event === "end").map((row) => row.status), [200, 502, 502, 502])
    assert.ok(!JSON.stringify(rows()).includes("NEVER_LOG"))
  })
})

test("missing observation destination fails setup", async () => {
  const previous = process.env.OPENCODE_OBSERVATION_FILE
  delete process.env.OPENCODE_OBSERVATION_FILE
  try { await assert.rejects(observer.setup({}), /Observation file is required/) }
  finally { if (previous !== undefined) process.env.OPENCODE_OBSERVATION_FILE = previous }
})
