from textwrap import dedent

from .domain import TaskSpec


def source(value: str) -> str:
    return dedent(value).lstrip("\n")


def task(identifier, phase, family, request, files, reference, acceptance, structural=None):
    files = {path: source(value) for path, value in files.items()}
    files["src/__init__.py"] = ""
    files["README.md"] = (
        "# Service component\n\n" + request + "\n\n"
        "Run `python3 checks/public.py` from the project root. "
        "Implementation belongs in src/. Add checks under checks/.\n"
    )
    files["checks/public.py"] = (
        "import os, sys\nsys.path.insert(0, os.getcwd())\n" + files["checks/public.py"]
    )
    return TaskSpec(identifier, phase, family, "python", request, files,
                    {p: source(v) for p, v in reference.items()},
                    "import os, sys\nsys.path.insert(0, os.getcwd())\n" + source(acceptance),
                    ("src/", "checks/"), source(structural) if structural else None)


IMPORT = task(
    "py-atomic-import", "screening", "feature",
    "Add import_contacts(connection, rows) in src/service.py and expose it through "
    "src/api.py.handle_import. Each row has exactly email and name strings. Trim both; "
    "email must contain exactly one @, with nonempty sides and no whitespace. Normalize "
    "email to lowercase; name must remain nonempty. Reject non-object rows, unknown or "
    "missing fields and duplicate normalized emails within a batch using ValueError. "
    "Validate the complete batch before writing. Insert new contacts and update names "
    "for existing emails, returning {'inserted': N, 'updated': N}; count an existing "
    "email as updated even when its name is unchanged. Empty batches return zero counts. "
    "Any validation or database failure must leave all contacts unchanged. The API "
    "receives {'contacts': [...]}, rejects malformed envelopes with ValueError and returns "
    "the summary. Preserve add_contact, list_contacts and the existing API. Start in "
    "src/service.py, src/repository.py and src/api.py. Connections are idle at entry.",
    {
        "src/repository.py": '''
            def initialize(connection):
                connection.execute("CREATE TABLE contacts (email TEXT PRIMARY KEY, name TEXT NOT NULL)")
                connection.commit()

            def list_contacts(connection):
                return connection.execute("SELECT email, name FROM contacts ORDER BY email").fetchall()

            def put_contact(connection, email, name):
                connection.execute("INSERT INTO contacts VALUES (?, ?) ON CONFLICT(email) DO UPDATE SET name=excluded.name", (email, name))
        ''',
        "src/service.py": '''
            from .repository import put_contact

            def add_contact(connection, email, name):
                with connection:
                    put_contact(connection, email, name)

            def import_contacts(connection, rows):
                raise NotImplementedError("Batch imports are unavailable")
        ''',
        "src/api.py": '''
            from .service import add_contact

            def handle_add(connection, payload):
                add_contact(connection, payload["email"], payload["name"])
                return {"ok": True}

            def handle_import(connection, payload):
                raise NotImplementedError("Batch endpoint is unavailable")
        ''',
        "checks/public.py": '''
            import sqlite3
            from src.repository import initialize, list_contacts
            from src.api import handle_add
            c = sqlite3.connect(":memory:")
            initialize(c)
            assert handle_add(c, {"email": "a@b", "name": "Alice"}) == {"ok": True}
            assert list_contacts(c) == [("a@b", "Alice")]
        ''',
    },
    {
        "src/service.py": '''
            from .repository import put_contact

            def add_contact(connection, email, name):
                with connection:
                    put_contact(connection, email, name)

            def import_contacts(connection, rows):
                if not isinstance(rows, list):
                    raise ValueError("contacts must be a list")
                clean, seen = [], set()
                for row in rows:
                    if not isinstance(row, dict) or set(row) != {"email", "name"}:
                        raise ValueError("invalid contact")
                    if not all(isinstance(row[key], str) for key in ("email", "name")):
                        raise ValueError("contact fields must be strings")
                    email, name = row["email"].strip().lower(), row["name"].strip()
                    if email.count("@") != 1 or not all(email.split("@")) or any(ch.isspace() for ch in email) or not name:
                        raise ValueError("invalid contact values")
                    if email in seen:
                        raise ValueError("duplicate email")
                    seen.add(email)
                    clean.append((email, name))
                inserted = updated = 0
                with connection:
                    for email, name in clean:
                        exists = connection.execute("SELECT 1 FROM contacts WHERE email=?", (email,)).fetchone()
                        put_contact(connection, email, name)
                        if exists:
                            updated += 1
                        else:
                            inserted += 1
                return {"inserted": inserted, "updated": updated}
        ''',
        "src/api.py": '''
            from .service import add_contact, import_contacts

            def handle_add(connection, payload):
                add_contact(connection, payload["email"], payload["name"])
                return {"ok": True}

            def handle_import(connection, payload):
                if not isinstance(payload, dict) or set(payload) != {"contacts"}:
                    raise ValueError("invalid import envelope")
                return import_contacts(connection, payload["contacts"])
        ''',
    },
    '''
        import sqlite3
        from src.repository import initialize, list_contacts
        from src.api import handle_import
        c = sqlite3.connect(":memory:")
        initialize(c)
        c.execute("INSERT INTO contacts VALUES ('old@x', 'Old')")
        c.commit()
        assert handle_import(c, {"contacts": [{"email": " NEW@X ", "name": " New "}, {"email": "old@x", "name": "Changed"}]}) == {"inserted": 1, "updated": 1}
        assert list_contacts(c) == [("new@x", "New"), ("old@x", "Changed")]
        assert handle_import(c, {"contacts": []}) == {"inserted": 0, "updated": 0}
        assert handle_import(c, {"contacts": [{"email": "OLD@X", "name": "Changed"}]}) == {"inserted": 0, "updated": 1}
        invalid = [None, {}, "text", [None], [{"email": "a@x"}], [{"email": "a@x", "name": "A", "extra": 1}], [{"email": "a b@x", "name": "A"}], [{"email": "a@@x", "name": "A"}], [{"email": "@x", "name": "A"}], [{"email": "x@", "name": "A"}], [{"email": 1, "name": "A"}], [{"email": "a@x", "name": " "}], [{"email": "A@x", "name": "A"}, {"email": " a@X ", "name": "B"}], [{"email": "temp@x", "name": "T"}, {"email": "bad", "name": "B"}]]
        for rows in invalid:
            before = list_contacts(c)
            try:
                handle_import(c, {"contacts": rows})
            except ValueError:
                pass
            else:
                raise AssertionError("invalid batch accepted")
            assert list_contacts(c) == before
        for payload in [None, [], {}, {"contacts": [], "extra": 1}]:
            try:
                handle_import(c, payload)
            except ValueError:
                pass
            else:
                raise AssertionError("invalid envelope accepted")
        c.execute("CREATE TRIGGER reject_blocked BEFORE INSERT ON contacts WHEN NEW.email='blocked@x' BEGIN SELECT RAISE(ABORT, 'blocked'); END")
        c.commit()
        before = list_contacts(c)
        try:
            handle_import(c, {"contacts": [{"email": "old@x", "name": "Wrong"}, {"email": "other@x", "name": "Other"}, {"email": "blocked@x", "name": "B"}]})
        except sqlite3.DatabaseError:
            pass
        else:
            raise AssertionError("database error swallowed")
        assert list_contacts(c) == before
    ''',
)


TRANSFER = task(
    "py-transfer-commit", "screening", "effects",
    "Fix transfer(connection, publisher, source, target, amount) in src/service.py. "
    "A successful transfer debits and credits exactly once, appends one ledger row, "
    "commits, then publishes {'source': source, 'target': target, 'amount': amount}. "
    "source and target must differ and exist; amount is a positive integer, excluding "
    "bool, and cannot exceed the source balance. Invalid transfers raise ValueError "
    "without writes or publication. Database failure at any statement or commit "
    "rolls back all changes and never publishes. Publication failure propagates after "
    "the committed transfer and must not undo it. Caller connections are idle at entry. "
    "Keep balance reads and account setup intact. Start in src/service.py and src/repository.py.",
    {
        "src/repository.py": '''
            def initialize(connection):
                connection.executescript("CREATE TABLE accounts(id TEXT PRIMARY KEY, balance INTEGER NOT NULL); CREATE TABLE ledger(source TEXT, target TEXT, amount INTEGER);")
                connection.commit()

            def balance(connection, account):
                row = connection.execute("SELECT balance FROM accounts WHERE id=?", (account,)).fetchone()
                return None if row is None else row[0]

            def move(connection, source, target, amount):
                connection.execute("UPDATE accounts SET balance=balance-? WHERE id=?", (amount, source))
                connection.execute("UPDATE accounts SET balance=balance+? WHERE id=?", (amount, target))
                connection.execute("INSERT INTO ledger VALUES (?, ?, ?)", (source, target, amount))
        ''',
        "src/service.py": '''
            from .repository import move

            def transfer(connection, publisher, source, target, amount):
                publisher.publish({"source": source, "target": target, "amount": amount})
                move(connection, source, target, amount)
                connection.commit()
        ''',
        "src/events.py": '''
            class Recorder:
                def __init__(self):
                    self.events = []

                def publish(self, event):
                    self.events.append(event.copy())
        ''',
        "checks/public.py": '''
            import sqlite3
            from src.repository import initialize, balance
            from src.service import transfer
            from src.events import Recorder
            c = sqlite3.connect(":memory:")
            initialize(c)
            c.executemany("INSERT INTO accounts VALUES (?, ?)", [("a", 100), ("b", 20)])
            c.commit()
            p = Recorder()
            transfer(c, p, "a", "b", 10)
            assert (balance(c, "a"), balance(c, "b")) == (90, 30)
            assert p.events == [{"source": "a", "target": "b", "amount": 10}]
        ''',
    },
    {"src/service.py": '''
        from .repository import move, balance

        def transfer(connection, publisher, source, target, amount):
            available, destination = balance(connection, source), balance(connection, target)
            if type(amount) is not int or amount <= 0 or source == target or available is None or destination is None or amount > available:
                raise ValueError("invalid transfer")
            with connection:
                move(connection, source, target, amount)
            publisher.publish({"source": source, "target": target, "amount": amount})
    '''},
    '''
        import sqlite3, tempfile
        from src.repository import initialize, balance
        from src.service import transfer
        from src.events import Recorder

        def setup(c):
            initialize(c)
            c.executemany("INSERT INTO accounts VALUES (?, ?)", [("a", 100), ("b", 20)])
            c.commit()

        def state(c):
            return (balance(c, "a"), balance(c, "b"), c.execute("SELECT * FROM ledger").fetchall())

        c = sqlite3.connect(":memory:")
        setup(c)
        p = Recorder()
        for args in [("a", "b", 0), ("a", "b", -1), ("a", "b", True), ("a", "b", 1.5), ("a", "b", "1"), ("a", "a", 1), ("a", "missing", 1), ("missing", "b", 1), ("a", "b", 101)]:
            try:
                transfer(c, p, *args)
            except ValueError:
                pass
            else:
                raise AssertionError("invalid transfer accepted")
            assert state(c) == (100, 20, [])
            assert p.events == []
        c.execute("CREATE TRIGGER reject_ledger BEFORE INSERT ON ledger BEGIN SELECT RAISE(ABORT, 'ledger failure'); END")
        c.commit()
        try:
            transfer(c, p, "a", "b", 10)
        except sqlite3.DatabaseError:
            pass
        else:
            raise AssertionError("ledger failure swallowed")
        assert state(c) == (100, 20, [])
        assert p.events == []
        c.execute("DROP TRIGGER reject_ledger")
        c.commit()
        transfer(c, p, "a", "b", 100)
        assert state(c) == (0, 120, [("a", "b", 100)])
        assert p.events == [{"source": "a", "target": "b", "amount": 100}]
        with tempfile.TemporaryDirectory() as directory:
            path = directory + "/accounts.db"
            disk = sqlite3.connect(path)
            setup(disk)
            class FailingPublisher:
                def publish(self, event):
                    observer = sqlite3.connect(path)
                    assert state(observer) == (85, 35, [("a", "b", 15)])
                    observer.close()
                    raise RuntimeError("publication failed")
            try:
                transfer(disk, FailingPublisher(), "a", "b", 15)
            except RuntimeError as exc:
                assert str(exc) == "publication failed"
            else:
                raise AssertionError("publication failure swallowed")
            assert state(disk) == (85, 35, [("a", "b", 15)])
            disk.close()
        failing = sqlite3.connect(":memory:")
        setup(failing)
        failing.execute("PRAGMA foreign_keys=ON")
        failing.executescript("CREATE TABLE publication_ids(id INTEGER PRIMARY KEY); CREATE TABLE required_publication(id INTEGER REFERENCES publication_ids(id) DEFERRABLE INITIALLY DEFERRED); CREATE TRIGGER require_publication AFTER INSERT ON ledger BEGIN INSERT INTO required_publication VALUES (99); END;")
        failing.commit()
        recorder = Recorder()
        try:
            transfer(failing, recorder, "a", "b", 10)
        except sqlite3.DatabaseError:
            pass
        else:
            raise AssertionError("commit failure swallowed")
        assert state(failing) == (100, 20, [])
        assert recorder.events == []
        assert failing.execute("SELECT * FROM required_publication").fetchall() == []
        assert not failing.in_transaction
    ''',
)


DOCUMENTS = task(
    "py-document-scope", "screening", "authorization",
    "Secure get_document(connection, tenant, owner, document_id) and list_documents "
    "in src/service.py. Only documents matching both tenant and owner and having "
    "deleted_at IS NULL are accessible. get_document returns None for any unavailable "
    "ID without distinguishing cross-tenant, cross-owner or deleted records. Lists "
    "return dictionaries ordered by id, and no deletion metadata. All queries use "
    "bound parameters, including names containing quotes. Keep result fields id, "
    "title and body unchanged. Start in src/service.py and src/repository.py.",
    {
        "src/repository.py": '''
            def initialize(connection):
                connection.execute("CREATE TABLE documents(id INTEGER PRIMARY KEY, tenant TEXT, owner TEXT, title TEXT, body TEXT, deleted_at TEXT)")
                connection.commit()

            def decode(row):
                return {"id": row[0], "title": row[1], "body": row[2]}

            def find(connection, document_id):
                row = connection.execute("SELECT id, title, body FROM documents WHERE id=?", (document_id,)).fetchone()
                return None if row is None else decode(row)

            def listing(connection, owner):
                return [decode(row) for row in connection.execute("SELECT id, title, body FROM documents WHERE owner=? ORDER BY id", (owner,))]
        ''',
        "src/service.py": '''
            from .repository import find, listing

            def get_document(connection, tenant, owner, document_id):
                return find(connection, document_id)

            def list_documents(connection, tenant, owner):
                return listing(connection, owner)
        ''',
        "checks/public.py": '''
            import sqlite3
            from src.repository import initialize
            from src.service import get_document, list_documents
            c = sqlite3.connect(":memory:")
            initialize(c)
            c.execute("INSERT INTO documents VALUES (1, 't', 'o', 'Title', 'Body', NULL)")
            c.commit()
            assert get_document(c, "t", "o", 1) == {"id": 1, "title": "Title", "body": "Body"}
            assert list_documents(c, "t", "o") == [{"id": 1, "title": "Title", "body": "Body"}]
            assert get_document(c, "t", "o", 99) is None
        ''',
    },
    {
        "src/repository.py": '''
            def initialize(connection):
                connection.execute("CREATE TABLE documents(id INTEGER PRIMARY KEY, tenant TEXT, owner TEXT, title TEXT, body TEXT, deleted_at TEXT)")
                connection.commit()

            def decode(row):
                return {"id": row[0], "title": row[1], "body": row[2]}

            def find(connection, tenant, owner, document_id):
                row = connection.execute("SELECT id, title, body FROM documents WHERE id=? AND tenant=? AND owner=? AND deleted_at IS NULL", (document_id, tenant, owner)).fetchone()
                return None if row is None else decode(row)

            def listing(connection, tenant, owner):
                return [decode(row) for row in connection.execute("SELECT id, title, body FROM documents WHERE tenant=? AND owner=? AND deleted_at IS NULL ORDER BY id", (tenant, owner))]
        ''',
        "src/service.py": '''
            from .repository import find, listing

            def get_document(connection, tenant, owner, document_id):
                return find(connection, tenant, owner, document_id)

            def list_documents(connection, tenant, owner):
                return listing(connection, tenant, owner)
        ''',
    },
    '''
        import sqlite3
        from src.repository import initialize
        from src.service import get_document, list_documents
        c = sqlite3.connect(":memory:")
        initialize(c)
        c.executemany("INSERT INTO documents VALUES (?, ?, ?, ?, ?, ?)", [(5,"a","same","Five","5",None), (1,"a","same","One","1",None), (2,"b","same","Other tenant","2",None), (3,"a","different","Other owner","3",None), (4,"a","same","Deleted","4","yesterday"), (6,"t' OR 1=1 --","o'","Quoted","6",None)])
        c.commit()
        assert list_documents(c, "a", "same") == [{"id":1,"title":"One","body":"1"}, {"id":5,"title":"Five","body":"5"}]
        for identifier in (2, 3, 4, 999):
            assert get_document(c, "a", "same", identifier) is None
        assert get_document(c, "b", "same", 2) == {"id":2,"title":"Other tenant","body":"2"}
        assert list_documents(c, "a' OR 1=1 --", "same") == []
        assert list_documents(c, "t' OR 1=1 --", "o'") == [{"id":6,"title":"Quoted","body":"6"}]
        assert get_document(c, "a", "same' OR 1=1 --", 1) is None
        assert c.execute("SELECT COUNT(*) FROM documents").fetchone() == (6,)
    ''',
)


MONEY = task(
    "py-money-contract", "screening", "contracts",
    "Replace float-based parsing in src/money.py. parse_amount accepts Decimal, "
    "integers excluding bool, and plain decimal strings without whitespace or "
    "exponents, optionally signed. Reject floats, other types, non-finite numbers, "
    "zero, negatives, values over 1000000.00, and values not exactly representable "
    "in cents with ValueError. Extra trailing zeros are fine; never round a nonzero "
    "fractional cent. Return a Decimal with exponent -2. Preserve format_amount "
    "and make src/api.py.make_invoice apply the same rules. The API accepts a list "
    "of amounts and returns {'total': a two-decimal string, 'count': N}; its total "
    "must also be at most 1000000.00 and an empty list totals 0.00. Do not mutate "
    "the global decimal context or the caller's input. Start in src/money.py and src/api.py.",
    {
        "src/money.py": '''
            from decimal import Decimal

            def parse_amount(value):
                return Decimal(str(round(float(value), 2)))

            def format_amount(value):
                return format(value, ".2f")
        ''',
        "src/api.py": '''
            from .money import parse_amount, format_amount

            def make_invoice(amounts):
                total = sum((parse_amount(item) for item in amounts), start=parse_amount("0"))
                return {"total": format_amount(total), "count": len(amounts)}
        ''',
        "checks/public.py": '''
            from src.money import parse_amount, format_amount
            from src.api import make_invoice
            assert format_amount(parse_amount("12.50")) == "12.50"
            assert make_invoice(["1.20", "2.30"]) == {"total": "3.50", "count": 2}
            assert make_invoice([]) == {"total": "0.00", "count": 0}
        ''',
    },
    {
        "src/money.py": '''
            from decimal import Decimal, InvalidOperation, localcontext
            import re

            def parse_amount(value):
                if isinstance(value, str):
                    if re.fullmatch(r"[+-]?[0-9]+(?:\\.[0-9]+)?", value) is None:
                        raise ValueError("invalid decimal spelling")
                elif not isinstance(value, Decimal) and type(value) is not int:
                    raise ValueError("invalid amount type")
                try:
                    number = Decimal(value)
                    if not number.is_finite() or number <= 0 or number > Decimal("1000000.00"):
                        raise ValueError("amount outside limits")
                    with localcontext() as context:
                        context.prec = max(32, len(number.as_tuple().digits) + 4)
                        cents = number.quantize(Decimal("0.01"))
                    if cents != number:
                        raise ValueError("fractional cent")
                    return cents
                except InvalidOperation as exc:
                    raise ValueError("invalid amount") from exc

            def format_amount(value):
                return format(value, ".2f")
        ''',
        "src/api.py": '''
            from decimal import Decimal, localcontext
            from .money import parse_amount, format_amount

            def make_invoice(amounts):
                if not isinstance(amounts, list):
                    raise ValueError("amounts must be a list")
                clean = [parse_amount(item) for item in amounts]
                with localcontext() as context:
                    context.prec = 32
                    total = sum(clean, Decimal("0.00"))
                if total > Decimal("1000000.00"):
                    raise ValueError("invoice exceeds limit")
                return {"total": format_amount(total), "count": len(clean)}
        ''',
    },
    '''
        from decimal import Decimal, getcontext, localcontext
        from src.money import parse_amount, format_amount
        from src.api import make_invoice
        for value, expected in [("0.01", "0.01"), ("+0012.3400", "12.34"), (Decimal("1E+2"), "100.00"), (5, "5.00"), ("1000000.00", "1000000.00"), ("0.1000000000000000000000000000000000000000", "0.10")]:
            result = parse_amount(value)
            assert isinstance(result, Decimal)
            assert result.as_tuple().exponent == -2
            assert format_amount(result) == expected
        invalid = [True, False, 1.2, None, [], {}, "", " 1.00", "1.00 ", "1e2", ".1", "1.", "1_000", "NaN", "Infinity", Decimal("NaN"), Decimal("Infinity"), "0", "-0.00", "-1", "0.001", "1.005", "999999.999", "1000000.01", Decimal("12.0001")]
        for value in invalid:
            try:
                parse_amount(value)
            except ValueError:
                pass
            else:
                raise AssertionError("invalid amount accepted: " + repr(value))
        values = ["0.10", "0.20", "999999.70"]
        assert make_invoice(values) == {"total": "1000000.00", "count": 3}
        assert values == ["0.10", "0.20", "999999.70"]
        for amounts in [["999999.99", "0.02"], ["1.00", "0.001"], "1.00", None]:
            try:
                make_invoice(amounts)
            except ValueError:
                pass
            else:
                raise AssertionError("invalid invoice accepted")
        with localcontext() as context:
            context.prec = 3
            assert parse_amount("123456.78") == Decimal("123456.78")
            assert make_invoice(["123456.78", "0.22"]) == {"total": "123457.00", "count": 2}
            assert getcontext().prec == 3
        assert make_invoice([]) == {"total": "0.00", "count": 0}
    ''',
)


STREAM = task(
    "py-generator-cleanup", "screening", "streaming",
    "Fix stream_rows(resource, transform) in src/service.py so each started iterator "
    "closes its resource exactly once on exhaustion, explicit generator.close(), "
    "iteration errors and transformation errors. A transform failure propagates "
    "and no further row is read. Keep processing lazy, preserving order and transformed "
    "values; constructing or closing an unstarted generator performs no read or close. "
    "If cleanup also raises while an iteration or transform error is active, preserve "
    "the original error; otherwise propagate the cleanup error. src/consumer.py.take "
    "must close the iterator after taking its requested positive number of rows or "
    "if consuming fails. A limit of zero returns [] without starting the stream. "
    "Start in src/service.py and src/consumer.py. Resource.read_next() returns None at EOF.",
    {
        "src/resource.py": '''
            class Rows:
                def __init__(self, rows):
                    self.rows = list(rows)
                    self.index = 0
                    self.reads = 0
                    self.closes = 0

                def read_next(self):
                    self.reads += 1
                    if self.index == len(self.rows):
                        return None
                    value = self.rows[self.index]
                    self.index += 1
                    return value

                def close(self):
                    self.closes += 1
        ''',
        "src/service.py": '''
            def stream_rows(resource, transform):
                while True:
                    row = resource.read_next()
                    if row is None:
                        break
                    yield transform(row)
                resource.close()
        ''',
        "src/consumer.py": '''
            from .service import stream_rows

            def take(resource, transform, limit):
                stream = stream_rows(resource, transform)
                result = []
                for row in stream:
                    result.append(row)
                    if len(result) >= limit:
                        break
                return result
        ''',
        "checks/public.py": '''
            from src.resource import Rows
            from src.service import stream_rows
            r = Rows([1, 2, 3])
            assert list(stream_rows(r, lambda value: value * 2)) == [2, 4, 6]
            assert (r.reads, r.closes) == (4, 1)
        ''',
    },
    {
        "src/service.py": '''
            def stream_rows(resource, transform):
                failed = False
                try:
                    while True:
                        row = resource.read_next()
                        if row is None:
                            break
                        yield transform(row)
                except GeneratorExit:
                    raise
                except BaseException:
                    failed = True
                    raise
                finally:
                    try:
                        resource.close()
                    except BaseException:
                        if not failed:
                            raise
        ''',
        "src/consumer.py": '''
            from .service import stream_rows

            def take(resource, transform, limit):
                if limit == 0:
                    return []
                stream = stream_rows(resource, transform)
                result = []
                try:
                    for row in stream:
                        result.append(row)
                        if len(result) >= limit:
                            break
                    return result
                finally:
                    stream.close()
        ''',
    },
    '''
        from src.resource import Rows
        from src.service import stream_rows
        from src.consumer import take
        r = Rows([0, 1, 2])
        stream = stream_rows(r, lambda value: value + 10)
        assert (r.reads, r.closes) == (0, 0)
        assert next(stream) == 10
        assert (r.reads, r.closes) == (1, 0)
        stream.close()
        stream.close()
        assert (r.reads, r.closes) == (1, 1)
        untouched = Rows([1])
        stream_rows(untouched, str).close()
        assert (untouched.reads, untouched.closes) == (0, 0)
        r = Rows([])
        assert list(stream_rows(r, str)) == []
        assert (r.reads, r.closes) == (1, 1)
        r = Rows([1, 2, 3])
        assert take(r, lambda value: value * 3, 2) == [3, 6]
        assert (r.reads, r.closes) == (2, 1)
        import src.consumer as consumer
        original = consumer.stream_rows
        held = []
        def hold(resource, transform):
            stream = original(resource, transform)
            held.append(stream)
            return stream
        consumer.stream_rows = hold
        r = Rows([2, 4])
        assert consumer.take(r, str, 1) == ["2"]
        assert (r.reads, r.closes) == (1, 1)
        consumer.stream_rows = original
        r = Rows([1])
        assert take(r, str, 0) == []
        assert (r.reads, r.closes) == (0, 0)
        failure = RuntimeError("transform failed")
        def explode(value):
            raise failure
        r = Rows([1, 2])
        try:
            take(r, explode, 1)
        except RuntimeError as exc:
            assert exc is failure
        else:
            raise AssertionError("transform error swallowed")
        assert (r.reads, r.closes) == (1, 1)
        class BrokenRead(Rows):
            def read_next(self):
                self.reads += 1
                raise failure
            def close(self):
                self.closes += 1
                raise ValueError("close failed")
        r = BrokenRead([])
        try:
            list(stream_rows(r, str))
        except RuntimeError as exc:
            assert exc is failure
        else:
            raise AssertionError("read error lost")
        assert (r.reads, r.closes) == (1, 1)
        class BrokenClose(Rows):
            def close(self):
                self.closes += 1
                raise ValueError("close failed")
        for rows in ([], [1]):
            r = BrokenClose(rows)
            try:
                list(stream_rows(r, str))
            except ValueError as exc:
                assert str(exc) == "close failed"
            else:
                raise AssertionError("cleanup error swallowed")
            assert r.closes == 1
        r = BrokenClose([1])
        try:
            list(stream_rows(r, explode))
        except RuntimeError as exc:
            assert exc is failure
        else:
            raise AssertionError("transform error masked by cleanup")
        assert (r.reads, r.closes) == (1, 1)
    ''',
)


EXPORTS = task(
    "py-exporter-consolidation", "screening", "refactoring",
    "Unify the duplicated export pipeline without changing public behavior. Keep "
    "src/csv_exporter.py.export_csv(rows) and src/json_exporter.py.export_json(rows) "
    "returning the exact same strings, including header and final newline rules. "
    "Introduce src/exporter.py.export_rows(rows, format) supporting 'csv' and 'json', "
    "and ValueError for unsupported formats. Both public wrappers must call that "
    "shared entry point; remove their duplicated row normalization and serialization "
    "loops. Normalization chooses only id and name, uses '' for missing or None values, "
    "stringifies other values, preserves order and supports one-shot iterables without "
    "mutating inputs. JSON uses ensure_ascii=False and separators=(',', ':'). "
    "CSV uses LF line endings, standard CSV quoting and an id,name header even with "
    "no rows. The existing dispatcher must keep working. Start in src/dispatcher.py "
    "and the two exporter modules.",
    {
        "src/csv_exporter.py": '''
            import csv
            import io

            def export_csv(rows):
                buffer = io.StringIO(newline="")
                writer = csv.writer(buffer, lineterminator="\\n")
                writer.writerow(["id", "name"])
                for row in rows:
                    clean = ["" if row.get(key) is None else str(row[key]) for key in ("id", "name")]
                    writer.writerow(clean)
                return buffer.getvalue()
        ''',
        "src/json_exporter.py": '''
            import json

            def export_json(rows):
                clean = []
                for row in rows:
                    clean.append({key: "" if row.get(key) is None else str(row[key]) for key in ("id", "name")})
                return json.dumps(clean, ensure_ascii=False, separators=(",", ":"))
        ''',
        "src/dispatcher.py": '''
            from .csv_exporter import export_csv
            from .json_exporter import export_json

            def export(rows, format):
                if format == "csv":
                    return export_csv(rows)
                if format == "json":
                    return export_json(rows)
                raise ValueError("unsupported format")
        ''',
        "checks/public.py": '''
            from src.dispatcher import export
            assert export([{"id": 1, "name": "Alice"}], "csv") == "id,name\\n1,Alice\\n"
            assert export([{"id": 1, "name": "Alice"}], "json") == '[{"id":"1","name":"Alice"}]'
            assert export([], "csv") == "id,name\\n"
            assert export([], "json") == "[]"
        ''',
    },
    {
        "src/exporter.py": '''
            import csv
            import io
            import json

            def export_rows(rows, format):
                if format not in ("csv", "json"):
                    raise ValueError("unsupported format")
                clean = [{key: "" if row.get(key) is None else str(row[key]) for key in ("id", "name")} for row in rows]
                if format == "json":
                    return json.dumps(clean, ensure_ascii=False, separators=(",", ":"))
                buffer = io.StringIO(newline="")
                writer = csv.writer(buffer, lineterminator="\\n")
                writer.writerow(["id", "name"])
                writer.writerows((row["id"], row["name"]) for row in clean)
                return buffer.getvalue()
        ''',
        "src/csv_exporter.py": '''
            from .exporter import export_rows

            def export_csv(rows):
                return export_rows(rows, "csv")
        ''',
        "src/json_exporter.py": '''
            from .exporter import export_rows

            def export_json(rows):
                return export_rows(rows, "json")
        ''',
    },
    '''
        from src.dispatcher import export
        from src.csv_exporter import export_csv
        from src.json_exporter import export_json
        rows = [{"id": 0, "name": 'A,"B"', "ignored": "secret"}, {"name": "á\\nβ"}, {"id": None, "name": False}]
        assert export_csv(iter(rows)) == 'id,name\\n0,"A,""B"""\\n,"á\\nβ"\\n,False\\n'
        assert export_json(iter(rows)) == r'[{"id":"0","name":"A,\\"B\\""},{"id":"","name":"á\\nβ"},{"id":"","name":"False"}]'
        assert rows == [{"id":0,"name":'A,"B"',"ignored":"secret"},{"name":"á\\nβ"},{"id":None,"name":False}]
        assert export([], "csv") == "id,name\\n"
        assert export([], "json") == "[]"
        try:
            export([], "xml")
        except ValueError:
            pass
        else:
            raise AssertionError("unsupported format accepted")
    ''',
    '''
        import ast, importlib, os, sys
        sys.path.insert(0, os.getcwd())
        from src.exporter import export_rows
        assert export_rows([{"id": 2, "name": "B"}], "csv") == "id,name\\n2,B\\n"
        assert export_rows([{"id": 2, "name": "B"}], "json") == '[{"id":"2","name":"B"}]'
        try:
            export_rows([], "other")
        except ValueError:
            pass
        else:
            raise AssertionError("shared entry accepted unsupported format")
        for module_name, function_name, format_name in [("csv_exporter", "export_csv", "csv"), ("json_exporter", "export_json", "json")]:
            module = importlib.import_module("src." + module_name)
            tree = ast.parse(open("src/" + module_name + ".py").read())
            assert not any(isinstance(node, (ast.For, ast.While, ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)) for node in ast.walk(tree)), "wrapper keeps duplicated iteration"
            calls = []
            def profile(frame, event, argument):
                if event == "call" and frame.f_code is export_rows.__code__:
                    calls.append(True)
            sys.setprofile(profile)
            try:
                result = getattr(module, function_name)([{"id": 3}])
            finally:
                sys.setprofile(None)
            assert calls, "wrapper does not delegate to shared entry"
            assert result == ("id,name\\n3,\\n" if format_name == "csv" else '[{"id":"3","name":""}]')
    ''',
)


RESERVATIONS = task(
    "py-stock-reservations", "confirmation", "feature",
    "Add reserve(connection, key, items) in src/service.py and src/api.py.handle_reserve. "
    "items is a nonempty dict from nonempty SKU strings to positive integer quantities "
    "excluding bool, and key is a nonempty string. Atomically deduct available stock "
    "and persist a receipt using the key. Return {'key': key, 'items': a copy of items}. "
    "Reusing the same key and identical quantities returns that receipt without "
    "deducting again, even if stock is now insufficient. Dictionary insertion order "
    "is irrelevant to equality. Reusing a key with different items raises ValueError. "
    "Unknown SKUs, insufficient stock or invalid input raise ValueError with no "
    "reservation or stock changes. A database failure rolls back every change. "
    "Idempotency must survive closing and reopening the database. Preserve the "
    "stock listing. The API envelope has exactly key and items. Connections are "
    "idle at entry. Start in src/service.py, src/api.py and src/repository.py.",
    {
        "src/repository.py": '''
            def initialize(connection):
                connection.executescript("CREATE TABLE stock(sku TEXT PRIMARY KEY, quantity INTEGER NOT NULL); CREATE TABLE reservations(key TEXT PRIMARY KEY, items TEXT NOT NULL);")
                connection.commit()

            def list_stock(connection):
                return dict(connection.execute("SELECT sku, quantity FROM stock ORDER BY sku"))
        ''',
        "src/service.py": '''
            def reserve(connection, key, items):
                raise NotImplementedError("Reservations are unavailable")
        ''',
        "src/api.py": '''
            from .repository import list_stock

            def handle_stock(connection):
                return {"stock": list_stock(connection)}

            def handle_reserve(connection, payload):
                raise NotImplementedError("Reservation endpoint is unavailable")
        ''',
        "checks/public.py": '''
            import sqlite3
            from src.repository import initialize
            from src.api import handle_stock
            c = sqlite3.connect(":memory:")
            initialize(c)
            c.executemany("INSERT INTO stock VALUES (?, ?)", [("a", 4), ("b", 2)])
            c.commit()
            assert handle_stock(c) == {"stock": {"a": 4, "b": 2}}
        ''',
    },
    {
        "src/service.py": '''
            import json

            def reserve(connection, key, items):
                if not isinstance(key, str) or not key or not isinstance(items, dict) or not items:
                    raise ValueError("invalid reservation")
                if any(not isinstance(sku, str) or not sku or type(quantity) is not int or quantity <= 0 for sku, quantity in items.items()):
                    raise ValueError("invalid items")
                encoded = json.dumps(items, sort_keys=True, separators=(",", ":"))
                with connection:
                    previous = connection.execute("SELECT items FROM reservations WHERE key=?", (key,)).fetchone()
                    if previous:
                        if json.loads(previous[0]) != items:
                            raise ValueError("key already used")
                        return {"key": key, "items": json.loads(previous[0])}
                    for sku, quantity in items.items():
                        row = connection.execute("SELECT quantity FROM stock WHERE sku=?", (sku,)).fetchone()
                        if row is None or row[0] < quantity:
                            raise ValueError("unavailable stock")
                    for sku, quantity in items.items():
                        connection.execute("UPDATE stock SET quantity=quantity-? WHERE sku=?", (quantity, sku))
                    connection.execute("INSERT INTO reservations VALUES (?, ?)", (key, encoded))
                return {"key": key, "items": dict(items)}
        ''',
        "src/api.py": '''
            from .repository import list_stock
            from .service import reserve

            def handle_stock(connection):
                return {"stock": list_stock(connection)}

            def handle_reserve(connection, payload):
                if not isinstance(payload, dict) or set(payload) != {"key", "items"}:
                    raise ValueError("invalid envelope")
                return reserve(connection, payload["key"], payload["items"])
        ''',
    },
    '''
        import sqlite3, tempfile
        from src.repository import initialize, list_stock
        from src.api import handle_reserve
        with tempfile.TemporaryDirectory() as directory:
            path = directory + "/stock.db"
            c = sqlite3.connect(path)
            initialize(c)
            c.executemany("INSERT INTO stock VALUES (?, ?)", [("a", 5), ("b", 3)])
            c.commit()
            items = {"b": 2, "a": 4}
            receipt = handle_reserve(c, {"key": "one", "items": items})
            assert receipt == {"key": "one", "items": {"a": 4, "b": 2}}
            receipt["items"]["a"] = 999
            assert items == {"b": 2, "a": 4}
            assert list_stock(c) == {"a": 1, "b": 1}
            c.close()
            c = sqlite3.connect(path)
            assert handle_reserve(c, {"key": "one", "items": {"a": 4, "b": 2}}) == {"key":"one","items":{"a":4,"b":2}}
            assert list_stock(c) == {"a": 1, "b": 1}
            bad = [{"key":"one","items":{"a":1}}, {"key":"two","items":{"a":1,"missing":1}}, {"key":"two","items":{"a":1,"b":2}}, {"key":"two","items":{}}, {"key":"two","items":{"a":True}}, {"key":"two","items":{"a":0}}, {"key":"two","items":{"a":-1}}, {"key":"two","items":{"a":1.5}}, {"key":"two","items":{"":1}}, {"key":"","items":{"a":1}}, {"key":None,"items":{"a":1}}, {"key":"two","items":[]}, {"key":"two","items":{"a":1},"extra":1}, None]
            for payload in bad:
                try:
                    handle_reserve(c, payload)
                except ValueError:
                    pass
                else:
                    raise AssertionError("invalid reservation accepted")
                assert list_stock(c) == {"a":1,"b":1}
                assert c.execute("SELECT COUNT(*) FROM reservations").fetchone() == (1,)
            c.execute("CREATE TRIGGER reject_receipt BEFORE INSERT ON reservations BEGIN SELECT RAISE(ABORT, 'receipt unavailable'); END")
            c.commit()
            try:
                handle_reserve(c, {"key":"two","items":{"a":1,"b":1}})
            except sqlite3.DatabaseError:
                pass
            else:
                raise AssertionError("receipt error swallowed")
            assert list_stock(c) == {"a":1,"b":1}
            assert c.execute("SELECT COUNT(*) FROM reservations").fetchone() == (1,)
            c.execute("DROP TRIGGER reject_receipt")
            c.commit()
            assert handle_reserve(c, {"key":"two","items":{"a":1,"b":1}}) == {"key":"two","items":{"a":1,"b":1}}
            assert list_stock(c) == {"a":0,"b":0}
            c.close()
    ''',
)


SHARES = task(
    "py-expiring-shares", "confirmation", "authorization",
    "Implement share-token access and revocation in src/service.py, preserving "
    "the ordinary owner lookup. read_shared(connection, token, now) returns only "
    "{'id': document_id, 'title': title} when the exact token exists, is not revoked, "
    "expires_at is strictly greater than now, and its document is active and belongs "
    "to the tenant recorded on the token. Otherwise return None, with no writes. "
    "revoke_share(connection, tenant, owner, token) returns True and commits revocation "
    "only when both the token and its active document belong to that tenant and the "
    "document belongs to that owner. Authorized repeated revocation returns True; "
    "unknown, wrong-tenant, wrong-owner or deleted-document tokens return False with "
    "no changes. Expiration does not prevent an authorized revocation. now and "
    "expires_at are integer epoch seconds supplied by callers, with no wall-clock "
    "dependency. Bind SQL parameters, including tokens with quotes. Start in "
    "src/service.py and src/repository.py.",
    {
        "src/repository.py": '''
            def initialize(connection):
                connection.executescript("CREATE TABLE documents(id INTEGER PRIMARY KEY, tenant TEXT, owner TEXT, title TEXT, deleted INTEGER NOT NULL); CREATE TABLE shares(token TEXT PRIMARY KEY, document_id INTEGER, tenant TEXT, expires_at INTEGER, revoked INTEGER NOT NULL);")
                connection.commit()

            def owner_document(connection, tenant, owner, document_id):
                row = connection.execute("SELECT id, title FROM documents WHERE id=? AND tenant=? AND owner=? AND deleted=0", (document_id, tenant, owner)).fetchone()
                return None if row is None else {"id": row[0], "title": row[1]}
        ''',
        "src/service.py": '''
            from .repository import owner_document

            def read_owned(connection, tenant, owner, document_id):
                return owner_document(connection, tenant, owner, document_id)

            def read_shared(connection, token, now):
                row = connection.execute("SELECT d.id, d.title FROM shares s JOIN documents d ON d.id=s.document_id WHERE s.token=?", (token,)).fetchone()
                return None if row is None else {"id": row[0], "title": row[1]}

            def revoke_share(connection, tenant, owner, token):
                with connection:
                    cursor = connection.execute("UPDATE shares SET revoked=1 WHERE token=?", (token,))
                return cursor.rowcount == 1
        ''',
        "checks/public.py": '''
            import sqlite3
            from src.repository import initialize
            from src.service import read_owned, read_shared
            c = sqlite3.connect(":memory:")
            initialize(c)
            c.execute("INSERT INTO documents VALUES (1, 'a', 'owner', 'Title', 0)")
            c.execute("INSERT INTO shares VALUES ('token', 1, 'a', 200, 0)")
            c.commit()
            assert read_owned(c, "a", "owner", 1) == {"id":1,"title":"Title"}
            assert read_owned(c, "b", "owner", 1) is None
            assert read_shared(c, "token", 100) == {"id":1,"title":"Title"}
        ''',
    },
    {"src/service.py": '''
        from .repository import owner_document

        def read_owned(connection, tenant, owner, document_id):
            return owner_document(connection, tenant, owner, document_id)

        def read_shared(connection, token, now):
            row = connection.execute("SELECT d.id, d.title FROM shares s JOIN documents d ON d.id=s.document_id AND d.tenant=s.tenant WHERE s.token=? AND s.revoked=0 AND s.expires_at>? AND d.deleted=0", (token, now)).fetchone()
            return None if row is None else {"id": row[0], "title": row[1]}

        def revoke_share(connection, tenant, owner, token):
            with connection:
                row = connection.execute("SELECT s.token FROM shares s JOIN documents d ON d.id=s.document_id AND d.tenant=s.tenant WHERE s.token=? AND s.tenant=? AND d.owner=? AND d.deleted=0", (token, tenant, owner)).fetchone()
                if row is None:
                    return False
                connection.execute("UPDATE shares SET revoked=1 WHERE token=?", (token,))
            return True
    '''},
    '''
        import sqlite3
        from src.repository import initialize
        from src.service import read_owned, read_shared, revoke_share
        c = sqlite3.connect(":memory:")
        initialize(c)
        c.executemany("INSERT INTO documents VALUES (?, ?, ?, ?, ?)", [(1,"a","owner","A",0), (2,"b","owner","B",0), (3,"a","owner","Deleted",1), (4,"a","other","Other",0)])
        c.executemany("INSERT INTO shares VALUES (?, ?, ?, ?, ?)", [("good",1,"a",200,0), ("expired",1,"a",100,0), ("revoked",1,"a",200,1), ("cross",2,"a",200,0), ("deleted",3,"a",200,0), ("other",4,"a",200,0), ("orphan",99,"a",200,0), ("q' OR 1=1 --",1,"a",200,0)])
        c.commit()
        assert read_shared(c, "good", 199) == {"id":1,"title":"A"}
        for token in ("good", "expired"):
            assert read_shared(c, token, 200) is None
        assert read_shared(c, "expired", 100) is None
        for token in ("revoked", "cross", "deleted", "orphan", "missing", "' OR 1=1 --"):
            assert read_shared(c, token, 50) is None
        assert read_shared(c, "q' OR 1=1 --", 50) == {"id":1,"title":"A"}
        before = c.execute("SELECT * FROM shares ORDER BY token").fetchall()
        for tenant, owner, token in [("b","owner","good"), ("a","wrong","good"), ("a","owner","cross"), ("a","owner","deleted"), ("a","owner","other"), ("a","owner","missing"), ("a' OR 1=1 --","owner","good")]:
            assert revoke_share(c, tenant, owner, token) is False
            assert c.execute("SELECT * FROM shares ORDER BY token").fetchall() == before
        assert revoke_share(c, "a", "owner", "good") is True
        assert revoke_share(c, "a", "owner", "good") is True
        assert read_shared(c, "good", 50) is None
        assert revoke_share(c, "a", "owner", "expired") is True
        assert revoke_share(c, "a", "owner", "q' OR 1=1 --") is True
        assert read_owned(c, "a", "owner", 1) == {"id":1,"title":"A"}
        assert read_shared(c, "other", 50) == {"id":4,"title":"Other"}
        assert not c.in_transaction
    ''',
)


CONFIG = task(
    "py-layered-queue-config", "confirmation", "contracts",
    "Implement queue configuration overlays through src/service.py.build_queue. "
    "Defaults are retries=3, timeout_ms=1000 and label='jobs'. Resolve two dict layers "
    "in order, organization then job. Omitted fields inherit; an explicit None resets "
    "that field to its built-in default rather than inheriting the earlier layer. "
    "retries is an integer 0..10 and timeout_ms an integer 1..60000; bool is invalid. "
    "label is a string, trimmed, and must remain nonempty. Reject unknown fields, "
    "non-dict layers or any invalid layer values with ValueError, even when a later "
    "layer would replace them. Do not mutate either layer or share returned state "
    "between calls. Keep src/config.py.resolve as the shared entry and make build_queue "
    "return {'queue': resolved_config}. Preserve default-only calls. Start in src/config.py "
    "and src/service.py.",
    {
        "src/config.py": '''
            DEFAULTS = {"retries": 3, "timeout_ms": 1000, "label": "jobs"}

            def resolve(organization, job):
                result = DEFAULTS.copy()
                result.update(organization)
                result.update(job)
                return result
        ''',
        "src/service.py": '''
            from .config import resolve

            def build_queue(organization=None, job=None):
                return {"queue": resolve({} if organization is None else organization, {} if job is None else job)}
        ''',
        "checks/public.py": '''
            from src.service import build_queue
            assert build_queue() == {"queue":{"retries":3,"timeout_ms":1000,"label":"jobs"}}
            assert build_queue({"retries":5}, {"timeout_ms":200}) == {"queue":{"retries":5,"timeout_ms":200,"label":"jobs"}}
        ''',
    },
    {"src/config.py": '''
        DEFAULTS = {"retries": 3, "timeout_ms": 1000, "label": "jobs"}

        def resolve(organization, job):
            result = DEFAULTS.copy()
            for layer in (organization, job):
                if not isinstance(layer, dict) or not set(layer).issubset(DEFAULTS):
                    raise ValueError("invalid configuration layer")
                for field, value in layer.items():
                    if value is None:
                        result[field] = DEFAULTS[field]
                    elif field == "label":
                        if not isinstance(value, str) or not value.strip():
                            raise ValueError("invalid label")
                        result[field] = value.strip()
                    else:
                        lower, upper = (0, 10) if field == "retries" else (1, 60000)
                        if type(value) is not int or not lower <= value <= upper:
                            raise ValueError("invalid numeric option")
                        result[field] = value
            return result
    '''},
    '''
        from src.config import resolve
        from src.service import build_queue
        assert resolve({"retries":8,"timeout_ms":60000,"label":"Org"}, {"retries":None,"label":None}) == {"retries":3,"timeout_ms":60000,"label":"jobs"}
        assert build_queue({"timeout_ms":50}, {"timeout_ms":None,"retries":0,"label":" Custom "}) == {"queue":{"retries":0,"timeout_ms":1000,"label":"Custom"}}
        assert resolve({"retries":10}, {"timeout_ms":1}) == {"retries":10,"timeout_ms":1,"label":"jobs"}
        invalid = [{"retries":True}, {"retries":-1}, {"retries":11}, {"retries":1.5}, {"timeout_ms":False}, {"timeout_ms":0}, {"timeout_ms":60001}, {"timeout_ms":"100"}, {"label":"  "}, {"label":5}, {"extra":1}, [], "text", None]
        for layer in invalid:
            for layers in [(layer, {"retries":1,"timeout_ms":2,"label":"override"}), ({}, layer)]:
                try:
                    resolve(*layers)
                except ValueError:
                    pass
                else:
                    raise AssertionError("invalid layer accepted")
        organization = {"label":" Org ","retries":6}
        job = {"retries":None}
        first = build_queue(organization, job)
        first["queue"]["label"] = "mutated"
        assert organization == {"label":" Org ","retries":6}
        assert job == {"retries":None}
        assert build_queue(organization, job) == {"queue":{"retries":3,"timeout_ms":1000,"label":"Org"}}
        assert build_queue() == {"queue":{"retries":3,"timeout_ms":1000,"label":"jobs"}}
    ''',
)


LINES = task(
    "py-incremental-lines", "confirmation", "streaming",
    "Fix iter_lines(source) in src/reader.py and src/service.py.collect_lines. "
    "source is an iterable yielding byte chunks with close(). Decode UTF-8 strictly "
    "across arbitrary chunk boundaries, including multibyte characters. Split on LF; "
    "remove one immediately preceding CR, preserve other characters and empty lines, "
    "and emit a nonempty final unterminated line. A trailing newline creates no "
    "additional line. Empty byte chunks have no effect and an empty source returns "
    "no lines. Be lazy: once a complete line is available, yield it before requesting "
    "another source chunk. No whole-source buffering. Close a started source exactly "
    "once on exhaustion, explicit iterator close(), source errors or decoding errors; "
    "an unstarted iterator has no source effects. collect_lines delegates to iter_lines "
    "and returns a list. Source.close does not raise. Start in src/reader.py and src/service.py.",
    {
        "src/chunks.py": '''
            class Chunks:
                def __init__(self, chunks):
                    self.chunks = iter(chunks)
                    self.reads = 0
                    self.closes = 0

                def __iter__(self):
                    return self

                def __next__(self):
                    self.reads += 1
                    return next(self.chunks)

                def close(self):
                    self.closes += 1
        ''',
        "src/reader.py": '''
            def iter_lines(source):
                for chunk in source:
                    for line in chunk.decode("utf-8").splitlines():
                        yield line
                source.close()
        ''',
        "src/service.py": '''
            from .reader import iter_lines

            def collect_lines(source):
                return list(iter_lines(source))
        ''',
        "checks/public.py": '''
            from src.chunks import Chunks
            from src.service import collect_lines
            source = Chunks([b"one\\n", b"two\\n"])
            assert collect_lines(source) == ["one", "two"]
            assert source.closes == 1
        ''',
    },
    {"src/reader.py": '''
        import codecs

        def iter_lines(source):
            decoder = codecs.getincrementaldecoder("utf-8")("strict")
            pending = ""
            try:
                for chunk in source:
                    pending += decoder.decode(chunk)
                    while "\\n" in pending:
                        line, pending = pending.split("\\n", 1)
                        yield line[:-1] if line.endswith("\\r") else line
                pending += decoder.decode(b"", final=True)
                if pending:
                    yield pending
            finally:
                source.close()
    '''},
    '''
        from src.chunks import Chunks
        from src.reader import iter_lines
        from src.service import collect_lines
        encoded = "á\\nβ\\r\\n\\nlast\\r".encode("utf-8")
        chunks = [encoded[index:index+1] for index in range(len(encoded))]
        source = Chunks(chunks)
        assert collect_lines(source) == ["á", "β", "", "last\\r"]
        assert source.closes == 1
        for chunks, expected in [([], []), ([b"", b""], []), ([b"\\n"], [""]), ([b"a\\n\\n"], ["a", ""]), ([b"a\\r", b"\\n", b"b"], ["a", "b"]), ([b"a\\rb\\n"], ["a\\rb"]), ([b"head", b"", b"tail"], ["headtail"])]:
            source = Chunks(chunks)
            assert collect_lines(source) == expected
            assert source.closes == 1
        source = Chunks([b"one\\ntwo\\n", b"three\\n"])
        stream = iter_lines(source)
        assert (source.reads, source.closes) == (0, 0)
        assert next(stream) == "one"
        assert next(stream) == "two"
        assert (source.reads, source.closes) == (1, 0)
        stream.close()
        stream.close()
        assert (source.reads, source.closes) == (1, 1)
        source = Chunks([b"unused"])
        iter_lines(source).close()
        assert (source.reads, source.closes) == (0, 0)
        for chunks in ([b"\\xff"], [b"\\xc3"], [b"ok\\n", b"\\xe2", b"bad"]):
            source = Chunks(chunks)
            try:
                collect_lines(source)
            except UnicodeDecodeError:
                pass
            else:
                raise AssertionError("malformed UTF-8 accepted")
            assert source.closes == 1
        failure = RuntimeError("read failed")
        class FailingChunks(Chunks):
            def __next__(self):
                if self.reads == 1:
                    raise failure
                return super().__next__()
        source = FailingChunks([b"first\\n"])
        stream = iter_lines(source)
        assert next(stream) == "first"
        try:
            next(stream)
        except RuntimeError as exc:
            assert exc is failure
        else:
            raise AssertionError("source error swallowed")
        assert source.closes == 1
    ''',
)


TASKS: tuple[TaskSpec, ...] = (
    IMPORT, TRANSFER, DOCUMENTS, MONEY, STREAM, EXPORTS,
    RESERVATIONS, SHARES, CONFIG, LINES,
)
