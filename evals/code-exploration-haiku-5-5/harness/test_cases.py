import copy
import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

import cases


ANSWERS = {
    "route": {"chain": ["service.handlers.create_order", "service.orders.submit_order", "service.repository.OrderRepository.insert_order", "service.client.DatabaseClient.execute"], "registration": "service/routes.py"},
    "config": {"endpoint": "", "timeout": 7, "precedence": ["environment", "tenant", "file", "default"]},
    "retry": {"owner": "service.client.DatabaseClient.execute", "max_attempts": 3, "retryable": ["ConnectionError", "TimeoutError"], "value_error_retried": False, "event_inside_retry": False},
    "permission": {"ids": ["o1", "o3"], "authorization": "service.permissions.can_read", "deleted_filter": "service.orders.visible_orders"},
    "feature": {"renderer": "service.renderers.json_rows", "flag": "stream_exports", "effective_value": False, "winning_source": "tenant", "environment_affects_route": False},
    "absence": {"registered": False, "status": 404, "body": "unknown route", "registration": "service/routes.py"},
}


def reference(case):
    evidence = []
    for path, symbol, quote in cases.CASES[case]["anchors"]:
        evidence.append({"path": path, "symbol": symbol, "line": cases.FILES[path].splitlines().index(quote) + 1, "quote": quote})
    return {"answer": copy.deepcopy(ANSWERS[case]), "evidence": evidence}


class GradingCases(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.work = Path(self.directory.name)
        cases.build(self.work)

    def test_reference_answers_pass_for_all_cases(self):
        for case in ANSWERS:
            with self.subTest(case=case):
                result = cases.grade(case, self.work, json.dumps(reference(case)))
                self.assertEqual(result, {"passed": True, "answer_correct": True, "evidence_correct": True, "checks": {"json": True, "shape": True, "workspace_unchanged": True, "evidence_valid": True, "anchors_present": True}})

    def test_reversed_route_chain_is_incorrect(self):
        response = reference("route")
        response["answer"]["chain"].reverse()
        result = cases.grade("route", self.work, response)
        self.assertEqual((result["passed"], result["answer_correct"], result["evidence_correct"]), (False, False, True))

    def test_unrelated_real_citation_cannot_replace_anchor(self):
        response = reference("config")
        response["evidence"][0] = {"path": "service/health.py", "symbol": "health", "line": 2, "quote": '    return {"status": 200, "body": "ready"}'}
        result = cases.grade("config", self.work, response)
        self.assertEqual((result["passed"], result["checks"]["evidence_valid"], result["checks"]["anchors_present"]), (False, True, False))

    def test_definition_only_citations_are_insufficient(self):
        response = reference("retry")
        response["evidence"] = [{"path": "service/client.py", "symbol": "DatabaseClient.execute", "line": 5, "quote": "    def execute(self, statement, params):"}]
        result = cases.grade("retry", self.work, response)
        self.assertEqual((result["passed"], result["checks"]["evidence_valid"], result["checks"]["anchors_present"]), (False, True, False))

    def test_symbol_must_enclose_the_quoted_line(self):
        response = reference("route")
        response["evidence"][1]["symbol"] = "list_orders"
        result = cases.grade("route", self.work, response)
        self.assertEqual((result["passed"], result["checks"]["evidence_valid"]), (False, False))

    def test_fabricated_quote_or_file_is_rejected_even_as_extra_evidence(self):
        for extra in [
            {"path": "service/health.py", "symbol": "health", "line": 2, "quote": "    return None"},
            {"path": "service/missing.py", "symbol": "health", "line": 1, "quote": "def health():"},
            {"path": "../outside.py", "symbol": "health", "line": 1, "quote": "def health():"},
        ]:
            with self.subTest(extra=extra):
                response = reference("absence")
                response["evidence"].append(extra)
                result = cases.grade("absence", self.work, response)
                self.assertEqual((result["passed"], result["evidence_correct"]), (False, False))

    def test_wrong_case_answer_is_rejected(self):
        result = cases.grade("feature", self.work, reference("permission"))
        self.assertEqual((result["passed"], result["answer_correct"], result["evidence_correct"]), (False, False, False))

    def test_empty_search_response_does_not_prove_absence(self):
        response = reference("absence")
        response["evidence"] = []
        result = cases.grade("absence", self.work, response)
        self.assertEqual((result["passed"], result["evidence_correct"]), (False, False))

    def test_missing_route_table_citation_does_not_prove_absence(self):
        response = reference("absence")
        response["evidence"] = response["evidence"][1:]
        result = cases.grade("absence", self.work, response)
        self.assertEqual((result["passed"], result["checks"]["anchors_present"]), (False, False))

    def test_mutated_source_is_rejected(self):
        response = reference("config")
        path = self.work / "service/config.py"
        path.write_text(path.read_text().replace('"timeout": 30', '"timeout": 99'))
        result = cases.grade("config", self.work, response)
        self.assertEqual((result["passed"], result["answer_correct"], result["evidence_correct"], result["checks"]["workspace_unchanged"]), (False, True, True, False))

    def test_symlink_source_is_rejected(self):
        path = self.work / "service/config.py"
        content = path.read_text()
        path.unlink()
        outside = self.work / "copy.py"
        outside.write_text(content)
        path.symlink_to(outside)
        result = cases.grade("config", self.work, reference("config"))
        self.assertEqual((result["passed"], result["checks"]["workspace_unchanged"], result["evidence_correct"]), (False, False, False))

    def test_json_field_types_are_strict(self):
        response = reference("retry")
        response["answer"]["max_attempts"] = 3.0
        result = cases.grade("retry", self.work, response)
        self.assertEqual((result["passed"], result["answer_correct"]), (False, False))

    def test_evidence_limit_is_enforced(self):
        response = reference("route")
        response["evidence"] *= 2
        result = cases.grade("route", self.work, response)
        self.assertEqual((result["passed"], result["checks"]["evidence_valid"]), (False, False))

    def test_malformed_output_is_rejected_without_crashing(self):
        for response in ["not json", "[]", "null", {}, {"answer": {}, "evidence": 1}, {"answer": {}, "evidence": [{"path": []}]}]:
            with self.subTest(response=response):
                self.assertEqual(cases.grade("route", self.work, response)["passed"], False)


class FixtureBehavior(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.work = Path(self.directory.name)
        cases.build(self.work)
        self.previous_bytecode = sys.dont_write_bytecode
        sys.dont_write_bytecode = True
        sys.path.insert(0, str(self.work))
        self.addCleanup(self.restore_imports)
        self.routes = importlib.import_module("service.routes")

    def restore_imports(self):
        sys.path.remove(str(self.work))
        for name in list(sys.modules):
            if name == "service" or name.startswith("service."):
                del sys.modules[name]
        sys.dont_write_bytecode = self.previous_bytecode

    def test_active_route_calls_database_and_then_event(self):
        client = importlib.import_module("service.client").DatabaseClient
        repository = importlib.import_module("service.repository").OrderRepository
        events = []

        class Transport:
            def send(self, statement, params):
                events.append(("database", params["request_id"]))
                return {"id": params["id"]}

        class Bus:
            def publish(self, topic, payload):
                events.append((topic, payload["id"]))

        context = {"repository": repository(client(Transport())), "events": Bus(), "request_id": "r1"}
        result = self.routes.dispatch("POST", "/orders", {"body": {"id": "o1"}}, context)
        self.assertEqual(result, {"status": 201, "body": {"id": "o1"}})
        self.assertEqual(events, [("database", "r1"), ("order.created", "o1")])

    def test_config_preserves_empty_environment_value_and_falls_back(self):
        load = importlib.import_module("service.config").load_config
        self.assertEqual(load({"APP_ENDPOINT": ""}, {"endpoint": "https://tenant.local", "timeout": 7}, {"endpoint": "https://file.local", "timeout": 15}), {"endpoint": "", "timeout": 7})
        self.assertEqual(load({}, {}, {}), {"endpoint": "https://db.local", "timeout": 30})
        self.assertEqual(load({}, {}, {"timeout": 15}), {"endpoint": "https://db.local", "timeout": 15})

    def test_transport_retries_transient_errors_and_preserves_params(self):
        client = importlib.import_module("service.client").DatabaseClient

        class Transport:
            def __init__(self):
                self.calls = []

            def send(self, statement, params):
                self.calls.append((statement, params.copy()))
                if len(self.calls) == 1:
                    raise ConnectionError("offline")
                if len(self.calls) == 2:
                    raise TimeoutError("late")
                return "saved"

        transport = Transport()
        self.assertEqual(client(transport).execute("insert", {"request_id": "r1"}), "saved")
        self.assertEqual(transport.calls, [("insert", {"request_id": "r1"}), ("insert", {"request_id": "r1"}), ("insert", {"request_id": "r1"})])

    def test_value_error_is_not_retried_and_timeout_stops_at_three(self):
        client = importlib.import_module("service.client").DatabaseClient

        class Transport:
            def __init__(self, exception):
                self.calls = 0
                self.exception = exception

            def send(self, statement, params):
                self.calls += 1
                raise self.exception("failed")

        for exception, attempts in [(ValueError, 1), (TimeoutError, 3)]:
            with self.subTest(exception=exception):
                transport = Transport(exception)
                with self.assertRaises(exception):
                    client(transport).execute("insert", {})
                self.assertEqual(transport.calls, attempts)

    def test_event_failure_does_not_retry_database(self):
        client = importlib.import_module("service.client").DatabaseClient
        repository = importlib.import_module("service.repository").OrderRepository

        class Transport:
            calls = 0

            def send(self, statement, params):
                self.calls += 1
                return {"id": "o1"}

        class Bus:
            def publish(self, topic, payload):
                raise TimeoutError("bus unavailable")

        transport = Transport()
        context = {"repository": repository(client(transport)), "events": Bus(), "request_id": "r1"}
        with self.assertRaises(TimeoutError):
            self.routes.dispatch("POST", "/orders", {"body": {"id": "o1"}}, context)
        self.assertEqual(transport.calls, 1)

    def test_permissions_filter_tenant_deleted_and_unpublished_rows(self):
        class Repository:
            def list_orders(self):
                return [
                    {"id": "o1", "tenant": "north", "owner": "u1", "status": "draft"},
                    {"id": "o2", "tenant": "north", "owner": "u2", "status": "draft"},
                    {"id": "o3", "tenant": "north", "owner": "u2", "status": "published"},
                    {"id": "o4", "tenant": "south", "owner": "u1", "status": "published"},
                    {"id": "o5", "tenant": "north", "owner": "u1", "status": "deleted"},
                ]

        context = {"principal": {"id": "u1", "tenant": "north", "role": "member"}, "repository": Repository()}
        rows = self.routes.dispatch("GET", "/orders", {}, context)
        self.assertEqual([row["id"] for row in rows], ["o1", "o3"])

    def test_tenant_false_overrides_global_true_and_legacy_environment(self):
        context = {"tenant_flags": {"stream_exports": False}, "global_flags": {"stream_exports": True}, "environment": {"EXPORT_STREAMING": "1"}}
        result = self.routes.dispatch("GET", "/exports", {"body": [{"id": "o1"}, {"id": "o2"}]}, context)
        self.assertEqual(result, '[{"id": "o1"}, {"id": "o2"}]')
        context["tenant_flags"] = {}
        result = self.routes.dispatch("GET", "/exports", {"body": [{"id": "o1"}, {"id": "o2"}]}, context)
        self.assertEqual(result, '{"id": "o1"}\n{"id": "o2"}')

    def test_bulk_delete_is_unregistered_while_health_is_registered(self):
        self.assertEqual(self.routes.dispatch("DELETE", "/orders/bulk", {}, {}), {"status": 404, "body": "unknown route"})
        self.assertEqual(self.routes.dispatch("GET", "/health", {}, {}), {"status": 200, "body": "ready"})


if __name__ == "__main__":
    unittest.main()
