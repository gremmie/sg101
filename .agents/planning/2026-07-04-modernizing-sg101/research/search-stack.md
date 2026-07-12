# Research: Search Subsystem (Haystack / Xapian / queued_search / queues)

**Status:** Static analysis complete. **CORRECTION (per user, 2026-07-04):
search IS live in production.** The disabled state seen on the branch is a
`modernize`-branch artifact, not the production reality.

## Important clarification

**Search is LIVE in production** (Haystack + Xapian). On the `modernize` branch
it *appears* disabled, but that is only because **the user commented it out on
the branch** — they couldn't get Xapian to run on their old laptop.

Evidence of the branch-level disabling (do NOT read as production state):

- `INSTALLED_APPS` has `#'haystack'`, `#'queued_search'`, `#'custom_search'`
  commented out (`sg101/settings/base.py`) — *on the branch*.
- `sg101/urls.py` has the real Haystack search views commented out and replaced
  with a "Temporary" stub rendering the *About* page for `/search/` and
  `/search/ajax/` — *on the branch*.
- The Celery Beat entry `custom_search.tasks.process_search_queue_task` (every
  20 min) is live in production.

**Revised implication:** there **is** live search behavior to preserve or
deliberately replace — this is a real feature migration, not a free deletion.
However, this discovery is itself telling: **the fact that the user cannot even
run Xapian on a modern machine is the core pain point** and a strong argument
*for* replacing it (Postgres FTS) rather than porting it. Two things follow:
1. The Docker legacy environment must either get Xapian running *or* we accept
   that search is validated separately via its Postgres replacement.
2. We must **document the current production search UX** (what's searchable,
   result layout, relevance expectations) so the replacement can be validated
   against real behavior, since we can't bug-for-bug diff a stack we can't run.

## How search was designed to work (when enabled)

```mermaid
graph LR
    subgraph Models[Indexed content 7 types]
      T[forums: Topic, Post]
      B[bio: UserProfile]
      N[news: Story]
      W[weblinks: Link]
      P[podcast: Item]
      D[downloads: Download]
      Y[ygroup: Post]
    end
    SIG[Model signals] --> QSP[custom_search<br/>QueuedSignalProcessor]
    QSP --> QQ[queued_search + queues<br/>Redis-backed queue]
    QQ --> BEAT[Celery Beat:<br/>process_search_queue_task]
    BEAT --> IDX[(Xapian index<br/>local disk)]
    Models --> SI[search_indexes.py x7]
    SI --> IDX
    UI[/search/ view] --> IDX
```

Components involved (all candidates for deletion if we move to Postgres FTS):

- **django-haystack** (search abstraction) — `HAYSTACK_CONNECTIONS` →
  `xapian_backend.XapianEngine`, index at `sg101/xapian_index` (hg-ignored).
- **xapian-haystack** (`xapian_backend`) — pinned to an old git commit; requires
  the native `xapian` C++ library + Python bindings (the hardest thing to
  install and the reason for the persistent-local-disk hosting constraint).
- **queued_search** (`queued-search==2.1.0`) + the custom **`queues`** package
  (from the private `bobcat` hg server; `QUEUE_BACKEND='redisd'`) — async index
  update queue.
- **custom_search** app — `QueuedSignalProcessor`, `MaxTermSizeCharField`,
  search forms/views/fields/receivers.
- **7 × `search_indexes.py`** — Topic, Post, UserProfile, Story, Link, Item,
  Download, ygroup Post. Simple `text`/`author`/`pub_date` document indexes using
  `use_template=True` (search templates under `templates/search/`).

## Options

### (A) Port Xapian/Haystack forward to Py3 + modern Django
- **Pros:** keeps the same relevance behavior; no data model change.
- **Cons:** xapian-haystack + native xapian bindings are painful on modern
  Python/Django; forces persistent local disk in hosting (fights the "simpler,
  more managed" hosting goal); keeps the fragile `queues`/`queued_search`/private-
  repo dependencies alive; must re-enable and debug a currently-dead subsystem.

### (B) Replace with PostgreSQL full-text search  ⭐ recommended (pending Postgres decision)
- Use Django's built-in `django.contrib.postgres.search` (`SearchVector`,
  `SearchQuery`, `SearchRank`, `SearchVectorField` + GIN index).
- **Deletes:** haystack, xapian-haystack, xapian, queued_search, `queues`,
  `custom_search`, all 7 `search_indexes.py`, the Xapian index, and the search-
  queue Beat task — a large prune of the most fragile, hardest-to-host,
  hardest-to-*run* code (the very code the user couldn't run on a modern laptop).
- **Hosting win:** eliminates the persistent-local-disk constraint entirely →
  unlocks simpler/managed hosting and any stateless container platform.
- **Indexing:** maintain a `SearchVectorField` per searchable model, updated via
  `save()`/signals or a periodic job (Celery already present) — no separate
  search server, no queue package.
- **Cons:** requires the MySQL→Postgres move (Q9); relevance ranking differs from
  Xapian (acceptable — nothing live to match); need to (re)build search UI/view.
- **Good fit** because the 7 indexes are simple text documents, not exotic.

### (C) Managed/hosted search (e.g., a search-as-a-service)
- Overkill and adds recurring cost/ops for a hobby community site. Not recommended
  unless Postgres FTS proves inadequate.

## Recommendation

**DECISION DEFERRED (user, 2026-07-04): decide after examining a production DB
snapshot** and documenting current search behavior/volume, then choose Postgres
FTS vs. porting Xapian with data in hand.

Working hypothesis (subject to that snapshot): pursue **(B) Postgres full-text
search**, contingent on the MySQL→Postgres decision (see `database-migration.md`).
It is squarely in the spirit of the lift-**and-prune** scope, resolves the Xapian
hosting *and runnability* problems, and removes the most private-repo
dependencies. Keep **(A)** as the fallback only if the snapshot shows Postgres FTS
can't match important behavior, or if Postgres is rejected.

**Snapshot investigation checklist (before final call):**
- Row counts / content volume for the 7 indexed types (indexing feasibility).
- What users actually search and expected relevance (forum-heavy?).
- Any non-trivial relevance features in use (weighting, stemming, phrase search)
  that Postgres FTS must replicate.
- Search templates under `templates/search/` and current results UX.

**Sequencing (revised):** because search is live in production, the replacement
must reach parity *before the final production cutover* — it cannot ship broken.
But it need not block the Django ladder: keep Xapian search running in production
(old box) untouched while climbing the ladder locally, then bring up Postgres FTS
as part of (or just after) the MySQL→Postgres move, validate it against documented
current behavior, and only then cut over. During local development search can stay
stubbed until the Postgres FTS work begins.

## Follow-ups / to confirm
- User note (Q9): leaning Postgres if it simplifies the stack — this is the
  strongest single simplification available, and directly cures the "can't run
  Xapian" pain.
- **Document current production search UX** (what users can search — forums/
  posts, bios, news, weblinks, podcast, downloads, ygroup; result layout;
  relevance expectations) so the Postgres FTS replacement can be validated.
- Decide whether to invest any effort in getting Xapian to run in Docker at all,
  or skip straight to building the Postgres FTS replacement (likely the latter).
