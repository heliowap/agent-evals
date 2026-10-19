# round-3/sentinel-v2/jev.py
"""Minimal Jev client (OpenRouter Decisions endpoint) with per-call spend logging.

Error contract:
- JevError: this call failed, and we know it cost nothing beyond what was recorded.
  Callers may fall back (sentinel marks the function `jev: "unavailable"`).
- JevUnknownCost: the call may have been billed but its cost is unknown (no `usage.cost`,
  or a timeout after the request was sent). Budget rule: the caller must pause. Deliberately
  NOT a JevError subclass, so fallback handlers don't swallow it.
- RuntimeError: configuration problem (no API key, 401/402/403). Also not swallowed.
"""
import json, os, socket, time, urllib.error, urllib.request
from pathlib import Path

URL = "https://openrouter.ai/api/alpha/decisions"
MODEL = "typesafe/jev-1.13"
ROUND3 = Path(__file__).resolve().parent.parent
SPEND_PATH = ROUND3 / "jev_spend.json"
TIMEOUT = 60
RETRY_DELAYS = (1, 3)


class JevError(Exception):
    pass


class JevUnknownCost(Exception):
    pass


def record_spend(spend_path: Path, entry: dict) -> None:
    spend_path = Path(spend_path)
    entries = json.loads(spend_path.read_text()) if spend_path.exists() else []
    entries.append(entry)
    tmp = spend_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(entries, indent=1) + "\n")
    tmp.replace(spend_path)


def _post(req) -> bytes:
    """urlopen with retries on HTTP 429/5xx (waits RETRY_DELAYS between attempts), then JevError."""
    for attempt in range(len(RETRY_DELAYS) + 1):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            detail = e.read()[:500].decode(errors="replace")
            e.close()
            if e.code in (401, 402, 403):
                raise RuntimeError(f"Jev HTTP {e.code} (auth/credits): {detail}") from e
            if (e.code == 429 or e.code >= 500) and attempt < len(RETRY_DELAYS):
                time.sleep(RETRY_DELAYS[attempt])
                continue
            raise JevError(f"Jev HTTP {e.code}: {detail}") from e


def ask(payload: dict, *, case: str, function: str, spend_path: Path = SPEND_PATH) -> dict:
    """POST one decisions request; return {question: noul float}. Records usage.cost to spend_path."""
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY is not set")
    body = dict(payload)
    body.setdefault("model", MODEL)
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), method="POST", headers={
        "Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        raw = _post(req)
    except (TimeoutError, socket.timeout) as e:
        raise JevUnknownCost(f"Jev timed out after sending ({case} {function}); cost unknown") from e
    except urllib.error.URLError as e:
        if isinstance(e.reason, (TimeoutError, socket.timeout)):
            raise JevUnknownCost(f"Jev timed out ({case} {function}); cost unknown") from e
        raise JevError(f"Jev connection failed: {e.reason}") from e
    try:
        data = json.loads(raw)
    except ValueError as e:
        raise JevUnknownCost(f"Jev returned non-JSON 200 ({case} {function}); cost unknown") from e

    cost = (data.get("usage") or {}).get("cost")
    if not isinstance(cost, (int, float)) or isinstance(cost, bool):
        raise JevUnknownCost(f"Jev response {data.get('id')} has no usage.cost ({case} {function})")
    record_spend(spend_path, {"id": data.get("id"), "case": case, "function": function, "cost": cost})

    answers = data.get("answers") or {}
    out = {}
    for q in body.get("questions", {}):
        a = answers.get(q)
        v = a.get("noul") if isinstance(a, dict) else None
        if not isinstance(v, (int, float)) or isinstance(v, bool) or not 0.0 <= v <= 1.0:
            raise JevError(f"Jev answer {q!r} missing or invalid: {a!r}")
        out[q] = float(v)
    return out
