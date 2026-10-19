"""Fail if anything in a directory still carries a local identifier or a secret.

usage: python3 -I tools/scan.py [DIR ...]   (default: the repository root)

Reads .gz files too. Exits 1 on findings; prints file, rule and a masked match.
Also reports files over 50 MB, which GitHub rejects past 100 MB.
"""
import gzip
import ipaddress
import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from anonymize import CGNAT, MAC_TMP, DOC_IPS, FAKE_SECRETS, IPV4, SECRET_PATTERNS, load_config  # noqa: E402

LIMIT = 50 * 1024 * 1024


def rules(cfg):
    keep = [re.escape(k) for k in cfg.get('keep', [])]
    out = [(f'private:{i}', re.compile(re.escape(old), re.I)) for i, (old, _) in enumerate(cfg['replace'])]
    out += [(f'private-ip:{i}', re.compile(re.escape(ip))) for i, ip in enumerate(cfg.get('ips', []))]
    out += [('secret', re.compile(p)) for p in SECRET_PATTERNS]
    out += [('mac-tmpdir', MAC_TMP)]
    out += [('home-path', re.compile(r'/Users/[A-Za-z0-9._-]+|/home/(?!user\b)[A-Za-z0-9._-]+'))]
    return out, re.compile('|'.join(keep)) if keep else None


def main():
    cfg = load_config()
    checks, keep = rules(cfg)
    roots = sys.argv[1:] or [os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]
    findings = 0
    for top in roots:
        for root, dirs, files in os.walk(top):
            dirs[:] = [d for d in dirs if d != '.git']
            for f in files:
                path = os.path.join(root, f)
                if os.path.getsize(path) > LIMIT:
                    print(f'{path}: size {os.path.getsize(path) >> 20} MB')
                    findings += 1
                raw = open(path, 'rb').read()
                if f.endswith('.gz'):
                    raw = gzip.decompress(raw)
                text = raw.decode('utf-8', 'replace')
                text = keep.sub('', text) if keep else text
                for name, rx in checks:
                    for m in rx.finditer(text):
                        if name == 'secret' and FAKE_SECRETS.match(m.group(0)):
                            continue
                        print(f'{path}: {name}: {m.group(0)[:6]}…')
                        findings += 1
                        break
                for m in IPV4.finditer(text):
                    try:
                        a = ipaddress.ip_address(m.group(0))
                    except ValueError:
                        continue
                    if a in CGNAT and m.group(0) not in DOC_IPS:
                        print(f'{path}: cgnat-ip')
                        findings += 1
                        break
    print(f'findings={findings}')
    sys.exit(1 if findings else 0)


if __name__ == '__main__':
    main()
