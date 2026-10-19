import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import analysis
from verify import audit, AuditError, CONFIGS, digest
import fixtures as f


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def fail(self, stage, pattern=None):
        if pattern is None:
            return super().fail(stage)
        with self.assertRaisesRegex(AuditError, pattern):
            audit(self.root, stage)

    def first(self):
        return f.read(self.root, "execution/index.json")["cases"][0]

    def grade_path(self):
        return str(next(self.root.glob("grades/shard-a/*.json")).relative_to(self.root))

    def test_frozen_zero_execution_and_hashes(self):
        f.frozen(self.root)
        self.assertEqual(audit(self.root, "frozen")["candidate_post_starts"], 0)
        (self.root/"dataset/archive/T1-1.txt").write_text("changed gold source")
        self.fail("frozen", "changed hash")

    def test_changed_uncovered_code_rejected(self):
        f.frozen(self.root)
        f.write(self.root, "tests/audit/new.py", "# added after freeze")
        self.fail("frozen", "uncovered immutable")

    def test_frozen_rejects_post_starts_and_prefreeze_inputs(self):
        f.frozen(self.root)
        f.collected(self.root)
        self.fail("frozen", "zero POST starts")
        ledger = (self.root/"execution/post-starts.jsonl").read_text().splitlines()
        row = json.loads(ledger[0]); row["started_utc"] = f.stamp(-1)
        ledger[0] = json.dumps(row)
        f.write(self.root, "execution/post-starts.jsonl", "\n".join(ledger)+"\n")
        self.fail("collected", "POST started before seal")

    def test_schedule_and_parent_proof(self):
        f.frozen(self.root)
        f.edit(self.root, "schedule.json", lambda d: d["cases"][0].update(configuration_id="glm-low"))
        f.reseal(self.root)
        self.fail("frozen", "case model/effort")
        f.frozen(self.root)
        f.edit(self.root, "preflight/workflow.json", lambda d: d.update(external_secret_paths_imported=True))
        self.fail("frozen", "parent workflow|changed hash")

    def test_complete_final_and_commands(self):
        f.complete(self.root)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(analysis.main(["--root", str(self.root)]), 0)
        f.final_review(self.root)
        result = audit(self.root, write=True)
        self.assertTrue(result["completed_comparison"])
        self.assertFalse(result["semantic_truth_proven_by_audit"])
        self.assertTrue((self.root/"analysis/paired.csv").is_file())
        self.assertTrue((self.root/"analysis/tasks.csv").is_file())
        self.assertTrue((self.root/"audit.json").is_file())

    def test_valid_gate_is_not_speed_comparison(self):
        f.frozen(self.root); f.collected(self.root, "access_blocked")
        self.assertEqual(audit(self.root, "collected")["study_status"], "access_blocked")
        result = analysis.analyze(self.root)
        self.assertIsNone(result["qualified_latency"])
        f.write(self.root, "analysis/block-report.json", result)
        f.final_review(self.root)
        self.assertEqual(audit(self.root)["completion"], "honest_access_block")
        f.edit(self.root, "execution/index.json", lambda d: d.update(attempted_cases=72))
        self.fail(None, "count mismatch")

    def test_other_interruption_preserves_rows_but_fails_final(self):
        f.frozen(self.root); f.collected(self.root, "incomplete")
        self.assertEqual(audit(self.root, "collected")["study_status"], "incomplete")
        self.fail(None, "incomplete.*missing")
        with self.assertRaisesRegex(AuditError, "incomplete study"):
            analysis.analyze(self.root)
        self.assertEqual(len(f.read(self.root, "execution/index.json")["cases"]), 72)

    def test_missing_later_stage_is_failure(self):
        f.frozen(self.root); f.collected(self.root)
        self.fail(None, "missing grades stage artifact")
        f.blinded(self.root); f.grades(self.root)
        (self.root/"grades-seal.json").unlink()
        self.fail("graded", "missing graded stage artifact")

    def test_duplicate_and_hidden_requests(self):
        for extra in (False, True):
            with self.subTest(extra=extra):
                f.frozen(self.root); f.collected(self.root)
                if extra:
                    f.write(self.root, "execution/hidden/arbitrary-outbound.json", {"model": "hidden", "reasoning_effort": "low", "messages": []})
                    self.fail("collected", "unledgered")
                    (self.root/"execution/hidden/arbitrary-outbound.json").unlink()
                else:
                    path = self.root/"execution/post-starts.jsonl"
                    text = path.read_text(); path.write_text(text+text.splitlines()[0]+"\n")
                    self.fail("collected", "duplicate, hidden extra")

    def test_actual_model_all_steps_and_step8_no_tools(self):
        f.frozen(self.root); f.collected(self.root, steps=8)
        self.assertTrue(audit(self.root, "collected")["ok"])
        r = f.read(self.root, self.first())
        last = r["requests"][-1]["request_path"]
        f.edit(self.root, last, lambda d: d.update(tools=f.read(self.root, "tools.json")))
        self.fail("collected", "step 8 tools")
        f.edit(self.root, last, lambda d: d.update(tools=[], reasoning_effort="low" if r["effort"] != "low" else "high"))
        self.fail("collected", "actual model/reasoning_effort")

    def test_usage_missing_remains_null_and_inclusive(self):
        f.frozen(self.root); f.collected(self.root)
        path = self.first(); r = f.read(self.root, path)
        for req in r["requests"]:
            f.edit(self.root, req["response_path"], lambda d: d.pop("usage"))
            req["usage"] = None
        r["usage"] = f.usage([None]*len(r["requests"]))
        f.write(self.root, path, r)
        self.assertTrue(audit(self.root, "collected")["ok"])
        r["usage"]["completion_tokens"] = 0
        f.write(self.root, path, r)
        self.fail("collected", "unknown must stay null")
        f.collected(self.root)
        f.edit(self.root, self.first(), lambda d: d["usage"].update(completion_tokens=50))
        self.fail("collected", "native completion is inclusive")

    def test_overlap_limits_and_cleanup(self):
        f.frozen(self.root); f.collected(self.root)
        f.edit(self.root, self.first(), lambda d: d.update(wall_s=181))
        self.fail("collected", "wall/deadline")
        f.collected(self.root)
        f.edit(self.root, "execution/cleanup/credentials.json", lambda d: d.update(secret_matches=1))
        self.fail("collected", "credential hygiene")
        f.collected(self.root)
        p = f.read(self.root, "execution/index.json")["cases"][1]
        f.edit(self.root, p, lambda d: d.update(start_utc=f.stamp(11)))
        self.fail("collected", "sequential overlap")

    def test_source_full_body_truncation_and_drift(self):
        f.frozen(self.root); f.collected(self.root)
        path = self.first(); r = f.read(self.root, path)
        fetch = r["fetches"][0]
        f.write(self.root, fetch["model_text_path"], "Official documented claim.")
        fetch["model_text_sha256"] = digest(self.root/fetch["model_text_path"])
        f.write(self.root, path, r)
        self.fail("collected", "false truncation")
        fetch["truncated"] = True
        history = f.read(self.root, r["history_path"])
        next(m for m in history if m.get("role") == "tool")["content"] = "Official documented claim."
        f.write(self.root, r["history_path"], history)
        f.write(self.root, path, r)
        next_body = r["requests"][1]["request_path"]
        f.edit(self.root, next_body, lambda d: next(m for m in d["messages"] if m.get("role") == "tool").update(content="Official documented claim."))
        self.assertTrue(audit(self.root, "collected")["ok"])
        (self.root/fetch["raw_path"]).unlink()
        self.fail("collected", "missing collected stage artifact")

    def test_blind_leaks_shards_and_quote_fabrication(self):
        f.complete(self.root)
        self.assertTrue(audit(self.root, "grades", "a")["ok"])
        blind = f.read(self.root, "blind/index.json")["cases"][0]
        path = f"blind/cases/{blind}/case.json"
        f.edit(self.root, path, lambda d: d["mechanical"].update(wall_s=1))
        f.edit(self.root, "private/unblind.json", lambda d: d["sealed_hashes"].update({path: digest(self.root/path)}))
        self.fail("grades", "metadata leak")
        f.blinded(self.root); f.grades(self.root)
        f.edit(self.root, self.grade_path(), lambda d: d["checks"][0].update(answer_quote="fabricated claim"))
        self.fail("grades", "fabricated answer quote")
        f.grades(self.root)
        f.edit(self.root, self.grade_path(), lambda d: d["checks"][0]["evidence"][0].update(quote="fabricated source"))
        self.fail("grades", "fabricated source quote")
        f.grades(self.root)
        f.edit(self.root, "blind/index.json", lambda d: d["shards"]["b"].__setitem__(0, d["shards"]["a"][0]))
        self.fail("grades", "disjoint 36/36")

    def test_missing_checks_require_empty_quote_and_rationale(self):
        f.complete(self.root)
        path = self.grade_path()
        def missing(d):
            d["checks"][0].update(status="missing", answer_quote="", evidence=[], citation_status="missing", rationale="Required claim absent.")
        f.edit(self.root, path, missing)
        self.assertTrue(audit(self.root, "grades")["ok"])
        f.edit(self.root, path, lambda d: d["checks"][0].update(rationale=""))
        self.fail("grades", "semantic rationale")

    def test_private_join_tamper_and_unlisted_blind_artifact(self):
        f.complete(self.root)
        mapping = f.read(self.root, "private/unblind.json")
        ids = [b for b in mapping["mapping"] if f.read(self.root, f"blind/cases/{b}/case.json")["task_id"] == "T1"][:2]
        mapping["mapping"][ids[0]], mapping["mapping"][ids[1]] = mapping["mapping"][ids[1]], mapping["mapping"][ids[0]]
        f.write(self.root, "private/unblind.json", mapping)
        self.fail("graded", "identity mapping changed")
        f.blinded(self.root); f.grades(self.root)
        f.write(self.root, "blind/hidden-native-response.json", {"backend_id": "private-identity", "completion_tokens": 10})
        self.fail("grades", "extra grader input artifact")

    def test_missing_native_history_and_fabricated_mechanical(self):
        f.complete(self.root)
        record = f.read(self.root, self.first())
        native = record["requests"][-1]["response_path"]
        f.edit(self.root, native, lambda d: d["choices"][0]["message"].update(content="hidden different answer"))
        self.fail("collected", "native assistant response absent")
        f.collected(self.root); f.blinded(self.root); f.grades(self.root)
        blind = f.read(self.root, "blind/index.json")["cases"][0]
        path = f"blind/cases/{blind}/case.json"
        f.edit(self.root, path, lambda d: d["mechanical"].update(fetched_two_sources=False))
        f.edit(self.root, "private/unblind.json", lambda d: d["sealed_hashes"].update({path: digest(self.root/path)}))
        self.fail("grades", "fabricated mechanical fetched_two_sources")

    def test_runner_style_complete_and_gate_exports(self):
        for status in ("completed", "access_blocked", "incomplete"):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                f.frozen(root); f.collected(root, status)
                self.assertEqual(audit(root, "collected")["study_status"], status)
                f.blinded(root); f.runner_blind_style(root); f.grades(root)
                self.assertTrue(audit(root, "graded")["ok"])
                if status == "incomplete":
                    with self.assertRaisesRegex(AuditError, "incomplete.*missing"):
                        audit(root)

    def test_redirect_objects_and_authenticated_post_redirect_denial(self):
        f.frozen(self.root); f.collected(self.root)
        path = self.first(); r = f.read(self.root, path)
        fetch = r["fetches"][0]
        fetch["redirects"] = [{"from": fetch["requested_url"], "to": fetch["final_url"], "status": 301}]
        f.write(self.root, path, r)
        self.assertTrue(audit(self.root, "collected")["ok"])
        fetch["redirects"][0]["to"] = "https://evil.example/"
        f.write(self.root, path, r)
        self.fail("collected", "outside official frozen URL")
        f.collected(self.root)
        f.edit(self.root, "protocol.json", lambda d: d["security"].update(auth_post_redirects=True))
        f.reseal(self.root)
        self.fail("frozen", "auth redirects forbidden")

    def test_native_cache_aliases_unknown_writes_cost_and_inclusive_output(self):
        f.frozen(self.root); f.collected(self.root)
        path = self.first(); r = f.read(self.root, path)
        raw = {"prompt_tokens": 100, "completion_tokens": 40, "prompt_cache_hit_tokens": 20,
               "prompt_cache_miss_tokens": 80, "prompt_tokens_details": {"cached_tokens": 20},
               "completion_tokens_details": {"reasoning_tokens": 10}, "new_upstream_field": "preserved"}
        for req in r["requests"]:
            f.edit(self.root, req["response_path"], lambda d: d.update(usage=raw))
            req["usage"] = raw
        r["usage"] = f.usage([raw]*len(r["requests"]))
        f.write(self.root, path, r)
        self.assertTrue(audit(self.root, "collected")["ok"])
        self.assertEqual(r["usage"]["uncached_input_tokens"], 160)
        self.assertEqual(r["usage"]["completion_tokens"], 80)
        self.assertIsNone(r["usage"]["cache_write_tokens"])
        self.assertIsNone(r["usage"]["reported_cost"])
        self.assertFalse(r["usage"]["complete"])
        r["usage"]["cache_write_tokens"] = 0
        f.write(self.root, path, r)
        self.fail("collected", "unknown must stay null")

    def test_timeout_teardown_overshoot_is_truthful_not_success(self):
        f.frozen(self.root); f.collected(self.root, "incomplete")
        path = self.first(); r = f.read(self.root, path)
        r.update(status="timeout", end_utc=f.stamp(190.02), monotonic_end=190.02, wall_s=180.02)
        r["cleanup"].update(kill_sent=True, worker_awaited=True, output_drained=True)
        req = r["requests"][0]
        (self.root/req["response_path"]).unlink()
        req.update(response_path=None, http_status=None, ended_utc=None, elapsed_s=None,
                   error={"type": "SupervisoryTimeout", "message": "ambiguous interrupted request; not replayed"}, usage=None)
        r["usage"] = f.usage([None])
        f.write(self.root, path, r)
        self.assertTrue(audit(self.root, "collected")["ok"])
        self.fail(None, "incomplete.*missing")

    def test_visible_markers_and_frozen_rule(self):
        from verify import visible_words
        self.assertEqual(visible_words("# **Ready** | > _now_ [official page](https://example.test/) https://example.test/ `x`"), 5)
        f.frozen(self.root)
        f.edit(self.root, "protocol.json", lambda d: d.update(visible_word_rule="ignore all commentary"))
        f.reseal(self.root)
        self.fail("frozen", "unsupported visible word rule")

    def test_unfetched_frozen_reference_cannot_ground_citation(self):
        f.complete(self.root)
        f.runner_blind_style(self.root); f.grades(self.root)
        path = self.grade_path(); g = f.read(self.root, path)
        row = f.read(self.root, f"blind/cases/{g['blind_id']}/case.json")
        reference = next(s for s in row["sources"] if s["status"] == "frozen_reference")
        g["citations"][0]["evidence"][0]["source_path"] = reference["source_path"]
        f.write(self.root, path, g)
        self.fail("grades", "grounding must use fetched evidence")
        f.grades(self.root)
        # A real frozen page, absent from this candidate's fetched pages.
        other = next(s for s in f.read(self.root, "dataset/sources.json") if s["id"] == "T6-2")
        path = self.grade_path(); g = f.read(self.root, path)
        g["citations"][0].update(url=other["url"])
        g["compliance"]["full_urls"] = False
        for check in g["checks"]: check["citation_status"] = "missing"
        f.write(self.root, path, g)
        self.fail("grades", "never actually fetched")

    def test_fake_supplied_anchor(self):
        f.complete(self.root)
        path = self.grade_path(); g = f.read(self.root, path)
        g["citations"][0]["url"] += "#made-up-anchor"
        f.write(self.root, path, g)
        self.fail("grades", "anchor does not exist")

    def test_native_mirror_is_not_two_canonical_content_pages(self):
        f.frozen(self.root)
        sources = f.read(self.root, "dataset/sources.json")
        mirror = copy.deepcopy(sources[0])
        mirror.update(id="T1-native", url=mirror["url"]+".md", final_url=mirror["url"]+".md")
        sources.append(mirror)
        f.write(self.root, "dataset/sources.json", sources); f.reseal(self.root)
        f.collected(self.root)
        path = self.first(); r = f.read(self.root, path)
        r["fetches"][1].update(requested_url=mirror["url"], final_url=mirror["url"])
        for kind in ("raw", "text", "model_text"):
            body = (self.root/r["fetches"][0][f"{kind}_path"]).read_bytes()
            (self.root/r["fetches"][1][f"{kind}_path"]).write_bytes(body)
            r["fetches"][1][f"{kind}_sha256"] = digest(self.root/r["fetches"][1][f"{kind}_path"])
        r["fetches"][1]["raw_bytes"] = r["fetches"][0]["raw_bytes"]
        r["fetches"][1]["text_bytes"] = r["fetches"][0]["text_bytes"]
        history = f.read(self.root, r["history_path"])
        history[2]["tool_calls"][1]["function"]["arguments"] = json.dumps({"url": mirror["url"]})
        tool = next(m for m in history if m.get("tool_call_id") == "tool2")
        output = json.loads(tool["content"]); output["url"] = mirror["url"]
        output["text"] = (self.root/r["fetches"][0]["text_path"]).read_text(); tool["content"] = json.dumps(output)
        f.write(self.root, r["history_path"], history)
        f.edit(self.root, r["requests"][0]["response_path"], lambda d: d["choices"][0].update(message=history[2]))
        f.edit(self.root, r["requests"][1]["request_path"], lambda d: d.update(messages=history[:-1]))
        f.write(self.root, path, r)
        self.assertTrue(audit(self.root, "collected")["ok"])
        f.blinded(self.root); f.grades(self.root)
        private = f.read(self.root, "private/unblind.json")
        blind = next(b for b, c in private["mapping"].items() if c == r["case_id"])
        name = f"blind/cases/{blind}/case.json"
        row = f.read(self.root, name)
        row["sources"][1]["url"] = mirror["url"]
        source_path = row["sources"][1]["source_path"]
        f.write(self.root, source_path, (self.root/r["fetches"][0]["text_path"]).read_text())
        f.write(self.root, name, row)
        f.edit(self.root, "private/unblind.json", lambda d: d["sealed_hashes"].update({source_path: digest(self.root/source_path)}))
        f.edit(self.root, "private/unblind.json", lambda d: d["sealed_hashes"].update({name: digest(self.root/name)}))
        self.fail("grades", "fabricated mechanical fetched_two_sources")

    def test_seal_order_overrides_and_initial_preserved(self):
        f.complete(self.root)
        f.edit(self.root, "private/unblind.json", lambda d: d.update(unblinded_utc=f.stamp(2999)))
        self.fail("graded", "before unblinding")
        f.grade_seal(self.root)
        initial = self.grade_path(); g = f.read(self.root, initial)
        original = (self.root/initial).read_bytes()
        g["checks"][0].update(status="unverifiable", citation_status="non_entailing", rationale="Scope not established.")
        name = f"adjudication/{g['blind_id']}.json"
        f.write(self.root, name, {"blind_id": g["blind_id"], "initial_grade_path": initial,
                                  "rationale": "Blind independent scope review.", "effective_grade": g})
        f.grade_seal(self.root, {g["blind_id"]: name})
        self.assertTrue(audit(self.root, "graded")["ok"])
        self.assertEqual((self.root/initial).read_bytes(), original)
        f.edit(self.root, initial, lambda d: d.update(notes="modified after seal"))
        self.fail("graded", "changed hash")


class StatisticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        f.complete(cls.root)
        from verify import Auditor
        cls.a = Auditor(cls.root).frozen().collected().blind().grades().graded()
        grades = {cls.a.mapping[b]: g for b, g in cls.a.effective.items()}
        cls.rows = [analysis.judgment(r, grades[r["case_id"]]) for r in cls.a.records]

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_ordinary_median_p90_and_no_subset(self):
        self.assertEqual(analysis.median([1, 2, 3, 4]), 2.5)
        self.assertEqual(analysis.p90(list(range(1, 13))), 11)
        self.assertIsNone(analysis.median([])); self.assertIsNone(analysis.p90([]))
        rows = copy.deepcopy(self.rows[:12])
        for r in rows:
            r["qualified"] = False
        summary = analysis.summarize(rows)
        self.assertIsNone(summary["qualified_latency"]["median_s"])
        self.assertEqual(summary["qualified_latency"]["n"], 0)

    def test_score_qualification_extras_cap_and_flags_not_trusted(self):
        r = self.a.records[0]
        grade = copy.deepcopy(next(iter(self.a.effective.values())))
        grade["qualified"] = True
        grade["checks"][0]["status"] = "contradicted"
        grade["checks"][1]["status"] = "missing"
        grade["unsupported_extras"] = [{}]*8
        row = analysis.judgment(r, grade)
        self.assertEqual(row["factual_raw"], 3)
        self.assertEqual(row["factual_adjusted"], 1)
        self.assertEqual(row["extra_penalty"], 2)
        self.assertFalse(row["qualified"])
        good = copy.deepcopy(next(iter(self.a.effective.values())))
        for key in analysis.COMPLIANCE:
            altered = copy.deepcopy(good); altered["compliance"][key] = False
            self.assertFalse(analysis.judgment(r, altered)["qualified"], key)
        good["uncertainty"]["status"] = "omit"
        self.assertFalse(analysis.judgment(r, good)["qualified"])

    def test_eligibility_per_task_and_contradictions_all_attempts(self):
        rows = copy.deepcopy([r for r in self.rows if r["configuration_id"] == "deepseek-low"])
        self.assertTrue(analysis.summarize(rows)["eligible"])
        rows[0]["qualified"] = False; rows[1]["qualified"] = False
        self.assertTrue(analysis.summarize(rows)["eligible"])
        rows[2]["qualified"] = False
        self.assertFalse(analysis.summarize(rows)["eligible"])
        rows = copy.deepcopy([r for r in self.rows if r["configuration_id"] == "deepseek-low"])
        for r in rows:
            if r["task_id"] == "T1": r["qualified"] = False
        self.assertFalse(analysis.summarize(rows)["eligible"])
        rows = copy.deepcopy([r for r in self.rows if r["configuration_id"] == "deepseek-low"])
        rows[0]["qualified"] = False; rows[0]["checks"]["contradicted"] = 1
        self.assertFalse(analysis.summarize(rows)["eligible"])

    def test_errors_never_enter_success_speed(self):
        r = copy.deepcopy(self.a.records[0]); g = next(iter(self.a.effective.values()))
        r.update(status="access_gate_error", wall_s=.01, operational_complete=False, errors=["denied"])
        row = analysis.judgment(r, g)
        self.assertFalse(row["qualified"])
        rows = [row, copy.deepcopy(self.rows[0])]
        self.assertEqual(analysis.summarize(rows)["qualified_latency"]["median_s"], 20)
        self.assertEqual(analysis.summarize(rows)["failed_latency"]["median_s"], .01)
        r = copy.deepcopy(self.a.records[0]); r["wall_s"] = 180.02
        self.assertFalse(analysis.judgment(r, g)["qualified"])

    def test_quality_first_price_excluded_and_no_eligible(self):
        rows = copy.deepcopy(self.rows)
        summaries = {c: analysis.summarize([r for r in rows if r["configuration_id"] == c]) for c in CONFIGS}
        for c, s in summaries.items():
            s["reported_cost"] = -1e99 if c == "glm-max" else 1e99
        baseline = analysis.recommendation(rows, summaries, [])
        self.assertIsNone(baseline["winner"])
        summaries["deepseek-low"]["qualified"] = 11
        others = {c: s for c, s in summaries.items()}
        for c in others:
            if c != "deepseek-low": others[c]["eligible"] = False
        self.assertEqual(analysis.recommendation(rows, others, [])["winner"], "deepseek-low")
        for s in others.values(): s["eligible"] = False
        rec = analysis.recommendation(rows, others, [])
        self.assertEqual(rec["decision"], "no_decisive_winner")
        self.assertNotIn("ranking", rec)

    def test_pairs_exclusions_coverage_and_speed_margin(self):
        rows = copy.deepcopy(self.rows)
        for r in rows:
            if r["configuration_id"] == "deepseek-low": r["wall_s"] = 16
        p = analysis.pair(rows, "deepseek-low", "glm-low")
        self.assertTrue(p["coverage_sufficient"])
        self.assertEqual(p["jointly_qualified_blocks"], 12)
        s = {c: analysis.summarize([r for r in rows if r["configuration_id"] == c]) for c in CONFIGS}
        self.assertTrue(analysis.practical_speed(s["deepseek-low"], s["glm-low"], p))
        rec = analysis.recommendation(rows, s, [])
        self.assertEqual(rec["winner"], "deepseek-low")
        for r in rows:
            if r["configuration_id"] == "deepseek-low" and r["task_id"] in {"T1", "T2", "T3"}: r["qualified"] = False
        p = analysis.pair(rows, "deepseek-low", "glm-low")
        self.assertEqual(len(p["exclusions"]), 6)
        self.assertIn("left_case_id", p["exclusions"][0])
        self.assertIsNone(p["decision_latency"])
        self.assertFalse(analysis.practical_speed(s["deepseek-low"], s["glm-low"], p))

    def test_bootstrap_whole_task_shared_repetitions_deterministic(self):
        rows = copy.deepcopy(self.rows)
        # Both repetitions and all configurations have the same task score.
        for r in rows: r["factual_adjusted"] = int(r["task_id"][1:])
        pairs = [analysis.pair(rows, "deepseek-low", "glm-low")]
        b = analysis.bootstrap(rows, pairs, 123, 10000)
        self.assertEqual(b["draws"], 10000); self.assertEqual(b["cluster_count"], 6)
        self.assertEqual(b["cells_per_cluster"], 12)
        self.assertTrue(b["shared_draws_all_configurations"])
        self.assertEqual(b["configurations"]["deepseek-low"], b["configurations"]["glm-max"])
        self.assertEqual(b, analysis.bootstrap(rows, pairs, 123, 10000))
        # Independent known whole-task bootstrap interval, not an implementation copy.
        self.assertEqual(b["configurations"]["glm-low"]["quality"]["low"], 13/6)
        self.assertEqual(b["configurations"]["glm-low"]["quality"]["high"], 29/6)
        with self.assertRaisesRegex(AuditError, "whole task clusters"):
            analysis.bootstrap(rows[:12], [], 123, 10)


if __name__ == "__main__":
    unittest.main()
