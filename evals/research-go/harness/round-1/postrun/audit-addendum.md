# Post-run audit amendment: public documentation field false positive

**Independent review pending. This is a saved-audit correction, not permission
for new inference, reruns, scoring changes or unblinding.**

After all 72 scheduled cases completed and the access gate passed, the original
sealed collected-stage audit stopped at its generic credential regex. Examination
of the saved artifacts found 36 matches in 12 execution text files: the literal
public documentation field `"Authorization":`, not a credential value. Each match
has SHA-256 `81d54facb40f6897ee428462a51dbaa0fde638e5b023f15811d05d66923b4e19`.
The field occurs three times in each of the two frozen Cloudflare D1 replication
extractions (canonical HTML and native Markdown). Their public source URLs are:

* https://developers.cloudflare.com/d1/best-practices/read-replication/
* https://developers.cloudflare.com/d1/best-practices/read-replication/index.md

The 12 execution files are six successful fetches' full/model text copies of the
canonical archive, with 3 matches per file. Both frozen extractions establish the
public-field provenance; no model preview transformation or controller re-fetch
is used as substitute evidence. The saved parent provisioning proof reports zero
exact selected-key matches. This amendment never reads a credential store or key.

## Mechanism and limits

`postrun/verify.py` pins the exact original freeze, freeze receipt, original verifier
and source manifest hashes. It verifies both allowed sources' raw/extracted hashes
against that freeze, then compiles the **unchanged original verifier bytes** as a
non-main module with the original `__file__`. All original audit classes, stages,
CLI parsing, grade/seal checks and analysis behavior remain original code.

Only that private module's `re` binding receives a proxy. Stdlib `re` is untouched.
Every operation delegates unchanged except `search` of the exact original generic
credential pattern with default flags, called directly by the exact original
`Auditor.collected` code object at its scan site. Even the same pattern on the same
document outside that scan context remains a match.

At that site, a match can be disregarded only if:

1. The current path is a `.txt` file inside that case's opaque `fetches/` directory,
   explicitly linked as `text_path` or `model_text_path` by a successful, error-free
   fetch of one of the two exact source URLs.
2. Requested/final URLs identify the frozen archive, both stored text hashes equal
   the frozen extraction, truncation is false, and actual bytes equal that archive.
3. The on-disk bytes and the exact text being scanned still have that same hash.
4. **Every** generic-regex match has the one known public-field match hash; bearer,
   sk-style or other structured-key matches cannot ride on a benign first match.

The original collected audit has already checked the complete request ledger,
native histories, tool results, fetch hashes/provenance and case cleanup before
this scan. The wrapper does not trust a success boolean alone. Request bodies,
API headers, arbitrary copies, modified documents, unlinked text and unknown JSON
fields are not exempt. Original saved process/credential hygiene proof remains
mandatory. The wrapper introduces no broad keyword or field-name allowlist.

## Preservation and proof

All original code, tests, protocol, tasks/gold, archives, schedule, preflight,
freeze and execution evidence remain unchanged. No run was repeated; no prompts,
rubrics, qualification, eligibility, statistics, speed margins or price policy
changed. Original frozen hashes are regression-checked. These new `postrun/` files
are deliberately outside the original experiment seal; review and seal this
amendment separately, with its provenance recorded in the later report.

`correction.json` records pinned inputs, source/match hashes, linked text paths,
proof counts and amendment helper hashes. It is not a grade, completed-comparison
report, independent review seal or authorization to bypass later stages.

Development proof commands:

```sh
python3 -B postrun/verify.py -h
python3 -B -m unittest discover -s postrun/tests -p 'test_*.py'
python3 -B postrun/verify.py --stage collected
```

Collected passes with this narrow amendment; the unmodified original still fails
on the same public-field false positive. Default final audit remains unsuccessful
while blind grades, grade seals, analysis/report and final review are missing.
The tests exercise this in an isolated copy without fabricating later evidence.
They also reject synthetic bearer/sk markers, unknown Authorization keys, changed
or unlinked documents and sealed-input tampering, and preserve unrelated original
audit failures. No native answers or credential values are printed or added here.
