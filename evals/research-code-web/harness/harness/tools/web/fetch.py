"""Public HTTPS retrieval with DNS pinning and whole-document, non-AI extraction."""
import base64
import hashlib
import http.client
import ipaddress
import json
import re
import socket
import ssl
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit, urlunsplit

RAW_LIMIT = 2 * 1024 * 1024
TEXT_LIMIT = 256 * 1024
REDIRECTS = {301, 302, 303, 307, 308}


class Rejected(ValueError):
    pass


def validate_url(url):
    if not isinstance(url, str) or not url or any(ord(c) < 33 or ord(c) == 127 for c in url) or "\\" in url:
        raise Rejected("malformed URL")
    p = urlsplit(url)
    try:
        port = p.port
    except ValueError:
        raise Rejected("invalid port") from None
    if p.scheme != "https" or not p.hostname or p.username is not None or p.password is not None or port not in (None, 443):
        raise Rejected("public HTTPS without credentials on port 443 required")
    host = p.hostname.encode("idna").decode("ascii")
    if "%" in host:
        raise Rejected("ambiguous hostname")
    authority = "[" + host + "]" if ":" in host else host
    # Fragments are local references, never sent. Public documentation queries are retained.
    return urlunsplit(("https", authority, p.path or "/", p.query, ""))


def public_addresses(host):
    addresses = list(dict.fromkeys(item[4][0] for item in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)))
    if not addresses:
        raise Rejected("DNS has no destination")
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if not ip.is_global or ip.is_multicast or ip.is_reserved or ip.is_loopback or ip.is_link_local or ip.is_private:
            raise Rejected("DNS includes nonpublic destination")
        if isinstance(ip, ipaddress.IPv6Address) and (ip.ipv4_mapped or ip.sixtofour or ip.teredo):
            raise Rejected("IPv6 transition addresses are not accepted")
    return addresses


class PinnedHTTPS(http.client.HTTPSConnection):
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


def https_get(url, address, timeout):
    started = time.monotonic()
    p = urlsplit(url)
    connection = PinnedHTTPS(p.hostname, address, timeout)
    try:
        connection.request("GET", (p.path or "/") + ("?" + p.query if p.query else ""),
                           headers={"User-Agent": "research-eval/1.0", "Accept-Encoding": "identity"})
        sock = connection.sock
        response = connection.getresponse()
        chunks, size = [], 0
        try:
            while size <= RAW_LIMIT:
                remaining = timeout - (time.monotonic() - started)
                if remaining <= 0:
                    raise TimeoutError("response deadline exhausted")
                sock.settimeout(remaining)
                chunk = response.read1(min(65536, RAW_LIMIT + 1 - size))
                if not chunk:
                    break
                chunks.append(chunk)
                size += len(chunk)
        except (OSError, http.client.HTTPException):
            return response.status, dict((k.lower(), v) for k, v in response.getheaders()), b"".join(chunks), "incomplete body"
        return response.status, dict((k.lower(), v) for k, v in response.getheaders()), b"".join(chunks), None
    finally:
        connection.close()


class DocumentParser(HTMLParser):
    """Keep all visible sections, including nav, header, aside and blockquotes."""
    BLOCKS = {"p", "div", "section", "article", "main", "aside", "nav", "header", "footer", "li", "ul", "ol", "pre", "blockquote", "table", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "br"}
    IGNORED = {"script", "style", "template"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.ignored = []

    def handle_starttag(self, tag, attrs):
        if tag in self.IGNORED:
            self.ignored.append(tag)
        if not self.ignored and tag in self.BLOCKS:
            self.parts.append("\n")
        if not self.ignored and tag in {"td", "th"}:
            self.parts.append(" | ")

    def handle_endtag(self, tag):
        if self.ignored:
            if tag == self.ignored[-1]:
                self.ignored.pop()
            return
        if tag in self.BLOCKS:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.ignored:
            self.parts.append(data)


def extract_document(raw, content_type):
    charset = re.search(r"charset=[\"']?([\w-]+)", content_type, re.I)
    try:
        text = raw.decode(charset.group(1) if charset else "utf-8", errors="replace")
    except LookupError:
        text = raw.decode("utf-8", errors="replace")
    if content_type.split(";", 1)[0].strip().lower() in {"text/html", "application/xhtml+xml"}:
        parser = DocumentParser()
        parser.feed(text)
        text = "".join(parser.parts)
    # Only whitespace normalization; no summaries, selection of main, or dropped nav.
    return "\n".join(re.sub(r"[^\S\n]+", " ", line).strip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n") if line.strip()) + "\n"


def fetch(url, offset, limit, context, deadline):
    metadata = {"requested_url": url, "final_url": None, "http_status": None, "content_type": None,
                "redirects": [], "responses": [], "started_utc": datetime.now(timezone.utc).isoformat(),
                "cache": "none; every continuation refetches live", "offset": offset, "limit": limit,
                "raw_truncated": False, "normalized_truncated": False, "source_untrusted": True}
    archives, full_text, status, error = {}, "", "rejected", None
    try:
        current = validate_url(url)
        transport = context.get("_fetch_transport", https_get)
        for hop in range(6):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("deadline exhausted")
            addresses = public_addresses(urlsplit(current).hostname)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("deadline exhausted")
            response = transport(current, addresses[0], min(20, remaining))
            http_status, headers, raw = response[:3]
            incomplete = response[3] if len(response) > 3 else None
            headers = {k.lower(): v for k, v in headers.items()}
            content_type = headers.get("content-type", "")
            clipped = raw[:RAW_LIMIT]
            archive = f"response-{hop}-raw.base64"
            archives[archive] = base64.b64encode(clipped).decode("ascii")
            metadata.update(final_url=current, http_status=http_status, content_type=content_type)
            metadata["raw_truncated"] = metadata["raw_truncated"] or len(raw) > RAW_LIMIT or bool(incomplete)
            metadata["responses"].append({"url": current, "http_status": http_status, "content_type": content_type,
                                          "raw_archive": archive, "raw_sha256": hashlib.sha256(clipped).hexdigest(),
                                          "raw_bytes_retained": len(clipped), "raw_truncated": len(raw) > RAW_LIMIT or bool(incomplete)})
            mime = content_type.split(";", 1)[0].strip().lower()
            supported = mime.startswith("text/") or mime in {"application/xhtml+xml", "application/json"}
            if supported and headers.get("content-encoding", "identity").lower() == "identity":
                normalized = extract_document(clipped, content_type)
                encoded = normalized.encode("utf-8")
                full_text = encoded[:TEXT_LIMIT].decode("utf-8", "ignore")
                metadata["normalized_truncated"] = len(encoded) > TEXT_LIMIT
                archives[f"response-{hop}-normalized.txt"] = full_text
                metadata["responses"][-1]["normalized_sha256"] = hashlib.sha256(full_text.encode()).hexdigest()
            else:
                full_text = ""
            if incomplete:
                status, error = "fetch_error", "incomplete response body; retained prefix only"
                break
            if http_status in REDIRECTS:
                target = urljoin(current, headers.get("location", ""))
                metadata["redirects"].append({"from": current, "to": target, "status": http_status})
                if hop == 5 or not headers.get("location"):
                    raise Rejected("redirect limit or missing Location")
                current = validate_url(target)
                continue
            if not 200 <= http_status < 300:
                status, error = "http_error", f"HTTP {http_status}"
            elif headers.get("content-encoding", "identity").lower() != "identity":
                status, error = "rejected", "compressed body not supported; raw bytes retained"
            elif not supported:
                status, error = "rejected", "unsupported document MIME; raw bytes retained"
            else:
                status = "ok"
            break
    except (ValueError, OSError, http.client.HTTPException) as exc:
        status = "rejected" if isinstance(exc, ValueError) else "fetch_error"
        error = str(exc) if isinstance(exc, Rejected) else "Fetch transport or URL decoding failed"
    visible = full_text[offset:offset + limit]
    end = min(offset + len(visible), len(full_text))
    metadata.update(normalized_characters=len(full_text), next_offset=end if end < len(full_text) else None,
                    slice_truncated=offset > 0 or offset + len(visible) < len(full_text))
    payload = {"url": metadata["final_url"], "http_status": metadata["http_status"], "content_type": metadata["content_type"],
               "offset": offset, "next_offset": metadata["next_offset"], "content": visible,
               "truncated": metadata["raw_truncated"] or metadata["normalized_truncated"] or metadata["slice_truncated"],
               "refetched_live": True, "error": error}
    return {"status": status, "text": json.dumps(payload, ensure_ascii=False, sort_keys=True),
            "archives": archives, "metadata": metadata}
