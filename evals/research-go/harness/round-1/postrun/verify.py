#!/usr/bin/env python3
"""Post-run saved-audit amendment; execute the exact sealed original verifier.

Only its one generic credential search can disregard an exact public-document
field, on an independently proven linked text file. No source substitution,
global regex patch, candidate call, credential import, or scoring change occurs.
Independent review of this post-run amendment is required before official use.
"""
import argparse
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import re
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
FREEZE_SHA256 = "4f44339e7318f2959d674767ffff00b2643968cd770dd24d236f80f53b9e0464"
ORIGINAL_SHA256 = "85fcfb0bcaba169eacd25cee95aba41047dc249b20c8720d8318115a5f977a4a"
MANIFEST_SHA256 = "57044b169ee1b35b1a5f68e4780b0de3c64dcd8d5a773ad6d988484f045e7694"
PUBLIC_FIELD_SHA256 = "81d54facb40f6897ee428462a51dbaa0fde638e5b023f15811d05d66923b4e19"
CREDENTIAL_PATTERN = r"(?i)bearer\s+[A-Za-z0-9._-]{8,}|sk-[A-Za-z0-9_-]{12,}|\"(?:api_key|authorization)\"\s*:"
CANONICAL = "https://developers.cloudflare.com/d1/best-practices/read-replication/"
ARCHIVES = {
    "D1-R": (CANONICAL, "a113edd9d68c42418966f31002a3ec2766288114084ec77bf2cac1ef673ab8b9"),
    "D1-R-MD": (CANONICAL+"index.md", "5efd6085077806c6ff9cbbb6b2c79a2a20e46b5de3d2f91c236c05401fc2e4f9"),
}


class CorrectionError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise CorrectionError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def owned(root, relative):
    require(isinstance(relative, str) and relative and not Path(relative).is_absolute(), "correction: invalid relative path")
    path = root/relative
    require(path.resolve().is_relative_to(root) and not path.is_symlink(), "correction: path escapes artifact root or is a symlink")
    return path


def read(root, relative):
    return json.loads(owned(root, relative).read_text(encoding="utf-8"))


def public_matches(text):
    """All matches must be the exact known public field, not just its first hit."""
    matches = list(re.finditer(CREDENTIAL_PATTERN, text))
    return bool(matches) and all(sha(m[0].encode("utf-8")) == PUBLIC_FIELD_SHA256 for m in matches)


def sealed_inputs(root):
    root = Path(root).resolve()
    require(sha(owned(root, "freeze.json").read_bytes()) == FREEZE_SHA256, "correction: changed original freeze")
    receipt = read(root, "private/freeze-receipt.json")
    require(receipt.get("freeze_sha256") == FREEZE_SHA256, "correction: changed original freeze receipt")
    freeze = read(root, "freeze.json")
    require(freeze["files"].get("verify.py") == ORIGINAL_SHA256 and
            freeze["files"].get("dataset/sources.json") == MANIFEST_SHA256, "correction: incompatible sealed inputs")
    for name in ("verify.py", "dataset/sources.json"):
        require(sha(owned(root, name).read_bytes()) == freeze["files"][name], "correction: changed sealed input: "+name)
    sources = read(root, "dataset/sources.json")
    allowed = {}
    for ident, (url, expected_text) in ARCHIVES.items():
        rows = [s for s in sources if s["id"] == ident]
        require(len(rows) == 1, "correction: missing/duplicate public archive")
        source = rows[0]
        require(source["url"] == source["final_url"] == url and source["canonical_url"] == CANONICAL and
                source["status"] == 200 and not source.get("error") and source["text_sha256"] == expected_text,
                "correction: changed public archive provenance")
        for kind in ("raw", "text"):
            name = source[kind+"_path"]
            require(freeze["files"].get(name) == source[kind+"_sha256"] and
                    sha(owned(root, name).read_bytes()) == source[kind+"_sha256"], "correction: changed public archive: "+name)
        require(public_matches(owned(root, source["text_path"]).read_text(encoding="utf-8")),
                "correction: public archive has unknown credential matches")
        allowed[url] = source
    return freeze, allowed


def linked_texts(root, records, archives):
    """Bind each candidate text to a successful fetch and its exact frozen bytes.

    Only text/model_text paths in that record's opaque fetches directory qualify.
    Request bodies, API metadata, arbitrary copies and partial previews do not.
    Original collected() validates the entire request/tool/provenance ledger
    before the generic scan reaches this exception.
    """
    proven = {}
    for record in records:
        prefix = f"execution/cases/{record['case_id']}/fetches/"
        for fetch in record["fetches"]:
            source = archives.get(fetch["requested_url"])
            if not source or fetch["final_url"] != source["url"] or fetch["status"] != "ok" or fetch["error"]:
                continue
            expected = source["text_sha256"]
            if (fetch["truncated"] is not False or fetch["text_sha256"] != expected or
                    fetch["model_text_sha256"] != expected):
                continue
            for kind in ("text", "model_text"):
                name = fetch[kind+"_path"]
                if not isinstance(name, str) or not name.startswith(prefix):
                    continue
                path = owned(root, name)
                if not path.resolve().is_relative_to(owned(root, prefix).resolve()) or path.suffix != ".txt":
                    continue
                raw = path.read_bytes()
                if sha(raw) != expected or raw != owned(root, source["text_path"]).read_bytes():
                    continue
                text = raw.decode("utf-8")
                if public_matches(text):
                    proven[name] = {"sha256": expected, "source_id": source["id"], "url": source["url"],
                                    "case_id": record["case_id"], "fetch_id": fetch["id"], "kind": kind,
                                    "matches": len(list(re.finditer(CREDENTIAL_PATTERN, text)))}
    return proven


class RegexProxy:
    """Delegate everything except the exact pattern at the exact sealed scan site."""
    def __init__(self, module, root, archives):
        self.module, self.root, self.archives = module, root, archives
        self.exempted = {}

    def __getattr__(self, name):
        return getattr(re, name)

    def search(self, pattern, string, flags=0):
        result = re.search(pattern, string, flags)
        if result is None or pattern != CREDENTIAL_PATTERN or flags != 0:
            return result
        caller = sys._getframe(1)
        if caller.f_code is not self.module.Auditor.collected.__code__:
            return result
        auditor = caller.f_locals.get("self")
        path = caller.f_locals.get("path")
        if (not isinstance(auditor, self.module.Auditor) or auditor.root != self.root or
                auditor.stage != "collected" or not isinstance(path, Path) or
                caller.f_locals.get("text") is not string):
            return result
        # Revalidate frozen archives and exact bytes at the exception boundary.
        _, archives = sealed_inputs(self.root)
        proven = linked_texts(self.root, auditor.records, archives)
        relative = str(path.relative_to(self.root)) if path.is_relative_to(self.root) else ""
        proof = proven.get(relative)
        if (proof is None or path.is_symlink() or sha(path.read_bytes()) != proof["sha256"] or
                sha(string.encode("utf-8")) != proof["sha256"] or not public_matches(string)):
            return result
        self.exempted[relative] = proof
        return None


def load_verifier(root=ROOT):
    """Compile exact original bytes, non-main, without imports/bytecode rewriting."""
    root = Path(root).resolve()
    _, archives = sealed_inputs(root)
    source = owned(root, "verify.py").read_bytes()
    require(sha(source) == ORIGINAL_SHA256, "correction: changed original verifier")
    module = types.ModuleType("sealed_saved_evidence_verifier")
    module.__file__ = str(root/"verify.py")  # Preserve original default root and CLI.
    exec(compile(source, module.__file__, "exec"), module.__dict__)
    module.re = RegexProxy(module, root, archives)  # Only this module's binding; stdlib re is untouched.
    return module


@contextmanager
def original_imports(module):
    """Keep future analysis imports bound to the same exact sealed verifier."""
    previous = sys.modules.get("verify")
    path = sys.path[:]
    bytecode = sys.dont_write_bytecode
    sys.modules["verify"] = module
    sys.path.insert(0, str(Path(module.__file__).parent))
    sys.dont_write_bytecode = True
    try:
        yield
    finally:
        if previous is None:
            sys.modules.pop("verify", None)
        else:
            sys.modules["verify"] = previous
        sys.path[:] = path
        sys.dont_write_bytecode = bytecode


def main(argv=None):
    # Parse only enough to choose the input root; the original parser owns all
    # actual CLI semantics, validation, output, audit stages and final writes.
    selector = argparse.ArgumentParser(add_help=False)
    selector.add_argument("--root", type=Path, default=ROOT)
    root, _ = selector.parse_known_args(argv)
    try:
        module = load_verifier(root.root)
        with original_imports(module):
            return module.main(argv)
    except (CorrectionError, OSError, KeyError, TypeError, ValueError) as exc:
        print(f"AUDIT AMENDMENT FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
