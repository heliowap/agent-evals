import datetime
import hashlib
import http.client
import json
from pathlib import Path
import re
from urllib.parse import urlsplit


def strict_json(text):
    text=text.strip()
    if text.startswith('```'):
        match=re.fullmatch(r'```(?:json)?\s*([\s\S]*?)\s*```',text)
        if not match:
            raise ValueError('incomplete JSON code fence')
        text=match.group(1)
    return json.loads(text)


def generate(job_id,prompt,directory,authorization,contract):
    directory=Path(directory)
    directory.mkdir(parents=True,exist_ok=True,mode=0o700)
    lease=directory/(job_id+'-lease.json')
    started=datetime.datetime.now(datetime.timezone.utc).isoformat()
    with lease.open('x') as stream:
        stream.write(json.dumps({'job_id':job_id,'started_utc':started,'request_count':1,'retries':0})+'\n')
    body={'model':contract['selected_controller'],'prompt':prompt}
    raw=json.dumps(body,ensure_ascii=False).encode()
    endpoint=urlsplit(contract['endpoint'])
    if endpoint.scheme!='http' or endpoint.hostname!='127.0.0.1':
        raise RuntimeError('unexpected controller broker; no request')
    request_path=directory/(job_id+'-request.json')
    request_path.write_bytes(raw)
    connection=http.client.HTTPConnection(endpoint.hostname,endpoint.port,timeout=300)
    try:
        connection.request('POST',endpoint.path,body=raw,headers={'Content-Type':'application/json','Authorization':authorization})
        response=connection.getresponse()
        payload=response.read()
        secret_encodings=[authorization.encode(),authorization.split(' ',1)[-1].encode()]
        if any(secret and secret in payload for secret in secret_encodings):
            raise RuntimeError('controller response contains authentication; not persisted')
        (directory/(job_id+'-response.json')).write_bytes(payload)
        receipt={'job_id':job_id,'http_status':response.status,'request_sha256':hashlib.sha256(raw).hexdigest(),
                 'response_sha256':hashlib.sha256(payload).hexdigest(),'requested_controller':body['model'],
                 'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 'client_requests':1,'client_retries':0,'native_usage_and_version':'not exposed by broker',
                 'upstream_attempts':'UNVERIFIED'}
        (directory/(job_id+'-receipt.json')).write_text(json.dumps(receipt,indent=2)+'\n')
        if response.status!=200:
            raise RuntimeError('controller generation unavailable; HTTP '+str(response.status))
        native=json.loads(payload)
        text=native['data']['text']
        return strict_json(text)
    finally:
        connection.close()
