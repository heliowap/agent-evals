"""One POST, without redirects, reconnects, parameter fallback, or retries."""

import http.client
import json
import time
from urllib.parse import urlsplit

USER_AGENT = "research-eval/1.0 (stdlib direct Chat; once-only)"


def chat(body, credentials, session_id, deadline, mark_started, *, endpoint):
    url = urlsplit(endpoint)
    if url.scheme not in ("http", "https") or not url.hostname or url.username or url.password:
        raise ValueError("invalid Chat endpoint")
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("deadline before POST")
    cls = http.client.HTTPSConnection if url.scheme == "https" else http.client.HTTPConnection
    conn = cls(url.hostname, url.port, timeout=remaining)
    headers = {"Content-Type": "application/json", "User-Agent": USER_AGENT,
               "x-opencode-session": session_id}
    if credentials.get("api_key"):
        headers["Authorization"] = "Bearer " + credentials["api_key"]
    try:
        mark_started()
        conn.request("POST", url.path + ("?" + url.query if url.query else ""),
                     body=json.dumps(body, ensure_ascii=False).encode("utf-8"), headers=headers)
        response = conn.getresponse()
        return response.status, response.read()
    finally:
        conn.close()
