import json
from textwrap import dedent

from domain import TaskSpec


def source(value: str) -> str:
    return dedent(value).strip() + "\n"


def task(identity, phase, family, request, files, reference, public, acceptance, structural=None):
    project = {
        "tsconfig.json": json.dumps({
            "compilerOptions": {"target": "ES2022", "module": "CommonJS", "strict": True,
                                "outDir": ".build", "rootDir": "src", "lib": ["ES2022", "DOM"],
                                "forceConsistentCasingInFileNames": True},
            "include": ["src/**/*.ts"],
        }, indent=2) + "\n",
        ".gitignore": ".build/\n",
        "README.md": "# Service workspace\n\nRun `tsc -p tsconfig.json && node checks/public.cjs` from this directory.\n",
        "checks/public.cjs": source("const assert = require('node:assert/strict');\n" + public),
        **{path: source(content) for path, content in files.items()},
    }
    return TaskSpec(identity, phase, family, "typescript", source(request) +
                    "\nYou may change src/ and add or update checks/. Preserve public interfaces unless the request explicitly changes them. "
                    "Run tsc -p tsconfig.json && node checks/public.cjs and describe the change.\n",
                    project, {path: source(content) for path, content in reference.items()},
                    source("const assert = require('node:assert/strict');\n" + acceptance),
                    ("src/", "checks/"), source(structural) if structural else None)


PAGINATION = task(
    "ts-cursor-orders", "screening", "feature",
    r"""
    Add cursor pagination to OrderHandler.list in src/handler.ts and src/repository.ts.
    Orders must be sorted ascending by createdAt, then id using lexicographic string order.
    Keep the tenant filter and limit behavior for requests without a cursor. A cursor is
    the literal createdAt + '|' + id of the last returned order; IDs and dates never contain '|'.
    Add nextCursor: string | null to the response: null if no further matching order exists.
    A cursor resumes strictly after that pair, even if its row has since been deleted.
    Never repeat or skip equal-date orders. An empty tenant or cursor without exactly two
    nonempty parts, or a limit that is not an integer from 1 through 100, throws Error('invalid request').
    Filtering must precede pagination, including when the cursor pair belongs to another tenant.
    Do not mutate the repository's input array or rows.
    """,
    {
        "src/types.ts": r"""
            export interface Order { id: string; tenant: string; createdAt: string; total: number }
            export interface ListRequest { tenant: string; limit: number; cursor?: string }
            export interface Page { items: Order[]; nextCursor: string | null }
        """,
        "src/repository.ts": r"""
            import { Order } from './types';
            export class OrderRepository {
              constructor(private readonly rows: Order[]) {}
              list(tenant: string): Order[] {
                return this.rows.filter(row => row.tenant === tenant).sort((a, b) =>
                  a.createdAt < b.createdAt ? -1 : a.createdAt > b.createdAt ? 1 : a.id < b.id ? -1 : a.id > b.id ? 1 : 0);
              }
            }
        """,
        "src/handler.ts": r"""
            import { OrderRepository } from './repository';
            import { ListRequest, Page } from './types';
            export class OrderHandler {
              constructor(private readonly repository: OrderRepository) {}
              list(request: ListRequest): Page {
                if (!request.tenant || !Number.isInteger(request.limit) || request.limit < 1 || request.limit > 100) {
                  throw new Error('invalid request');
                }
                return { items: this.repository.list(request.tenant).slice(0, request.limit), nextCursor: null };
              }
            }
        """,
    },
    {"src/handler.ts": r"""
        import { OrderRepository } from './repository';
        import { ListRequest, Page } from './types';
        export class OrderHandler {
          constructor(private readonly repository: OrderRepository) {}
          list(request: ListRequest): Page {
            if (!request.tenant || !Number.isInteger(request.limit) || request.limit < 1 || request.limit > 100) {
              throw new Error('invalid request');
            }
            let rows = this.repository.list(request.tenant);
            if (request.cursor !== undefined) {
              const parts = request.cursor.split('|');
              const date = parts[0];
              const id = parts[1];
              if (parts.length !== 2 || !date || !id) throw new Error('invalid request');
              rows = rows.filter(row => row.createdAt > date || (row.createdAt === date && row.id > id));
            }
            const items = rows.slice(0, request.limit);
            const last = items[items.length - 1];
            return { items, nextCursor: rows.length > request.limit && last ? last.createdAt + '|' + last.id : null };
          }
        }
    """},
    r"""
        const { OrderHandler } = require('../.build/handler');
        const { OrderRepository } = require('../.build/repository');
        const handler = new OrderHandler(new OrderRepository([
          { id: 'b', tenant: 'a', createdAt: '2026-01-02', total: 2 },
          { id: 'x', tenant: 'b', createdAt: '2026-01-01', total: 3 },
          { id: 'a', tenant: 'a', createdAt: '2026-01-01', total: 1 }
        ]));
        assert.deepEqual(handler.list({ tenant: 'a', limit: 1 }).items.map(x => x.id), ['a']);
        assert.throws(() => handler.list({ tenant: 'a', limit: 0 }), /invalid request/);
    """,
    r"""
        const { OrderHandler } = require('./.build/handler');
        const { OrderRepository } = require('./.build/repository');
        const rows = [
          { id: 'z', tenant: 'a', createdAt: '2026-01-03', total: 4 },
          { id: 'b', tenant: 'a', createdAt: '2026-01-01', total: 2 },
          { id: 'c', tenant: 'a', createdAt: '2026-01-01', total: 3 },
          { id: 'aa', tenant: 'b', createdAt: '2026-01-01', total: 99 },
          { id: 'a', tenant: 'a', createdAt: '2026-01-01', total: 1 }
        ];
        const before = JSON.stringify(rows);
        const h = new OrderHandler(new OrderRepository(rows));
        let page = h.list({ tenant: 'a', limit: 2 });
        assert.deepEqual(page.items.map(x => x.id), ['a', 'b']);
        assert.equal(page.nextCursor, '2026-01-01|b');
        page = h.list({ tenant: 'a', limit: 1, cursor: page.nextCursor });
        assert.deepEqual(page.items.map(x => x.id), ['c']);
        assert.equal(page.nextCursor, '2026-01-01|c');
        assert.deepEqual(h.list({ tenant: 'a', limit: 2, cursor: '2026-01-01|c' }),
          { items: [rows[0]], nextCursor: null });
        assert.deepEqual(h.list({ tenant: 'a', limit: 10, cursor: '2026-01-01|bb' }).items.map(x => x.id), ['c', 'z']);
        assert.deepEqual(h.list({ tenant: 'a', limit: 10, cursor: '2026-01-01|aa' }).items.map(x => x.id), ['b', 'c', 'z']);
        assert.deepEqual(h.list({ tenant: 'none', limit: 100 }), { items: [], nextCursor: null });
        assert.deepEqual(h.list({ tenant: 'a', limit: 2, cursor: '9999|z' }), { items: [], nextCursor: null });
        for (const cursor of ['', '|x', 'x|', 'x', 'x|y|z']) {
          assert.throws(() => h.list({ tenant: 'a', limit: 1, cursor }), /invalid request/);
        }
        for (const limit of [0, 101, 1.2, NaN, Infinity]) {
          assert.throws(() => h.list({ tenant: 'a', limit }), /invalid request/);
        }
        assert.throws(() => h.list({ tenant: '', limit: 1 }), /invalid request/);
        assert.equal(JSON.stringify(rows), before);
    """,
)


RETRY = task(
    "ts-idempotent-payment", "screening", "effects",
    r"""
    Fix PaymentService.pay in src/service.ts and Ledger.apply in src/ledger.ts so retries
    never duplicate a debit. Idempotency is scoped by tenant and key; a repeated equal
    amount returns the original receipt, including during concurrent calls. Reusing that
    tenant/key with another amount throws Error('key conflict') without another debit.
    Acknowledgement is external and may throw Transient after the debit committed.
    Retry only Transient, up to attempts total tries, forwarding the same receipt each time.
    Preserve the final thrown exception if retries are exhausted; do not retry other errors.
    Validate nonempty tenant/key, positive integer cents and attempts integer 1..5 before
    any ledger or transport action; invalid input throws Error('invalid payment').
    """,
    {
        "src/ledger.ts": r"""
            export interface Receipt { id: number; tenant: string; key: string; cents: number }
            export class Ledger {
              readonly entries: Receipt[] = [];
              async apply(tenant: string, key: string, cents: number): Promise<Receipt> {
                const receipt = { id: this.entries.length + 1, tenant, key, cents };
                this.entries.push(receipt);
                return receipt;
              }
            }
        """,
        "src/transport.ts": r"""
            import { Receipt } from './ledger';
            export class Transient extends Error {}
            export interface Transport { acknowledge(receipt: Receipt): Promise<void> }
        """,
        "src/service.ts": r"""
            import { Ledger, Receipt } from './ledger';
            import { Transient, Transport } from './transport';
            export class PaymentService {
              constructor(private readonly ledger: Ledger, private readonly transport: Transport) {}
              async pay(tenant: string, key: string, cents: number, attempts = 3): Promise<Receipt> {
                if (!tenant || !key || !Number.isInteger(cents) || cents <= 0) throw new Error('invalid payment');
                for (let n = 0; n < attempts; n++) {
                  try {
                    const receipt = await this.ledger.apply(tenant, key, cents);
                    await this.transport.acknowledge(receipt);
                    return receipt;
                  } catch (error) {
                    if (!(error instanceof Transient) || n === attempts - 1) throw error;
                  }
                }
                throw new Error('invalid payment');
              }
            }
        """,
    },
    {
        "src/ledger.ts": r"""
            export interface Receipt { id: number; tenant: string; key: string; cents: number }
            export class Ledger {
              readonly entries: Receipt[] = [];
              private readonly receipts = new Map<string, Map<string, Receipt>>();
              async apply(tenant: string, key: string, cents: number): Promise<Receipt> {
                let tenantReceipts = this.receipts.get(tenant);
                const prior = tenantReceipts?.get(key);
                if (prior) {
                  if (prior.cents !== cents) throw new Error('key conflict');
                  return prior;
                }
                const receipt = { id: this.entries.length + 1, tenant, key, cents };
                if (!tenantReceipts) {
                  tenantReceipts = new Map();
                  this.receipts.set(tenant, tenantReceipts);
                }
                tenantReceipts.set(key, receipt);
                this.entries.push(receipt);
                return receipt;
              }
            }
        """,
        "src/service.ts": r"""
            import { Ledger, Receipt } from './ledger';
            import { Transient, Transport } from './transport';
            export class PaymentService {
              constructor(private readonly ledger: Ledger, private readonly transport: Transport) {}
              async pay(tenant: string, key: string, cents: number, attempts = 3): Promise<Receipt> {
                if (!tenant || !key || !Number.isInteger(cents) || cents <= 0 || !Number.isInteger(attempts) || attempts < 1 || attempts > 5) {
                  throw new Error('invalid payment');
                }
                for (let n = 0; n < attempts; n++) {
                  try {
                    const receipt = await this.ledger.apply(tenant, key, cents);
                    await this.transport.acknowledge(receipt);
                    return receipt;
                  } catch (error) {
                    if (!(error instanceof Transient) || n === attempts - 1) throw error;
                  }
                }
                throw new Error('invalid payment');
              }
            }
        """,
    },
    r"""
        const { Ledger } = require('../.build/ledger');
        const { PaymentService } = require('../.build/service');
        async function main() {
          const ledger = new Ledger(); const receipts = [];
          const service = new PaymentService(ledger, { acknowledge: async r => { receipts.push(r); } });
          assert.deepEqual(await service.pay('shop', 'sale', 123), { id: 1, tenant: 'shop', key: 'sale', cents: 123 });
          assert.equal(ledger.entries.length, 1); assert.equal(receipts.length, 1);
          await assert.rejects(service.pay('shop', 'bad', 0), /invalid payment/);
        }
        module.exports = main();
    """,
    r"""
        const { Ledger } = require('./.build/ledger');
        const { PaymentService } = require('./.build/service');
        const { Transient } = require('./.build/transport');
        async function main() {
          const ledger = new Ledger(); const acknowledgements = []; let failures = 2;
          const service = new PaymentService(ledger, { acknowledge: async r => {
            acknowledgements.push(r.id); if (failures-- > 0) throw new Transient('try later');
          } });
          const receipt = await service.pay('a', 'k', 50, 3);
          assert.deepEqual(acknowledgements, [1, 1, 1]); assert.equal(ledger.entries.length, 1);
          assert.deepEqual(await service.pay('a', 'k', 50), receipt);
          assert.equal(ledger.entries.length, 1);
          const callsBefore = acknowledgements.length;
          await assert.rejects(service.pay('a', 'k', 51), /key conflict/);
          assert.equal(acknowledgements.length, callsBefore); assert.equal(ledger.entries.length, 1);
          assert.equal((await service.pay('b', 'k', 50)).id, 2);
          assert.equal((await service.pay('a', 'other', 50)).id, 3);
          const results = await Promise.all([service.pay('a', 'parallel', 20), service.pay('a', 'parallel', 20)]);
          assert.deepEqual(results[0], results[1]); assert.equal(ledger.entries.length, 4);
          const beforeInvalid = acknowledgements.length;
          for (const args of [['', 'v', 1, 3], ['a', '', 1, 3], ['a', 'v', 0, 3], ['a', 'v', -1, 3],
            ['a', 'v', 1.5, 3], ['a', 'v', Infinity, 3], ['a', 'v', 1, 0], ['a', 'v', 1, 6], ['a', 'v', 1, 1.5]]) {
            await assert.rejects(service.pay(...args), /invalid payment/);
          }
          assert.equal(ledger.entries.length, 4); assert.equal(acknowledgements.length, beforeInvalid);
          let count = 0; const terminal = new Transient('terminal');
          const exhausted = new PaymentService(ledger, { acknowledge: async () => { count++; throw terminal; } });
          await assert.rejects(exhausted.pay('a', 'exhaust', 1, 5), e => e === terminal);
          assert.equal(count, 5); assert.equal(ledger.entries.length, 5);
          count = 0; const permanent = new Error('permanent');
          const fatal = new PaymentService(ledger, { acknowledge: async () => { count++; throw permanent; } });
          await assert.rejects(fatal.pay('a', 'fatal', 1, 5), e => e === permanent);
          assert.equal(count, 1); assert.equal(ledger.entries.length, 6);
          const colliding = new Ledger(); const direct = new PaymentService(colliding, { acknowledge: async () => {} });
          await direct.pay('a:b', 'c', 10); await direct.pay('a', 'b:c', 20);
          assert.equal(colliding.entries.length, 2);
          const conflicting = await Promise.allSettled([direct.pay('a', 'race', 10), direct.pay('a', 'race', 11)]);
          assert.equal(conflicting[0].status, 'fulfilled'); assert.equal(conflicting[1].status, 'rejected');
          assert.equal(conflicting[1].reason.message, 'key conflict'); assert.equal(colliding.entries.length, 3);
          let once = 0;
          const single = new PaymentService(colliding, { acknowledge: async () => { once++; throw terminal; } });
          await assert.rejects(single.pay('a', 'one-try', 1, 1), e => e === terminal); assert.equal(once, 1);
        }
        module.exports = main();
    """,
)


AUTHORIZATION = task(
    "ts-archive-document", "screening", "authorization",
    r"""
    Add authorization to DocumentService.archive in src/service.ts. Actors have tenant,
    user and role: admin, editor or viewer. Only active documents in the actor's tenant
    are visible. Missing, deleted and foreign-tenant documents all throw Error('not found'),
    even for admin. An admin may archive any visible document; an editor only one they own;
    a viewer never may. Unauthorized visible requests throw Error('forbidden'). On success
    set archived true and append exactly {actor: actor.user, document: id} to audit.
    Repeating archive on an already archived visible document is a no-op, but still enforce
    permission first. Failures must leave every document and audit entry unchanged.
    """,
    {
        "src/types.ts": r"""
            export interface Document { id: string; tenant: string; owner: string; deleted: boolean; archived: boolean }
            export interface Actor { tenant: string; user: string; role: 'admin' | 'editor' | 'viewer' }
        """,
        "src/repository.ts": r"""
            import { Document } from './types';
            export class DocumentRepository {
              readonly audit: { actor: string; document: string }[] = [];
              constructor(readonly documents: Document[]) {}
              find(id: string): Document | undefined { return this.documents.find(row => row.id === id); }
              archive(document: Document, actor: string): void {
                document.archived = true; this.audit.push({ actor, document: document.id });
              }
            }
        """,
        "src/service.ts": r"""
            import { Actor } from './types';
            import { DocumentRepository } from './repository';
            export class DocumentService {
              constructor(private readonly repository: DocumentRepository) {}
              archive(actor: Actor, id: string): void {
                const document = this.repository.find(id);
                if (!document) throw new Error('not found');
                if (!document.archived) this.repository.archive(document, actor.user);
              }
            }
        """,
    },
    {"src/service.ts": r"""
        import { Actor } from './types';
        import { DocumentRepository } from './repository';
        export class DocumentService {
          constructor(private readonly repository: DocumentRepository) {}
          archive(actor: Actor, id: string): void {
            const document = this.repository.find(id);
            if (!document || document.tenant !== actor.tenant || document.deleted) throw new Error('not found');
            if (actor.role === 'viewer' || (actor.role === 'editor' && document.owner !== actor.user)) throw new Error('forbidden');
            if (!document.archived) this.repository.archive(document, actor.user);
          }
        }
    """},
    r"""
        const { DocumentRepository } = require('../.build/repository');
        const { DocumentService } = require('../.build/service');
        const repo = new DocumentRepository([{ id: 'one', tenant: 'a', owner: 'u', deleted: false, archived: false }]);
        const service = new DocumentService(repo); const admin = { tenant: 'a', user: 'u', role: 'admin' };
        service.archive(admin, 'one'); assert.equal(repo.documents[0].archived, true);
        service.archive(admin, 'one'); assert.deepEqual(repo.audit, [{ actor: 'u', document: 'one' }]);
        assert.throws(() => service.archive(admin, 'missing'), /not found/);
    """,
    r"""
        const { DocumentRepository } = require('./.build/repository');
        const { DocumentService } = require('./.build/service');
        const fresh = () => new DocumentRepository([
          { id: 'own', tenant: 'a', owner: 'me', deleted: false, archived: false },
          { id: 'other', tenant: 'a', owner: 'else', deleted: false, archived: false },
          { id: 'foreign', tenant: 'b', owner: 'me', deleted: false, archived: false },
          { id: 'deleted', tenant: 'a', owner: 'me', deleted: true, archived: false },
          { id: 'done', tenant: 'a', owner: 'else', deleted: false, archived: true }
        ]);
        for (const role of ['admin', 'editor', 'viewer']) {
          for (const id of ['foreign', 'deleted', 'missing']) {
            const repo = fresh(); const before = JSON.stringify(repo);
            assert.throws(() => new DocumentService(repo).archive({ tenant: 'a', user: 'me', role }, id), /^Error: not found$/);
            assert.equal(JSON.stringify(repo), before);
          }
        }
        for (const [role, id] of [['viewer', 'own'], ['viewer', 'done'], ['editor', 'other'], ['editor', 'done']]) {
          const repo = fresh(); const before = JSON.stringify(repo);
          assert.throws(() => new DocumentService(repo).archive({ tenant: 'a', user: 'me', role }, id), /^Error: forbidden$/);
          assert.equal(JSON.stringify(repo), before);
        }
        const repo = fresh(); const service = new DocumentService(repo);
        service.archive({ tenant: 'a', user: 'me', role: 'editor' }, 'own');
        service.archive({ tenant: 'a', user: 'me', role: 'editor' }, 'own');
        service.archive({ tenant: 'a', user: 'boss', role: 'admin' }, 'other');
        service.archive({ tenant: 'a', user: 'boss', role: 'admin' }, 'done');
        assert.deepEqual(repo.audit, [{ actor: 'me', document: 'own' }, { actor: 'boss', document: 'other' }]);
        assert.equal(repo.documents[2].archived, false); assert.equal(repo.documents[3].archived, false);
    """,
)


VALIDATION = task(
    "ts-profile-patch", "screening", "validation",
    r"""
    Implement the PATCH contract in src/parser.ts and src/service.ts. Input is an unknown
    plain object with only displayName and tags keys, with Object.prototype or null as its
    prototype. Arrays, null and nonobjects are invalid.
    Absent fields retain the stored value. displayName null clears it; a string is trimmed
    and must have length 1..40 after trimming. tags null or [] clears tags; otherwise tags
    is an array of at most five distinct nonempty strings, trimmed before uniqueness checks.
    Every tag may have at most 12 characters after trimming. Do not coerce numeric values.
    Any invalid field or unknown key throws Error('invalid profile') and leaves storage unchanged.
    An empty object is a valid no-op. Return the resulting profile without changing the input
    object or reusing the caller's tags array for storage. Begin with ProfileService.patch.
    """,
    {
        "src/types.ts": r"""
            export interface Profile { displayName: string | null; tags: string[] }
            export type Field<T> = { kind: 'keep' } | { kind: 'set'; value: T };
            export interface ProfilePatch { displayName: Field<string | null>; tags: Field<string[]> }
        """,
        "src/parser.ts": r"""
            import { ProfilePatch } from './types';
            export function parseProfile(input: unknown): ProfilePatch {
              if (typeof input !== 'object' || input === null || Array.isArray(input)) throw new Error('invalid profile');
              let displayName: ProfilePatch['displayName'] = { kind: 'keep' };
              let tags: ProfilePatch['tags'] = { kind: 'keep' };
              if ('displayName' in input && typeof input.displayName === 'string' && input.displayName) {
                displayName = { kind: 'set', value: input.displayName };
              }
              if ('tags' in input && Array.isArray(input.tags)) {
                const strings: string[] = [];
                for (const value of input.tags) if (typeof value === 'string') strings.push(value);
                tags = { kind: 'set', value: strings };
              }
              return { displayName, tags };
            }
        """,
        "src/service.ts": r"""
            import { Profile } from './types';
            import { parseProfile } from './parser';
            export class ProfileService {
              constructor(readonly profile: Profile) {}
              patch(input: unknown): Profile {
                const parsed = parseProfile(input);
                if (parsed.displayName.kind === 'set') this.profile.displayName = parsed.displayName.value;
                if (parsed.tags.kind === 'set') this.profile.tags = parsed.tags.value;
                return this.profile;
              }
            }
        """,
    },
    {"src/parser.ts": r"""
        import { ProfilePatch } from './types';
        export function parseProfile(input: unknown): ProfilePatch {
          if (typeof input !== 'object' || input === null || Array.isArray(input)) throw new Error('invalid profile');
          if (Object.getPrototypeOf(input) !== Object.prototype && Object.getPrototypeOf(input) !== null) throw new Error('invalid profile');
          for (const key of Object.keys(input)) if (key !== 'displayName' && key !== 'tags') throw new Error('invalid profile');
          let displayName: ProfilePatch['displayName'] = { kind: 'keep' };
          let tags: ProfilePatch['tags'] = { kind: 'keep' };
          if ('displayName' in input) {
            const value = input.displayName;
            if (value === null) displayName = { kind: 'set', value: null };
            else if (typeof value === 'string' && value.trim().length >= 1 && value.trim().length <= 40) {
              displayName = { kind: 'set', value: value.trim() };
            } else throw new Error('invalid profile');
          }
          if ('tags' in input) {
            if (input.tags === null) tags = { kind: 'set', value: [] };
            else {
              if (!Array.isArray(input.tags) || input.tags.length > 5) throw new Error('invalid profile');
              const values: string[] = [];
              for (const value of input.tags) {
                if (typeof value !== 'string') throw new Error('invalid profile');
                const trimmed = value.trim();
                if (!trimmed || trimmed.length > 12 || values.includes(trimmed)) throw new Error('invalid profile');
                values.push(trimmed);
              }
              tags = { kind: 'set', value: values };
            }
          }
          return { displayName, tags };
        }
    """},
    r"""
        const { ProfileService } = require('../.build/service');
        const service = new ProfileService({ displayName: 'before', tags: ['old'] });
        assert.deepEqual(service.patch({ displayName: 'after' }), { displayName: 'after', tags: ['old'] });
        assert.deepEqual(service.patch({ tags: ['new'] }), { displayName: 'after', tags: ['new'] });
        assert.throws(() => service.patch(null), /invalid profile/);
    """,
    r"""
        const { ProfileService } = require('./.build/service');
        const service = new ProfileService({ displayName: 'before', tags: ['old'] });
        assert.deepEqual(service.patch({}), { displayName: 'before', tags: ['old'] });
        assert.deepEqual(service.patch({ displayName: null }), { displayName: null, tags: ['old'] });
        const input = { displayName: '  Ada  ', tags: [' a ', 'b'] }; const before = JSON.stringify(input);
        assert.deepEqual(service.patch(input), { displayName: 'Ada', tags: ['a', 'b'] });
        assert.equal(JSON.stringify(input), before); input.tags.push('caller');
        assert.deepEqual(service.profile.tags, ['a', 'b']);
        assert.deepEqual(service.patch({ tags: null }), { displayName: 'Ada', tags: [] });
        assert.deepEqual(service.patch({ displayName: 'x'.repeat(40), tags: ['x'.repeat(12)] }),
          { displayName: 'x'.repeat(40), tags: ['x'.repeat(12)] });
        const bad = [[], 3, 'x', null, new Date(), new (class ProfileInput {})(), { extra: 1 }, { displayName: undefined }, { displayName: 5 },
          { displayName: '' }, { displayName: '   ' }, { displayName: 'x'.repeat(41) },
          { tags: undefined }, { tags: 'a' }, { tags: [1] }, { tags: [''] }, { tags: ['  '] },
          { tags: ['same', ' same '] }, { tags: ['x'.repeat(13)] }, { tags: ['a', 'b', 'c', 'd', 'e', 'f'] },
          { displayName: 'must not commit', tags: [false] }, { tags: ['valid'], displayName: '' }];
        for (const input of bad) {
          const snapshot = JSON.stringify(service.profile);
          assert.throws(() => service.patch(input), /^Error: invalid profile$/);
          assert.equal(JSON.stringify(service.profile), snapshot);
        }
        assert.deepEqual(service.patch({ tags: [] }).tags, []);
        assert.deepEqual(service.patch({ tags: ['a', 'b', 'c', 'd', 'e'] }).tags, ['a', 'b', 'c', 'd', 'e']);
        const noPrototype = Object.create(null); noPrototype.displayName = '  Grace ';
        assert.equal(service.patch(noPrototype).displayName, 'Grace');
    """,
)


STREAMING = task(
    "ts-event-stream", "screening", "streaming",
    r"""
    Fix EventService.stream in src/service.ts so each opened lease is closed exactly once
    on normal exhaustion, consumer break/return, source read failure, mapper failure or a
    consumer-injected throw. Preserve the original read, mapper or injected exception if close also fails;
    otherwise propagate a close failure. Do not open a lease until first iteration and do
    not read ahead: one read for each next(), except the read establishing exhaustion.
    stream still yields mapped records in order. Returning an unopened generator must not
    open or close anything. Add relevant checks with the source interface in src/source.ts.
    """,
    {
        "src/source.ts": r"""
            export interface Lease { read(): Promise<string | null>; close(): Promise<void> }
            export interface Source { open(): Promise<Lease> }
        """,
        "src/mapper.ts": r"""
            export function mapEvent(value: string): string { return value.toUpperCase(); }
        """,
        "src/service.ts": r"""
            import { Source } from './source';
            import { mapEvent } from './mapper';
            export class EventService {
              constructor(private readonly source: Source, private readonly mapper: (value: string) => string = mapEvent) {}
              async *stream(): AsyncGenerator<string> {
                const lease = await this.source.open();
                for (;;) {
                  const value = await lease.read();
                  if (value === null) break;
                  yield this.mapper(value);
                }
                await lease.close();
              }
            }
        """,
    },
    {"src/service.ts": r"""
        import { Source } from './source';
        import { mapEvent } from './mapper';
        export class EventService {
          constructor(private readonly source: Source, private readonly mapper: (value: string) => string = mapEvent) {}
          async *stream(): AsyncGenerator<string> {
            const lease = await this.source.open();
            let failed = false;
            try {
              for (;;) {
                const value = await lease.read();
                if (value === null) break;
                yield this.mapper(value);
              }
            } catch (error) { failed = true; throw error; }
            finally {
              try { await lease.close(); }
              catch (error) { if (!failed) throw error; }
            }
          }
        }
    """},
    r"""
        const { EventService } = require('../.build/service');
        async function main() {
          let closes = 0; const values = ['a', 'b', null];
          const service = new EventService({ open: async () => ({ read: async () => values.shift(), close: async () => { closes++; } }) });
          const found = []; for await (const value of service.stream()) found.push(value);
          assert.deepEqual(found, ['A', 'B']); assert.equal(closes, 1);
        }
        module.exports = main();
    """,
    r"""
        const { EventService } = require('./.build/service');
        function fixture({ values = ['a', 'b'], readError, closeError } = {}) {
          const counts = { opens: 0, reads: 0, closes: 0 }; let position = 0;
          const source = { open: async () => { counts.opens++; return {
            read: async () => { counts.reads++; if (readError && position === 1) throw readError; return values[position++] ?? null; },
            close: async () => { counts.closes++; if (closeError) throw closeError; }
          }; } }; return { counts, source };
        }
        async function main() {
          const unused = fixture(); const unopened = new EventService(unused.source).stream();
          assert.deepEqual(unused.counts, { opens: 0, reads: 0, closes: 0 });
          await unopened.return(); assert.deepEqual(unused.counts, { opens: 0, reads: 0, closes: 0 });
          const early = fixture(); const iter = new EventService(early.source).stream();
          assert.deepEqual(await iter.next(), { value: 'A', done: false });
          assert.deepEqual(early.counts, { opens: 1, reads: 1, closes: 0 });
          await iter.return(); await iter.return(); assert.deepEqual(early.counts, { opens: 1, reads: 1, closes: 1 });
          const broken = fixture(); for await (const value of new EventService(broken.source).stream()) { assert.equal(value, 'A'); break; }
          assert.deepEqual(broken.counts, { opens: 1, reads: 1, closes: 1 });
          const full = fixture(); const all = []; for await (const v of new EventService(full.source).stream()) all.push(v);
          assert.deepEqual(all, ['A', 'B']); assert.deepEqual(full.counts, { opens: 1, reads: 3, closes: 1 });
          const empty = fixture({ values: [] }); for await (const _ of new EventService(empty.source).stream()) assert.fail('unexpected value');
          assert.deepEqual(empty.counts, { opens: 1, reads: 1, closes: 1 });
          const original = new Error('read failed'); const close = new Error('close failed');
          const failing = fixture({ readError: original, closeError: close });
          const failingIter = new EventService(failing.source).stream(); await failingIter.next();
          await assert.rejects(failingIter.next(), e => e === original); assert.equal(failing.counts.closes, 1);
          const mapped = fixture({ closeError: close }); const mapperError = new Error('mapping failed');
          await assert.rejects(new EventService(mapped.source, () => { throw mapperError; }).stream().next(), e => e === mapperError);
          assert.equal(mapped.counts.closes, 1);
          const injected = fixture({ closeError: close }); const injectedIter = new EventService(injected.source).stream();
          await injectedIter.next(); const injectedError = new Error('consumer failed');
          await assert.rejects(injectedIter.throw(injectedError), e => e === injectedError); assert.equal(injected.counts.closes, 1);
          const closing = fixture({ closeError: close }); const closingIter = new EventService(closing.source).stream();
          await closingIter.next(); await assert.rejects(closingIter.return(), e => e === close);
          assert.deepEqual(closing.counts, { opens: 1, reads: 1, closes: 1 });
          const complete = fixture({ values: [], closeError: close });
          await assert.rejects(new EventService(complete.source).stream().next(), e => e === close);
          let opened = 0; const openError = new Error('open failed');
          await assert.rejects(new EventService({ open: async () => { opened++; throw openError; } }).stream().next(), e => e === openError);
          assert.equal(opened, 1);
        }
        module.exports = main();
    """,
)


REFACTOR = task(
    "ts-money-consolidation", "screening", "refactor",
    r"""
    Consolidate the duplicated cent conversions used by invoice.ts and report.ts into
    src/money.ts exporting formatAmount(cents: number): string. Both existing renderers
    must import and use this shared function. Remove the old exported API names
    invoiceAmount and reportAmount from all src/ code, migrating all callers in one change;
    the old modules may be deleted or left empty. Preserve renderInvoice and renderReport
    interfaces and exact existing output for positive, zero and negative integer cents.
    formatAmount returns sign plus absolute whole currency units and exactly two fraction
    digits, with no currency symbol. Do not change rounding or report line order.
    """,
    {
        "src/invoiceAmount.ts": r"""
            export function invoiceAmount(cents: number): string {
              const sign = cents < 0 ? '-' : ''; const absolute = Math.abs(cents);
              return sign + Math.floor(absolute / 100) + '.' + String(absolute % 100).padStart(2, '0');
            }
        """,
        "src/reportAmount.ts": r"""
            export function reportAmount(cents: number): string {
              const absolute = Math.abs(cents);
              return (cents < 0 ? '-' : '') + Math.floor(absolute / 100) + '.' + String(absolute % 100).padStart(2, '0');
            }
        """,
        "src/invoice.ts": r"""
            import { invoiceAmount } from './invoiceAmount';
            export function renderInvoice(id: string, cents: number): string { return id + ': $' + invoiceAmount(cents); }
        """,
        "src/report.ts": r"""
            import { reportAmount } from './reportAmount';
            export function renderReport(rows: { id: string; cents: number }[]): string {
              return rows.map(row => row.id + ',' + reportAmount(row.cents)).join('\n');
            }
        """,
    },
    {
        "src/invoiceAmount.ts": "export {};",
        "src/reportAmount.ts": "export {};",
        "src/money.ts": r"""
            export function formatAmount(cents: number): string {
              const absolute = Math.abs(cents);
              return (cents < 0 ? '-' : '') + Math.floor(absolute / 100) + '.' + String(absolute % 100).padStart(2, '0');
            }
        """,
        "src/invoice.ts": r"""
            import { formatAmount } from './money';
            export function renderInvoice(id: string, cents: number): string { return id + ': $' + formatAmount(cents); }
        """,
        "src/report.ts": r"""
            import { formatAmount } from './money';
            export function renderReport(rows: { id: string; cents: number }[]): string {
              return rows.map(row => row.id + ',' + formatAmount(row.cents)).join('\n');
            }
        """,
    },
    r"""
        const { renderInvoice } = require('../.build/invoice'); const { renderReport } = require('../.build/report');
        assert.equal(renderInvoice('inv', 123), 'inv: $1.23');
        assert.equal(renderReport([{ id: 'a', cents: 0 }, { id: 'b', cents: -1 }]), 'a,0.00\nb,-0.01');
    """,
    r"""
        const { renderInvoice } = require('./.build/invoice'); const { renderReport } = require('./.build/report');
        const examples = [[0, '0.00'], [1, '0.01'], [9, '0.09'], [100, '1.00'], [199, '1.99'],
          [-1, '-0.01'], [-100, '-1.00'], [-199, '-1.99'], [100001, '1000.01'], [-100001, '-1000.01']];
        for (const [cents, expected] of examples) assert.equal(renderInvoice('item', cents), 'item: $' + expected);
        assert.equal(renderReport([]), '');
        assert.equal(renderReport([{ id: 'z', cents: -199 }, { id: 'a', cents: 1 }]), 'z,-1.99\na,0.01');
    """,
    r"""
        const fs = require('node:fs'); const path = require('node:path'); const assert = require('node:assert/strict');
        function texts(dir) { return fs.readdirSync(dir, { withFileTypes: true }).flatMap(e =>
          e.isDirectory() ? texts(path.join(dir, e.name)) : e.name.endsWith('.ts') ? [fs.readFileSync(path.join(dir, e.name), 'utf8')] : []); }
        const joined = texts('src').join('\n');
        assert.equal(/\b(invoiceAmount|reportAmount)\b/.test(joined), false, 'retire both old APIs and callers');
        const { formatAmount } = require('./.build/money');
        assert.equal(formatAmount(-9), '-0.09'); assert.equal(formatAmount(1200), '12.00');
        for (const name of ['invoice', 'report']) {
          assert.match(fs.readFileSync('src/' + name + '.ts', 'utf8'), /from\s*['"]\.\/money['"]/, 'import the shared conversion');
        }
        const money = require('./.build/money'); money.formatAmount = () => 'shared';
        assert.equal(require('./.build/invoice').renderInvoice('id', 1), 'id: $shared');
        assert.equal(require('./.build/report').renderReport([{ id: 'id', cents: 1 }]), 'id,shared');
    """,
)


INVENTORY = task(
    "ts-atomic-reservation", "confirmation", "feature-effects",
    r"""
    Extend ReservationService.reserve in src/service.ts to reserve a whole batch atomically.
    Lines contain sku and quantity. Quantity must be a positive safe integer and the batch
    must be nonempty; otherwise throw Error('invalid reservation'). Aggregate repeated SKUs
    before checking stock; aggregate quantities must remain safe integers. A missing SKU, a foreign-tenant SKU or insufficient aggregate
    stock throws Error('stock unavailable'). No stock or reservation record may change on
    any failure, including a bad final line. A successful reservation deducts the aggregate
    once and stores one record with lines sorted by sku using lexicographic string order.
    Require nonempty tenant and key. Scope idempotency by tenant/key: an equivalent batch
    in any line order returns the existing record without another deduction. A changed
    aggregate for the same tenant/key throws Error('key conflict'). Existing-record checks
    happen after input validation but before availability checks. Keep input arrays unchanged.
    """,
    {
        "src/types.ts": r"""
            export interface Line { sku: string; quantity: number }
            export interface Stock { tenant: string; sku: string; available: number }
            export interface Reservation { id: number; tenant: string; key: string; lines: Line[] }
        """,
        "src/store.ts": r"""
            import { Stock, Reservation } from './types';
            export class Store {
              readonly reservations: Reservation[] = [];
              constructor(readonly stock: Stock[]) {}
              find(tenant: string, sku: string): Stock | undefined {
                return this.stock.find(row => row.tenant === tenant && row.sku === sku);
              }
            }
        """,
        "src/service.ts": r"""
            import { Line, Reservation } from './types';
            import { Store } from './store';
            export class ReservationService {
              constructor(private readonly store: Store) {}
              reserve(tenant: string, key: string, lines: Line[]): Reservation {
                if (!tenant || !key || !lines.length) throw new Error('invalid reservation');
                for (const line of lines) {
                  if (!line.sku || !Number.isSafeInteger(line.quantity) || line.quantity <= 0) throw new Error('invalid reservation');
                  const row = this.store.find(tenant, line.sku);
                  if (!row || row.available < line.quantity) throw new Error('stock unavailable');
                  row.available -= line.quantity;
                }
                const record = { id: this.store.reservations.length + 1, tenant, key, lines: lines.map(line => ({ ...line })) };
                this.store.reservations.push(record);
                return record;
              }
            }
        """,
    },
    {"src/service.ts": r"""
        import { Line, Reservation, Stock } from './types';
        import { Store } from './store';
        export class ReservationService {
          constructor(private readonly store: Store) {}
          reserve(tenant: string, key: string, lines: Line[]): Reservation {
            if (!tenant || !key || !lines.length) throw new Error('invalid reservation');
            const totals = new Map<string, number>();
            for (const line of lines) {
              if (!line.sku || !Number.isSafeInteger(line.quantity) || line.quantity <= 0) throw new Error('invalid reservation');
              const total = (totals.get(line.sku) ?? 0) + line.quantity;
              if (!Number.isSafeInteger(total)) throw new Error('invalid reservation');
              totals.set(line.sku, total);
            }
            const normalized = [...totals].sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0).map(([sku, quantity]) => ({ sku, quantity }));
            const prior = this.store.reservations.find(record => record.tenant === tenant && record.key === key);
            if (prior) {
              if (JSON.stringify(prior.lines) !== JSON.stringify(normalized)) throw new Error('key conflict');
              return prior;
            }
            const adjustments: { row: Stock; quantity: number }[] = [];
            for (const line of normalized) {
              const row = this.store.find(tenant, line.sku);
              if (!row || row.available < line.quantity) throw new Error('stock unavailable');
              adjustments.push({ row, quantity: line.quantity });
            }
            for (const adjustment of adjustments) adjustment.row.available -= adjustment.quantity;
            const record = { id: this.store.reservations.length + 1, tenant, key, lines: normalized };
            this.store.reservations.push(record);
            return record;
          }
        }
    """},
    r"""
        const { Store } = require('../.build/store'); const { ReservationService } = require('../.build/service');
        const store = new Store([{ tenant: 'a', sku: 'x', available: 5 }]);
        assert.deepEqual(new ReservationService(store).reserve('a', 'one', [{ sku: 'x', quantity: 2 }]),
          { id: 1, tenant: 'a', key: 'one', lines: [{ sku: 'x', quantity: 2 }] });
        assert.equal(store.stock[0].available, 3);
    """,
    r"""
        const { Store } = require('./.build/store'); const { ReservationService } = require('./.build/service');
        const fresh = () => new Store([{ tenant: 'a', sku: 'x', available: 5 },
          { tenant: 'a', sku: 'y', available: 10 }, { tenant: 'b', sku: 'private', available: 100 }]);
        for (const lines of [[{ sku: 'x', quantity: 3 }, { sku: 'x', quantity: 3 }],
          [{ sku: 'x', quantity: 1 }, { sku: 'missing', quantity: 1 }],
          [{ sku: 'x', quantity: 1 }, { sku: 'private', quantity: 1 }]]) {
          const store = fresh(); const before = JSON.stringify(store);
          assert.throws(() => new ReservationService(store).reserve('a', 'fail', lines), /^Error: stock unavailable$/);
          assert.equal(JSON.stringify(store), before);
        }
        for (const quantity of [0, -1, 1.5, NaN, Infinity, Number.MAX_SAFE_INTEGER + 1]) {
          const store = fresh(); const before = JSON.stringify(store);
          assert.throws(() => new ReservationService(store).reserve('a', 'bad', [{ sku: 'x', quantity: 1 }, { sku: 'y', quantity }]), /invalid reservation/);
          assert.equal(JSON.stringify(store), before);
        }
        const store = fresh(); const service = new ReservationService(store);
        const input = [{ sku: 'y', quantity: 2 }, { sku: 'x', quantity: 2 }, { sku: 'x', quantity: 3 }];
        const before = JSON.stringify(input); const record = service.reserve('a', 'ok', input);
        assert.deepEqual(record.lines, [{ sku: 'x', quantity: 5 }, { sku: 'y', quantity: 2 }]);
        assert.equal(JSON.stringify(input), before);
        assert.deepEqual(store.stock.map(row => row.available), [0, 8, 100]);
        assert.deepEqual(service.reserve('a', 'ok', [{ sku: 'x', quantity: 5 }, { sku: 'y', quantity: 2 }]), record);
        assert.deepEqual(store.stock.map(row => row.available), [0, 8, 100]); assert.equal(store.reservations.length, 1);
        const snapshot = JSON.stringify(store);
        assert.throws(() => service.reserve('a', 'ok', [{ sku: 'x', quantity: 4 }]), /^Error: key conflict$/);
        assert.equal(JSON.stringify(store), snapshot);
        assert.throws(() => service.reserve('a', 'ok', [{ sku: 'x', quantity: 0 }]), /^Error: invalid reservation$/);
        assert.equal(JSON.stringify(store), snapshot);
        assert.equal(service.reserve('b', 'ok', [{ sku: 'private', quantity: 1 }]).id, 2);
        for (const [tenant, key, lines] of [['', 'k', [{ sku: 'x', quantity: 1 }]], ['a', '', [{ sku: 'x', quantity: 1 }]],
          ['a', 'k', []], ['a', 'k', [{ sku: '', quantity: 1 }]],
          ['a', 'big', [{ sku: 'x', quantity: Number.MAX_SAFE_INTEGER }, { sku: 'x', quantity: 1 }]]]) {
          const snapshot = JSON.stringify(store);
          assert.throws(() => service.reserve(tenant, key, lines), /invalid reservation/);
          assert.equal(JSON.stringify(store), snapshot);
        }
    """,
)


CACHE = task(
    "ts-singleflight-cache", "confirmation", "streaming-effects",
    r"""
    Repair CatalogService.get in src/service.ts so concurrent requests for the same
    tenant/key share one loader invocation, while unrelated keys and tenants remain independent.
    Cache successful results for ttl milliseconds measured from successful completion using
    the injected clock; an entry expires at now >= completedAt + ttl. ttl must be a nonnegative
    finite number, validated by the constructor with Error('invalid ttl'). ttl zero still
    coalesces simultaneous pending calls but does not cache completed results. A rejected
    load is not cached; all waiting callers receive the original error, and the next call
    can load again. Only the leader starts the loader. Keep get returning Promise<string>
    and do not use real timers; fake clocks and controllable promises are supported.
    """,
    {
        "src/types.ts": r"""
            export type Loader = (tenant: string, key: string) => Promise<string>;
            export type Clock = () => number;
        """,
        "src/cache.ts": r"""
            export interface CacheEntry { value: string; expires: number }
            export class CatalogCache {
              private readonly entries = new Map<string, Map<string, CacheEntry>>();
              get(tenant: string, key: string): CacheEntry | undefined { return this.entries.get(tenant)?.get(key); }
              set(tenant: string, key: string, entry: CacheEntry): void {
                let items = this.entries.get(tenant);
                if (!items) { items = new Map(); this.entries.set(tenant, items); }
                items.set(key, entry);
              }
            }
        """,
        "src/service.ts": r"""
            import { Loader, Clock } from './types';
            import { CatalogCache } from './cache';
            export class CatalogService {
              private readonly cache = new CatalogCache();
              constructor(private readonly loader: Loader, private readonly clock: Clock, private readonly ttl: number) {}
              async get(tenant: string, key: string): Promise<string> {
                const existing = this.cache.get(tenant, key);
                if (existing && existing.expires > this.clock()) return existing.value;
                const started = this.clock(); const value = await this.loader(tenant, key);
                this.cache.set(tenant, key, { value, expires: started + this.ttl });
                return value;
              }
            }
        """,
    },
    {"src/service.ts": r"""
        import { Loader, Clock } from './types';
        import { CatalogCache } from './cache';
        export class CatalogService {
          private readonly cache = new CatalogCache();
          private readonly pending = new Map<string, Map<string, Promise<string>>>();
          constructor(private readonly loader: Loader, private readonly clock: Clock, private readonly ttl: number) {
            if (!Number.isFinite(ttl) || ttl < 0) throw new Error('invalid ttl');
          }
          async get(tenant: string, key: string): Promise<string> {
            const existing = this.cache.get(tenant, key);
            if (existing && existing.expires > this.clock()) return existing.value;
            let items = this.pending.get(tenant);
            const running = items?.get(key);
            if (running) return running;
            if (!items) { items = new Map(); this.pending.set(tenant, items); }
            const tenantItems = items;
            const promise = Promise.resolve().then(() => this.loader(tenant, key)).then(value => {
              if (this.ttl > 0) this.cache.set(tenant, key, { value, expires: this.clock() + this.ttl });
              return value;
            }).finally(() => {
              tenantItems.delete(key);
              if (tenantItems.size === 0) this.pending.delete(tenant);
            });
            tenantItems.set(key, promise);
            return promise;
          }
        }
    """},
    r"""
        const { CatalogService } = require('../.build/service');
        async function main() {
          let calls = 0; const service = new CatalogService(async () => { calls++; return 'book'; }, () => 0, 10);
          assert.equal(await service.get('shop', 'book'), 'book'); assert.equal(await service.get('shop', 'book'), 'book');
          assert.equal(calls, 1);
        }
        module.exports = main();
    """,
    r"""
        const { CatalogService } = require('./.build/service');
        function deferred() { let resolve, reject; const promise = new Promise((yes, no) => { resolve = yes; reject = no; }); return { promise, resolve, reject }; }
        async function main() {
          let now = 0; const starts = []; let gate = deferred();
          const service = new CatalogService((tenant, key) => { starts.push([tenant, key]); return gate.promise; }, () => now, 10);
          const a = service.get('a', 'book'); const b = service.get('a', 'book');
          await Promise.resolve(); assert.deepEqual(starts, [['a', 'book']]);
          now = 100; gate.resolve('first'); assert.deepEqual(await Promise.all([a, b]), ['first', 'first']);
          now = 109; assert.equal(await service.get('a', 'book'), 'first'); assert.equal(starts.length, 1);
          now = 110; gate = deferred(); const expired = service.get('a', 'book');
          await Promise.resolve(); assert.equal(starts.length, 2); gate.resolve('second'); assert.equal(await expired, 'second');
          let calls = 0; const independent = new CatalogService(async (tenant, key) => { calls++; return tenant + '/' + key; }, () => 0, 100);
          assert.deepEqual(await Promise.all([independent.get('a:b', 'c'), independent.get('a', 'b:c'), independent.get('a', 'c')]), ['a:b/c', 'a/b:c', 'a/c']);
          assert.equal(calls, 3);
          const error = new Error('backend down'); let failures = 0; let failGate = deferred();
          const recovering = new CatalogService(() => { failures++; return failGate.promise; }, () => 0, 100);
          const one = recovering.get('a', 'x'); const two = recovering.get('a', 'x');
          const observed = Promise.allSettled([one, two]); await Promise.resolve(); assert.equal(failures, 1);
          failGate.reject(error); const results = await observed;
          assert.equal(results[0].status, 'rejected'); assert.equal(results[0].reason, error);
          assert.equal(results[1].status, 'rejected'); assert.equal(results[1].reason, error);
          failGate = deferred(); const retry = recovering.get('a', 'x'); await Promise.resolve(); assert.equal(failures, 2);
          failGate.resolve('recovered'); assert.equal(await retry, 'recovered');
          let zeroCalls = 0; let zeroGate = deferred();
          const zero = new CatalogService(() => { zeroCalls++; return zeroGate.promise; }, () => 0, 0);
          const z1 = zero.get('a', 'z'); const z2 = zero.get('a', 'z'); await Promise.resolve(); assert.equal(zeroCalls, 1);
          zeroGate.resolve('zero'); assert.deepEqual(await Promise.all([z1, z2]), ['zero', 'zero']);
          zeroGate = deferred(); const z3 = zero.get('a', 'z'); await Promise.resolve(); assert.equal(zeroCalls, 2);
          zeroGate.resolve('again'); assert.equal(await z3, 'again');
          for (const ttl of [-1, NaN, Infinity]) assert.throws(() => new CatalogService(async () => 'x', () => 0, ttl), /invalid ttl/);
          const throwing = new CatalogService(() => { throw error; }, () => 0, 10);
          await assert.rejects(throwing.get('a', 'x'), e => e === error);
          await assert.rejects(throwing.get('a', 'x'), e => e === error);
        }
        module.exports = main();
    """,
)


CANCELLATION = task(
    "ts-batch-job-cancel", "confirmation", "authorization-feature",
    r"""
    Implement atomic batch cancellation in JobService.cancel in src/service.ts. Accept
    a nonempty list of unique job IDs; empty IDs, duplicates or an empty list throw
    Error('invalid batch'). All jobs must exist in the actor's tenant or throw Error('not found').
    Check visibility for the entire batch before permission or status, so a foreign ID does
    not expose state. Only admin may cancel someone else's job; member may cancel only their
    own, and guest none. Then reject any running or completed job with Error('not cancellable').
    Check all permissions before statuses; failures must not alter any job or audit.
    Queued jobs become cancelled; already cancelled jobs are idempotent and do not add audit.
    Add audit {actor, id} for each changed job in request order. Return all requested IDs in
    request order, including already cancelled jobs. Preserve input arrays and existing public API.
    """,
    {
        "src/types.ts": r"""
            export interface Job { id: string; tenant: string; owner: string; state: 'queued' | 'running' | 'completed' | 'cancelled' }
            export interface Actor { tenant: string; user: string; role: 'admin' | 'member' | 'guest' }
        """,
        "src/store.ts": r"""
            import { Job } from './types';
            export class JobStore {
              readonly audit: { actor: string; id: string }[] = [];
              constructor(readonly jobs: Job[]) {}
              find(id: string): Job | undefined { return this.jobs.find(job => job.id === id); }
            }
        """,
        "src/service.ts": r"""
            import { Actor } from './types';
            import { JobStore } from './store';
            export class JobService {
              constructor(private readonly store: JobStore) {}
              cancel(actor: Actor, ids: string[]): string[] {
                for (const id of ids) {
                  const job = this.store.find(id);
                  if (!job) throw new Error('not found');
                  if (job.state !== 'cancelled') {
                    job.state = 'cancelled'; this.store.audit.push({ actor: actor.user, id });
                  }
                }
                return [...ids];
              }
            }
        """,
    },
    {"src/service.ts": r"""
        import { Actor, Job } from './types';
        import { JobStore } from './store';
        export class JobService {
          constructor(private readonly store: JobStore) {}
          cancel(actor: Actor, ids: string[]): string[] {
            if (!ids.length || ids.some(id => !id) || new Set(ids).size !== ids.length) throw new Error('invalid batch');
            const jobs: Job[] = [];
            for (const id of ids) {
              const job = this.store.find(id);
              if (!job || job.tenant !== actor.tenant) throw new Error('not found');
              jobs.push(job);
            }
            for (const job of jobs) {
              if (actor.role === 'guest' || (actor.role === 'member' && job.owner !== actor.user)) throw new Error('forbidden');
            }
            if (jobs.some(job => job.state === 'running' || job.state === 'completed')) throw new Error('not cancellable');
            for (const job of jobs) {
              if (job.state !== 'cancelled') {
                job.state = 'cancelled'; this.store.audit.push({ actor: actor.user, id: job.id });
              }
            }
            return [...ids];
          }
        }
    """},
    r"""
        const { JobStore } = require('../.build/store'); const { JobService } = require('../.build/service');
        const store = new JobStore([{ id: 'job', tenant: 'a', owner: 'u', state: 'queued' }]);
        assert.deepEqual(new JobService(store).cancel({ tenant: 'a', user: 'u', role: 'admin' }, ['job']), ['job']);
        assert.equal(store.jobs[0].state, 'cancelled'); assert.deepEqual(store.audit, [{ actor: 'u', id: 'job' }]);
    """,
    r"""
        const { JobStore } = require('./.build/store'); const { JobService } = require('./.build/service');
        const fresh = () => new JobStore([
          { id: 'q1', tenant: 'a', owner: 'u', state: 'queued' },
          { id: 'q2', tenant: 'a', owner: 'u', state: 'queued' },
          { id: 'other', tenant: 'a', owner: 'v', state: 'queued' },
          { id: 'foreign', tenant: 'b', owner: 'u', state: 'running' },
          { id: 'running', tenant: 'a', owner: 'u', state: 'running' },
          { id: 'done', tenant: 'a', owner: 'u', state: 'completed' },
          { id: 'cancelled', tenant: 'a', owner: 'u', state: 'cancelled' }
        ]);
        const bad = [
          ['admin', [], 'invalid batch'], ['admin', ['q1', 'q1'], 'invalid batch'], ['admin', ['q1', ''], 'invalid batch'],
          ['admin', ['q1', 'missing'], 'not found'], ['admin', ['q1', 'foreign'], 'not found'],
          ['guest', ['running', 'foreign'], 'not found'], ['member', ['other', 'missing'], 'not found'],
          ['guest', ['cancelled'], 'forbidden'], ['member', ['q1', 'other'], 'forbidden'],
          ['member', ['running', 'other'], 'forbidden'], ['admin', ['q1', 'running'], 'not cancellable'],
          ['admin', ['q1', 'done'], 'not cancellable']
        ];
        for (const [role, ids, message] of bad) {
          const store = fresh(); const snapshot = JSON.stringify(store);
          assert.throws(() => new JobService(store).cancel({ tenant: 'a', user: 'u', role }, ids), e => e.message === message);
          assert.equal(JSON.stringify(store), snapshot);
        }
        const store = fresh(); const service = new JobService(store); const ids = ['q2', 'cancelled', 'q1'];
        assert.deepEqual(service.cancel({ tenant: 'a', user: 'u', role: 'member' }, ids), ['q2', 'cancelled', 'q1']);
        assert.deepEqual(ids, ['q2', 'cancelled', 'q1']);
        assert.deepEqual(store.audit, [{ actor: 'u', id: 'q2' }, { actor: 'u', id: 'q1' }]);
        service.cancel({ tenant: 'a', user: 'u', role: 'member' }, ids); assert.equal(store.audit.length, 2);
        assert.deepEqual(store.jobs.map(job => job.state), ['cancelled', 'cancelled', 'queued', 'running', 'running', 'completed', 'cancelled']);
        service.cancel({ tenant: 'a', user: 'boss', role: 'admin' }, ['other']);
        assert.deepEqual(store.audit[2], { actor: 'boss', id: 'other' });
    """,
)


MASS_PROTOCOL = task(
    "ts-versioned-mass", "confirmation", "validation-refactor",
    r"""
    Add version 2 mass records to ShipmentService.quote in src/service.ts and TrackingService
   .label in src/tracking.ts. Version 1 is exactly {version: 1, grams: number}; version 2 is
    exactly {version: 2, quantity: number, unit: 'g' | 'kg'}. Reject arrays, null, nonobjects,
    extra fields, missing fields, unsupported versions or units, numeric strings and nonfinite
    quantities with Error('invalid mass'). Converted grams must be greater than zero and at
    most 1000000; fractional grams are permitted and must not be rounded. Keep v1 quote
    output and label output unchanged. Consolidate parsing/conversion into src/mass.ts
    exporting parseMass(input: unknown): number. Both services must import and use it, and
    remove the old gramsFromRecord API and its callers from src/ code. legacy.ts can be
    deleted or left empty. Inputs must remain unchanged. The shipping price is ceil(grams / 100) * 2.
    """,
    {
        "src/legacy.ts": r"""
            export function gramsFromRecord(input: unknown): number {
              if (typeof input !== 'object' || input === null || !('version' in input) || input.version !== 1 || !('grams' in input) ||
                  typeof input.grams !== 'number' || !Number.isFinite(input.grams) || input.grams <= 0 || input.grams > 1000000) {
                throw new Error('invalid mass');
              }
              return input.grams;
            }
        """,
        "src/service.ts": r"""
            import { gramsFromRecord } from './legacy';
            export class ShipmentService {
              quote(input: unknown): { grams: number; price: number } {
                const grams = gramsFromRecord(input); return { grams, price: Math.ceil(grams / 100) * 2 };
              }
            }
        """,
        "src/tracking.ts": r"""
            import { gramsFromRecord } from './legacy';
            export class TrackingService {
              label(input: unknown): string { return gramsFromRecord(input) + ' g'; }
            }
        """,
    },
    {
        "src/legacy.ts": "export {};",
        "src/mass.ts": r"""
            export function parseMass(input: unknown): number {
              if (typeof input !== 'object' || input === null || Array.isArray(input) || !('version' in input)) throw new Error('invalid mass');
              let grams: number;
              if (input.version === 1) {
                if (Object.keys(input).length !== 2 || !('grams' in input) || typeof input.grams !== 'number') throw new Error('invalid mass');
                grams = input.grams;
              } else if (input.version === 2) {
                if (Object.keys(input).length !== 3 || !('quantity' in input) || typeof input.quantity !== 'number' ||
                    !('unit' in input) || (input.unit !== 'g' && input.unit !== 'kg')) throw new Error('invalid mass');
                grams = input.quantity * (input.unit === 'kg' ? 1000 : 1);
              } else throw new Error('invalid mass');
              if (!Number.isFinite(grams) || grams <= 0 || grams > 1000000) throw new Error('invalid mass');
              return grams;
            }
        """,
        "src/service.ts": r"""
            import { parseMass } from './mass';
            export class ShipmentService {
              quote(input: unknown): { grams: number; price: number } {
                const grams = parseMass(input); return { grams, price: Math.ceil(grams / 100) * 2 };
              }
            }
        """,
        "src/tracking.ts": r"""
            import { parseMass } from './mass';
            export class TrackingService {
              label(input: unknown): string { return parseMass(input) + ' g'; }
            }
        """,
    },
    r"""
        const { ShipmentService } = require('../.build/service'); const { TrackingService } = require('../.build/tracking');
        assert.deepEqual(new ShipmentService().quote({ version: 1, grams: 150 }), { grams: 150, price: 4 });
        assert.equal(new TrackingService().label({ version: 1, grams: 0.5 }), '0.5 g');
    """,
    r"""
        const { ShipmentService } = require('./.build/service'); const { TrackingService } = require('./.build/tracking');
        const shipping = new ShipmentService(); const tracking = new TrackingService();
        for (const [input, grams, price] of [
          [{ version: 1, grams: 150 }, 150, 4], [{ version: 2, quantity: 1.5, unit: 'kg' }, 1500, 30],
          [{ version: 2, quantity: 100, unit: 'g' }, 100, 2], [{ version: 2, quantity: 0.0005, unit: 'kg' }, 0.5, 2],
          [{ version: 2, quantity: 1000, unit: 'kg' }, 1000000, 20000], [{ version: 1, grams: 1000000 }, 1000000, 20000]
        ]) {
          const before = JSON.stringify(input);
          assert.deepEqual(shipping.quote(input), { grams, price }); assert.equal(tracking.label(input), grams + ' g');
          assert.equal(JSON.stringify(input), before);
        }
        for (const input of [null, [], 4, 'x', {}, { version: 0, grams: 1 }, { version: '1', grams: 1 },
          { version: 1 }, { version: 1, grams: '1' }, { version: 1, grams: NaN }, { version: 1, grams: Infinity },
          { version: 1, grams: 0 }, { version: 1, grams: -1 }, { version: 1, grams: 1000001 }, { version: 1, grams: 1, unit: 'g' },
          { version: 2, quantity: 1 }, { version: 2, quantity: '1', unit: 'g' }, { version: 2, quantity: 1, unit: 'lb' },
          { version: 2, quantity: 0, unit: 'kg' }, { version: 2, quantity: -1, unit: 'g' },
          { version: 2, quantity: NaN, unit: 'kg' }, { version: 2, quantity: Infinity, unit: 'g' },
          { version: 2, quantity: 1000.001, unit: 'kg' }, { version: 2, quantity: 1, unit: 'g', grams: 1 }]) {
          assert.throws(() => shipping.quote(input), /^Error: invalid mass$/);
          assert.throws(() => tracking.label(input), /^Error: invalid mass$/);
        }
    """,
    r"""
        const fs = require('node:fs'); const path = require('node:path'); const assert = require('node:assert/strict');
        function texts(dir) { return fs.readdirSync(dir, { withFileTypes: true }).flatMap(e =>
          e.isDirectory() ? texts(path.join(dir, e.name)) : e.name.endsWith('.ts') ? [fs.readFileSync(path.join(dir, e.name), 'utf8')] : []); }
        assert.equal(/\bgramsFromRecord\b/.test(texts('src').join('\n')), false, 'retire the old API and callers');
        const mass = require('./.build/mass'); assert.equal(mass.parseMass({ version: 2, quantity: 1, unit: 'kg' }), 1000);
        for (const name of ['service', 'tracking']) assert.match(fs.readFileSync('src/' + name + '.ts', 'utf8'), /from\s*['"]\.\/mass['"]/);
        mass.parseMass = () => 250;
        assert.deepEqual(new (require('./.build/service').ShipmentService)().quote({}), { grams: 250, price: 6 });
        assert.equal(new (require('./.build/tracking').TrackingService)().label({}), '250 g');
    """,
)


TASKS: tuple[TaskSpec, ...] = (
    PAGINATION, RETRY, AUTHORIZATION, VALIDATION, STREAMING, REFACTOR,
    INVENTORY, CACHE, CANCELLATION, MASS_PROTOCOL,
)
