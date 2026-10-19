import { spawn } from "node:child_process"
import { appendFileSync } from "node:fs"

export function executeTerminal(command, timeout, signal, { docker, container }) {
  if (typeof command !== "string" || !command.trim() || command.length > 65536) throw new Error("Invalid terminal command")
  if (!Number.isInteger(timeout) || timeout < 1 || timeout > 180000) throw new Error("Invalid terminal timeout")
  if (!/^[a-f0-9]{12,64}$/.test(container)) throw new Error("Invalid private container identity")
  return new Promise((resolve, reject) => {
    if (signal?.aborted) { reject(new Error("Terminal aborted")); return }
    const child = spawn(docker, ["exec", "--workdir", "/workspace", container, "sh", "-c", command], {
      stdio: ["ignore", "pipe", "pipe"], env: { PATH: process.env.PATH, HOME: process.env.HOME, DOCKER_HOST: process.env.DOCKER_HOST },
    })
    let output = "", truncated = false, cancelled = false, timedOut = false, stopped
    const collect = (bytes) => {
      output += bytes.toString()
      if (output.length > 65536) { output = output.slice(-65536); truncated = true }
    }
    child.stdout.on("data", collect)
    child.stderr.on("data", collect)
    const stop = () => {
      if (cancelled) return
      cancelled = true
      stopped = new Promise((resolveStop) => {
        const killer = spawn(docker, ["kill", container], { stdio: "ignore", env: { PATH: process.env.PATH, HOME: process.env.HOME, DOCKER_HOST: process.env.DOCKER_HOST } })
        const timer = setTimeout(() => { killer.kill("SIGKILL"); resolveStop(false) }, 15000)
        killer.on("error", () => { clearTimeout(timer); resolveStop(false) })
        killer.on("close", (code) => { clearTimeout(timer); resolveStop(code === 0) })
      })
      child.kill("SIGKILL")
    }
    const timer = setTimeout(() => { timedOut = true; stop() }, timeout)
    signal?.addEventListener("abort", stop, { once: true })
    const cleanup = () => { clearTimeout(timer); signal?.removeEventListener("abort", stop) }
    child.on("error", (error) => { cleanup(); reject(error) })
    child.on("close", async (exitCode, signalName) => {
      cleanup()
      if (stopped && !(await stopped)) { reject(new Error("Private container cancellation failed")); return }
      resolve({ output, exit_code: exitCode, signal: signalName, cancelled, timeout: timedOut, truncated })
    })
  })
}

export function exposedToolName(tool) {
  return tool.options?.namespace === undefined ? tool.name : `${tool.options.namespace.replaceAll(".", "_")}_${tool.name}`
}

export default {
  id: "haiku-serena-surface",
  async setup(ctx) {
    const allowed = new Set(JSON.parse(process.env.EVAL_ALLOWED_TOOLS))
    const role = process.env.EVAL_ROLE
    const log = process.env.EVAL_SURFACE_LOG
    let allowedIds = new Set()
    const record = (tools) => {
      allowedIds = new Set(tools.filter((tool) => allowed.has(exposedToolName(tool))).map((tool) => tool.id))
      appendFileSync(log, JSON.stringify({ event: "surface", at_ms: Date.now(), tools: tools.map((tool) => ({ id: tool.id, name: exposedToolName(tool), raw_name: tool.name, namespace: tool.options?.namespace })) }) + "\n", { mode: 0o600 })
    }
    const registration = await ctx.tool.transform((editor) => {
      for (const tool of editor.list()) if (!allowed.has(exposedToolName(tool)) || exposedToolName(tool) === "terminal") editor.remove(tool.id)
      if (role === "implementation") editor.add({
        name: "terminal",
        options: { codemode: false, permission: "terminal" },
        description: "Run a command in the isolated Linux project at /workspace. Read and edit project files and run checks. Python 3, Node 24.9.0 and TypeScript 5.9.3 are installed. Network is unavailable. Timeout stops the workspace process tree.",
        input: { type: "object", properties: { command: { type: "string", minLength: 1, maxLength: 65536 }, timeout: { type: "integer", minimum: 1, maximum: 180000 } }, required: ["command"], additionalProperties: false },
        execute: async (input, context) => {
          const result = await executeTerminal(input.command, input.timeout ?? 120000, context.signal, { docker: process.env.OPENCODE_DOCKER_BINARY, container: process.env.OPENCODE_CODE_CONTAINER })
          appendFileSync(process.env.OPENCODE_TERMINAL_LOG, JSON.stringify({ event: "terminal", session_id: context.sessionID, call_id: context.id, exit_code: result.exit_code, cancelled: result.cancelled, timeout: result.timeout }) + "\n", { mode: 0o600 })
          return { content: JSON.stringify(result) }
        },
      })
      record(editor.list())
    })
    const guard = await ctx.tool.hook("execute.before", (event) => {
      if (!allowedIds.has(event.tool)) throw new Error("Tool execution outside the frozen surface refused")
    })
    const poll = setInterval(async () => { try { record(await ctx.tool.list()) } catch {} }, 1000)
    record(await ctx.tool.list())
    return async () => { clearInterval(poll); await guard.dispose(); await registration.dispose() }
  },
}
