import assert from 'node:assert/strict'
import { readFileSync, writeFileSync, mkdtempSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import plugin, { exposedToolName } from '../../surface.js'

const proof = JSON.parse(readFileSync(new URL('./implementation-private-configs-r2.json', import.meta.url)))
const observed = JSON.parse(readFileSync(new URL('./observed-catalog.json', import.meta.url)))
const browser = observed.filter((name) => name.startsWith('browser_'))
const results = []
for (const prepared of proof.rows) {
  const folder = mkdtempSync(join(tmpdir(), 'surface-replay-'))
  const before = { ...process.env }
  const names = prepared.config.permissions.filter((permission) => permission.effect === 'allow').map((permission) => permission.action)
  process.env.EVAL_ALLOWED_TOOLS = JSON.stringify(names)
  process.env.EVAL_ROLE = prepared.role
  process.env.EVAL_SURFACE_LOG = join(folder, 'surface.jsonl')
  const transforms = []
  const snapshot = () => {
    let tools = []
    const editor = { list: () => tools, remove: (id) => { tools = tools.filter((tool) => tool.id !== id) },
      add: (tool) => { tools.push({ ...tool, id: exposedToolName(tool) }) } }
    for (const transform of transforms) transform(editor)
    return tools
  }
  transforms.push((editor) => {
    for (const name of ['read', 'glob', 'grep', 'terminal', 'bash']) editor.add({ name, options: { codemode: false } })
  })
  const ctx = { tool: {
    transform: async (fn) => { transforms.push(fn); snapshot(); return { dispose: async () => {} } },
    list: async () => snapshot(), hook: async () => ({ dispose: async () => {} }),
  } }
  let dispose
  try {
    dispose = await plugin.setup(ctx)
    if (prepared.arm === 'serena') transforms.push((editor) => {
      for (const name of names.filter((name) => name.startsWith('serena_'))) editor.add({
        name: name.slice('serena_'.length), options: { namespace: 'serena', codemode: prepared.config.mcp.serena.codemode !== false },
      })
    })
    assert.ok(prepared.config.plugins.includes('-opencode.browser'))
    const final = await ctx.tool.list()
    assert.deepEqual(final.map(exposedToolName).sort(), [...names].sort())
    for (const tool of final) {
      assert.equal(tool.id, exposedToolName(tool))
      assert.equal(tool.options.codemode, false)
      assert.equal(tool.options.permission ?? tool.id, exposedToolName(tool))
    }
    transforms.push((editor) => {
      for (const name of browser) editor.add({ name: name.slice('browser_'.length), options: { namespace: 'browser', codemode: true, permission: 'browser' } })
    })
    const unexpected = (await ctx.tool.list()).filter((tool) => !names.includes(exposedToolName(tool)))
    assert.equal(unexpected.length, browser.length)
    results.push({ role: prepared.role, configuration: prepared.configuration, direct_names: final.map(exposedToolName),
      browser_after_filter_without_private_removal: unexpected.length, passed: true })
  } finally {
    if (dispose) await dispose()
    for (const key of Object.keys(process.env)) if (!(key in before)) delete process.env[key]
    Object.assign(process.env, before)
    rmSync(folder, { recursive: true, force: true })
  }
}
writeFileSync(new URL('./implementation-replay.json', import.meta.url), JSON.stringify({ model_inference_calls: 0, registry: 'initial state plus all transforms in insertion order', results }, null, 2) + '\n')
console.log(`PASS: ${results.length} private configurations have exact direct surfaces; post-filter browser remains observable without removal`)
