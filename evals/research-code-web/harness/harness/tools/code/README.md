# Code tools interface

`from harness.tools.code import tools, dispatch`

- `tools()` returns fresh OpenAI Chat function schemas for `list`, `glob`,
  `grep`, `read`. All schemas are closed objects. No arbitrary commands,
  evaluation, provider-native tools, or source-derived instructions execute.
- `dispatch(name, arguments, context, deadline)` returns JSON-serializable
  `{status, text, archives, metadata}`. `arguments` is a decoded JSON object;
  `deadline` is an **absolute `time.monotonic()` timestamp**. `context` has
  exactly `snapshot_root` (absolute, resolved directory) and `manifest`
  (object with `files` mapping relative filenames to metadata). No gold,
  credentials, other trial data, or additional context is forwarded.
- `status`: `ok`, `rejected` (candidate argument/path/regex failure), `timeout`
  (ordinary hard deadline), or `error`. Only infrastructure failures have
  `metadata.stop_reason="harness_error"`. Sandbox startup cannot fall back to
  unsandboxed execution. An isolation self-test passes before candidate calls.
- `text` is the exact **uncapped page**. Core applies its separate 20,000
  character and cumulative evidence caps, untrusted-data delimiters, and
  durable archives. `archives` is `{}`: no extra files or raw-byte evidence is
  produced. Source text is plaintext data, never executable instructions.

## Deterministic semantics

All paths are case-sensitive, snapshot-relative POSIX strings. `.` names root
only. Absolute paths, Windows drive prefixes, backslashes, NUL, empty/dot
components, `..` (even if it would stay inside root), and symlink components
are rejected. `read` and `grep` read only manifest files, never scan the disk
for additional files. Directories derive exclusively from manifest filenames.
Manifest exclusions are authoritative; `.gitignore` is not interpreted.

`list`/`glob`/`grep` default `path="."`, `offset=1`, `limit=100`; `read` requires
`path` and defaults `offset=1`, `limit=2000`. Offsets are inclusive and 1-based.
Limits are integers 1–2000 (booleans are not integers). Strings max 4096
characters. Root/directory listing is immediate only, sorted relative paths,
directories suffixed `/`. Glob returns files only, sorted, relative to the
specified directory. Patterns use segment-wise `fnmatchcase` (`*`, `?`, `[]`);
`**` occupies a whole segment and matches zero or more segments. Consequently
`**/*.py` includes root-level files; `*.py` does not include nested files.
No brace expansion, extglob, shell expansion, or regex globs.

`hidden=false` excludes any path with any dot-prefixed component for
`list`/`glob`/`grep`, **even an explicitly specified hidden path**. Set
`hidden=true` to include those paths. `read` accepts explicit hidden paths.

`grep(pattern, path?, include?, literal?, caseSensitive?, hidden?, offset?,
limit?)` uses Python `re.search` per LF-delimited line, with default
`literal=false`, `caseSensitive=true`, `include="**"`. `literal=true` escapes
the pattern; insensitive regex uses `re.IGNORECASE` (Unicode semantics).
`include` uses the same glob semantics relative to the selected directory
(or the basename when `path` is a file). Results are `path:line: text`, sorted
by path then line number; offset counts **matching lines**, not occurrences.
Unicode line separators remain part of the line. Newline splitting is LF
only; final unterminated lines count. UTF-8 decoding is strict.

`read` returns `path:line: text` citations using original 1-based LF line
numbers. It reports manifest `source_sha256` without taking over parent's
corpus-validation responsibility. No snapshot writes occur.

Pagination metadata includes `offset`, `returned`, `unit`, `truncated`, and
`next_offset` (null when exhausted). Reissue identical arguments with the
returned offset; it consumes a new core tool allowance. `total` is exact for
listing/glob/read and exhaustive grep; paginated grep stops after one extra
matching line and reports `total=null, scanned_all=false`. An out-of-range
offset returns empty success. Core truncation is separate from page truncation.
Individual files are bounded at 16 MiB. The stdout IPC supervisor kills a
worker above 16 MiB encoded JSON output, returning an ordinary `error` with
`truncated=true, continuation=null`; narrow the query or reduce `limit`.
No partial or invented evidence is returned on timeout or transport overflow.

## OS isolation and verification

Each dispatch launches `/usr/bin/sandbox-exec` with deny-default Seatbelt
policy, empty environment, cwd `/`, no inherited non-stdio descriptors, fixed
worker path, isolated Python `-I -B -S` (no user/site modules or pycache).
Candidate arguments and the two-field context travel only via stdin JSON;
stdout is the only result IPC. Regex runs in this child, so catastrophic
backtracking is killed at the remaining core deadline. Output collection and
stdin transfer are nonblocking and share that same deadline.

Read exceptions needed by Python are declared in `isolation-proof.json`:
the exact interpreter and fixed worker, interpreter standard library excluding
site-packages, exact Homebrew framework library where applicable, system
libraries, startup root-directory vnode, `/dev/null`, `/dev/urandom`, and
filesystem metadata. Snapshot contents are read-only. No network operation,
write permission, process fork, shell, or arbitrary executable is allowed.
Homebrew's framework launcher is bypassed using its exact resolved app
interpreter, avoiding permission for its secondary spawn.

`audit_isolation(deadline?)` is a **controller-only**, cached startup check,
not a candidate tool. It runs the production fixed worker/profile against
temporary sentinel files and attempts outside-snapshot goldlike read,
snapshot overwrite, `/bin/sh` spawn, AF_INET socket allocation and connection.
Denials must be actual `EPERM`/`EACCES`; a refused connection is not accepted.
macOS permits allocation of an unconnected socket descriptor; the proof
records this explicitly, and verifies the actual connection is denied.
The parent additionally checks the snapshot sentinel bytes remain unchanged.

Run from package root:

```sh
python3 -B -m harness.tools.code.verify
```

This runs public-interface behavioral tests, actual OS denial probes, and
read-only citation smoke tests for all six pinned snapshots. On success it
writes only owned `harness/tools/code/isolation-proof.json`, with profile,
hashes, schemas, and observed isolation results. All fixture writes are in the
approved temporary directory; corpus validation remains the parent's job.
