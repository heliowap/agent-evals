import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tasks_python import TASKS


def run_fixture(spec, *, reference, script, changes=None):
    with tempfile.TemporaryDirectory(prefix="authored-python-") as directory:
        root = Path(directory)
        files = dict(spec.files)
        if reference:
            files.update(spec.reference)
        if changes:
            files.update(changes)
        for path, content in files.items():
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
        entry = root / "private_check.py"
        entry.write_text(script)
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        environment.pop("PYTHONPATH", None)
        return subprocess.run([sys.executable, "-B", str(entry)], cwd=root,
                              env=environment, capture_output=True, text=True, timeout=15)


class PythonFixtures(unittest.TestCase):
    def test_original_public_regressions_pass(self):
        for spec in TASKS:
            with self.subTest(task=spec.id):
                result = run_fixture(spec, reference=False, script=spec.files["checks/public.py"])
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_reference_preserves_public_behavior(self):
        for spec in TASKS:
            with self.subTest(task=spec.id):
                result = run_fixture(spec, reference=True, script=spec.files["checks/public.py"])
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_reference_meets_complete_acceptance(self):
        for spec in TASKS:
            with self.subTest(task=spec.id):
                result = run_fixture(spec, reference=True, script=spec.acceptance)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                if spec.structural:
                    result = run_fixture(spec, reference=True, script=spec.structural)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_baseline_does_not_satisfy_new_request(self):
        for spec in TASKS:
            with self.subTest(task=spec.id):
                result = run_fixture(spec, reference=False, script=spec.structural or spec.acceptance)
                self.assertNotEqual(result.returncode, 0, "baseline already satisfies requested change")

    def test_behavior_preserving_refactor_baseline_acceptance(self):
        spec = next(item for item in TASKS if item.id == "py-exporter-consolidation")
        result = run_fixture(spec, reference=False, script=spec.acceptance)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_acceptance_rejects_plausible_incomplete_changes(self):
        mutations = [
            ("py-atomic-import", "src/service.py", "email in seen", "False", "duplicate normalized contact"),
            ("py-atomic-import", "src/service.py", "put_contact(connection, email, name)\n            if exists:", "put_contact(connection, email, name)\n            connection.commit()\n            if exists:", "partial batch commit"),
            ("py-transfer-commit", "src/service.py", "with connection:\n        move(connection, source, target, amount)\n    publisher.publish", "publisher.publish({\"source\": source, \"target\": target, \"amount\": amount})\n    with connection:\n        move(connection, source, target, amount)\n    publisher.publish", "publish before commit"),
            ("py-document-scope", "src/repository.py", "AND tenant=? AND owner=? AND deleted_at IS NULL", "AND ? IS NOT NULL AND owner=? AND deleted_at IS NULL", "tenant bypass"),
            ("py-document-scope", "src/repository.py", "AND deleted_at IS NULL", "", "deleted record disclosure"),
            ("py-money-contract", "src/money.py", "if cents != number:", "if False:", "fractional cent rounding"),
            ("py-money-contract", "src/money.py", "type(value) is not int", "not isinstance(value, int)", "boolean amount"),
            ("py-generator-cleanup", "src/service.py", "resource.close()", "pass", "skipped resource cleanup"),
            ("py-generator-cleanup", "src/consumer.py", "stream.close()", "pass", "early consumer leak"),
            ("py-stock-reservations", "src/service.py", "if previous:", "if False:", "missing persistent idempotency"),
            ("py-expiring-shares", "src/service.py", "s.expires_at>?", "s.expires_at>=?", "expired-at-boundary access"),
            ("py-expiring-shares", "src/service.py", "AND d.tenant=s.tenant", "", "share crosses tenant"),
            ("py-layered-queue-config", "src/config.py", "result[field] = DEFAULTS[field]", "continue", "null inherits instead of reset"),
            ("py-incremental-lines", "src/reader.py", "pending += decoder.decode(chunk)", "pending += chunk.decode('utf-8')", "chunk-local UTF-8 decode"),
            ("py-incremental-lines", "src/reader.py", "source.close()", "pass", "line reader resource leak"),
        ]
        by_id = {spec.id: spec for spec in TASKS}
        for identifier, path, before, after, defect in mutations:
            with self.subTest(defect=defect):
                spec = by_id[identifier]
                original = spec.reference[path]
                self.assertIn(before, original, "mutation no longer applies")
                changed = original.replace(before, after)
                compile(changed, path, "exec")
                result = run_fixture(spec, reference=True, script=spec.acceptance,
                                     changes={path: changed})
                self.assertNotEqual(result.returncode, 0, "acceptance missed " + defect)

    def test_shared_exporter_requirement_detects_unmigrated_wrapper(self):
        spec = next(item for item in TASKS if item.id == "py-exporter-consolidation")
        result = run_fixture(spec, reference=True, script=spec.structural,
                             changes={"src/csv_exporter.py": spec.files["src/csv_exporter.py"]})
        self.assertNotEqual(result.returncode, 0, "old wrapper still accepted")


if __name__ == "__main__":
    unittest.main()
