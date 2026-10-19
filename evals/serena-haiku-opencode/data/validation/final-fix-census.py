import ast
import hashlib
import io
import json
from pathlib import Path
import re
import tokenize

root = Path(__file__).resolve().parent.parent
names = (
    'bench.py', 'runtime.py', 'installation.py', 'mcp_bridge.py', 'surface.js',
    'test_bench.py', 'test_surface.mjs', 'README.md', 'DESIGN.md', 'domain.py',
    'cases.py', 'observer.js', 'models.json', 'provenance.json',
    'validation/implementation-binary-surface.json',
)
snapshot = []
for name in names:
    content = (root / name).read_bytes()
    snapshot.append({'file': name, 'lines': len(content.splitlines()),
                     'sha256': hashlib.sha256(content).hexdigest()})
comments = []
docstrings = []
suppression_files = []
for path in sorted(root.glob('*.py')):
    code = path.read_text()
    for token in tokenize.generate_tokens(io.StringIO(code).readline):
        if token.type == tokenize.COMMENT:
            comments.append({'file': path.name, 'line': token.start[0], 'text': token.string})
    for node in ast.walk(ast.parse(code)):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and ast.get_docstring(node):
            docstrings.append({'file': path.name, 'line': getattr(node, 'lineno', 1)})
markers = r'#\s*(?:noqa|type:\s*ignore)|@ts-(?:ignore|nocheck|expect-error)|eslint-disable|nosec|pragma:\s*no cover|pyright:\s*ignore'
for path in sorted(root.iterdir()):
    if path.is_file() and path.suffix in {'.py', '.js', '.mjs'} and re.search(markers, path.read_text()):
        suppression_files.append(path.name)
print(json.dumps({'snapshot': snapshot, 'python_comments': comments,
                  'python_docstrings': docstrings, 'suppressions': suppression_files}, indent=2))
