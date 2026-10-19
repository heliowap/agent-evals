"""Offline verification entry point; records actual isolation only on success."""

import hashlib
import json
from pathlib import Path
import sys
import unittest

from . import _HERE, _profile, _runtime, audit_isolation, tools


def main():
    root = Path(__file__).resolve().parents[3]
    suite = unittest.TestLoader().discover(str(root / "tests" / "codetools"), pattern="test_*.py")
    outcome = unittest.TextTestRunner(verbosity=2).run(suite)
    if not outcome.wasSuccessful():
        return 1
    audit = audit_isolation()
    if audit["status"] != "ok":
        print(json.dumps(audit, indent=2))
        return 1
    profile = _profile("SNAPSHOT_ROOT")
    interpreter, stdlib, libraries = _runtime()
    record = {
        "schema_version": 1,
        "verify_command": "python3 -B -m harness.tools.code.verify",
        "tests_run": outcome.testsRun,
        "actual_isolation_proof": audit["metadata"],
        "profile_template": profile.replace(str(_HERE), "PACKAGE_CODE_DIRECTORY"),
        "profile_template_sha256": hashlib.sha256(profile.encode()).hexdigest(),
        "runtime_read_exceptions": {"interpreter": str(interpreter), "stdlib": str(stdlib),
                                    "framework_libraries": list(map(str, libraries)),
                                    "os_libraries": ["/System/Library", "/usr/lib"],
                                    "other": ["fixed worker script", "/ (startup directory vnode)", "/dev/null", "/dev/urandom"],
                                    "metadata": "filesystem metadata for interpreter startup; contents remain restricted",
                                    "excluded": ["site-packages"]},
        "socket_caveat": "macOS allows unconnected socket allocation; actual network connect is denied with EPERM/EACCES. No network descriptors are inherited.",
        "tool_schemas": tools(),
        "semantics_document": "README.md",
        "owned_source_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                                for path in sorted(_HERE.glob("*.py"))},
        "corpus_mutation": "none; fixture artifacts only in approved temporary directory",
        "candidate_calls": 0,
    }
    (_HERE / "isolation-proof.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"PASS: {outcome.testsRun} tests; actual OS denial probes passed; isolation-proof.json recorded.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
