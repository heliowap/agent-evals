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

export default {
  id: "workspace-terminal",
  async setup(ctx) {
    const container = process.env.OPENCODE_CODE_CONTAINER
    const docker = process.env.OPENCODE_DOCKER_BINARY
    const log = process.env.OPENCODE_TERMINAL_LOG
    if (!docker || !container || !log) throw new Error("Private terminal runtime is required")
    const registration = await ctx.tool.transform((editor) => {
      for (const tool of editor.list()) editor.remove(tool.id)
      editor.add({
        name: "terminal",
        options: { codemode: false, permission: "terminal" },
        description: "Run a command in the Linux project workspace at /workspace. Read and edit project files with shell, Python or Node commands and run the project checks. Python 3, Node 24.9.0 and TypeScript 5.9.3 are installed. Network is unavailable. Commands cannot access the operator computer. A command timeout stops the whole workspace process tree.",
        input: { type: "object", properties: { command: { type: "string", minLength: 1, maxLength: 65536 }, timeout: { type: "integer", minimum: 1, maximum: 180000, description: "Timeout in milliseconds; default 120000" } }, required: ["command"], additionalProperties: false },
        execute: async (input, context) => {
          const result = await executeTerminal(input.command, input.timeout ?? 120000, context.signal, { docker, container })
          appendFileSync(log, JSON.stringify({ event: "terminal", session_id: context.sessionID, call_id: context.id, exit_code: result.exit_code, signal: result.signal, cancelled: result.cancelled, timeout: result.timeout }) + "\n", { mode: 0o600 })
          return { output: result, content: JSON.stringify(result) }
        },
      })
      const tools = editor.list()
      if (tools.length !== 1 || tools[0].name !== "terminal") throw new Error("Host tools remain enabled")
      appendFileSync(log, JSON.stringify({ event: "ready", tools: tools.map((tool) => ({ id: tool.id, name: tool.name })), tool_surface: "isolated_terminal_only" }) + "\n", { mode: 0o600 })
    })
    const guard = await ctx.tool.hook("execute.before", (event) => {
      if (event.tool !== "terminal") throw new Error("Host tool execution refused")
    })
    const tools = await ctx.tool.list()
    if (tools.length !== 1 || tools[0].name !== "terminal") throw new Error("Host tools remain enabled")
    return async () => { await guard.dispose(); await registration.dispose() }
  },
}
