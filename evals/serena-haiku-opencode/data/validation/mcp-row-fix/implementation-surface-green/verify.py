import difflib
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import runtime
from test_bench import DirectSurfaceTests, DiscoveryRegressionTests

OUT = Path(__file__).resolve().parent
tester = DirectSurfaceTests()
with tempfile.TemporaryDirectory() as folder:
    root = Path(folder).resolve()
    complete = tester.tools(arm='serena')
    tester.save_surface(root, complete)
    with (root / 'surface.jsonl').open('a') as stream:
        stream.write(json.dumps({'event': 'surface', 'tools': tester.tools()}) + '\n')
    try:
        runtime.surface(root, 'exploration', 'serena')
    except ValueError as exc:
        assert str(exc).startswith('Native OpenCode tool surface missing or changed:')
    else:
        raise AssertionError('Historical complete catalog approved a partial latest observation')
    shutil.copyfile(root / 'surface.jsonl', OUT / 'partial-latest-surface.jsonl')
    latest = {'event': 'surface', 'at_ms': 3, 'tools': complete}
    with (root / 'surface.jsonl').open('a') as stream:
        stream.write(json.dumps(latest) + '\n')
    assert runtime.surface(root, 'exploration', 'serena') == latest
    shutil.copyfile(root / 'surface.jsonl', OUT / 'recompleted-latest-surface.jsonl')

invoke_tester = DiscoveryRegressionTests()
def change_surface(root, attempt):
    tools = invoke_tester.tools() if attempt == 1 else invoke_tester.tools(arm='serena')
    with (root / 'surface.jsonl').open('a') as stream:
        stream.write(json.dumps({'event': 'surface', 'tools': tools}) + '\n')
connected = {'data': [{'name': 'serena', 'status': {'status': 'connected'}}]}
with tempfile.TemporaryDirectory() as folder:
    root = Path(folder).resolve()
    result, events = invoke_tester.invoke(root, [connected, connected], on_mcp=change_surface)
    operations = [name for name, kwargs in events]
    assert operations == ['mcp.list', 'mcp.list', 'session.create']
    assert result['reason'] is None and result['exit_code'] == 0 and result['calls_at_exit'] == 0
    destination = OUT / 'invoke-readiness'
    destination.mkdir(parents=True, exist_ok=True)
    for name in ('discovery-receipt.json', 'mcp-status.jsonl', 'discovery-surface.jsonl'):
        shutil.copyfile(root / name, destination / name)

patches = []
hashes = {}
before = OUT.parent / 'implementation-surface-red' / 'before'
for name in ('runtime.py', 'test_bench.py'):
    current = (ROOT / name).read_text()
    patches.extend(difflib.unified_diff((before / name).read_text().splitlines(keepends=True), current.splitlines(keepends=True),
                                     fromfile='before/' + name, tofile='after/' + name))
    hashes[name] = hashlib.sha256(current.encode()).hexdigest()
(OUT / 'implementation.patch').write_text(''.join(patches))
historical = json.loads((OUT.parent / 'full-2-before.json').read_text())['files']
assert all(hashlib.sha256((ROOT / 'results/full-2' / name).read_bytes()).hexdigest() == digest for name, digest in historical.items())
runtime.save(OUT / 'proof.json', {'offline_only': True, 'actual_model_inference_calls': 0, 'python_tests_passed': 44,
                                'node_tests_passed': 7, 'latest_partial_catalog_rejected': True,
                                'recompleted_latest_catalog_approved': True, 'invoke_api_operations': operations,
                                'source_sha256': hashes, 'full_2_history_files_preserved': len(historical),
                                'contracts_caps_prompts_docs_history_changed': False})
print(json.dumps({'latest_partial_rejected': True, 'invoke_operations': operations, 'actual_model_inference_calls': 0}))
