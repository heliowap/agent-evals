import assert from "node:assert/strict"
import { chmodSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs"
import { tmpdir } from "node:os"
import { resolve, join } from "node:path"
import terminal from "./terminal.js"

if (!process.env.OPENCODE_SOURCE || !process.env.OPENCODE_DEPS || !process.env.OPENCODE_EFFECT) {
  throw new Error("Run with Bun and set OPENCODE_SOURCE, OPENCODE_DEPS and OPENCODE_EFFECT to the checkout, dependencies and its pinned Effect package")
}
const source = resolve(process.env.OPENCODE_SOURCE)
const dependencies = resolve(process.env.OPENCODE_DEPS)
const effect = resolve(process.env.OPENCODE_EFFECT)
const catalog = JSON.parse(readFileSync(join(source, "package.json"), "utf8")).workspaces.catalog
assert.equal(JSON.parse(readFileSync(join(effect, "package.json"), "utf8")).version, catalog.effect)
const plugin = { name: "native-contract-dependencies", setup(build) {
  build.onResolve({ filter: /^effect(\/|$)/ }, args => ({ path: join(effect, "dist", args.path === "effect" ? "index.js" : args.path.slice(7) + ".js") }))
  build.onResolve({ filter: /^zod(\/|$)/ }, args => ({ path: Bun.resolveSync(args.path, dependencies) }))
  build.onResolve({ filter: /^@opencode\/schema\// }, args => ({ path: join(source, "packages/schema/src", args.path.slice("@opencode/schema/".length) + ".ts") }))
} }
const root = mkdtempSync(join(tmpdir(), "native-terminal-"))
const previous = { ...process.env }
try {
  const entry = join(root, "entry.mjs")
  writeFileSync(entry, `export { execute } from ${JSON.stringify(join(source, "packages/core/src/tool/runtime.ts"))}; export { Effect } from 'effect';`)
  const build = await Bun.build({ entrypoints: [entry], target: "bun", plugins: [plugin], outfile: join(root, "native.mjs") })
  if (!build.success) throw new AggregateError(build.logs, "Could not load native tool runtime")
  const native = await import("data:text/javascript;base64," + Buffer.from(await build.outputs[0].text()).toString("base64"))
  const { Effect } = native
  const docker = join(root, "docker")
  writeFileSync(docker, "#!/usr/bin/env node\nconsole.log('fixture output')\n")
  chmodSync(docker, 0o700)
  process.env.OPENCODE_DOCKER_BINARY = docker
  process.env.OPENCODE_CODE_CONTAINER = "a".repeat(64)
  process.env.OPENCODE_TERMINAL_LOG = join(root, "terminal.jsonl")
  let definition
  await terminal.setup({ tool: {
    transform: async callback => {
      callback({ list: () => definition ? [{ ...definition, id: "terminal" }] : [], remove() {}, add(value) { definition = value } })
      return { dispose: async () => {} }
    },
    hook: async () => ({ dispose: async () => {} }),
    list: async () => [{ ...definition, id: "terminal" }],
  } })
  const tool = { ...definition, execute: (input, context) => Effect.tryPromise(() => definition.execute(input, context)) }
  const result = await Effect.runPromise(native.execute(tool, { command: "read fixture" }, { sessionID: "session", id: "call", signal: new AbortController().signal }))
  assert.equal(result.output, undefined)
  assert.equal(result.content.length, 1)
  assert.equal(result.content[0].type, "text")
  assert.equal(JSON.parse(result.content[0].text).output, "fixture output\n")
  console.log("Native checkout core version: " + JSON.parse(readFileSync(join(source, "packages/core/package.json"), "utf8")).version)
  console.log("Native tool runtime accepted the terminal result")
} catch (error) {
  console.error(error.message ?? String(error))
  process.exitCode = 1
} finally {
  for (const key of Object.keys(process.env)) if (!(key in previous)) delete process.env[key]
  Object.assign(process.env, previous)
  rmSync(root, { recursive: true, force: true })
}
