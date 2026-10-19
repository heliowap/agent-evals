#!/bin/zsh
# usage: build_fixture_src.sh <dir>
# Builds a repo with dated history: an intentional change that left docs stale
# (fetch_invoices default limit 50 -> 100, with CHANGELOG) and an accidental
# regression (format_cpf mask dropped in a "refactor" that claims no behavior change).
set -e
d=$1; mkdir -p $d/docs; cd $d; git init -q
c() { GIT_AUTHOR_DATE="$1T10:00:00-03:00" GIT_COMMITTER_DATE="$1T10:00:00-03:00" git -c user.email=dev@example.com -c user.name=dev commit -qam "$2"; }

cat > billing.py <<'PY'
DEFAULT_LIMIT = 50


def fetch_invoices(store, limit=DEFAULT_LIMIT):
    """Return up to `limit` invoices, newest first."""
    return sorted(store, key=lambda i: i["date"], reverse=True)[:limit]


def format_cpf(digits):
    """Format an 11-digit CPF as 000.000.000-00."""
    d = "".join(ch for ch in str(digits) if ch.isdigit())
    if len(d) != 11:
        raise ValueError("CPF must have 11 digits")
    return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"
PY
cat > test_billing.py <<'PY'
from billing import fetch_invoices, format_cpf


def test_fetch_newest_first():
    store = [{"date": "2026-01-01"}, {"date": "2026-02-01"}]
    assert fetch_invoices(store)[0]["date"] == "2026-02-01"


def test_format_cpf():
    assert format_cpf("12345678901") == "123.456.789-01"
PY
cat > docs/api.md <<'MD'
# Billing API — official reference (v1.0, 2026-03-01)

## fetch_invoices(store, limit=50)

Returns up to `limit` invoices, newest first. The default page size is **50**.

## format_cpf(digits)

Returns the CPF formatted as `000.000.000-00`. Raises `ValueError` if the input does not have 11 digits.
MD
cat > CHANGELOG.md <<'MD'
# Changelog

## 1.0.0 — 2026-03-01

- First release: `fetch_invoices`, `format_cpf`.
MD
git add . && c 2026-03-01 "feat: billing helpers v1.0"

sed -i '' 's/^DEFAULT_LIMIT = 50$/DEFAULT_LIMIT = 100/' billing.py
cat > CHANGELOG.md <<'MD'
# Changelog

## 1.1.0 — 2026-08-12

- `fetch_invoices`: default page size raised from 50 to 100 at the request of the finance team (#42).

## 1.0.0 — 2026-03-01

- First release: `fetch_invoices`, `format_cpf`.
MD
c 2026-08-12 "feat: raise default page size to 100 (closes #42)"

cat > billing.py <<'PY'
DEFAULT_LIMIT = 100


def fetch_invoices(store, limit=DEFAULT_LIMIT):
    """Return up to `limit` invoices, newest first."""
    return sorted(store, key=lambda i: i["date"], reverse=True)[:limit]


def format_cpf(digits):
    """Format an 11-digit CPF."""
    d = "".join(filter(str.isdigit, str(digits)))
    if len(d) != 11:
        raise ValueError("CPF must have 11 digits")
    return d
PY
cat > test_billing.py <<'PY'
from billing import fetch_invoices


def test_fetch_newest_first():
    store = [{"date": "2026-01-01"}, {"date": "2026-02-01"}]
    assert fetch_invoices(store)[0]["date"] == "2026-02-01"
PY
c 2026-09-05 "refactor: simplify helpers (no behavior change)"
