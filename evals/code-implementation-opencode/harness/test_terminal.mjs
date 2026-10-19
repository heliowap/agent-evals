import test from "node:test"
import assert from "node:assert/strict"
import { chmodSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs"
import { tmpdir } from "node:os"
import { join } from "node:path"
import terminal, { executeTerminal } from "./terminal.js"

test("terminal sends literal command only to docker exec", async () => {
  const root = mkdtempSync(join(tmpdir(), "terminal-test-"))
  try {
    const fake = join(root, "docker")
    writeFileSync(fake, "#!/usr/bin/env node\nconsole.log(JSON.stringify(process.argv.slice(2)))\n")
    chmodSync(fake, 0o700)
    const command = "echo $(cat /secret) ; touch /operator"
    const result = await executeTerminal(command, 1000, undefined, { docker: fake, container: "a".repeat(64) })
    assert.deepEqual(JSON.parse(result.output), ["exec", "--workdir", "/workspace", "a".repeat(64), "sh", "-c", command])
    assert.equal(result.exit_code, 0)
    assert.equal(result.cancelled, false)
  } finally { rmSync(root, { recursive: true, force: true }) }
})

test("abort and timeout stop the private container without command-controlled flags", async () => {
  const root = mkdtempSync(join(tmpdir(), "terminal-test-"))
  try {
    const fake = join(root, "docker")
    const log = join(root, "calls.jsonl")
    writeFileSync(fake, `#!/usr/bin/env node\nrequire('fs').appendFileSync(${JSON.stringify(log)}, JSON.stringify(process.argv.slice(2))+'\\n'); if(process.argv[2]==='exec') setInterval(()=>{},1000);\n`)
    chmodSync(fake, 0o700)
    const abort = new AbortController()
    setTimeout(() => abort.abort(), 800)
    const cancelled = await executeTerminal("sleep 30", 3000, abort.signal, { docker: fake, container: "b".repeat(64) })
    assert.equal(cancelled.cancelled, true)
    assert.equal(cancelled.timeout, false)
    const timed = await executeTerminal("sleep 30", 800, undefined, { docker: fake, container: "b".repeat(64) })
    assert.equal(timed.timeout, true)
    await new Promise(resolve => setTimeout(resolve, 100))
    const calls = readFileSync(log, "utf8").trim().split("\n").map(JSON.parse)
    assert.equal(calls.filter(call => call[0] === "kill" && call[1] === "b".repeat(64)).length, 2)
  } finally { rmSync(root, { recursive: true, force: true }) }
})

test("tool transform removes every host tool and rejects host execution", async () => {
  const root = mkdtempSync(join(tmpdir(), "terminal-test-"))
  const names = ["shell", "read", "edit", "patch", "job", "codemode", "skill", "subagent", "webfetch"]
  const entries = new Map(names.map(name => [name, { id: name, name }]))
  let guard
  const env = { ...process.env }
  try {
    process.env.OPENCODE_CODE_CONTAINER = "c".repeat(64)
    const docker = join(root, "docker")
    writeFileSync(docker, "#!/usr/bin/env node\nconsole.log('fixture output')\n")
    chmodSync(docker, 0o700)
    process.env.OPENCODE_DOCKER_BINARY = docker
    process.env.OPENCODE_TERMINAL_LOG = join(root, "log")
    await terminal.setup({ tool: {
      transform: async callback => { callback({ list: () => [...entries.values()], remove: id => entries.delete(id), add: tool => entries.set(tool.name, { ...tool, id: tool.name }) }); return { dispose: async () => {} } },
      hook: async (name, callback) => { assert.equal(name, "execute.before"); guard = callback; return { dispose: async () => {} } },
      list: async () => [...entries.values()],
    } })
    assert.deepEqual([...entries.keys()], ["terminal"])
    assert.equal(entries.get("terminal").options.codemode, false)
    assert.equal(entries.get("terminal").input.additionalProperties, false)
    assert.throws(() => guard({ tool: "shell" }), /refused/)
    assert.doesNotThrow(() => guard({ tool: "terminal" }))
    const ready = JSON.parse(readFileSync(join(root, "log"), "utf8"))
    assert.deepEqual(ready.tools, [{ id: "terminal", name: "terminal" }])
    const tool = entries.get("terminal")
    const returned = await tool.execute({ command: "read fixture" }, { sessionID: "session", id: "call", signal: new AbortController().signal })
    assert.equal(tool.output, undefined)
    assert.equal("output" in returned, false)
    assert.equal(JSON.parse(returned.content).output, "fixture output\n")
  } finally {
    for (const key of Object.keys(process.env)) if (!(key in env)) delete process.env[key]
    Object.assign(process.env, env)
    rmSync(root, { recursive: true, force: true })
  }
})

test("invalid container and command are rejected before host spawn", async () => {
  assert.throws(() => executeTerminal("ls", 1000, undefined, { docker: "docker", container: "--privileged" }), /identity/)
  assert.throws(() => executeTerminal("", 1000, undefined, { docker: "docker", container: "a".repeat(64) }), /command/)
  assert.throws(() => executeTerminal("ls", 0, undefined, { docker: "docker", container: "a".repeat(64) }), /timeout/)
})
