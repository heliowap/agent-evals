import datetime
import difflib
import hashlib
import json
from pathlib import Path
import subprocess
import sys

OUT = Path(__file__).resolve().parent
PACKAGE = OUT.parents[1]
EVALS = PACKAGE.parents[1]
sys.path.insert(0, str(PACKAGE))
import runtime

RESULTS = PACKAGE / 'results/full-3'


def surface_verdict(trial, arm, until_ms=None):
    try:
        runtime.surface(RESULTS / trial, 'implementation', arm, 'timed-surface.jsonl', until_ms)
        return 'accepted'
    except ValueError as exc:
        return str(exc)


replay = {}
for trial, arm in (('trial-0001', 'native'), ('trial-0002', 'serena')):
    session = json.loads((RESULTS / trial / 'session.json').read_text())
    activity = session['info']['time']['updated']
    completed = [message['time'].get('completed') for message in session['messages'] if isinstance(message.get('time'), dict)]
    completed += [part['time'].get('completed') for message in session['messages'] if isinstance(message.get('content'), list)
                  for part in message['content'] if isinstance(part, dict) and isinstance(part.get('time'), dict)]
    margin = activity - max(value for value in completed if type(value) in (int, float))
    assert margin >= 0, (trial, margin)
    rows = [json.loads(line) for line in (RESULTS / trial / 'timed-surface.jsonl').read_text().splitlines()]
    replay[trial] = {'arm': arm, 'session_updated_ms': activity, 'updated_minus_last_completed_ms': margin, 'rows': len(rows),
                     'rows_after_activity_ms': [row['at_ms'] - activity for row in rows if row['at_ms'] > activity],
                     'unbounded_verdict': surface_verdict(trial, arm), 'activity_bounded_verdict': surface_verdict(trial, arm, activity)}
assert replay['trial-0002']['unbounded_verdict'].startswith('Native OpenCode tool surface missing or changed:'), replay
assert all(row['activity_bounded_verdict'] == 'accepted' for row in replay.values()), replay

tests = ['test_bench.DirectSurfaceTests.test_surface_ignores_catalog_unloaded_after_session_activity',
         'test_bench.DirectSurfaceTests.test_surface_rejects_catalog_lost_before_session_activity',
         'test_bench.DirectSurfaceTests.test_surface_after_session_activity_still_rejects_unexpected_tools',
         'test_bench.DirectSurfaceTests.test_surface_activity_bound_requires_observation_times',
         'test_bench.MetadataTests.test_export_without_session_activity_time_is_rejected',
         'test_bench.FailureRegressionTests.test_teardown_catalog_does_not_fail_completed_serena_trial',
         'test_bench.BridgeTests.test_initialize_advertises_only_the_fixed_tools_protocol']
suites = {}
for label, argv in [('targeted', ['-m', 'unittest', *tests]), ('python', ['-m', 'unittest', 'test_bench'])]:
    result = subprocess.run([sys.executable, '-B', *argv], cwd=PACKAGE, capture_output=True, text=True)
    suites[label] = {'exit_code': result.returncode, 'tail': result.stderr.strip().splitlines()[-3:]}
node = subprocess.run(['node', '--test', 'test_surface.mjs'], cwd=PACKAGE, capture_output=True, text=True)
suites['node'] = {'exit_code': node.returncode, 'tail': [line for line in node.stdout.splitlines() if line.startswith(('# pass', '# fail'))]}
assert all(suite['exit_code'] == 0 for suite in suites.values()), suites

patches, hashes = [], {}
for name in ('runtime.py', 'bench.py', 'mcp_bridge.py', 'test_bench.py'):
    current = (PACKAGE / name).read_text()
    patches.extend(difflib.unified_diff((OUT / 'before' / name).read_text().splitlines(keepends=True),
                                        current.splitlines(keepends=True), fromfile='before/' + name, tofile='after/' + name))
    hashes[name] = hashlib.sha256(current.encode()).hexdigest()
(OUT / 'implementation.patch').write_text(''.join(patches))


def preserved(snapshot, base):
    files = json.loads(snapshot.read_text())['files']
    missing = [name for name in files if not (base / name).is_file()]
    changed = [name for name in files if name not in missing and hashlib.sha256((base / name).read_bytes()).hexdigest() != files[name]]
    return {'snapshot': str(snapshot.relative_to(EVALS)), 'checked': len(files), 'changed': changed, 'missing': missing,
            'passed': not changed and not missing}


preservation = {'full_3': preserved(OUT / 'full-3-before.json', PACKAGE / 'results/full-3'),
                'full_4': preserved(OUT / 'full-4-before.json', PACKAGE / 'results/full-4'),
                'historical_campaigns': preserved(PACKAGE / 'validation/history-before.json', EVALS),
                'full_1': preserved(PACKAGE / 'validation/surface-fix/full-1-before.json', PACKAGE / 'results/full-1'),
                'full_2': preserved(PACKAGE / 'validation/mcp-row-fix/full-2-before.json', PACKAGE / 'results/full-2'),
                'operator_config': preserved(PACKAGE / 'validation/surface-fix/operator-config-before.json', Path.home() / '.config/opencode')}
assert all(check['passed'] for check in preservation.values()), preservation

runtime.save(OUT / 'proof.json', {'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'replay': replay,
                                  'tests': suites, 'source_sha256': hashes, 'preservation': preservation,
                                  'model_inference_calls': 0})
print(json.dumps({'replay': replay, 'tests': {k: v['exit_code'] for k, v in suites.items()},
                  'preservation': {k: v['passed'] for k, v in preservation.items()}}, indent=2))
