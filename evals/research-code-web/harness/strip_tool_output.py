"""Remove third-party tool output (web pages, search results, corpus files) from published data.

Publication helper, not part of the original harness. Every candidate-visible
tool result in this study is wrapped in <untrusted_tool_result>...</untrusted_tool_result>,
and that wrapper is copied verbatim (possibly JSON-escaped one or more times)
into histories, request bodies, grading packets and grading job files. Each
wrapped span is replaced by a stub with the length and SHA-256 of the span as
it appeared in that file (escaped form). Tool names, arguments, status flags,
model outputs and grades are unchanged.

usage: python3 -I strip_tool_output.py DATA_DIR
"""
import gzip
import hashlib
import os
import re
import sys

SPAN = re.compile(r'<untrusted_tool_result>(.*?)</untrusted_tool_result>', re.S)


def stub(m):
    body = m.group(1)
    if body.startswith('[omitted third-party tool output'):
        return m.group(0)
    raw = body.encode('utf-8')
    return ('<untrusted_tool_result>[omitted third-party tool output: '
            f'{len(raw)} bytes, sha256 {hashlib.sha256(raw).hexdigest()}]</untrusted_tool_result>')


def main(root):
    files = spans = 0
    for dirpath, _, names in os.walk(root):
        for name in names:
            path = os.path.join(dirpath, name)
            raw = open(path, 'rb').read()
            gz = name.endswith('.gz')
            text = (gzip.decompress(raw) if gz else raw).decode('utf-8')
            new, n = SPAN.subn(stub, text)
            if n and new != text:
                out = new.encode('utf-8')
                open(path, 'wb').write(gzip.compress(out, mtime=0) if gz else out)
                files += 1
                spans += n
    print(f'files_changed={files} spans={spans}')


if __name__ == '__main__':
    main(sys.argv[1])
