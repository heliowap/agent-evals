import argparse
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
VERIFY_MODULES = [
    ('contracts.verify', []), ('preparation.corpus', ['--verify']), ('preparation.schedule', []),
    ('harness.tools.web.verify', []), ('harness.tools.code.verify', []), ('harness.core.verify', []),
    ('tasks.web.verify', []), ('tasks.code.verify', []), ('grading.verify', []), ('analysis.verify', []),
    ('preparation.integration', []),
]
INPUT_DIRS = ('contracts', 'preparation', 'harness', 'tasks', 'gold', 'corpus', 'corpus-manifests', 'tests', 'research', 'grading', 'analysis')
INPUT_FILES = ('PLAN.md', 'proposal.json', 'scope.json', 'execution-plan.md', 'schedule.json')


def input_hashes(root=ROOT):
    paths = set(INPUT_FILES)
    for folder in INPUT_DIRS:
        for path in (root / folder).rglob('*'):
            if path.is_symlink():
                raise ValueError('symlink in freeze inputs')
            if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
                paths.add(path.relative_to(root).as_posix())
    for path in (root / 'preflight').rglob('*'):
        if path.is_file() and path.name not in {'offline-checks.json', 'freeze-receipt.json'} and '__pycache__' not in path.parts and path.suffix != '.pyc':
            paths.add(path.relative_to(root).as_posix())
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in sorted(paths)}


def verify_inputs(root=ROOT):
    outcomes = []
    for module, arguments in VERIFY_MODULES:
        result = subprocess.run([sys.executable, '-B', '-m', module, *arguments], cwd=root, capture_output=True, timeout=180)
        outcomes.append({'module': module, 'exit_code': result.returncode,
                         'stdout': result.stdout.decode(errors='replace'), 'stderr': result.stderr.decode(errors='replace')})
        if result.returncode:
            raise RuntimeError('Offline verification failed: ' + module + '\n' + outcomes[-1]['stdout'] + outcomes[-1]['stderr'])
    return outcomes


def check(root=ROOT):
    manifest = json.loads((root / 'freeze' / 'manifest.json').read_text())
    receipt = json.loads((root / 'freeze' / 'receipt.json').read_text())
    assert receipt['sha256'] == hashlib.sha256((root / 'freeze' / 'manifest.json').read_bytes()).hexdigest()
    assert manifest['files'] == input_hashes(root), 'frozen inputs changed'
    assert manifest['candidate_calls_before_freeze'] == 0
    return manifest


def seal(root=ROOT):
    if (root / 'execution').exists() or (root / 'freeze').exists():
        raise RuntimeError('existing execution/freeze; no replacement or implicit rerun')
    outcomes = verify_inputs(root)
    review = json.loads((root / 'preflight' / 'review.json').read_text())
    if not review.get('passed') or review.get('blockers'):
        raise RuntimeError('independent review has unresolved blockers')
    files = input_hashes(root)
    frozen = {'schema_version': 1, 'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'files': files, 'candidate_calls_before_freeze': 0, 'approved_trials': 648,
              'checks': outcomes, 'authorization': 'User selected 648 trials (Recommended) after explicitly requesting execution.'}
    directory = root / 'freeze'
    directory.mkdir()
    path = directory / 'manifest.json'
    with path.open('x') as stream:
        stream.write(json.dumps(frozen, indent=2) + '\n')
    with (directory / 'receipt.json').open('x') as stream:
        stream.write(json.dumps({'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}, indent=2) + '\n')
    return check(root)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--verify', action='store_true')
    action.add_argument('--seal', action='store_true')
    args = parser.parse_args()
    if args.seal:
        result = seal()
        print(json.dumps({'status':'PASS', 'frozen_files':len(result['files']), 'approved_trials':result['approved_trials']}))
    elif (ROOT / 'freeze/manifest.json').exists():
        result = check()
        print(json.dumps({'status':'PASS', 'frozen_files':len(result['files']), 'approved_trials':result['approved_trials']}))
    else:
        outcomes = verify_inputs()
        print(json.dumps({'status':'PASS', 'modules':len(outcomes), 'sealed':False}))
