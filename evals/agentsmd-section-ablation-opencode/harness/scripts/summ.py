import json,sys
for path in sys.argv[1:]:
    print("=====",path.split('/')[-1])
    texts=[]
    for line in open(path):
        try: e=json.loads(line)
        except: continue
        p=e.get('part',{})
        if e.get('type')=='tool_use':
            inp=p.get('state',{}).get('input',{})
            s=json.dumps(inp,ensure_ascii=False)
            print("  TOOL",p.get('tool'),s[:260])
        elif e.get('type')=='text':
            texts.append(p.get('text',''))
    print("  FINAL:",(texts[-1] if texts else '')[:900].replace('\n','\n         '))
