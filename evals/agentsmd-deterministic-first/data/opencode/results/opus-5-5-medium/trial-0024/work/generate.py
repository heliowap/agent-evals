import json, hashlib
raw = open('settings.json', 'rb').read()
json.dump({'mode': json.loads(raw)['mode'], 'sha256': hashlib.sha256(raw).hexdigest()}, open('manifest.json','w'))
