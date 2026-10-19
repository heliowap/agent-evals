import hashlib
from collections import Counter
import json
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "frozen-source"))
import bench
import cases
import runtime

frozen = json.loads((ROOT / "freeze.json").read_text())
analysis = json.loads((ROOT / "analysis.json").read_text())
assert analysis["freeze"] == frozen
for name, expected in {**frozen["source_sha256"], "README.md": frozen["protocol_sha256"]}.items():
    assert hashlib.sha256((ROOT / "frozen-source" / name).read_bytes()).hexdigest() == expected, name
expected_rows = {row["id"]: row for row in analysis["rows"]}
assert len(expected_rows) == len(frozen["schedule"]) == 120
count = failures = completed = 0
flags = {candidate["id"]: Counter() for candidate in frozen["candidates"]}
models = {candidate["id"]: Counter() for candidate in frozen["candidates"]}
with tempfile.TemporaryDirectory() as folder:
    work = Path(folder) / "orders-service"
    cases.build(work)
    assert cases.snapshot(work) == frozen["fixture_sha256"]
    replica = Path(folder) / "report"
    replica.mkdir()
    shutil.copyfile(ROOT / "freeze.json", replica / "freeze.json")
    for row in frozen["schedule"]:
        trial = ROOT / row["id"]
        result = json.loads((trial / "result.json").read_text())
        assert result == expected_rows[row["id"]]
        assert all(result[key] == value for key, value in row.items())
        assert result["fixture_unchanged"]
        assert json.loads((trial / "initial-files.json").read_text()) == frozen["fixture_sha256"]
        assert (trial / "prompt.txt").read_text() == frozen["cases"][row["case"]]["prompt"]
        item = next(c for c in frozen["candidates"] if c["id"] == row["candidate"])
        assert result["requested"] == item
        candidate = runtime.Candidate(**{key: value for key, value in item.items() if key != "selection"})
        requests = json.loads((trial / "requests.json").read_text())
        flags[row["candidate"]].update(str(request["status"]) for request in requests if request.get("error"))
        models[row["candidate"]].update(response["model"] for request in requests
                                        for response in request["responses"] if response.get("model"))
        assert all(request["complete"] for request in requests)
        assert runtime.verify_requests(candidate, requests, result.get("session_id")) == result["transport"]
        count += len(requests)
        if result["status"] == "completed":
            completed += 1
            exported = json.loads((trial / "session.json").read_text())
            parsed = runtime.parse_session(exported, candidate, Path(exported["info"]["location"]["directory"]))
            assert parsed["final"] == (trial / "answer.json.txt").read_text()
            assert cases.grade(row["case"], work, parsed["final"]) == result["grade"]
            assert parsed["usage"] == result["usage"]
            assert parsed["observed_identity"] == result["observed_identity"]
            assert all(request["status"] == 200 for request in requests)
        else:
            failures += 1
            assert result["status"] == "task_error" and row["candidate"].startswith("gemini-")
            events = [json.loads(line) for line in (trial / "events.jsonl").read_text().splitlines() if line.startswith("{")]
            errors = [event["error"] for event in events if event["type"] == "error"]
            assert len(errors) == 1 and errors[0]["status"] == 400
            assert errors[0]["message"] == "Requests ending with a model turn are not supported."
            assert len(requests) == 25 and requests[-1]["status"] == 400
            assert all(request["status"] == 200 for request in requests[:-1])
            assert sum(event["type"] == "step_finish" for event in events) == 24
        target = replica / row["id"]
        target.mkdir()
        shutil.copyfile(trial / "result.json", target / "result.json")
    assert bench.report(replica) == analysis["summary"] == json.loads((ROOT / "summary.json").read_text())
assert count == analysis["request_count"] == 1365
assert completed == 103 and failures == 17
for candidate in frozen["candidates"]:
    name = candidate["id"]
    assert dict(flags[name]) == analysis["details"][name]["observer_error_flags_by_status"]
    assert dict(models[name]) == analysis["details"][name]["reported_response_models"]
assert sum(value["200"] for value in flags.values()) == 743
assert set(models["gemini-medium"]) == set(models["gemini-high"]) == {"gemini-3.8-flash-n"}
print(f"Verified 120 trials, 103 completed answers, 17 protocol errors and {count} model requests; no inference.")
