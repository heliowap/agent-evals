import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent
SERENA_SOURCE = Path('~/VSCode/Lab/serena')
SERENA_COMMIT = '8e1a255e979746597f6cc05a94022ec2d3d3a3ca'
DEPENDENCIES = ROOT / 'dependencies/pyright-1.1.403'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree(root):
    return {str(path.relative_to(root)): sha(path) for path in sorted(root.rglob('*'))
            if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc'}


def bootstrap(cache):
    if DEPENDENCIES.exists():
        if json.loads((DEPENDENCIES / 'package.json').read_text())['version'] != '1.1.403':
            raise ValueError('Dependency version mismatch')
        return {'status': 'already_present', 'files': len(tree(DEPENDENCIES))}
    distributions = sorted(cache.glob('archive-v0/**/pyright/dist/package.json'))
    found = next((path.parent for path in distributions if json.loads(path.read_text()).get('version') == '1.1.403'), None)
    if found is None:
        raise ValueError('Cached Pyright 1.1.403 distribution missing. Prepare it explicitly with uvx --from pyright==1.1.403 pyright --version, then rerun installation.py. No download was attempted.')
    temporary = DEPENDENCIES.with_name(DEPENDENCIES.name + '.preparing')
    shutil.copytree(found, temporary, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    if not (temporary / 'langserver.index.js').is_file() or not (temporary / 'dist/pyright.js').is_file():
        shutil.rmtree(temporary)
        raise ValueError('Cached distribution is incomplete')
    temporary.rename(DEPENDENCIES)
    return {'status': 'copied_cached_distribution', 'source': str(found), 'files': len(tree(DEPENDENCIES)), 'network_used': False}


def fingerprint(binary, serena, node):
    launcher = Path(serena).resolve()
    shebang = launcher.read_text().splitlines()[0]
    if not shebang.startswith('#!'):
        raise ValueError('Serena launcher must expose pinned Python')
    python = Path(shebang[2:]).absolute()
    probe = subprocess.run([str(python), '-B', '-c', "import importlib.metadata as m,json,serena; print(json.dumps({'source':serena.__file__,'packages':sorted((d.metadata['Name'],d.version) for d in m.distributions())}))"],
                           capture_output=True, text=True, timeout=30, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
    if probe.returncode:
        raise ValueError('Serena installed environment probe failed')
    metadata = json.loads(probe.stdout)
    if not Path(metadata['source']).resolve().is_relative_to(SERENA_SOURCE / 'src'):
        raise ValueError('Serena editable installation points to another source')
    commit = subprocess.check_output(['git', '-C', str(SERENA_SOURCE), 'rev-parse', 'HEAD'], text=True, timeout=20).strip()
    status = subprocess.check_output(['git', '-C', str(SERENA_SOURCE), 'status', '--porcelain'], text=True, timeout=20)
    if commit != SERENA_COMMIT or status.strip():
        raise ValueError('Serena source differs from pinned clean commit')
    if not DEPENDENCIES.exists():
        raise ValueError('Offline Pyright dependency missing; run python3 -B ferramentas/haiku-serena-opencode/installation.py first')
    if json.loads((DEPENDENCIES / 'package.json').read_text())['version'] != '1.1.403':
        raise ValueError('Wrong Pyright version')
    resolved = {'opencode': Path(binary).resolve(), 'serena': launcher, 'python': python, 'node': Path(node).resolve()}
    for name, path in resolved.items():
        if not path.is_file():
            raise ValueError(f'Missing executable {name}')
    environment = launcher.parent.parent
    return {'commit': commit, 'source': str(SERENA_SOURCE), 'source_sha256': {
        **{'src/' + k: v for k, v in tree(SERENA_SOURCE / 'src').items()},
        **{'resources/' + k: v for k, v in tree(SERENA_SOURCE / 'resources').items()}},
        'executables': {name: {'path': str(path), 'sha256': sha(path)} for name, path in resolved.items()},
        'packages': metadata['packages'],
        'installed_environment_sha256': tree(environment / 'lib'),
        'pyright': {'version': '1.1.403', 'path': str(DEPENDENCIES), 'files': tree(DEPENDENCIES)},
        'node_version': subprocess.check_output([str(resolved['node']), '--version'], text=True, timeout=20).strip()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Prepare only cached Pyright distribution, without network')
    parser.add_argument('--uv-cache', type=Path, default=Path.home() / '.cache/uv')
    args = parser.parse_args()
    print(json.dumps(bootstrap(args.uv_cache), indent=2))
