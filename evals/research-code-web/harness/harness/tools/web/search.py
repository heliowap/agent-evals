"""Single authenticated request to the frozen local broker, never a candidate URL."""
import hashlib
import http.client
import json
import math
import os
import time
from datetime import datetime, timezone
from urllib.parse import urlencode

BASE = "http://127.0.0.1:49374"
ROOT = "~/VSCode/Lab/evals/research-eval-design-20261007T184125Z"
RESPONSE_LIMIT = 2 * 1024 * 1024


def broker_post(path, body, authorization, timeout):
    connection = http.client.HTTPConnection("127.0.0.1", 49374, timeout=timeout)
    try:
        connection.request("POST", path, body=body, headers={
            "Content-Type": "application/json", "Authorization": authorization,
            "Accept-Encoding": "identity"})
        response = connection.getresponse()
        return response.status, response.read(RESPONSE_LIMIT + 1)
    finally:
        connection.close()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def search(query, context, deadline):
    metadata = {"provider_id": "exa", "archive_scope": "service-normalized JSON, not raw upstream SERP",
                "locale": "provider default unknown", "requested_upstream_count": 8,
                "started_utc": datetime.now(timezone.utc).isoformat(), "retries": 0}
    archives = {}

    def outage(reason, message):
        metadata["stop_reason"] = reason
        return {"status": "search_outage", "text": canonical({"error": message}),
                "archives": archives, "metadata": metadata}

    contract = context.get("search_contract", {})
    expected = {"provider_id": "exa", "service_base_url": BASE, "query_path": "/api/websearch",
                "provider_argument": "providerID", "location_directory": ROOT}
    if not isinstance(contract, dict) or any(contract.get(k) != v for k, v in expected.items()):
        return outage("search_outage", "Frozen search contract unavailable or mismatched")
    authorization = os.environ.get("WEBSEARCH_SERVICE_AUTH", "")
    if not authorization.startswith("Basic ") or any(c in authorization for c in "\r\n"):
        return outage("auth_error", "Process-local broker authorization unavailable")
    try:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return outage("search_outage", "Search deadline exhausted")
        path = "/api/websearch?" + urlencode({"location[directory]": ROOT})
        transport = context.get("_search_transport", broker_post)
        status, raw = transport(path, canonical({"query": query, "providerID": "exa"}).encode(),
                                authorization, min(20, remaining))
        metadata["http_status"] = status
        if len(raw) > RESPONSE_LIMIT:
            return outage("search_outage", "Service response exceeds archive cap")
        # A response reflecting authentication is not evidence and must not be archived.
        if authorization.encode() in raw or authorization[6:].encode() in raw:
            return outage("search_outage", "Service response contains sensitive transport material")
        exact = raw.decode("utf-8")
        archives["service-response.json"] = exact
        metadata["response_sha256"] = hashlib.sha256(raw).hexdigest()
        if status in (401, 403):
            return outage("auth_error", "Search service authentication failure")
        if status == 429:
            return outage("quota_error", "Search service quota failure")
        if not 200 <= status < 300:
            return outage("search_outage", "Search service HTTP failure")
        response = json.loads(exact)
        data = response.get("data") if isinstance(response, dict) else None
        if not isinstance(data, dict) or data.get("providerID") != "exa":
            return outage("search_outage", "Search provider identity missing or mismatched")
        results = data.get("results")
        if not isinstance(results, list):
            return outage("search_outage", "Search service result schema unavailable")
        ranked = []
        for rank, result in enumerate(results, 1):
            if not isinstance(result, dict) or not isinstance(result.get("url"), str) or not isinstance(result.get("time"), dict):
                return outage("search_outage", "Search service result schema unavailable")
            if any(k in result and not isinstance(result[k], str) for k in ("title", "content")):
                return outage("search_outage", "Search service result schema unavailable")
            published = result["time"].get("published")
            if published is not None and (type(published) not in (int, float) or not math.isfinite(published)):
                return outage("search_outage", "Search publication schema unavailable")
            ranked.append({"rank": rank, "url": result["url"], "title": result.get("title"),
                           "content": result.get("content"), "publication": result["time"]})
        metadata["returned_result_count"] = len(ranked)
        return {"status": "ok", "text": canonical({"provider_id": "exa", "query": query, "results": ranked}),
                "archives": archives, "metadata": metadata}
    except (OSError, http.client.HTTPException, ValueError, TypeError, UnicodeError):
        # Exception strings can reflect auth; never expose them.
        return outage("search_outage", "Search transport or response decoding unavailable")
