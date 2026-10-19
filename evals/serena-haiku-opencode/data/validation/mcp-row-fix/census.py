from pathlib import Path
import json

root = Path(__file__).resolve().parents[2]
rows = []
for name in ('full-1', 'full-2'):
    receipt = json.loads((root / 'results' / name / 'preflight.json').read_text())
    stages = receipt['stages']
    rows.append({'run': name, 'local_contracts': stages.get('contracts_local', {}).get('passed'),
                 'stdio_roles_passed': [p['role'] for p in stages.get('mcp_stdio_python_lsp', []) if p.get('passed')],
                 'docker_namespace_passed': stages.get('namespace', {}).get('passed'),
                 'native_completed_receipts': len(stages['native_opencode_discovery']) if 'native_opencode_discovery' in stages else None,
                 'native_raw_reply_captured': 'native_mcp_reply' in stages,
                 'failure': receipt.get('error'), 'model_inference_calls': receipt['model_inference_calls']})
print(json.dumps(rows, indent=2))
