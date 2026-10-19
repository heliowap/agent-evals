import json, hashlib
r = open('settings.json','rb').read()
m = json.load(open('manifest.json'))
assert m == {'mode': json.loads(r)['mode'], 'sha256': hashlib.sha256(r).hexdigest()}
assert m['mode'] == 'strict'
print('verified')
