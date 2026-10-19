# Web tools (P2)

`from harness.tools.web import tools, dispatch` exports the frozen OpenAI Chat
schemas and `dispatch(name, arguments, context, deadline)`. Deadline is absolute
`time.monotonic()` time. Every result has `status`, canonical JSON evidence in
`text`, text-valued safe-filename `archives`, and JSON metadata. Core archives
these before continuation, applies its additional evidence budgets, and wraps
source-derived text as untrusted. No page content drives actions here.

Search accepts only `query`. Controller context supplies `search_contract` from
`contracts/search.json`; provider, broker origin, directory and path must match
the frozen values. Core forwards `credentials['environment']` process-locally;
the only credential input used here is `WEBSEARCH_SERVICE_AUTH`, a complete
`Basic ...` header. Credentials in context are not supported. No auth-store read,
configuration change, retry, redirect, fallback or model inference occurs.
Only the broker may contact its upstream Exa service. The exact UTF-8 broker
response is archived in `service-response.json`, with timestamp and SHA-256 in
metadata. It is **service-normalized JSON**, not raw upstream SERP. Original
order supplies rank; titles, URLs, content and publication `time` are retained.
Upstream requested count is eight; actual returned count is reported, never
filled in. No explicit locale is controlled; provider default is unknown.
A broker response reflecting the credential is suppressed rather than archived.

Search status is `ok`, or `search_outage` with metadata `stop_reason` equal to
`auth_error` (missing auth/401/403), `quota_error` (429), or `search_outage`
(transport, HTTP, identity, decoding/schema or contract failure). Bad candidate
arguments return tool-only `rejected` without a stopping reason.

Fetch accepts any public **HTTPS on port 443** URL; HTTP is deliberately excluded.
There is no old task allowlist. URL queries survive, fragments are removed, and
credentials, malformed URLs and private destinations are rejected. Every hop
resolves DNS anew, rejects the entire answer set if any address is nonpublic,
then connects directly to one checked address with TLS hostname verification.
IPv6 transition addresses are excluded. No proxy, auth headers, cookies,
method override, implicit redirect, retry, browser, shell or script execution.
At most five redirects are followed, and every target is revalidated and pinned.
The supervisor owns the whole invocation timeout, including blocking DNS.

Each HTTP response, including redirect and error bodies, is archived as a raw
base64 prefix (2 MiB cap, explicit truncation and prefix hash). Supported types
are `text/*`, XHTML and JSON; compressed bodies and other MIME types are explicit
tool-only rejections with raw evidence retained. Normalized text preserves all
visible sections (including navigation, headers, quotes, asides/callouts); only
script/style/template payloads and whitespace are removed. No AI summary or
main-content selection. The normalized string archive is capped at 256 KiB
UTF-8, with explicit truncation and hash; it is never claimed to be an uncapped
document. Candidate content uses zero-based character `offset`, `limit` 1..20000,
explicit `next_offset`, and truncation flags. Raw and normalized caps are separate
from core's budgets. Every continuation refetches live; there is no cache of any
scope. `ok`, `rejected`, `http_error` (including recoverable 404), and `fetch_error`
never impose a blocking stop reason. Partial/error evidence remains archived.

Offline fixture seams in controller-only context are `_search_transport(path,
body_bytes, authorization, timeout)->(http_status, raw_bytes)` and
`_fetch_transport(url, checked_ip, timeout)->(http_status, headers, raw_bytes,
optional_incomplete_error)`. Candidate schemas cannot select these. Tests mock
DNS but exercise the actual address checks and dispatch behavior; no live request
is performed by verification.

Verify from the package root: `python3 -B -m harness.tools.web.verify`.
