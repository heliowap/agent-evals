import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

from tasks_typescript import TASKS


NODE = shutil.which("node")
TSC = Path.home() / ".bun/install/cache/typescript@5.9.3@@@1/bin/tsc"


def materialize(task, root, reference=False, overlay=None):
    files = dict(task.files)
    if reference:
        files.update(task.reference)
    if overlay:
        files.update(overlay)
    for name, content in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)


def command(root, arguments):
    return subprocess.run(arguments, cwd=root, capture_output=True, text=True, timeout=30)


def private_check(root, script, name):
    path = root / name
    path.write_text(script)
    return command(root, [NODE, str(path)])


class TypeScriptTaskTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if NODE is None or not TSC.is_file():
            raise unittest.SkipTest("Offline Node and TypeScript 5.9.3 are required")

    def compile(self, root):
        compiled = command(root, [NODE, str(TSC), "-p", "tsconfig.json"])
        self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)

    def test_catalog_contract_and_private_separation(self):
        self.assertEqual(len(TASKS), 10)
        self.assertEqual(len({task.id for task in TASKS}), 10)
        self.assertEqual(sum(task.phase == "screening" for task in TASKS), 6)
        self.assertEqual(sum(task.phase == "confirmation" for task in TASKS), 4)
        for task in TASKS:
            with self.subTest(task=task.id):
                self.assertEqual(task.language, "typescript")
                self.assertTrue(task.id.startswith("ts-"))
                self.assertEqual(task.allowed, ("src/", "checks/"))
                self.assertIsNone(re.search(r"\b(eval|benchmark|model|judge|hidden|reference|comparison)\b", task.request, re.I))
                self.assertIn("checks/public.cjs", task.files)
                self.assertNotIn("acceptance.cjs", task.files)
                self.assertNotIn("structural.cjs", task.files)
                self.assertNotIn(task.acceptance, task.files.values())
                config = json.loads(task.files["tsconfig.json"])
                self.assertTrue(config["compilerOptions"]["strict"])
                self.assertEqual(config["compilerOptions"]["target"], "ES2022")
                self.assertEqual(config["compilerOptions"]["module"], "CommonJS")
                self.assertEqual(config["compilerOptions"]["outDir"], ".build")
                self.assertGreaterEqual(sum(name.startswith("src/") for name in task.files), 3)
                for name in task.reference:
                    self.assertTrue(name.startswith("src/"))

    def test_every_baseline_public_green_and_new_requirement_red(self):
        for task in TASKS:
            with self.subTest(task=task.id), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                materialize(task, root)
                self.compile(root)
                public = command(root, [NODE, "checks/public.cjs"])
                self.assertEqual(public.returncode, 0, public.stdout + public.stderr)
                accepted = private_check(root, task.acceptance, "acceptance.cjs")
                structural = private_check(root, task.structural, "structural.cjs") if task.structural else None
                self.assertTrue(accepted.returncode != 0 or (structural is not None and structural.returncode != 0),
                                "baseline unexpectedly satisfies the complete request")
                if task.family == "refactor":
                    self.assertEqual(accepted.returncode, 0, accepted.stdout + accepted.stderr)
                    self.assertNotEqual(structural.returncode, 0)

    def test_every_reference_passes_public_acceptance_and_structure(self):
        for task in TASKS:
            with self.subTest(task=task.id), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                materialize(task, root, reference=True)
                self.compile(root)
                public = command(root, [NODE, "checks/public.cjs"])
                self.assertEqual(public.returncode, 0, public.stdout + public.stderr)
                accepted = private_check(root, task.acceptance, "acceptance.cjs")
                self.assertEqual(accepted.returncode, 0, accepted.stdout + accepted.stderr)
                if task.structural:
                    structural = private_check(root, task.structural, "structural.cjs")
                    self.assertEqual(structural.returncode, 0, structural.stdout + structural.stderr)

    def test_partial_fixes_fail_behavior_or_explicit_structure(self):
        mutations = {
            "ts-cursor-orders": ("src/handler.ts", "row.createdAt > date || (row.createdAt === date && row.id > id)", "row.createdAt > date"),
            "ts-idempotent-payment": ("src/ledger.ts", "if (prior) {", "if (prior && prior.cents === -1) {"),
            "ts-archive-document": ("src/service.ts", "document.tenant !== actor.tenant || ", ""),
            "ts-profile-patch": ("src/parser.ts", " || values.includes(trimmed)", ""),
            "ts-event-stream": ("src/service.ts", "await lease.close();", "void lease;"),
            "ts-money-consolidation": ("src/invoice.ts", "formatAmount(cents)", "String(cents)"),
            "ts-atomic-reservation": ("src/service.ts", "(totals.get(line.sku) ?? 0) + line.quantity", "line.quantity"),
            "ts-singleflight-cache": ("src/service.ts", "expires: this.clock() + this.ttl", "expires: this.ttl"),
            "ts-batch-job-cancel": ("src/service.ts", "if (jobs.some(job => job.state === 'running' || job.state === 'completed'))", "if (false)"),
            "ts-versioned-mass": ("src/mass.ts", "grams = input.quantity * (input.unit === 'kg' ? 1000 : 1);", "grams = Math.round(input.quantity * (input.unit === 'kg' ? 1000 : 1));"),
        }
        for task in TASKS:
            with self.subTest(task=task.id), tempfile.TemporaryDirectory() as directory:
                name, old, new = mutations[task.id]
                original = task.reference[name]
                self.assertIn(old, original)
                root = Path(directory)
                materialize(task, root, reference=True, overlay={name: original.replace(old, new)})
                self.compile(root)
                accepted = private_check(root, task.acceptance, "acceptance.cjs")
                structural = private_check(root, task.structural, "structural.cjs") if task.structural else None
                self.assertTrue(accepted.returncode != 0 or (structural is not None and structural.returncode != 0),
                                "partial fix passed despite dropping a required behavior")


if __name__ == "__main__":
    unittest.main()
