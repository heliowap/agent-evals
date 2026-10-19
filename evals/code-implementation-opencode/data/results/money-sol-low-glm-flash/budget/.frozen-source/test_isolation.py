from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

import isolation
import bench


class IsolationProofTests(unittest.TestCase):
    def container(self, denied_private_path=False, readable_private_path=False, tool_failure=None):
        class Container:
            def __init__(self, work, image, docker):
                self.work = work
                self.id = "a" * 64

            def __enter__(self):
                return self

            def __exit__(self, *_):
                pass

            def inspect(self):
                return {"network": "none"}

            def stop(self):
                pass

            def exec_argv(self, argv):
                result = {"passed": True, "exit_code": 0, "stdout": "", "stderr": ""}
                if argv[:3] == ["python3", "-B", "-c"]:
                    work = self.work

                    class ContainerPath:
                        def __init__(self, name):
                            self.name = name

                        def __truediv__(self, name):
                            return ContainerPath(self.name + "/" + name)

                        def exists(self):
                            if self.name.startswith("/root/") and denied_private_path:
                                raise PermissionError(13, "Permission denied", self.name)
                            return False

                        def read_bytes(self):
                            if denied_private_path:
                                raise PermissionError(13, "Permission denied", self.name)
                            if readable_private_path:
                                return b"fixture"
                            raise FileNotFoundError(self.name)

                        def read_text(self):
                            if self.name.endswith("/escape"):
                                raise FileNotFoundError(self.name)
                            return (work / Path(self.name).name).read_text()

                        def write_text(self, value):
                            if self.name.startswith("/etc/"):
                                raise PermissionError(self.name)
                            return (work / Path(self.name).name).write_text(value)

                    class Socket:
                        def settimeout(self, value):
                            pass

                        def connect(self, address):
                            raise OSError("Network is unreachable")

                        def close(self):
                            pass

                    modules = {"pathlib": types.SimpleNamespace(Path=ContainerPath),
                               "socket": types.SimpleNamespace(socket=Socket),
                               "os": types.SimpleNamespace(environ={})}
                    stdout, stderr = io.StringIO(), io.StringIO()
                    with patch.dict(sys.modules, modules), redirect_stdout(stdout), redirect_stderr(stderr):
                        try:
                            exec(argv[-1], {})
                        except Exception as error:
                            result.update(passed=False, exit_code=1)
                            print(f"{type(error).__name__}: {error}", file=sys.stderr)
                    result.update(stdout=stdout.getvalue(), stderr=stderr.getvalue())
                elif argv[-1] == "--version":
                    versions = {"node": "v24.9.0\n", "tsc": "Version 5.9.3\n", "python3": "Python 3.11.2\n"}
                    result["stdout"] = versions[argv[0]]
                    if argv[0] == tool_failure:
                        result.update(passed=False, exit_code=127, stdout="", stderr="tool unavailable")
                return result

        return Container

    def run_proof(self, **options):
        with patch.object(isolation, "CodeContainer", self.container(**options)), \
             patch.object(isolation, "docker_command", return_value=json.dumps([{"State": {"Running": False}}])):
            return isolation.prove_isolation("sha256:test")

    def test_permission_denied_on_private_path_does_not_fail_namespace(self):
        self.assertTrue(self.run_proof(denied_private_path=True)["passed"])

    def test_missing_private_path_passes_namespace(self):
        self.assertTrue(self.run_proof()["passed"])

    def test_readable_private_file_fails_with_diagnostic(self):
        with self.assertRaises(isolation.IsolationProofError) as raised:
            self.run_proof(readable_private_path=True)
        self.assertIn("Operator credential file is readable", str(raised.exception))
        self.assertFalse(raised.exception.report["namespace"]["passed"])
        self.assertIn("AssertionError", raised.exception.report["namespace"]["stderr"])

    def test_missing_tool_records_exit_code_and_stderr(self):
        with self.assertRaises(isolation.IsolationProofError) as raised:
            self.run_proof(tool_failure="node")
        self.assertIn("node (exit 127): tool unavailable", str(raised.exception))
        self.assertEqual(raised.exception.report["versions"]["node"]["exit_code"], 127)

    def test_preflight_preserves_failed_proof_and_starts_no_models(self):
        report = {"passed": False, "namespace": {"passed": False, "exit_code": 1, "stderr": "proof failed"}}
        error = isolation.IsolationProofError("Namespace proof failed", report)
        args = types.SimpleNamespace(docker="docker", image="image", build_image=False)
        with tempfile.TemporaryDirectory() as folder, \
             patch.object(bench, "validate", return_value={"status": "passed"}), \
             patch.object(isolation, "engine_endpoint", return_value="unix:///fixture.sock"), \
             patch.object(isolation, "docker_command", return_value="{}"), \
             patch.object(isolation, "image_info", return_value={"id": "sha256:test"}), \
             patch.object(isolation, "prove_isolation", side_effect=error):
            result = bench.preflight(Path(folder), args, (), ())
            saved = json.loads((Path(folder) / "preflight.json").read_text())
        self.assertEqual(saved, result)
        self.assertEqual(saved["isolation"], report)
        self.assertEqual(saved["status"], "blocked")
        self.assertEqual(saved["model_calls"], 0)
        self.assertFalse(saved["namespace_validated"])


if __name__ == "__main__":
    unittest.main()
