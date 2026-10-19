"""Copy only verified prior inputs, without execution, auth, or source archives."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parent.parent
OLD = Path('~/VSCode/Lab/evals/researcher-eval-20261007T021014Z')


def main():
    old_freeze = json.loads((OLD / 'freeze.json').read_text())
    copied = {}
    for name, expected in old_freeze['files'].items():
        source = OLD / name
        actual = hashlib.sha256(source.read_bytes()).hexdigest()
        if actual != expected:
            raise RuntimeError('Prior frozen input changed: ' + name)
        if name.startswith('preflight/') or name.startswith('dataset/sources/'):
            continue
        target = ROOT / name
        if target.exists():
            raise RuntimeError('Refuse to overwrite existing destination: ' + name)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        copied[name] = expected
    for name in ['research/tasks.md', 'research/harness.md']:
        target = ROOT / name
        if target.exists():
            raise RuntimeError('Refuse to overwrite research note: ' + name)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(OLD / name, target)
        copied[name] = hashlib.sha256(target.read_bytes()).hexdigest()
    provenance = {
        'source_root': str(OLD),
        'prior_freeze_sha256': hashlib.sha256((OLD / 'freeze.json').read_bytes()).hexdigest(),
        'copied_initial_input_hashes': copied,
        'source_bodies_copied': False,
        'execution_auth_or_identity_state_copied': False,
    }
    (ROOT / 'preflight/bootstrap.json').write_text(json.dumps(provenance, indent=2) + '\n')
    print(f'PASS: {len(copied)} prior inputs copied after hash checks; no execution, auth or source bodies copied.')


if __name__ == '__main__':
    main()
