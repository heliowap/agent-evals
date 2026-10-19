# Independent Haiku exploration review

One actionable finding, P2. No additional material issues found in the reviewed execution, capture, provenance, grading or privacy paths.

## P2: HTTP 200 observer failures pass the smoke gate

`runtime.py:370-371` records provider/transport/metadata failures as `record.error`. These failures can retain HTTP status 200 and have `complete=true`, for example an SSE provider failure or stream cancellation. `runtime.py:414-415` only counts non-200 and incomplete requests. `haiku.py:109` uses these two counters to authorize the 150-trial pilot, ignoring the error flag. The `successful` list in `runtime.py:402` excludes these calls, but that list only contributes Fast confirmation, which this cohort does not require.

Offline reproduction used the existing `CampaignProof.build_smoke()` fixture, added `error="Observed provider or transport failure"` to trial-0005's otherwise valid HTTP 200 complete request, and called `haiku.smoke_passed()`. It returned `True`. The error flag is a supported observer state, not malformed input. A request that fails within HTTP 200 and then recovers can therefore authorize the pilot, while an equivalent non-200 recovery is rejected.

Add an explicit observed-error count to transport summaries and include it in the smoke rejection conditions. Add a negative gate test for a completed HTTP 200 request carrying `error`. Preserve the request records and continue treating recovered calls in the pilot as observations if that remains the intended protocol.

## Verification and limits

Ran `python3 -B -m unittest discover -s exploracao/haiku-5-5 -p 'test_*.py'`: 37 passed. Ran `node --test exploracao/haiku-5-5/test_observer.mjs`: 7 passed. The Python provenance test checked the unchanged inherited files. No model CLI, preflight, inference, web access, historical report regeneration or repository edits were performed. The finding reproduction used a disposable temporary directory.

Reviewed the current wrapper, scheduling/core loop, runtime, observer, new tests, README and DESIGN. The native implementation remains unverified by this review. Synthetic export tests do not establish native export behavior or its prior failure cause. Review used the same GPT model family and does not supply independent-family evidence.

## Reviewed SHA-256

- `DESIGN.md`: `b0c19c85fc68d4897273fe32267bfa2322ff8207d3ff30cbf54448b0ed594836`
- `README.md`: `a91ef8dc2b06442a2ccdaeefebc8175b4239796dd16e43056dd3660a4c700c71`
- `haiku.py`: `5f76699caa12f828ddf68b0f14a71260ae0333faa503ffd2526abfea75c9e058`
- `bench.py`: `519faca3658a93385380373bd455c60fd2cac51ad9b7cdf3da7fbcab4e7b72b3`
- `runtime.py`: `6e2a17e5f5387e88d188faf652ab1812304dfe683e9ccde1c13d6de6aec26470`
- `test_haiku.py`: `d98b895af1eb3b300f38c2c5ff97b2b23d4da08f4ec127d6fa378319182cb831`
- `test_observer.mjs`: `62c4b754bff296ed4ef9cfcda24f9318170fff493a29855a4a2e59775711f511`
- `cases.py`: `5a32f8cf77552115f9c28bcf6ac543184e3258f0f43fb3e7a71917944a495d02`
- `test_cases.py`: `a3f1d71545f23843a3af80d7eee9bb42d7ed600d45d955a2553b6be957eee197`
- `observer.js`: `a9be79b410bc789d4e13013688ec07f484ee5415f82c149f0cd064794e98e622`
- `provenance.json`: `e12c22555fab65945fcd4d4286ac57b29123aca4ae018fde5b82618630dc5104`
- `models.json`: `f6a22feaaf4916289ead67712a27b2ba7ccdb38f6dc23ddfae11158b28a1a761`
