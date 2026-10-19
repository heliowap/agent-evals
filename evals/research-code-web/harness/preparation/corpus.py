import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def verify(root=ROOT):
    counts = {}
    for path in sorted((root / 'corpus-manifests').glob('*.json')):
        manifest = json.loads(path.read_text())
        snapshot = root / 'corpus' / manifest['name']
        archive = root / 'corpus-archives' / (manifest['name'] + '.tar.gz')
        assert hashlib.sha256(archive.read_bytes()).hexdigest() == manifest['archive_sha256']
        assert manifest['license_path'] in manifest['files']
        actual = {p.relative_to(snapshot).as_posix() for p in snapshot.rglob('*') if p.is_file()}
        assert actual == set(manifest['files'])
        for relative, entry in manifest['files'].items():
            file = snapshot / relative
            assert not file.is_symlink() and file.resolve().is_relative_to(snapshot.resolve())
            raw = file.read_bytes()
            assert hashlib.sha256(raw).hexdigest() == entry['sha256']
            assert len(raw) == entry['bytes']
            assert '\r' not in raw.decode('utf-8') and b'\0' not in raw
        assert not set(manifest['files']) & {item['path'] for item in manifest['exclusions']}
        counts[manifest['name']] = len(manifest['files'])
    assert set(counts) == {'click', 'httpx', 'cobra', 'prometheus', 'zod', 'opencode'}
    return {'repositories': len(counts), 'files': sum(counts.values()), 'counts': counts,
            'license_scope': 'Root licenses and original NOTICE preserved; excluded dependency directories, binary/non-UTF-8, large and nonregular files. Not a comprehensive third-party license audit.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify', action='store_true', required=True)
    parser.parse_args()
    print(json.dumps({'status': 'PASS', **verify()}, indent=2))
