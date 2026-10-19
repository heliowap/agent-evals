"""Import-safe whole-document extraction and pinned, first-party HTTPS retrieval."""
import hashlib
import html
from html.parser import HTMLParser
import http.client
import ipaddress
import re
import socket
import ssl
import time
from urllib.parse import unquote, urljoin, urlsplit, urlunsplit

USER_AGENT = "researcher-eval/1.0 (controlled engineering-documentation research)"
RAW_LIMIT = 2 * 1024 * 1024
TEXT_LIMIT = 256 * 1024
ALLOWLIST = {
    "T1": [("docs.github.com", r"/en/webhooks(?:/.*)?")],
    "T2": [("nodejs.org", r"/download/release/v24\.21\.0/docs/api/.*"),
           ("raw.githubusercontent.com", r"/nodejs/node/v24\.21\.0/SECURITY\.md"),
           ("github.com", r"/nodejs/node/(?:blob|tree)/v24\.21\.0(?:/.*)?")],
    "T3": [("www.postgresql.org", r"/docs/18/.*")],
    "T4": [("developers.cloudflare.com", r"/d1(?:/.*)?")],
    "T5": [("docs.docker.com", r"/(?:compose|reference/compose-file)(?:/.*|\.md)?"),
           ("github.com", r"/docker/compose/releases(?:/.*)?")],
    "T6": [("go.dev", r"/doc/(?:toolchain(?:/.*)?|modules(?:/.*)?)")],
}


def normalize_text(text):
    """Normalize whitespace only; never rewrite substantive words."""
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


class _Node:
    def __init__(self, tag="", attrs=()):
        self.tag, self.attrs, self.children = tag, dict(attrs), []


class _Tree(HTMLParser):
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = _Node()
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = _Node(tag, attrs)
        self.stack[-1].children.append(node)
        if tag not in self.VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def extract_document(raw: bytes, content_type: str, url: str) -> str:
    charset = re.search(r"charset=[\"']?([\w-]+)", content_type, re.I)
    try:
        text = raw.decode(charset.group(1) if charset else "utf-8", errors="replace")
    except LookupError:
        text = raw.decode("utf-8", errors="replace")
    if "html" not in content_type.lower():
        return text.replace("\r\n", "\n").replace("\r", "\n").strip() + "\n"
    tree = _Tree()
    tree.feed(text)

    def find(node, predicate):
        if predicate(node):
            return node
        for child in node.children:
            if isinstance(child, _Node):
                found = find(child, predicate)
                if found:
                    return found
        return None

    root = (find(tree.root, lambda n: n.tag == "main" or n.attrs.get("role") == "main")
            or find(tree.root, lambda n: n.tag == "article")
            or find(tree.root, lambda n: "markdown-body" in n.attrs.get("class", "").split())
            or tree.root)
    ignored = {"script", "style", "nav", "footer", "header", "noscript", "template", "head"}
    blocks = {"p", "div", "section", "article", "main", "aside", "li", "ul", "ol", "pre", "blockquote", "table", "tr", "h1", "h2", "h3", "h4", "h5", "h6"}

    def substantive_aside(node):
        role = (node.attrs.get("role") or "").lower()
        classes = (node.attrs.get("class") or "").lower().split()
        # Semantic documentation callouts carry facts, not navigation. Explicit
        # navigation/sidebar roles or classes take precedence over callout styling.
        navigation = role in {"navigation", "complementary"} or any(
            re.fullmatch(r"(?:sidebar|navigation|nav|toc|table-of-contents)(?:[-_].*)?", c) for c in classes)
        callout = role in {"note", "alert"} or any(
            re.fullmatch(r"(?:admonition|callout|starlight-aside)(?:[-_].*)?|note|tip|warning|caution|danger|important|info", c)
            for c in classes)
        return callout and not navigation

    def render(node):
        if isinstance(node, str):
            return node
        if node.tag in ignored or node.attrs.get("aria-hidden") == "true" or "hidden" in node.attrs:
            return ""
        if node.tag == "aside" and not substantive_aside(node):
            return ""
        body = "".join(render(c) for c in node.children)
        if node.tag == "a" and node.attrs.get("href"):
            link = urljoin(url, node.attrs["href"])
            if urlsplit(link).scheme == "https":
                body = "[" + normalize_text(body) + "](" + link + ")"
        if node.tag.startswith("h") and node.tag in blocks and node.attrs.get("id"):
            body += " [section](" + url.split("#")[0] + "#" + node.attrs["id"] + ")"
        if node.tag == "br":
            return "\n"
        if node.tag in {"td", "th"}:
            return body + " | "
        return "\n" + body + "\n" if node.tag in blocks else body

    return "\n".join(normalize_text(line) for line in render(root).splitlines() if normalize_text(line)) + "\n"


class Rejected(ValueError):
    pass


def validate_url(url, task_id):
    if not isinstance(url, str) or any(ord(c) < 33 for c in url) or "\\" in url:
        raise Rejected("malformed URL")
    p = urlsplit(url)
    try:
        port = p.port
    except ValueError:
        raise Rejected("invalid port") from None
    if p.scheme != "https" or p.username is not None or p.password is not None or port not in (None, 443):
        raise Rejected("HTTPS without credentials on port 443 required")
    if p.query:
        raise Rejected("query strings are outside the documentation allowlist")
    decoded = unquote(p.path)
    if "%" in decoded or "\\" in decoded or any(s in {".", ".."} for s in decoded.split("/")):
        raise Rejected("ambiguous path")
    if not any(p.hostname == host and re.fullmatch(pattern, decoded)
               for host, pattern in ALLOWLIST.get(task_id, [])):
        raise Rejected("outside task-scoped first-party allowlist")
    return urlunsplit(("https", p.hostname, p.path or "/", "", ""))


def public_addresses(host):
    addresses = list(dict.fromkeys(item[4][0] for item in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)))
    if not addresses or any(not ipaddress.ip_address(a).is_global for a in addresses):
        raise Rejected("DNS includes nonpublic destination")
    return addresses


class _PinnedHTTPS(http.client.HTTPSConnection):
    def __init__(self, host, address, timeout):
        super().__init__(host, timeout=timeout, context=ssl.create_default_context())
        self.address = address

    def connect(self):
        sock = socket.create_connection((self.address, 443), self.timeout)
        try:
            self.sock = self._context.wrap_socket(sock, server_hostname=self.host)
        except BaseException:
            sock.close()
            raise


def https_get(url, timeout):
    """One pinned GET; no proxy, auth, cookie jar or implicit redirect/retry."""
    p = urlsplit(url)
    addresses = public_addresses(p.hostname)
    conn = _PinnedHTTPS(p.hostname, addresses[0], timeout)
    try:
        conn.request("GET", p.path or "/", headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"})
        response = conn.getresponse()
        headers = dict((k.lower(), v) for k, v in response.getheaders())
        raw = response.read(RAW_LIMIT + 1) if 200 <= response.status < 300 else b""
        return response.status, headers, raw
    finally:
        conn.close()


def fetch_document(url, task_id, deadline, transport=None):
    """Return evidence and an honest model result, including denied attempts."""
    transport = transport or https_get
    result = {"requested_url": url, "final_url": None, "status": "rejected", "redirects": [],
              "raw": None, "text": None, "model_text": None, "truncated": False,
              "error": None, "content_type": None, "http_status": None}
    try:
        current = validate_url(url, task_id)
        for hop in range(6):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("case deadline exhausted")
            status, headers, raw = transport(current, min(20, remaining))
            result.update(final_url=current, http_status=status)
            if status in {301, 302, 303, 307, 308}:
                if hop == 5 or not headers.get("location"):
                    raise Rejected("redirect limit or missing Location")
                target = urljoin(current, headers["location"])
                result["redirects"].append({"from": current, "to": target, "status": status})
                current = validate_url(target, task_id)
                continue
            if not 200 <= status < 300:
                result.update(status="http_error", error="HTTP " + str(status))
                break
            result["content_type"] = headers.get("content-type", "")
            if headers.get("content-encoding", "identity") != "identity":
                raise Rejected("compressed body not accepted")
            if len(raw) > RAW_LIMIT:
                result.update(raw=raw[:RAW_LIMIT], truncated=True)
                raise Rejected("raw body exceeds 2 MiB; retained prefix only")
            if not any(t in result["content_type"].lower() for t in ("html", "text/", "markdown")):
                raise Rejected("unsupported document content type")
            text = extract_document(raw, result["content_type"], current)
            encoded = text.encode("utf-8")
            marker = "\n[TRUNCATED: whole-document text exceeded 256 KiB]\n"
            limited = (encoded[:TEXT_LIMIT - len(marker.encode())].decode("utf-8", "ignore") + marker
                       if len(encoded) > TEXT_LIMIT else text)
            result.update(status="ok", raw=raw, text=text, model_text=limited, truncated=len(encoded) > TEXT_LIMIT)
            break
    except (Rejected, ValueError, OSError, http.client.HTTPException) as exc:
        result.update(status="rejected" if isinstance(exc, (Rejected, ValueError)) else "fetch_error", error=str(exc))
    return result


def document_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
