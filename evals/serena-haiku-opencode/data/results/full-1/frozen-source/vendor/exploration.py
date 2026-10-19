from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from textwrap import dedent


FILES = {
    "service/__init__.py": "",
    "service/routes.py": '''
        from service.handlers import create_order, list_orders, export_orders
        from service.health import health

        ROUTES = {
            ("POST", "/orders"): create_order,
            ("GET", "/orders"): list_orders,
            ("GET", "/exports"): export_orders,
            ("GET", "/health"): health,
        }

        def dispatch(method, path, request, context):
            handler = ROUTES.get((method, path))
            if handler is None:
                return {"status": 404, "body": "unknown route"}
            return handler(request, context)
    ''',
    "service/handlers.py": '''
        from service.orders import submit_order, visible_orders
        from service.exports import render_export

        def create_order(request, context):
            return submit_order(request["body"], context)

        def list_orders(request, context):
            return visible_orders(context["principal"], context["repository"])

        def export_orders(request, context):
            return render_export(request["body"], context)
    ''',
    "service/orders.py": '''
        from service.events import publish_created
        from service.permissions import can_read

        def submit_order(body, context):
            row = context["repository"].insert_order(body, context["request_id"])
            publish_created(context["events"], row)
            return {"status": 201, "body": row}

        def visible_orders(principal, repository):
            rows = repository.list_orders()
            return [row for row in rows if row["status"] != "deleted" and can_read(principal, row)]
    ''',
    "service/repository.py": '''
        from service.sql import INSERT_ORDER, SELECT_ORDERS

        class OrderRepository:
            def __init__(self, client):
                self.client = client

            def insert_order(self, body, request_id):
                params = dict(body, request_id=request_id)
                return self.client.execute(INSERT_ORDER, params)

            def list_orders(self):
                return self.client.execute(SELECT_ORDERS, {})
    ''',
    "service/client.py": '''
        class DatabaseClient:
            def __init__(self, transport):
                self.transport = transport

            def execute(self, statement, params):
                for attempt in range(3):
                    try:
                        return self.transport.send(statement, params)
                    except (ConnectionError, TimeoutError):
                        if attempt == 2:
                            raise
    ''',
    "service/sql.py": '''
        INSERT_ORDER = "INSERT INTO orders VALUES (:id, :tenant, :owner, :status, :request_id) ON CONFLICT (request_id) DO NOTHING RETURNING *"
        SELECT_ORDERS = "SELECT * FROM orders ORDER BY id"
    ''',
    "service/events.py": '''
        def publish_created(bus, order):
            bus.publish("order.created", {"id": order["id"]})
    ''',
    "service/permissions.py": '''
        def can_read(principal, order):
            if order["tenant"] != principal["tenant"]:
                return False
            if principal["role"] == "admin" or order["owner"] == principal["id"]:
                return True
            return order["status"] == "published"
    ''',
    "service/config.py": '''
        DEFAULTS = {"endpoint": "https://db.local", "timeout": 30}
        ENV_KEYS = {"endpoint": "APP_ENDPOINT", "timeout": "APP_TIMEOUT"}

        def resolve_value(key, environment, tenant, file_config):
            if ENV_KEYS[key] in environment:
                return environment[ENV_KEYS[key]]
            if key in tenant:
                return tenant[key]
            if key in file_config:
                return file_config[key]
            return DEFAULTS[key]

        def load_config(environment, tenant, file_config):
            return {key: resolve_value(key, environment, tenant, file_config) for key in DEFAULTS}
    ''',
    "service/flags.py": '''
        def enabled(name, tenant_flags, global_flags):
            if name in tenant_flags:
                return tenant_flags[name]
            return global_flags.get(name, False)
    ''',
    "service/exports.py": '''
        from service.flags import enabled
        from service.renderers import stream_rows, json_rows

        def render_export(rows, context):
            if enabled("stream_exports", context["tenant_flags"], context["global_flags"]):
                return stream_rows(rows)
            return json_rows(rows)
    ''',
    "service/renderers.py": '''
        import json

        def stream_rows(rows):
            return "\\n".join(json.dumps(row, sort_keys=True) for row in rows)

        def json_rows(rows):
            return json.dumps(rows, sort_keys=True)
    ''',
    "service/health.py": '''
        def health(request, context):
            return {"status": 200, "body": "ready"}
    ''',
    "service/startup.py": '''
        from service.client import DatabaseClient
        from service.config import load_config
        from service.repository import OrderRepository

        def make_context(environment, tenant, file_config, transport, events):
            config = load_config(environment, tenant["connection"], file_config)
            return {
                "config": config,
                "repository": OrderRepository(DatabaseClient(transport)),
                "events": events,
                "tenant_flags": tenant["flags"],
                "global_flags": file_config.get("flags", {}),
            }
    ''',
    "service/models.py": '''
        from dataclasses import dataclass

        @dataclass(frozen=True)
        class Order:
            id: str
            tenant: str
            owner: str
            status: str
    ''',
    "service/cli.py": '''
        from service.config import load_config

        def connection_info(environment, tenant, file_config):
            settings = load_config(environment, tenant, file_config)
            return settings["endpoint"]
    ''',
    "service/legacy/__init__.py": "",
    "service/legacy/routes.py": '''
        from service.legacy.orders import create_order

        ROUTES = {
            ("POST", "/orders"): create_order,
            ("DELETE", "/orders/bulk"): "bulk_delete",
        }

        def dispatch(method, path, request, context):
            return ROUTES[(method, path)](request, context)
    ''',
    "service/legacy/orders.py": '''
        def create_order(request, context):
            return context["transport"].send("INSERT order", request["body"])

        def bulk_delete(ids, context):
            return context["transport"].send("DELETE orders", {"ids": ids})
    ''',
    "service/legacy/config.py": '''
        def endpoint(environment, tenant, file_config):
            return tenant.get("endpoint") or environment.get("APP_ENDPOINT") or file_config.get("endpoint")
    ''',
    "service/legacy/exports.py": '''
        from service.renderers import stream_rows, json_rows

        def render_export(rows, environment):
            if environment.get("EXPORT_STREAMING") == "1":
                return stream_rows(rows)
            return json_rows(rows)
    ''',
    "service/maintenance.py": '''
        def bulk_delete(repository, ids):
            for order_id in ids:
                repository.client.execute("DELETE FROM orders WHERE id = :id", {"id": order_id})
    ''',
}
FILES = {path: dedent(source).lstrip("\n") for path, source in FILES.items()}


CASES = {
    "route": {
        "request": "Trace the active POST /orders request from its registered handler through the application method that invokes the external database transport. Include only application functions or methods on this database path, in order, starting at the handler and ending at the method that invokes the transport. Use fully qualified names. Identify the active registration module. Ignore imported modules that are never used by this route.",
        "schema": {"chain": "ordered list of fully qualified function or method names", "registration": "relative path to active route registration"},
        "expected": {"chain": ["service.handlers.create_order", "service.orders.submit_order", "service.repository.OrderRepository.insert_order", "service.client.DatabaseClient.execute"], "registration": "service/routes.py"},
        "anchors": [
            ("service/routes.py", "ROUTES", '    ("POST", "/orders"): create_order,'),
            ("service/handlers.py", "create_order", '    return submit_order(request["body"], context)'),
            ("service/orders.py", "submit_order", '    row = context["repository"].insert_order(body, context["request_id"])'),
            ("service/repository.py", "OrderRepository.insert_order", '        return self.client.execute(INSERT_ORDER, params)'),
            ("service/client.py", "DatabaseClient.execute", '                return self.transport.send(statement, params)'),
        ],
    },
    "config": {
        "request": 'Explain load_config precedence. Resolve its result for environment={"APP_ENDPOINT": ""}, tenant={"endpoint": "https://tenant.local", "timeout": 7}, file_config={"endpoint": "https://file.local", "timeout": 15}. Report endpoint, timeout, and the source precedence from strongest to weakest. Preserve empty values exactly.',
        "schema": {"endpoint": "string", "timeout": "integer", "precedence": "ordered list using environment, tenant, file, default"},
        "expected": {"endpoint": "", "timeout": 7, "precedence": ["environment", "tenant", "file", "default"]},
        "anchors": [
            ("service/config.py", "resolve_value", '    if ENV_KEYS[key] in environment:'),
            ("service/config.py", "resolve_value", '        return environment[ENV_KEYS[key]]'),
            ("service/config.py", "resolve_value", '    if key in tenant:'),
            ("service/config.py", "resolve_value", '    if key in file_config:'),
            ("service/config.py", "resolve_value", '    return DEFAULTS[key]'),
        ],
    },
    "retry": {
        "request": "For active POST /orders, identify the function owning retries, the maximum number of transport attempts, and the exception types it retries. Say whether ValueError is retried and whether publishing order.created happens inside that retry loop. Do not include retries from unrelated or legacy code.",
        "schema": {"owner": "fully qualified method name", "max_attempts": "integer", "retryable": "alphabetically sorted list of exception class names", "value_error_retried": "boolean", "event_inside_retry": "boolean"},
        "expected": {"owner": "service.client.DatabaseClient.execute", "max_attempts": 3, "retryable": ["ConnectionError", "TimeoutError"], "value_error_retried": False, "event_inside_retry": False},
        "anchors": [
            ("service/client.py", "DatabaseClient.execute", '        for attempt in range(3):'),
            ("service/client.py", "DatabaseClient.execute", '            except (ConnectionError, TimeoutError):'),
            ("service/orders.py", "submit_order", '    row = context["repository"].insert_order(body, context["request_id"])'),
            ("service/orders.py", "submit_order", '    publish_created(context["events"], row)'),
        ],
    },
    "permission": {
        "request": 'Which IDs does active GET /orders return in input order for principal={"id":"u1","tenant":"north","role":"member"} and repository rows=[{"id":"o1","tenant":"north","owner":"u1","status":"draft"},{"id":"o2","tenant":"north","owner":"u2","status":"draft"},{"id":"o3","tenant":"north","owner":"u2","status":"published"},{"id":"o4","tenant":"south","owner":"u1","status":"published"},{"id":"o5","tenant":"north","owner":"u1","status":"deleted"}]? Identify the authorization function and the function that excludes deleted rows.',
        "schema": {"ids": "ordered list of order IDs", "authorization": "fully qualified function", "deleted_filter": "fully qualified function"},
        "expected": {"ids": ["o1", "o3"], "authorization": "service.permissions.can_read", "deleted_filter": "service.orders.visible_orders"},
        "anchors": [
            ("service/orders.py", "visible_orders", '    return [row for row in rows if row["status"] != "deleted" and can_read(principal, row)]'),
            ("service/permissions.py", "can_read", '    if order["tenant"] != principal["tenant"]:'),
            ("service/permissions.py", "can_read", '    if principal["role"] == "admin" or order["owner"] == principal["id"]:'),
            ("service/permissions.py", "can_read", '    return order["status"] == "published"'),
        ],
    },
    "feature": {
        "request": 'For active GET /exports, context has tenant_flags={"stream_exports":false}, global_flags={"stream_exports":true}, environment={"EXPORT_STREAMING":"1"}. Which renderer is used? Report the flag name, the effective flag value, its winning source, and whether EXPORT_STREAMING affects this active route. Trace the active route rather than the old export module.',
        "schema": {"renderer": "fully qualified function", "flag": "string", "effective_value": "boolean", "winning_source": "tenant or global", "environment_affects_route": "boolean"},
        "expected": {"renderer": "service.renderers.json_rows", "flag": "stream_exports", "effective_value": False, "winning_source": "tenant", "environment_affects_route": False},
        "anchors": [
            ("service/routes.py", "ROUTES", '    ("GET", "/exports"): export_orders,'),
            ("service/handlers.py", "export_orders", '    return render_export(request["body"], context)'),
            ("service/flags.py", "enabled", '    if name in tenant_flags:'),
            ("service/flags.py", "enabled", '        return tenant_flags[name]'),
            ("service/exports.py", "render_export", '    if enabled("stream_exports", context["tenant_flags"], context["global_flags"]):'),
            ("service/exports.py", "render_export", '    return json_rows(rows)'),
        ],
    },
    "absence": {
        "request": 'Does the active HTTP dispatcher expose DELETE /orders/bulk? Return whether it is registered and the dispatcher response when method="DELETE", path="/orders/bulk", request={}, context={}. There are functions and old route declarations with similar names. Base the answer on active registration and missing-route behavior.',
        "schema": {"registered": "boolean", "status": "integer", "body": "string", "registration": "relative path to active route registration"},
        "expected": {"registered": False, "status": 404, "body": "unknown route", "registration": "service/routes.py"},
        "anchors": [
            ("service/routes.py", "ROUTES", 'ROUTES = {'),
            ("service/routes.py", "dispatch", '    handler = ROUTES.get((method, path))'),
            ("service/routes.py", "dispatch", '        return {"status": 404, "body": "unknown route"}'),
        ],
    },
}


def snapshot(work: Path) -> dict[str, str]:
    work = Path(work)
    return {
        path.relative_to(work).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(work.rglob("*"))
        if path.is_file() and not path.is_symlink()
    }


def build(work: Path) -> dict[str, str]:
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    for relative, source in FILES.items():
        target = work / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source, encoding="utf-8")
    return snapshot(work)


def prompt(case: str) -> str:
    task = CASES[case]
    return (
        "Inspect this Python service in read-only mode. Do not modify files. "
        "The active HTTP entry point is service.routes.dispatch.\n\n"
        + task["request"]
        + "\n\nReturn one JSON object, with no Markdown fences or prose outside it. "
        'Use {"answer": ..., "evidence": [{"path": ..., "symbol": ..., "line": ..., "quote": ...}]}. '
        "The answer object must have exactly these fields, whose descriptions follow.\n"
        + json.dumps(task["schema"], ensure_ascii=False)
        + "\nProvide at most eight evidence entries. Each path must be relative to this directory. "
        "Use the local function name, Class.method, or top-level assignment name for symbol. "
        "Use a one-based line number and copy the entire source line exactly, including indentation. "
        "Cite the specific statements supporting every answer field. "
        "For absence of a route, cite the active registration table and missing-route branch."
    )


def _symbol_ranges(source: str) -> dict[str, tuple[int, int]]:
    result = {}
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            result[node.name] = (node.lineno, node.end_lineno)
            if isinstance(node, ast.ClassDef):
                for child in node.body:
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        result[f"{node.name}.{child.name}"] = (child.lineno, child.end_lineno)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name):
                    result[target.id] = (node.lineno, node.end_lineno)
    return result


def _same_value(actual, expected) -> bool:
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, dict):
        return actual.keys() == expected.keys() and all(_same_value(actual[key], value) for key, value in expected.items())
    if isinstance(expected, list):
        return len(actual) == len(expected) and all(_same_value(left, right) for left, right in zip(actual, expected))
    return actual == expected


def grade(case: str, work: Path, final: str | dict) -> dict:
    task = CASES[case]
    work = Path(work)
    checks = {"json": False, "shape": False, "workspace_unchanged": False, "evidence_valid": False, "anchors_present": False}
    answer_correct = False
    evidence_correct = False
    try:
        final = json.loads(final) if isinstance(final, str) else final
        checks["json"] = isinstance(final, dict)
        checks["shape"] = checks["json"] and set(final) == {"answer", "evidence"}
        expected_snapshot = {path: hashlib.sha256(source.encode()).hexdigest() for path, source in FILES.items()}
        current = snapshot(work)
        checks["workspace_unchanged"] = all(current.get(path) == digest for path, digest in expected_snapshot.items())
        checks["workspace_unchanged"] = checks["workspace_unchanged"] and all(not (work / path).is_symlink() for path in FILES)
        if checks["shape"]:
            answer_correct = _same_value(final["answer"], task["expected"])
            evidence = final["evidence"]
            valid = isinstance(evidence, list) and 1 <= len(evidence) <= 8
            anchors = set()
            for item in evidence if isinstance(evidence, list) else []:
                if not isinstance(item, dict) or set(item) != {"path", "symbol", "line", "quote"}:
                    valid = False
                    continue
                relative, symbol, line, quote = (item[key] for key in ("path", "symbol", "line", "quote"))
                if not isinstance(relative, str) or relative not in FILES or type(line) is not int or not isinstance(symbol, str) or not isinstance(quote, str):
                    valid = False
                    continue
                target = work / relative
                if not target.is_file() or target.is_symlink() or not target.resolve().is_relative_to(work.resolve()):
                    valid = False
                    continue
                source = target.read_text(encoding="utf-8")
                lines = source.splitlines()
                span = _symbol_ranges(source).get(symbol)
                if not span or not 1 <= line <= len(lines) or not span[0] <= line <= span[1] or lines[line - 1] != quote:
                    valid = False
                    continue
                anchors.add((relative, symbol, quote))
            checks["evidence_valid"] = valid
            checks["anchors_present"] = set(task["anchors"]).issubset(anchors)
            evidence_correct = valid and checks["anchors_present"]
    except (ValueError, TypeError, OSError, SyntaxError, KeyError):
        pass
    return {
        "passed": answer_correct and evidence_correct and all(checks.values()),
        "answer_correct": answer_correct,
        "evidence_correct": evidence_correct,
        "checks": checks,
    }
