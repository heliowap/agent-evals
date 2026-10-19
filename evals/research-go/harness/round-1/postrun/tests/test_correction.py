"""Read-only real-evidence regressions; mutations use isolated test-owned copies."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location("postrun_correction", Path(__file__).resolve().parents[1]/"verify.py")
correction = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(correction)
ROOT = correction.ROOT


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2)+"\n", encoding="utf-8")


class CorrectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.freeze, cls.archives = correction.sealed_inputs(ROOT)
        cls.records = [correction.read(ROOT, p) for p in correction.read(ROOT, "execution/index.json")["cases"]]
        cls.proven = correction.linked_texts(ROOT, cls.records, cls.archives)

    def copy_root(self):
        temp = tempfile.TemporaryDirectory(prefix="postrun-audit-", dir="/private/tmp/opencode")
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        names = list(self.freeze["files"]) + ["freeze.json", "private/freeze-receipt.json"]
        for name in names:
            target = root/name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT/name, target)
        shutil.copytree(ROOT/"execution", root/"execution")
        return root

    def assert_generic_failure(self, root):
        module = correction.load_verifier(root)
        with self.assertRaisesRegex(module.AuditError, "persisted credential material"):
            module.audit(root, "collected")

    def test_real_36_hits_are_only_proven_public_docs_and_collected_passes(self):
        paths, hits, hashes = set(), 0, set()
        for path in ROOT.glob("execution/**/*"):
            if path.is_file() and path.suffix in {".json", ".jsonl", ".txt", ".md"}:
                matches = list(re.finditer(correction.CREDENTIAL_PATTERN, path.read_text()))
                if matches:
                    paths.add(str(path.relative_to(ROOT)))
                    hits += len(matches)
                    hashes.update(correction.sha(m[0].encode()) for m in matches)
        self.assertEqual(hits, 36)
        self.assertEqual(len(paths), 12)
        self.assertEqual(paths, set(self.proven))
        self.assertEqual(hashes, {correction.PUBLIC_FIELD_SHA256})
        module = correction.load_verifier()
        self.assertEqual(module.audit(ROOT, "collected")["study_status"], "completed")
        self.assertEqual(set(module.re.exempted), paths)
        provisioning = correction.read(ROOT, "execution/parent-provisioning.json")
        self.assertEqual(provisioning["secret_matches"], 0)

    def test_original_failure_is_reproduced_without_any_original_edits(self):
        module = correction.load_verifier()
        module.re = re  # Undo only the private in-memory proxy, not stdlib state.
        with self.assertRaisesRegex(module.AuditError, "persisted credential material"):
            module.audit(ROOT, "collected")

    def test_exact_pattern_only_and_stdlib_regex_unchanged(self):
        search = re.search
        module = correction.load_verifier()
        self.assertIs(re.search, search)
        self.assertIs(module.re.fullmatch, re.fullmatch)
        text = next(iter(self.archives.values()))["text_path"]
        document = (ROOT/text).read_text()
        # Outside the exact original collected scan frame there is no exception,
        # even with the same pattern and byte-identical known document.
        self.assertIsNotNone(module.re.search(correction.CREDENTIAL_PATTERN, document))
        self.assertEqual(module.re.search(r"Authorization", document).span(), re.search(r"Authorization", document).span())
        self.assertIsNotNone(module.re.search(correction.CREDENTIAL_PATTERN, document, re.MULTILINE))

    def test_unknown_keys_and_synthetic_bearer_sk_patterns_fail(self):
        examples = ['{"Authorization": "SYNTHETIC_NOT_A_CREDENTIAL"}',
                    "Bearer <REDACTED_SECRET>",
                    "sk-SYNTHETIC-NOT-A-REAL-CREDENTIAL"]
        for marker in examples:
            with self.subTest(kind=marker.split()[0]):
                root = self.copy_root()
                (root/"execution/unknown-header.json").write_text(marker)
                self.assert_generic_failure(root)

    def test_unlinked_exact_public_copy_is_not_exempt(self):
        root = self.copy_root()
        source = next(iter(self.archives.values()))["text_path"]
        shutil.copyfile(root/source, root/"execution/unlinked-copy.txt")
        self.assert_generic_failure(root)

    def test_modified_unlinked_public_copy_is_not_exempt(self):
        root = self.copy_root()
        source = next(iter(self.archives.values()))["text_path"]
        (root/"execution/modified-copy.txt").write_text((root/source).read_text()+"\nSYNTHETIC_MODIFICATION\n")
        self.assert_generic_failure(root)

    def test_linked_modified_text_still_fails_original_hash_check(self):
        root = self.copy_root()
        name = next(iter(self.proven))
        (root/name).write_bytes((root/name).read_bytes()+b"\nSYNTHETIC_MODIFICATION\n")
        module = correction.load_verifier(root)
        with self.assertRaisesRegex(module.AuditError, "changed hash"):
            module.audit(root, "collected")

    def test_source_original_and_freeze_tampering_rejected(self):
        source = next(iter(self.archives.values()))["text_path"]
        for name, error in [(source, "changed public archive"), ("verify.py", "changed sealed input"),
                            ("dataset/sources.json", "changed sealed input"), ("freeze.json", "changed original freeze")]:
            with self.subTest(name=name):
                root = self.copy_root()
                (root/name).write_bytes((root/name).read_bytes()+b"\n")
                with self.assertRaisesRegex(correction.CorrectionError, error):
                    correction.load_verifier(root)

    def test_all_matches_must_be_public_not_just_first_match(self):
        source = next(iter(self.archives.values()))["text_path"]
        document = (ROOT/source).read_text()
        self.assertTrue(correction.public_matches(document))
        self.assertFalse(correction.public_matches(document+"\nBearer <REDACTED_SECRET>"))
        self.assertFalse(correction.public_matches(document+'\n{"api_key": "SYNTHETIC_NOT_A_CREDENTIAL"}'))

    def test_other_audit_errors_and_real_cleanup_proof_are_unchanged(self):
        root = self.copy_root()
        index = correction.read(root, "execution/index.json")
        index["attempted_cases"] = 71
        write_json(root/"execution/index.json", index)
        module = correction.load_verifier(root)
        with self.assertRaisesRegex(module.AuditError, "count mismatch"):
            module.audit(root, "collected")
        root = self.copy_root()
        name = "execution/cleanup/credentials.json"
        scan = correction.read(root, name); scan["secret_matches"] = 1
        write_json(root/name, scan)
        module = correction.load_verifier(root)
        with self.assertRaisesRegex(module.AuditError, "credential hygiene proof"):
            module.audit(root, "collected")

    def test_default_still_fails_missing_later_stage_without_writing_audit(self):
        root = self.copy_root()
        module = correction.load_verifier(root)
        with self.assertRaisesRegex(module.AuditError, "missing grades stage artifact"):
            module.audit(root)
        self.assertFalse((root/"audit.json").exists())
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(correction.main(["--root", str(root)]), 1)
        self.assertFalse((root/"audit.json").exists())

    def test_all_original_frozen_hashes_still_match(self):
        for name, expected in self.freeze["files"].items():
            self.assertEqual(correction.sha((ROOT/name).read_bytes()), expected, name)
        self.assertEqual(correction.sha((ROOT/"freeze.json").read_bytes()), correction.FREEZE_SHA256)
        module = correction.load_verifier()
        module.Auditor(ROOT).frozen()  # Integrity validation, not a zero-POST frozen stage claim.


if __name__ == "__main__":
    unittest.main()
