import json, sys
rows = json.load(open(sys.argv[1]))
rows = [r for r in rows if r['state'] == 'paid']
json.dump({'count': len(rows), 'cents': sum(r['cents'] for r in rows)}, open(sys.argv[2], 'w'))
