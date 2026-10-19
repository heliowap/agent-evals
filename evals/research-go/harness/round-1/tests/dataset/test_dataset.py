"""Offline public-command integration tests using copies of the saved archive."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
TESTS = Path(__file__).resolve().parent


class DatasetCommandTests(unittest.TestCase):
    def setUp(self):
        # All generated fixtures stay within P1's owned tests/dataset directory.
        self.temp = tempfile.TemporaryDirectory(prefix="fixture-", dir=TESTS)
        self.root = Path(self.temp.name)
        shutil.copyfile(ROOT / "dataset.py", self.root / "dataset.py")
        shutil.copytree(ROOT / "dataset", self.root / "dataset")
        state = json.loads((self.root / "dataset/archive-state.json").read_text(encoding="utf-8"))
        if state["shared_extraction_finalized"]:
            shutil.copyfile(ROOT / "webfetch.py", self.root / "webfetch.py")
        (self.root / "research").mkdir()
        shutil.copyfile(ROOT / "research/tasks.md", self.root / "research/tasks.md")

    def tearDown(self):
        self.temp.cleanup()

    def command(self, *args):
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        return subprocess.run([sys.executable, str(self.root / "dataset.py"), *args],
                              cwd=self.root, env=env, text=True, capture_output=True, timeout=30)

    def read_json(self, name):
        return json.loads((self.root / "dataset" / name).read_text(encoding="utf-8"))

    def write_json(self, name, data):
        (self.root / "dataset" / name).write_text(json.dumps(data), encoding="utf-8")

    def test_saved_archive_passes_and_distinguishes_pending_finalization(self):
        result = self.command("verify")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("53 quotes", result.stdout)
        report = self.read_json("verification.json")
        self.assertTrue(report["structurally_verified"])
        self.assertEqual(len(report["discovery_links"]), 11)
        self.assertIn("required", report["compose_required_context"]["paragraph"])
        self.assertIn("2.20.0", report["compose_required_context"]["paragraph"])
        strict = self.command("verify", "--require-finalized")
        if report["shared_extraction_finalized"]:
            self.assertEqual(strict.returncode, 0, strict.stdout + strict.stderr)
            self.assertIn("PASS: shared webfetch", result.stdout)
        else:
            self.assertIn("PENDING before freeze/inference", result.stdout)
            self.assertNotEqual(strict.returncode, 0)
            self.assertIn("finalization is pending", strict.stdout)

    def test_prompt_and_gold_mutations_are_detected(self):
        tasks = self.read_json("tasks.json")
        tasks[1]["prompt"] = tasks[1]["prompt"].replace("v24.21.0", "v24.0.0")
        tasks[0]["checks"] = ["leaked gold"]
        self.write_json("tasks.json", tasks)
        gold = self.read_json("gold.json")
        gold["tasks"]["T2"]["uncertainty"]["source_evidence"][0]["quote"] = "Workers always inherit."
        self.write_json("gold.json", gold)
        result = self.command("verify")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("tasks differ from research", result.stdout)
        self.assertIn("gold differs from research", result.stdout)
        self.assertIn("gold leaked", result.stdout)
        self.assertIn("unmatched quote", result.stdout)

    def test_body_corruption_is_detected_even_when_extract_is_unchanged(self):
        sources = self.read_json("sources.json")
        raw_path = self.root / sources[0]["raw_path"]
        raw_path.write_bytes(raw_path.read_bytes() + b"<!-- modified body -->")
        result = self.command("verify")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("raw size/hash mismatch", result.stdout)

    def test_missing_anchor_and_discovery_link_are_detected(self):
        sources = self.read_json("sources.json")
        for row in sources:
            if row["id"] == "GH-I":
                row["links"] = []
            if row["id"] == "GH-V":
                row["anchors"] = []
        self.write_json("sources.json", sources)
        result = self.command("verify")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing HTML anchor", result.stdout)
        self.assertIn("actual discovery link missing", result.stdout)

    def test_failed_http_row_cannot_masquerade_as_archived_page(self):
        sources = self.read_json("sources.json")
        sources[0].update(status=404, error="HTTP Error 404: Not Found", raw_path=None, text_path=None)
        self.write_json("sources.json", sources)
        result = self.command("verify")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("archive fetch failed", result.stdout)

    def test_finalize_requires_shared_contract_and_does_not_fetch(self):
        (self.root / "webfetch.py").unlink(missing_ok=True)
        result = self.command("finalize")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Shared extraction unavailable", result.stderr)

    def test_shared_extraction_contract_is_applied_and_reproducible(self):
        # A test-owned implementation exposes the real public contract. It
        # reproduces the previously saved generic whole bodies rather than
        # copying production extraction logic. No HTTP or candidate calls.
        sources = self.read_json("sources.json")
        fixtures = {row["raw_sha256"]: "Whole-page fixture extraction\n" + (self.root / row["text_path"]).read_text(encoding="utf-8") for row in sources}
        module = "import hashlib, json, re, html\n"
        module += "BODIES = json.loads(" + repr(json.dumps(fixtures)) + ")\n"
        module += "def extract_document(raw, content_type, url):\n    return BODIES[hashlib.sha256(raw).hexdigest()]\n"
        # Match the retained runner's whitespace-only normalization. Evidence
        # matching, not this interface, must strip presentation markup.
        module += "def normalize_text(text):\n    return re.sub(r'\\s+', ' ', html.unescape(text)).strip()\n"
        (self.root / "webfetch.py").write_text(module, encoding="utf-8")
        result = self.command("finalize")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS: shared webfetch", result.stdout)
        self.assertTrue(self.read_json("archive-state.json")["shared_extraction_finalized"])
        self.assertTrue(all(row["extraction"] == "webfetch.extract_document" for row in self.read_json("sources.json")))
        self.assertTrue((self.root / sources[0]["text_path"]).read_text(encoding="utf-8").startswith("Whole-page fixture extraction\n"))
        self.assertEqual(self.command("verify", "--require-finalized").returncode, 0)
        self.assertFalse((self.root / "__pycache__").exists())
        with (self.root / "webfetch.py").open("a", encoding="utf-8") as file:
            file.write("\n# changed contract implementation\n")
        changed = self.command("verify", "--require-finalized")
        self.assertNotEqual(changed.returncode, 0)
        self.assertIn("Shared extractor changed", changed.stdout)

    def test_link_wrapped_prose_code_and_emphasis_preserve_content(self):
        examples = [
            ("Use the [D1 Sessions API](https://developers.cloudflare.com/d1/worker-api/d1-database/#withsession).",
             "Use the D1 Sessions API."),
            ('with[Session](https://developers.cloudflare.com/d1/worker-api/d1-database/#withsession)() is [`withSession("first-unconstrained")`](https://developers.cloudflare.com/d1/worker-api/d1-database/#withsession)',
             'withSession() is withSession("first-unconstrained")'),
            ("After passing a wildcard character (`*`), `/srv/jobs/*.js` and `/srv/jobs/**` remain literal. Plain /srv/jobs/*.js also remains literal.",
             "After passing a wildcard character (*), /srv/jobs/*.js and /srv/jobs/** remain literal. Plain /srv/jobs/*.js also remains literal."),
            ("**not** *denied* _only_ __trusted__ `**literal**` `node:fs` `==`",
             "not denied only trusted **literal** node:fs =="),
            ("Introduced in Docker Compose version [**2.20.0**](https://github.com/docker/compose/releases/tag/v2.20.0).",
             "Introduced in Docker Compose version 2.20.0."),
            ("See [Table 13.1](https://www.postgresql.org/docs/18/example(foo)). The worker’s “restrictions” remain.",
             'See Table 13.1. The worker\'s "restrictions" remain.'),
        ]
        program = "import dataset, webfetch\n"
        for original, expected in examples:
            program += f"assert dataset.quote_normalize({original!r}, webfetch.normalize_text) == {expected!r}\n"
        result = subprocess.run([sys.executable, "-c", program], cwd=self.root,
                                env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
                                text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_verification_retains_shared_extraction_and_hash_text(self):
        # Actual retained runner extraction and whitespace hashes stay intact;
        # presentation-only evidence normalization is not a body transform.
        sources = self.read_json("sources.json")
        before = {row["text_path"]: (self.root / row["text_path"]).read_bytes() for row in sources}
        manifest = (self.root / "dataset/sources.json").read_bytes()
        extractor = (self.root / "webfetch.py").read_bytes()
        result = self.command("verify", "--require-finalized")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.root / "dataset/sources.json").read_bytes(), manifest)
        self.assertEqual((self.root / "webfetch.py").read_bytes(), extractor)
        for path, body in before.items():
            self.assertEqual((self.root / path).read_bytes(), body)


if __name__ == "__main__":
    unittest.main()
