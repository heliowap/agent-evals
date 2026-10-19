import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path
import re
import uuid

from .controller import generate
from .credentials import service_auth
from .freeze import check
from harness.core.audit import audit_execution
from grading import export, pack_jobs, validate_grade, seal_base, seal_final
from grading.common import digest, save, signed
from grading.sealing import _decisions
from analysis import write_artifacts, audit_artifacts

ROOT=Path(__file__).resolve().parent.parent


def normalized_records(root,index):
    rows=[]
    redactions={}
    for name in index['records']:
        raw=json.loads((root/name).read_text())
        trial=raw['trial']
        attempted=raw.get('attempted',True)
        answer=raw['final_answer'] if raw['operational_complete'] else '\n\n'.join(raw['intermediate_text'])
        pattern=r"\b(?:I am|I'm)\s+(?:an?\s+)?(?:Gemini|DeepSeek|GLM|GPT|OpenAI)(?:[^\n.!?]*)(?:[.!?]|$)"
        removed=[]
        def redact(match):
            removed.append(match.group())
            return '[Explicit model self-identification redacted]'
        answer=re.sub(pattern,redact,answer,flags=re.IGNORECASE)
        if removed:
            redactions[trial['id']]=removed
        evidence=[]
        directory=(root/name).parent
        for call in raw['tool_calls']:
            if call.get('visible_path'):
                visible=json.loads((directory/call['visible_path']).read_text())
                evidence.append({'name':call['name'],'status':call['status'],
                                 'visible_text':visible['message'],
                                 'visible_sha256':hashlib.sha256(visible['message'].encode()).hexdigest()})
        requests=raw['requests']
        actions=[r['monotonic_start'] for r in requests if r.get('monotonic_start') is not None]
        final_timing=requests[-1].get('monotonic_end') if raw['operational_complete'] and requests else None
        row={'id':trial['id'],'suite':trial['suite'],'task_id':trial['task_id'],
             'configuration_id':trial['configuration_id'],'repetition':trial['repetition'],
             'status':raw['status'] if attempted else 'stopped_unrun','attempted':attempted,
             'study_incomplete':index.get('status')=='incomplete','study_stop':index.get('stop'),
             'completed':raw['operational_complete'],'final_answer':answer,
             'wall_seconds':raw.get('wall_seconds') if attempted else None,'tool_evidence':evidence,
             'timings':{'first_action_seconds':min(actions)-raw['monotonic_start'] if actions else None,
                        'first_final_answer_seconds':final_timing-raw['monotonic_start'] if final_timing else None,
                        'request_seconds':sum(r.get('elapsed_seconds',0) for r in requests),
                        'tool_seconds':sum(c.get('elapsed_seconds',0) for c in raw['tool_calls'])},
             'resources':{'model_steps':len(requests),'tool_calls':len(raw['tool_calls']),
                          'evidence_characters':raw['evidence_characters']},
             'original_record_path':name,'original_record_sha256':hashlib.sha256((root/name).read_bytes()).hexdigest()}
        rows.append(row)
    return rows,redactions


def quote_encoding(grade,packet):
    if grade is None:
        return None,[]
    changes=[]
    sources={entry['id']:entry['text'] for entry in packet['candidate_evidence']}
    for unit in grade.get('units',[]):
        for reference in unit.get('evidence',[]):
            quote=reference.get('quote')
            text=sources.get(reference.get('source_id'),'')
            if isinstance(quote,str) and quote not in text:
                original=quote
                for _ in range(3):
                    quote=json.dumps(quote,ensure_ascii=False)[1:-1]
                    if quote in text:
                        reference['quote']=quote
                        changes.append({'unit_id':unit['id'],'source_id':reference['source_id'],
                                        'original':original,'encoded':quote,
                                        'reason':'JSON transport escaping only; semantic labels unchanged'})
                        break
    return grade,changes


def batches(jobs):
    output=[]
    for batch in jobs:
        if len(json.dumps(batch,ensure_ascii=False))<=250000 or len(batch['jobs'])==1:
            output.append(batch)
        else:
            for job in batch['jobs']:
                output.append({key:value for key,value in batch.items() if key!='jobs'}|{'jobs':[job]})
    return output


def call_batch(batch,stage,root,authorization,contract,instruction,bundle):
    context_id='stateless-'+stage+'-'+uuid.uuid4().hex
    payload=json.loads(json.dumps(batch))
    if stage=='review':
        for job in payload['jobs']:
            job.pop('base_grade',None)
    control={'stage':stage,'fresh_context_id':context_id,
             'session_id_convention':'This is the actual orchestrator-assigned fresh stateless request context, not a stored OpenCode session.'}
    prompt=instruction+'\n\nReturn ONLY a JSON array with one '+('review envelope' if stage=='review' else 'grade')+' per listed job, in order. '
    prompt+='Use short exact candidate-evidence substrings for support; do not silently clean JSON escapes. '
    prompt+='If the frozen rubric needs a semantic correction, flag uncertain and start the rationale with RUBRIC_REVIEW_REQUIRED; never silently repair gold.\n'
    prompt+=json.dumps({'control':control,**payload},ensure_ascii=False)
    returned=generate(context_id,prompt,root/'controller-work'/stage,authorization,contract)
    if isinstance(returned,dict) and len(batch['jobs'])==1:
        returned=[returned]
    if not isinstance(returned,list) or len(returned)!=len(batch['jobs']):
        raise ValueError('controller output cardinality mismatch; no automatic regeneration')
    output=[]
    for value,job in zip(returned,batch['jobs']):
        packet=job['packet']
        if value.get('blind_id')!=packet['blind_id']:
            raise ValueError('controller blind identity mismatch')
        grade=value.get('grade') if stage=='review' else value
        grade,encoding=quote_encoding(grade,packet)
        validated=validate_grade(grade,packet)
        if 'RUBRIC_REVIEW_REQUIRED' in json.dumps(value):
            raise ValueError('semantic rubric review required before sealing')
        if stage=='review':
            if value.get('session_id')!=context_id or value.get('base_grade_hash')!=job['base_grade_hash']:
                raise ValueError('review context/base provenance mismatch')
            value['grade']=validated
        else:
            value=validated
        save(root/'grades'/stage/(packet['blind_id']+'.json'),value,immutable=True)
        if encoding:
            save(root/'controller-work'/stage/(context_id+'-'+packet['blind_id']+'-encoding.json'),encoding,immutable=True)
        output.append(value)
    return output


def run_jobs(jobs,stage,root,authorization,contract,instruction,bundle):
    iterator=iter(jobs)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        active=set()
        for _ in range(2):
            job=next(iterator,None)
            if job is not None:
                active.add(pool.submit(call_batch,job,stage,root,authorization,contract,instruction,bundle))
        while active:
            finished,_=concurrent.futures.wait(active,return_when=concurrent.futures.FIRST_COMPLETED)
            # Inspect every completed future before queuing another generation.
            results=[future.result() for future in finished]
            active-=finished
            for result in results:
                yield result
                job=next(iterator,None)
                if job is not None:
                    active.add(pool.submit(call_batch,job,stage,root,authorization,contract,instruction,bundle))


def finalize(root=ROOT):
    check(root)
    index=json.loads((root/'execution/index.json').read_text())
    if index['terminal_trials']!=648 or index['status'] not in ('candidate_execution_complete','incomplete'):
        raise RuntimeError('execution is not terminal; do not grade a moving study')
    if index.get('credential_hygiene',{}).get('secret_matches')!=0:
        raise RuntimeError('credential hygiene not established; no grading generation dispatched')
    runtime=json.loads((root/'contracts/runtime.json').read_text())
    audit=audit_execution(root/'execution',runtime)
    if audit['status']!='passed' or audit['trials']!=648:
        raise RuntimeError('execution audit failed: '+json.dumps(audit))
    records,redactions=normalized_records(root,index)
    tasks=[]
    gold={}
    for suite in ('web','code'):
        tasks.extend(json.loads((root/f'tasks/{suite}/tasks.json').read_text()))
        gold.update(json.loads((root/f'gold/{suite}/gold.json').read_text()))
    schedule=json.loads((root/'schedule.json').read_text())
    def loader(name):
        path=(root/name).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError('grading evidence escapes owned root')
        return path.read_text()
    bundle=export(records,tasks,gold,loader,schedule)
    save(root/'blind/bundle.json',bundle,immutable=True)
    save(root/'private/normalized-records.json',records,immutable=True)
    save(root/'private/identity-redactions.json',redactions,immutable=True)
    contract=json.loads((root/'contracts/grader.json').read_text())
    base,authorization=service_auth()
    if not contract['endpoint'].startswith(base+'/'):
        raise RuntimeError('controller service changed; no grading generation dispatched')
    instruction=(root/'grading/prompt.md').read_text()
    work=root/'controller-work'
    work.mkdir(exist_ok=True)
    jobs=batches(pack_jobs(bundle,batch_size=2))
    save(work/'base-jobs.json',jobs,immutable=True)
    originals={}
    for results in run_jobs(jobs,'base',root,authorization,contract,instruction,bundle):
        for grade in results:
            originals[grade['blind_id']]=grade
        print(json.dumps({'grading':'base','sealed_candidates':len(originals),'required':sum(p['completed'] for p in bundle['packets'].values())}),flush=True)
    base_seal=seal_base(bundle,originals)
    save(root/'grades/base-seal.json',base_seal,immutable=True)
    review_jobs=batches(pack_jobs(bundle,batch_size=2,review=True,base_grades=base_seal['grades']))
    save(work/'review-jobs.json',review_jobs,immutable=True)
    reviews=[]
    for results in run_jobs(review_jobs,'review',root,authorization,contract,instruction,bundle):
        reviews.extend(results)
        print(json.dumps({'grading':'review','reviewed':len(reviews)}),flush=True)
    disagreements=[review for review in reviews if _decisions(review['grade'])!=_decisions(originals.get(review['blind_id']))]
    adjudications=[]
    for review in disagreements:
        identity=review['blind_id']
        payload={'packet':bundle['packets'][identity],'original_grade':originals.get(identity),'independent_review':review,
                 'base_grade_hash':digest(originals.get(identity)),'review_hash':digest(review)}
        job_id='stateless-adjudication-'+uuid.uuid4().hex
        prompt=instruction+'\n\nPerform separate blinded adjudication of this disagreement. Return ONLY the adjudication envelope JSON; preserve exact blind_id, base_grade_hash and review_hash. Do not change gold or conceal a rubric error.\n'+json.dumps(payload,ensure_ascii=False)
        event=generate(job_id,prompt,work/'adjudication',authorization,contract)
        event['grade'],encoding=quote_encoding(event.get('grade'),bundle['packets'][identity])
        event['grade']=validate_grade(event['grade'],bundle['packets'][identity])
        if 'RUBRIC_REVIEW_REQUIRED' in json.dumps(event):
            raise ValueError('adjudication requires consistent rubric review')
        save(root/'grades/adjudication'/(identity+'.json'),event,immutable=True)
        adjudications.append(event)
    final_seal=seal_final(bundle,base_seal,reviews,adjudications)
    save(root/'grades/final-seal.json',final_seal,immutable=True)
    write_artifacts(root/'report',records,final_seal,schedule,tasks,draws=10000)
    math_audit=audit_artifacts(root/'report')
    check(root)
    save(root/'report/execution-audit.json',audit,immutable=True)
    save(root/'report/analysis-audit.json',math_audit,immutable=True)
    receipt={'schema_version':1,'candidate_execution_status':index['status'],'terminal_trials':648,
             'attempted_trials':index['attempted_trials'],'reviews':final_seal['review_accounting'],
             'controller_client_requests':len(list(work.rglob('*-lease.json'))),
             'controller_upstream_attempts':'UNVERIFIED; broker returns text only',
             'execution_audit':audit['status'],'analysis_audit':math_audit,
             'freeze_unchanged':True,'semantic_truth_certified_by_integrity_audit':False}
    save(root/'report/final-audit.json',receipt,immutable=True)
    print(json.dumps(receipt,indent=2),flush=True)
    return receipt


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--finalize',action='store_true',required=True)
    parser.parse_args()
    finalize()
