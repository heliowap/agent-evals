"""Remove third-party page text from published conversation logs.

Publication helper, not part of the original harness. The original runs stored
the full text returned by the webfetch tool inside every chat history and
request body. That text is a copy of third-party documentation pages, so the
published copy replaces each tool-message body with a stub that keeps its
length and SHA-256 (of the UTF-8 string as copied, i.e. after anonymization,
which leaves ordinary documentation text unchanged).

usage: python3 -I strip_fetched_text.py DATA_DIR
"""
import gzip
import hashlib
import json
import os
import sys

TARGETS = ('history.json', '-body.json')


def stub(text):
    if not isinstance(text, str) or text.startswith('[omitted third-party page text'):
        return text
    raw = text.encode('utf-8')
    return f'[omitted third-party page text: {len(raw)} bytes, sha256 {hashlib.sha256(raw).hexdigest()}]'


def strip_messages(messages):
    n = 0
    for m in messages:
        if isinstance(m, dict) and m.get('role') == 'tool':
            c = m.get('content')
            if isinstance(c, list):
                for part in c:
                    if isinstance(part, dict) and 'text' in part:
                        part['text'] = stub(part['text'])
                        n += 1
            else:
                m['content'] = stub(c)
                n += 1
    return n


def main(root):
    files = changed = 0
    for dirpath, _, names in os.walk(root):
        for name in names:
            base = name[:-3] if name.endswith('.gz') else name
            if not base.endswith(TARGETS):
                continue
            path = os.path.join(dirpath, name)
            raw = open(path, 'rb').read()
            gz = name.endswith('.gz')
            data = json.loads(gzip.decompress(raw) if gz else raw)
            msgs = data if isinstance(data, list) else data.get('messages', [])
            n = strip_messages(msgs)
            files += 1
            if n:
                out = json.dumps(data, ensure_ascii=False, indent=1).encode('utf-8')
                open(path, 'wb').write(gzip.compress(out, mtime=0) if gz else out)
                changed += n
    print(f'files={files} tool_messages_stubbed={changed}')


if __name__ == '__main__':
    main(sys.argv[1])
