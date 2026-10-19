import assert from 'node:assert/strict'
import { test } from 'node:test'
import { readFileSync, mkdtempSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import plugin, { executeTerminal, exposedToolName } from './surface.js'

function registry(initial = []) {
  const transforms = [], hooks = new Map()
  let tools
  const snapshot = () => {
    tools = initial.map((tool) => ({ ...tool }))
    const editor = {
      list: () => tools,
      remove: (id) => { tools = tools.filter((tool) => tool.id !== id) },
      add: (tool) => { tools.push({ ...tool, id: exposedToolName(tool) }) },
    }
    for (const transform of transforms) transform(editor)
    return tools
  }
  return {
    tool: {
      transform: async (fn) => { transforms.push(fn); snapshot(); return { dispose: async () => { transforms.splice(transforms.indexOf(fn), 1) } } },
      hook: async (name, fn) => { hooks.set(name, fn); return { dispose: async () => { hooks.delete(name) } } },
      list: async () => snapshot(),
    },
    snapshot,
    before: (tool) => hooks.get('execute.before')({ tool }),
  }
}

async function privateSurface(role, names, run) {
  const folder = mkdtempSync(join(tmpdir(), 'surface-proof-'))
  const before = { ...process.env }
  Object.assign(process.env, {
    EVAL_ALLOWED_TOOLS: JSON.stringify(names), EVAL_ROLE: role,
    EVAL_SURFACE_LOG: join(folder, 'surface.jsonl'), OPENCODE_TERMINAL_LOG: join(folder, 'terminal.jsonl'),
    OPENCODE_DOCKER_BINARY: '/does-not-exist', OPENCODE_CODE_CONTAINER: 'a'.repeat(64),
  })
  try { await run(folder) } finally {
    for (const key of Object.keys(process.env)) if (!(key in before)) delete process.env[key]
    Object.assign(process.env, before)
    rmSync(folder, { recursive: true, force: true })
  }
}

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
  assert.match(source, /if \(!allowed(?:Ids)?.has\(event.tool\)\)/)
})

test('surface replaces an existing host terminal and rejects unknown execution', async () => {
  await privateSurface('implementation', ['terminal', 'serena_find_symbol'], async () => {
    const ctx = registry([{ id: 'terminal', name: 'terminal', execute: () => { throw new Error('HOST EXECUTED') } }, { id: 'bash', name: 'bash' },
                          { id: 'serena_find_symbol', name: 'find_symbol', options: { namespace: 'serena', codemode: false } }])
    const dispose = await plugin.setup(ctx)
    try {
      const tools = ctx.snapshot()
      assert.deepEqual(tools.map(exposedToolName), ['serena_find_symbol', 'terminal'])
      assert.equal(tools[1].id, 'terminal')
      assert.doesNotThrow(() => ctx.before('serena_find_symbol'))
      assert.throws(() => ctx.before('bash'), /refused/)
      await assert.rejects(tools[1].execute({ command: 'pwd' }, { signal: AbortSignal.abort() }), /aborted/)
    } finally { await dispose() }
  })
})

test('late MCP registration remains callable before the telemetry timer', async () => {
  await privateSurface('exploration', ['read', 'glob', 'grep', 'serena_find_symbol'], async () => {
    const ctx = registry(['read', 'glob', 'grep'].map((name) => ({ id: name, name, options: { codemode: false } })))
    const dispose = await plugin.setup(ctx)
    const late = await ctx.tool.transform((editor) => editor.add({ name: 'find_symbol', options: { namespace: 'serena', codemode: false } }))
    try {
      assert.equal(ctx.snapshot().at(-1).id, 'serena_find_symbol')
      assert.doesNotThrow(() => ctx.before('serena_find_symbol'))
      assert.throws(() => ctx.before('serena_execute_shell_command'), /refused/)
      assert.throws(() => ctx.before('execute'), /refused/)
    } finally { await late.dispose(); await dispose() }
  })
})

test('raw receipts preserve post-plugin browser additions in real registry order', async () => {
  await privateSurface('exploration', ['read', 'glob', 'grep'], async (folder) => {
    const ctx = registry(['read', 'glob', 'grep'].map((name) => ({ id: name, name, options: { codemode: false } })))
    const dispose = await plugin.setup(ctx)
    const post = await ctx.tool.transform((editor) => editor.add({ name: 'click', options: { namespace: 'browser', codemode: true, permission: 'browser' } }))
    try {
      assert.deepEqual((await ctx.tool.list()).map(exposedToolName).sort(), ['browser_click', 'glob', 'grep', 'read'])
      await new Promise((resolve) => setTimeout(resolve, 1100))
      const rows = readFileSync(join(folder, 'surface.jsonl'), 'utf8').trim().split('\n').map(JSON.parse)
      const browser = rows.flatMap((row) => row.tools).find((tool) => tool.name === 'browser_click')
      assert.equal(browser.id, 'browser_click')
      assert.equal(browser.codemode, true)
      assert.equal(browser.permission, 'browser')
      assert.throws(() => ctx.before('browser_click'), /refused/)
    } finally { await post.dispose(); await dispose() }
  })
})

test('direct tool receipts include effective fallback and explicit permissions', async () => {
  await privateSurface('exploration', ['read', 'glob', 'grep', 'serena_find_symbol'], async (folder) => {
    const ctx = registry([
      ...['read', 'glob', 'grep'].map((name) => ({ id: name, name, options: { codemode: false } })),
      { id: 'serena_find_symbol', name: 'find_symbol', options: { namespace: 'serena', codemode: false, permission: 'serena_find_symbol' } },
    ])
    const dispose = await plugin.setup(ctx)
    try {
      const rows = readFileSync(join(folder, 'surface.jsonl'), 'utf8').trim().split('\n').map(JSON.parse)
      for (const tool of rows.at(-1).tools) {
        assert.equal(tool.id, tool.name)
        assert.equal(tool.codemode, false)
        assert.equal(tool.permission, tool.name)
      }
    } finally { await dispose() }
  })
})
