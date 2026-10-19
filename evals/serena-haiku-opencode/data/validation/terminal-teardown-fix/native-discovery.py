import json
from contextlib import nullcontext
from pathlib import Path
import shutil
import sys
import tempfile
from types import SimpleNamespace

OUT = Path(__file__).resolve().parent
PACKAGE = OUT.parents[1]
sys.path.insert(0, str(PACKAGE))
import bench
import cases
from domain import CONFIGURATIONS
import runtime
from vendor import isolation

args = SimpleNamespace(binary='~/.opencode/bin/opencode', serena='~/.local/bin/serena',
                       node='~/.local/bin/node', python=sys.executable, docker='/usr/local/bin/docker',
                       image=bench.IMAGE, database=Path.home() / '.local/share/opencode/opencode.db', cache=(PACKAGE / 'models.json').resolve())
for name in ('binary', 'serena', 'node', 'python', 'docker'):
    setattr(args, name, str(Path(shutil.which(getattr(args, name)) or getattr(args, name)).absolute()))

rows = []
with tempfile.TemporaryDirectory(prefix='opencode-proof-', dir='/private/tmp') as folder:
    for configuration in (item for item in CONFIGURATIONS if item.id == 'haiku-medium-serena'):
        for name in ('route', 'py-document-scope'):
            case = cases.BY_ID[name]
            root = (Path(folder) / f'{configuration.id}-{case.role}').resolve()
            work = root / 'work'
            cases.build(case, work)
            scope = isolation.CodeContainer(work, args.image, args.docker) if case.role == 'implementation' else nullcontext(None)
            with scope as container:
                env, config = runtime.prepare(root, work, configuration, case, args, container)
                discovery = runtime.audit(root, work, configuration, case, args, env, config)
            log = [json.loads(line) for line in (root / 'mcp.jsonl').read_text().splitlines()]
            rows.append({'configuration': configuration.id, 'role': case.role, 'model_inference_calls': discovery['model_inference_calls'],
                         'client_methods': [row.get('method') for row in log if row['event'] in ('request', 'rejected')],
                         'rejected': [row.get('method') for row in log if row['event'] == 'rejected'],
                         'initialize_capabilities': next(row['response']['result']['capabilities'] for row in log
                                                         if row['event'] == 'response' and row.get('method') == 'initialize')})
runtime.save(OUT / 'native-discovery.json', rows)
print(json.dumps(rows, indent=2))
