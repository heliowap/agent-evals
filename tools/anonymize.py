"""Copy an eval's raw data into this repository with local identifiers and secrets removed.

usage: python3 -I tools/anonymize.py SRC DST [--exclude GLOB ...] [--gzip-over BYTES]

Text files are rewritten; binary files are skipped and listed. Machine-specific
strings (home path, user name, host name, private IPs) come from a private
config file that is never committed (default ~/.config/agent-evals-anon.json,
override with AGENT_EVALS_ANON). Session IDs are replaced by salted hashes so
runs stay linkable inside the dataset without matching the local database.
"""
import argparse
import fnmatch
import gzip
import hashlib
import hmac
import ipaddress
import json
import os
import re
import sys

ALWAYS_EXCLUDE = [
    '.git', '.venv', 'venv', 'node_modules', '.ruff_cache', '__pycache__', '.pytest_cache',
    '.cache', '.DS_Store', '*.pyc', '*.db', '*.db-*', '*.sqlite', '*.sqlite3',
    'opencode.json', 'opencode.jsonc', 'auth.json', '.env', '.env.*', '*.pem', '*.key',
]
SECRET_PATTERNS = [
    r'(?<![A-Za-z0-9])sk-(?:ant-|or-v1-|proj-)?[A-Za-z0-9_-]{20,}',
    r'(?<![A-Za-z0-9])mrl_[A-Za-z0-9_-]{16,}',
    r'(?<![A-Za-z0-9])gh[opsu]_[A-Za-z0-9]{30,}',
    r'(?<![A-Za-z0-9])github_pat_[A-Za-z0-9_]{30,}',
    r'(?<![A-Za-z0-9])AKIA[0-9A-Z]{16}',
    r'(?<![A-Za-z0-9])AIza[0-9A-Za-z_-]{35}',
    r'(?<![A-Za-z0-9])xox[abprs]-[A-Za-z0-9-]{10,}',
    r'-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----',
    r'(?<=Bearer )(?![$<{])[A-Za-z0-9._~+/=-]{24,}',
]
FAKE_SECRETS = re.compile(r'sk-(?:123456|SYNTHE|mock|test|fake|xxx|ant-api03-x{4})', re.I)
SESSION = re.compile(r'\bses_[A-Za-z0-9]{20,}\b')
MAC_TMP = re.compile(r'/(?:var|tmp)/folders/[A-Za-z0-9_+-]{2}/[A-Za-z0-9_+-]{20,}')
IPV4 = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
CGNAT = ipaddress.ip_network('100.64.0.0/10')
DOC_IPS = {'100.64.0.0', '100.64.0.1'}


def load_config():
    path = os.environ.get('AGENT_EVALS_ANON', os.path.expanduser('~/.config/agent-evals-anon.json'))
    cfg = json.load(open(path))
    cfg['replace'].sort(key=lambda kv: -len(kv[0]))
    return cfg


def scrubber(cfg):
    salt = cfg['salt'].encode()
    secrets = re.compile('|'.join(f'(?:{p})' for p in SECRET_PATTERNS))
    keep = {k: f'\x00KEEP{i}\x00' for i, k in enumerate(cfg.get('keep', []))}
    private_ips = set(cfg.get('ips', []))

    def secret(m):
        return m.group(0) if FAKE_SECRETS.match(m.group(0)) else '<REDACTED_SECRET>'

    def session(m):
        return 'ses_' + hmac.new(salt, m.group(0).encode(), hashlib.sha256).hexdigest()[:20]

    def ip(m):
        s = m.group(0)
        try:
            a = ipaddress.ip_address(s)
        except ValueError:
            return s
        if s in private_ips or (a in CGNAT and s not in DOC_IPS):
            return '<REDACTED_IP>'
        return s

    def scrub(text):
        for k, token in keep.items():
            text = text.replace(k, token)
        for old, new in cfg['replace']:
            text = re.sub(re.escape(old), new, text, flags=re.I)
        text = secrets.sub(secret, text)
        text = SESSION.sub(session, text)
        text = MAC_TMP.sub('/tmp/folders', text)
        text = IPV4.sub(ip, text)
        for k, token in keep.items():
            text = text.replace(token, k)
        return text
    return scrub


def excluded(rel, patterns):
    parts = rel.split(os.sep)
    return any(fnmatch.fnmatch(p, g) for p in parts for g in patterns) or \
        any(fnmatch.fnmatch(rel, g) for g in patterns)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('dst')
    ap.add_argument('--exclude', action='append', default=[])
    ap.add_argument('--gzip-over', type=int, default=0, help='gzip text files larger than this many bytes')
    a = ap.parse_args()
    cfg = load_config()
    scrub = scrubber(cfg)
    patterns = ALWAYS_EXCLUDE + a.exclude
    skipped, written = [], 0
    for root, dirs, files in os.walk(a.src):
        rel_root = os.path.relpath(root, a.src)
        dirs[:] = sorted(d for d in dirs if not excluded(os.path.normpath(os.path.join(rel_root, d)), patterns))
        for f in sorted(files):
            rel = os.path.normpath(os.path.join(rel_root, f))
            if excluded(rel, patterns) or os.path.islink(os.path.join(root, f)):
                continue
            raw = open(os.path.join(root, f), 'rb').read()
            if rel.endswith('.gz'):
                try:
                    raw, rel = gzip.decompress(raw), rel[:-3]
                except OSError:
                    skipped.append(rel)
                    continue
            try:
                text = raw.decode('utf-8')
            except UnicodeDecodeError:
                skipped.append(rel)
                continue
            out = scrub(text).encode()
            out_rel = scrub(rel)
            if a.gzip_over and len(out) > a.gzip_over:
                out, out_rel = gzip.compress(out, mtime=0), out_rel + '.gz'
            dest = os.path.join(a.dst, out_rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            open(dest, 'wb').write(out)
            written += 1
    print(f'written={written} skipped_binary={len(skipped)}')
    for s in skipped:
        print('  skipped', s, file=sys.stderr)


if __name__ == '__main__':
    main()
