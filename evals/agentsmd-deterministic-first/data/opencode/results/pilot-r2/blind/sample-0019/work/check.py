import ast, json, pathlib, sys
forbidden = set(json.load(open('checks.json'))['forbidden_builtins'])
bad = []
for p in pathlib.Path('src').rglob('*.py'):
    for n in ast.walk(ast.parse(p.read_text())):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in forbidden:
            bad.append(str(p))
print('\n'.join(bad))
sys.exit(bool(bad))
