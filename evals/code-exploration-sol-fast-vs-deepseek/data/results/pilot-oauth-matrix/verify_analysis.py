import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "frozen-source"))
import cases
import runtime

frozen = json.loads((ROOT / "freeze.json").read_text())
analysis = json.loads((ROOT / "analysis.json").read_text())
assert analysis["freeze"] == frozen
for name, expected in {**frozen["source_sha256"], "README.md": frozen["protocol_sha256"]}.items():
    assert runtime.source_hash(ROOT / "frozen-source" / name) == expected, name
expected_rows = {row["id"]: row for row in analysis["rows"]}
count = 0
with tempfile.TemporaryDirectory() as folder:
    work = Path(folder) / "orders-service"
    cases.build(work)
    assert cases.snapshot(work) == frozen["fixture_sha256"]
    for row in frozen["schedule"]:
        trial = ROOT / row["id"]
        result = json.loads((trial / "result.json").read_text())
        assert result == expected_rows[row["id"]]
        assert result["status"] == "completed" and result["fixture_unchanged"]
        item = next(c for c in frozen["candidates"] if c["id"] == row["candidate"])
        candidate = runtime.Candidate(**{k: v for k, v in item.items() if k != "selection"})
        exported = json.loads((trial / "session.json").read_text())
        parsed = runtime.parse_session(exported, candidate, Path(exported["info"]["location"]["directory"]))
        assert cases.grade(row["case"], work, parsed["final"]) == result["grade"]
        assert parsed["usage"] == result["usage"]
        requests = json.loads((trial / "requests.json").read_text())
        assert runtime.verify_requests(candidate, requests, result["session_id"]) == result["transport"]
        count += len(requests)
assert len(expected_rows) == 210 and count == 949
print(f"Verified 210 trials and {count} model requests against frozen sources; no inference.")
