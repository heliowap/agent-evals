import assert from 'node:assert/strict'
import { test } from 'node:test'
import { readFileSync } from 'node:fs'
import { executeTerminal, exposedToolName } from './surface.js'

test('terminal refuses wrong container and invalid timeout before spawning', async () => {
  assert.throws(() => executeTerminal('pwd', 1, null, { docker: '/does-not-exist', container: 'invalid' }))
  assert.throws(() => executeTerminal('pwd', 180001, null, { docker: '/does-not-exist', container: 'a'.repeat(64) }))
  assert.throws(() => executeTerminal('', 1, null, { docker: '/does-not-exist', container: 'a'.repeat(64) }))
})

test('pre-aborted terminal does not launch a process', async () => {
  const signal = AbortSignal.abort()
  await assert.rejects(executeTerminal('pwd', 1000, signal, { docker: '/does-not-exist', container: 'a'.repeat(64) }), /aborted/)
})

test('terminal command is passed only through Docker exec', () => {
  const source = readFileSync(new URL('./surface.js', import.meta.url), 'utf8')
  assert.match(source, /spawn\(docker, \["exec", "--workdir", "\/workspace", container, "sh", "-c", command\]/)
  assert.match(source, /if \(!allowedIds.has\(event.tool\)\)/)
})

test('surface replaces an existing host terminal and rejects unknown execution', async () => {
  const { default: plugin } = await import('./surface.js')
  const { mkdtempSync, rmSync } = await import('node:fs')
  const { tmpdir } = await import('node:os')
  const { join } = await import('node:path')
  const folder = mkdtempSync(join(tmpdir(), 'surface-proof-'))
  const before = { ...process.env }
  let tools = [{ id: 'host-terminal', name: 'terminal', execute: () => { throw new Error('HOST EXECUTED') } }, { id: 'host-bash', name: 'bash' }, { id: 'serena_find_symbol', name: 'find_symbol', options: { namespace: 'serena' } }]
  let guard
  process.env.EVAL_ALLOWED_TOOLS = '["terminal","serena_find_symbol"]'
  process.env.EVAL_ROLE = 'implementation'
  process.env.EVAL_SURFACE_LOG = join(folder, 'surface.jsonl')
  process.env.OPENCODE_TERMINAL_LOG = join(folder, 'terminal.jsonl')
  process.env.OPENCODE_DOCKER_BINARY = '/does-not-exist'
  process.env.OPENCODE_CODE_CONTAINER = 'a'.repeat(64)
  const editor = { list: () => tools, remove: (id) => { tools = tools.filter((tool) => tool.id !== id) }, add: (tool) => { tools.push({ ...tool, id: 'private-terminal' }) } }
  try {
    const dispose = await plugin.setup({ tool: { transform: async (fn) => { fn(editor); return { dispose: async () => {} } }, hook: async (name, fn) => { guard = fn; return { dispose: async () => {} } }, list: async () => tools } })
    try {
      assert.deepEqual(tools.map(exposedToolName), ['serena_find_symbol', 'terminal'])
      assert.equal(tools[1].id, 'private-terminal')
      assert.doesNotThrow(() => guard({ tool: 'serena_find_symbol' }))
      assert.throws(() => guard({ tool: 'bash' }), /refused/)
      await assert.rejects(tools[1].execute({ command: 'pwd' }, { signal: AbortSignal.abort() }), /aborted/)
    } finally { await dispose() }
  } finally {
    for (const key of Object.keys(process.env)) if (!(key in before)) delete process.env[key]
    Object.assign(process.env, before)
    rmSync(folder, { recursive: true, force: true })
  }
})
