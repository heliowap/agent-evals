# Small files A/B: report (stage-1)

**Verdict: reduction below 20%.** Next step: stop.

| | A | B |
|---|---|---|
| Trials | 12 | 12 |
| Passed | 12 | 12 |

Peak-context ratio B/A (geometric mean over tasks of median ratios): **1.152**, 95% bootstrap interval [0.985, 1.287].
Passing trials only (sensitivity): 1.152.

Excluded for invalid session configuration: none.

## Per task and arm (medians)

| Task | Arm | Pass | Peak ctx | Fresh in | Cache read | Cache create | Output | API calls | Turns | Cost $ | File exposure | Largest exposure | Exposures >5k | Reads | Chunked | Timeouts | Turn cap |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| t1-basic-auth-colon | A | 3/3 | 10,659 | 16 | 61,762 | 5,193 | 2,759 | 8 | 10 | 0.003 | 984 | 282 | 0 | 3 | 2 | 0 | 0 |
| t1-basic-auth-colon | B | 3/3 | 11,444 | 16 | 63,460 | 6,012 | 2,705 | 8 | 9 | 0.003 | 1,187 | 340 | 0 | 1 | 0 | 0 | 0 |
| t2-mount-multisegment | A | 3/3 | 21,056 | 24 | 159,229 | 15,536 | 8,027 | 12 | 12 | 0.009 | 4,664 | 1,167 | 0 | 0 | 1 | 0 | 0 |
| t2-mount-multisegment | B | 3/3 | 24,090 | 24 | 194,663 | 19,308 | 8,223 | 12 | 15 | 0.010 | 5,842 | 1,423 | 0 | 0 | 0 | 0 | 0 |
| t3-uuid-filter | A | 3/3 | 30,578 | 38 | 376,477 | 25,796 | 11,906 | 19 | 21 | 0.015 | 7,220 | 2,248 | 0 | 1 | 1 | 0 | 1 |
| t3-uuid-filter | B | 3/3 | 36,224 | 36 | 428,561 | 31,442 | 15,084 | 18 | 23 | 0.018 | 9,543 | 2,219 | 0 | 2 | 2 | 0 | 0 |
| t4-request-id | A | 3/3 | 59,851 | 34 | 604,824 | 54,250 | 32,637 | 17 | 22 | 0.033 | 13,407 | 3,181 | 0 | 2 | 2 | 0 | 0 |
| t4-request-id | B | 3/3 | 72,531 | 32 | 724,095 | 67,749 | 28,281 | 16 | 21 | 0.035 | 24,417 | 4,889 | 0 | 0 | 0 | 0 | 0 |

## Flags

- `s1-r3-t4-request-id-b`: {"network": ["S=<scratchpad> && cat > $S/e2e.py <<'EOF'\nimport bottle\napp = bottle.Bottle()\napp.config['request_id.header'] = 'X-Request-ID'\n\n@app.route('/')\ndef index(): return 'hi ' + bottle.request.request_id\n\n@app.route('/abort')\ndef abort_route(): bottle.abort(403, 'no')\n\napp.run(host='127.0.0.1', port=18765, quiet=True)\nEOF\ncd . && (PYTHONPATH=$PWD python $S/e2e.py &) && sleep 1 && curl -s -i http://127.0.0.1:18765/ ; echo; echo ----; curl -s -i -H 'X-Request-ID: from-client' http://127.0.0.1:18765/abort | head -5; echo ----; curl -s -i http://127.0.0.1:18765/nope | head -4; pkill -f \"$S/e2e.py\"; echo done", "S=<scratchpad> && cd . && (PYTHONPATH=$PWD python $S/e2e.py &) && sleep 1 && curl -s -D - -o /dev/null http://127.0.0.1:18765/nope; pkill -f \"$S/e2e.py\"; echo; cd . && git status --short"]}

Limitations: directional pilot; N per task is small; one interim look if stage 2 runs; bottle is in training data; token exposure for Bash file prints is matched by command name.
