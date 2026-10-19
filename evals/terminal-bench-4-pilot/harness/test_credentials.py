import json
import subprocess
import unittest
from unittest.mock import patch

from run_pilot import active_go_key


class CredentialsTest(unittest.TestCase):
    def test_reads_only_active_go_account_through_api(self):
        entries = [
            {"integrationID": "opencode-go", "active": False, "value": {"type": "key", "key": "old-fixture"}},
            {"integrationID": "opencode-go", "active": True, "value": {"type": "key", "key": "new-fixture"}},
            {"integrationID": "openrouter", "active": True, "value": {"type": "key", "key": "other-fixture"}},
        ]
        response = subprocess.CompletedProcess([], 0, stdout=json.dumps({"data": entries}))
        with patch("run_pilot.subprocess.run", return_value=response) as call:
            self.assertEqual(active_go_key(), "new-fixture")
        self.assertEqual(call.call_args.args[0], ["opencode", "api", "get", "/api/credential"])

    def test_fails_without_active_go_account(self):
        response = subprocess.CompletedProcess([], 0, stdout='{"data": []}')
        with patch("run_pilot.subprocess.run", return_value=response), self.assertRaisesRegex(RuntimeError, "one active"):
            active_go_key()

    def test_does_not_leak_api_output_on_failure(self):
        response = subprocess.CompletedProcess([], 1, stdout="secret-fixture", stderr="secret-fixture")
        with patch("run_pilot.subprocess.run", return_value=response), self.assertRaisesRegex(RuntimeError, "Could not read") as error:
            active_go_key()
        self.assertNotIn("secret-fixture", str(error.exception))


if __name__ == "__main__":
    unittest.main()
