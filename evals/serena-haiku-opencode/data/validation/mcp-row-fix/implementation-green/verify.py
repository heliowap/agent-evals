import difflib
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import bench
import runtime
from test_bench import DiscoveryRegressionTests

OUT = Path(__file__).resolve().parent
tester = DiscoveryRegressionTests()
connected = {'name': 'serena', 'status': {'status': 'connected'}}
scenarios = [
    ('empty-pending-connected', [{'data': []}, {'data': [{'name': 'serena', 'status': {'status': 'pending'}}]}, {'data': [connected]}], .1, 'passed'),
    ('empty-timeout', [{'data': []}], 100, 'blocked'),
    ('malformed-row', {'data': [{'name': 'serena', 'status': 'connected', 'credential': 'SECRET_FIELD'}]}, .1, 'blocked'),
    ('extra-server', {'data': [connected, {'name': 'other', 'status': {'status': 'connected'}}]}, .1, 'blocked'),
    ('duplicate-server', {'data': [connected, connected]}, .1, 'blocked'),
    ('failed-status', {'data': [{'name': 'serena', 'status': {'status': 'failed', 'error': 'SECRET_ERROR'}}]}, .1, 'blocked'),
]
results = []
for name, value, clock_step, expected in scenarios:
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder).resolve()
        try:
            tester.audit(root, value if isinstance(value, list) else [value], clock_step=clock_step)
        except ValueError:
            assert expected == 'blocked', name
        receipt = json.loads((root / 'discovery-receipt.json').read_text())
        assert receipt['outcome'] == expected, name
        assert receipt['model_inference_calls'] == 0, name
        destination = OUT / 'discovery' / name
        destination.mkdir(parents=True, exist_ok=True)
        for filename in ('discovery-receipt.json', 'mcp-status.jsonl', 'discovery-surface.jsonl'):
            source = root / filename
            if source.exists():
                text = source.read_text()
                assert not any(secret in text for secret in ('SECRET_COMMAND', 'SECRET_ENV', 'SECRET_CREDENTIAL', 'SECRET_FIELD', 'SECRET_ERROR')), name
                shutil.copyfile(source, destination / filename)
        results.append({'scenario': name, 'outcome': expected, 'model_inference_calls': 0, 'attempts': len(receipt['attempts'])})

with tempfile.TemporaryDirectory() as folder:
    root = Path(folder).resolve()
    work, configuration, case, args, expected, responses = tester.fixture(root)
    with patch('runtime.local_server', side_effect=ValueError('unit startup failure')), patch('runtime.read_requests', return_value=[{}, {}]):
        try:
            runtime.audit(root, work, configuration, case, args, {}, expected)
        except ValueError:
            pass
    receipt = json.loads((root / 'discovery-receipt.json').read_text())
    assert receipt['model_inference_calls'] == 2
    destination = OUT / 'discovery' / 'early-failure-observed-count'
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(root / 'discovery-receipt.json', destination / 'discovery-receipt.json')
    results.append({'scenario': 'early-failure-observed-count', 'outcome': 'blocked', 'model_inference_calls': 2,
                    'count_evidence': 'synthetic requests from a mock; no inference performed'})

patches = []
source_hashes = {}
before = OUT.parent / 'implementation-red' / 'before'
for name in ('runtime.py', 'bench.py', 'test_bench.py'):
    original = (before / name).read_text()
    current = (ROOT / name).read_text()
    patches.extend(difflib.unified_diff(original.splitlines(keepends=True), current.splitlines(keepends=True),
                                     fromfile='before/' + name, tofile='after/' + name))
    source_hashes[name] = hashlib.sha256(current.encode()).hexdigest()
(OUT / 'implementation.patch').write_text(''.join(patches))
assert 'native-catalog-fixture.json' in bench.source_files()
runtime.save(OUT / 'proof.json', {'offline_only': True, 'actual_model_inference_calls': 0, 'scenarios': results,
                                'source_sha256': source_hashes, 'native_fixture_in_freeze_inventory': True})
print(json.dumps({'offline_only': True, 'scenarios': len(results), 'actual_model_inference_calls': 0}))
