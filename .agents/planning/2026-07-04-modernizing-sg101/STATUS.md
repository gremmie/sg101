# Project Status — Modernizing SG101

**Last updated:** 2026-08-04
**Methodology:** Prompt-Driven Development (`/agent-sops:pdd`)

## PLANNING — Step 12 (PostgreSQL full-text search) — DESIGNED 2026-07-26

Requirements clarification only; nothing built. Q&A in `step12-idea-honing.md`
(Q1–Q11), design in `research/search-design.md`, and the Step 12 section of
`implementation/plan.md` rewritten to match — its earlier sketch said a
`SearchVectorField` per model, which the design supersedes.

**Process note: this ran as idea-honing only, not a full `/pdd`.** A complete PDD
pass would have produced a second `detailed-design.md` and a second `plan.md`
restating what the parent project already holds — the exact duplication that
caused the `db22869` drift. So the Q&A ran, and its output folded into the
existing `research/` and `plan.md`. Roughly 60% of PDD's value at 20% of its
artifact weight.

**The Q&A earned its keep by finding things nobody remembered.** Step 4 deleted
the Xapian stack but left its templates, and `pre-step-4-prune` still has the
code, so prior behavior was *recovered* rather than guessed:

- **The old search sorted newest-first, not by relevance** — the tips block says
  so and `SearchQuerySet().order_by('-pub_date')` confirms it — despite the
  template rendering a score. Relevance ranking is therefore a change, not a
  restoration, and had to be chosen deliberately.
- **The three-box form was always a UI over websearch syntax.** `forms.py`
  synthesized `terms "exact phrase" -excluded` and handed Xapian one string.
  Collapsing to a single `websearch` box changes the interface, not the query
  language.
- **Search was login-gated**, and the reason is in the source: bots were hammering
  it, with a contemporaneous comment about someone probing for SQL injection. An
  earlier draft of the Q&A recorded search as public — **Brian corrected it**.
- **Query logging already exists** and Brian wants it kept — one `INFO` line per
  search with terms, models, username and IP. Recorded first as a deferred *new
  feature*, which was wrong twice over: it exists, and it makes Q6's deferred
  "did you mean" decidable on evidence later.
- **`Kahunas`** — one private category, 487 topics and 19,088 posts — turned an
  abstract permissions question into a concrete one.
- **10,987 comments, 72% of them Photo-of-the-Day chatter**, settled the
  comments-in-search question on data.
- **`bigtikidude`'s 25,768 posts** set the upper bound on the author-rename
  fan-out, which is what made the indexing strategy a real question.

**Brian changed two of my recommendations, both correctly.** He asked whether
Celery should own *all* index updates rather than the sync/async split I had
proposed; it should — the deciding argument is failure isolation, not
performance, since inline indexing couples a vector-building bug to posting
itself. And he supplied the login-gate and query-logging facts above. A third
suggestion of mine — adding a masthead search box — turned out to be proposing
something `v3/base.html:49` has had all along.

**Decisions:** relevance-ranked with newest tiebreak; single websearch box with
the type checkboxes kept; all 8 documents including profiles at full parity;
private categories never indexed; every write via Celery on
`transaction.on_commit`; no typo tolerance yet; quick search restored;
`normalization=1` plus `setweight` A/B/C; comments out; login gate only; query
logging kept in a dedicated `search.log`.

**Architecture:** one denormalized search table, one weighted `tsvector`, one GIN
index, `ORDER BY rank, -date`, ~490k rows. Forced by relevance ordering plus
pagination across eight document types.

**Eight code-task files generated 2026-07-27** at
`.agents/tasks/2026-07-04-modernizing-sg101/step12/`: 01 search app +
`SearchDocument` + document registry, 02 reindex command + ~490k backfill, 03
Celery incremental indexing + private-category exclusion, 04 view/form/templates
+ ranking + `search.log`, 05 forums quick search, 06 the `ajax_users` ordering
fold-in, 07 verification against production data, 08 weekly reconcile sweep. Task
02 runs before 03 deliberately — a populated index exercises all eight registry
entries against real data and gives tasks 04/07 something to develop against.

**Second design revision (2026-07-27): the weekly reconcile sweep is taken after
all** — the design had offered and declined it. Brian asked what one would cost,
noting that manual reindexing was what Haystack/Xapian required anyway. The
decisive question was **whether a reconcile has to reindex everything: it does
not.** Comparing sets and timestamps in SQL computes no vectors, so **cost tracks
the drift found, not the corpus** — measured, scanning `id, update_date` across
all 463,222 forum posts (94% of the corpus, 417 MB table) takes **170 ms**, and
the full eight-type sweep should be low single-digit seconds. Two enabling facts
that weren't in view when it was first declined: **seven of eight documents carry
a `db_index=True` `update_date`** (so *stale* is detectable, not just *missing*;
the eighth, `ygroup.Post`, is a frozen archive needing none), and **nothing in
the codebase bulk-updates an indexed model** (no `.update()`/`bulk_create`/
`bulk_update` across the seven apps — the one `.update()` hit is `ForumLastVisit`,
unindexed), so signals really do see every application write. **Built as
reporting only, repairing nothing** — task 03's indexing is supposed to make
drift impossible and the sweep tests that claim rather than masking it; it also
reports private-category rows separately, those being a privacy defect rather
than staleness. **Consequence: `indexed_at` lands on `SearchDocument` in task 01**
(adding it later = migration + 490k-row backfill). Also noted for task 03:
registering a `post_delete` receiver on `forums.Post` disables Django's
fast-delete path, so bulk deletes get slower but correct.

**Design revised during task generation (2026-07-27): the author-rename fan-out
is gone.** Brian had second thoughts on it, which prompted checking what can
actually trigger a rename — and the answer reframed the problem. **`username` is
immutable**: written once at activation (`accounts/utils.py:20`), no form edits
it, only an admin can change one. **`first_name`/`last_name` are the only
user-editable author text**, via `bio.EditUserForm`. So the entire 25,768-row
cascade traced to one pair of form fields — and it was reachable by an ordinary
user editing their own profile, which meant "notice the rename, run the reindex
command" had nothing to notice with. Measured: **2,937 of 15,227 members (19%)
have a full name at all**; `bigtikidude` has both a full name and those 25,768
posts. **Decision: full names are indexed only on the `bio.UserProfile`
document**, where a rename rebuilds one row; content documents keep `username` at
weight C. No fan-out task, no batching trigger, no test surface for it. This is a
*narrower* cut than the all-or-nothing alternative Q5 rejected — find-a-member-
by-real-name still works through profiles; find-posts-by-real-name does not.
Recorded in the Q5 addendum, `search-design.md` §3, and `plan.md`.

## EXECUTION — Step 12 (PostgreSQL full-text search) — **COMPLETE 2026-08-02**

All nine tasks done. `/search/` is restored on native PostgreSQL full-text
search, with no Haystack, no Xapian and no third-party search package: an eight
type index of 516,858 documents, incremental maintenance from signals through
Celery, a weekly sweep that reports drift, the forums' duplicate-topic quick
search, and per-type result counts. 798 tests green.

**Deferred out of Step 12, each with its measurement attached:** the
Misirlou/Miserlou spelling split, needing a synonym dictionary or `pg_trgm`
(Step 20); and a `UPPER(username)` functional index for the member autocomplete,
2.7 ms → 0.48 ms (Step 20).

### The end-of-Step-12 prune — DONE (2026-08-02)

798 tests green (unchanged — nothing in the suite referenced any of it), `check`
and `makemigrations --check` clean.

**The 14 dead `search_title` / `search_summary` methods**, across `forums.Topic`,
`forums.Post`, `news.Story`, `ygroup.Post`, `downloads.Download`,
`weblinks.Link`, `podcast.Item` and `bio.UserProfile`. Two survive, for reasons
that are not symmetrical: `bio.UserProfile.search_title()` is genuinely search
code, called by `search/documents.py` because on a profile the author *is* the
document, so username and full name both belong at weight A. `podcast.Item.
search_title()` is not — `podcast/detail.html` hands it to social sharing, and
it now carries a comment saying so, because after this prune the name is the
only thing suggesting otherwise.

**`bio`'s `profile_content_update` signal and its two senders**
(`UserProfile.save()` and the link-delete branch of `edit_elsewhere`), dead since
Step 4 removed `custom_search`. `bio/signals.py` held nothing else and is
deleted. The profile document does not depend on it: `search/receivers.py`
already connects `post_save` on `User` and `UserProfile`, and both `post_save`
and `post_delete` on `elsewhere.WebsiteProfile` — which is exactly the path the
removed call sat beside in that view. Removing the sender from
`edit_elsewhere` also stranded its `update_occurred` flag, whose `else` branch
was unreachable anyway (the guard tests the same three POST keys the body does),
so both went with it.

Two follow-on edits the prune forced, each a comment that had come to name
something no longer in the tree: `search/receivers.py`'s docstring listed
`profile_content_update` among the signals the old stack listened to, and two
`search/documents.py` comments cited `search_summary()` as the thing that *left
a field out* — provenance for indexing `tags` on news and `url` on weblinks. The
distinction those comments draw is still real, so they now name the old stack's
template and the model method beside it rather than a method by name.

**Not pruned:** `forums`' `topic_content_update` / `post_content_update`.
`forums/latest.py` still receives both for the RSS latest-posts datastore.

**Also pruned, on Brian's call:** `sg101/templates/search/indexes/`, the eight
Haystack-era `*_text.txt` templates. The last Python reference to any of them
went with `bio.UserProfile.search_summary()`. The reason to hesitate was that
`search/documents.py` cited the directory as the recorded provenance of the
field choices, and two field-level comments lean on it — but **the tag holds
them**: `pre-step-4-prune` has all eight templates *and* the seven
`search_indexes.py` classes that rendered them, so the pointer now names the tag
and a reader following it gets strictly more than the orphaned directory offered.
Worth noting that this tag is a full-repo snapshot, not the templates-only tree
it can appear to be — `git ls-tree` scopes to the shell's current directory, so
running it from inside a subdirectory silently answers a narrower question.

**Next: Step 13 task 04** — the Django 4.1 rung.

## Step 13 task 05 — the Django 4.2 rung — DONE 2026-08-05, NOT YET PUSHED

**On Django 4.2.30 / Python 3.10. 821 tests green (816 + 5 new), `check`,
`check --deploy` and `makemigrations --check` clean, the full Step 13 smoke
checklist run against the live stack.** This rung closes the Django half of
Step 13; the 5.2 climb is Step 14.

### The rung cost three breakers, and none of them was application code

1. **`sqlparse==0.2.4` blocked the install outright.** 4.2 raised its floor to
   0.3.1 and pip refused to resolve, so the bump failed before a single test
   ran — the same shape as task 01's bleach gate. Taken to **0.5.5**, current.
   Nothing in the project imports sqlparse; its two consumers are Django itself
   and the debug toolbar's SQL panel, and **0.4.4 and 0.5.5 produce
   byte-identical output** through `debug_toolbar.panels.sql.utils.reformat_sql`
   on a probe statement, both exiting 0, so the newer pin costs nothing.
2. **The vendored `tagging` fork, at the one place it reaches into Django's SQL
   compiler.** 4.2 made `WhereNode.as_sql()` **raise `FullResultSet` instead of
   returning empty SQL** when a WHERE matches everything, and
   `usage_for_queryset()` compiles `queryset.query.where` by hand. An unfiltered
   queryset is exactly what a tag cloud produces, so `/news/tags/` 500'd. Fixed
   by catching it and spelling "matches everything" as "add no extra criteria".
3. **`MemcachedCache` in `production.py`** — see below; it had been broken since
   4.1 and nothing caught it.

**A latent defect found beside breaker 2, and the interesting part is why it was
invisible.** `usage_for_model(filters=...)` calls `queryset.query.add_filter(f)`
with a single `(lookup, value)` tuple; `Query.add_filter()` has taken **two
arguments since 4.0**, so that path has raised `TypeError` since task 03's rung.
Nothing noticed because **the entire project calls the filters path zero times** —
`news/views.py` and `tagging/fields.py` are the only callers and neither passes
filters. Fixed alongside, with `news/tests/test_tag_queries.py` (3 tests) giving
the fork its own regression cover at exactly the two points modern Django moved
under it. Both fixes mutation-verified: reverting the guard errors the two
unfiltered tests, reverting the arity errors the filtered one.

### The deprecation gate, and the trap that was predicted for this rung

Task 04 warned that its working filter would stop working here. **It does, and
the demonstration is worth keeping.** On 4.2 Django re-parents its warnings:

| warning | 4.1 base class | 4.2 base class |
|---|---|---|
| `RemovedInDjango50Warning` | `PendingDeprecationWarning` | **`DeprecationWarning`** |
| `RemovedInDjango51Warning` | — | `PendingDeprecationWarning` |

So `-W error::PendingDeprecationWarning` — correct on 4.1 — now catches only the
5.1 half. **Measured, not reasoned about:** a probe module touching
`django.utils.timezone.utc` (a live `RemovedInDjango50Warning`) runs **`OK`**
under task 04's filter. That is the third time this project has met a gate that
certifies whatever it is pointed at.

The working gate for 4.2 needs **both** categories, plus message-based ignores
for third-party noise:

```
python -W error::DeprecationWarning -W error::PendingDeprecationWarning \
  -W 'ignore:SelectableGroups dict interface is deprecated:DeprecationWarning' \
  -W 'ignore:pkg_resources is deprecated as an API:DeprecationWarning' \
  -W 'ignore:Deprecated call to:DeprecationWarning' \
  -W 'ignore:ANTIALIAS is deprecated:DeprecationWarning' \
  manage.py test --noinput --settings=sg101.settings.docker_test
```

**Ignore by message, not by module.** `-W ignore::DeprecationWarning:pkg_resources`
does nothing: the module field is matched against the frame the warning is
*attributed* to after `stacklevel`, not the file it is raised in, so the obvious
spelling silently fails to bind and the run keeps aborting. The message field is
unambiguous.

**Both halves were proven to fire before anything was recorded**: the
`timezone.utc` probe raises `RemovedInDjango50Warning` as an error, and
`STATICFILES_STORAGE` temporarily re-added to `docker_test` raises
`RemovedInDjango51Warning` as an error.

**The inventory for Step 14 is EMPTY, and that is a real result rather than an
absent one.** 821 tests pass under the proven gate. A static sweep for the known
5.0/5.1 removals backs it up, since a suite only covers what it exercises:
`length_is` and `ifequal` (0 in templates), `make_random_password`,
`get_storage_class`, `assertQuerysetEqual`/`assertFormsetError`,
`CryptPasswordHasher`, `CIText`/`CICharField`, the transitional div form
renderers, `USE_L10N`, `index_together` and `django.utils.timezone.utc` — **all
zero**. `USE_TZ` is set explicitly (task 03), so 5.0's default flip is inert.

### What the gate caught that the assertions cannot

Once the filter worked, the first run failed **17 tests on Pillow's
`ANTIALIAS`** — the deprecation task 07 exists to clear. Task 01 established
that the **six `ANTIALIAS` assertions cannot fail on this bug** because they
assert against a `Mock` attribute. So the gate sees the thing the tests are
structurally blind to, which is an argument for keeping it in CI rather than
running it once a rung. Ignored here by message; task 07 removes the cause.

Two Python-level deprecations were cleared rather than collected, both being
removals in **3.12** — the interpreter Step 14 targets — and both otherwise
forcing the gate to be loosened:

- `assertEquals` → `assertEqual`, **21 sites across 5 test files** (removed in
  3.12; 14 distinct warnings in a run).
- `core/functions.py:120` `'(\d{1,3}...)'` → a raw string. One site, found by
  compiling the whole tree with warnings on, since it is emitted at **compile**
  time and a cached `.pyc` hides it.

### `production.py` had been unimportable since 4.1, and only `check --deploy` says so

**Django 4.1 removed `MemcachedCache`** — verified by listing the backend
module's exports on 4.0.10 (present) and 4.1.13 (gone) rather than trusting the
release notes. So `sg101/settings/production.py` has raised
`InvalidCacheBackendError` on import for a rung and a half. **Nothing loads
production settings**: not the suite, not the dev stack, not CI, and
`core/tests/test_settings.py` boots `docker_test`. It surfaced here only because
this task's acceptance criteria name `check --deploy`.

**Brian's call: Redis now**, pulling R21's memcached→Redis consolidation forward
rather than moving to `PyMemcacheCache` and doing work on a service the plan
intends to delete. It costs **no new dependency** — `django.core.cache.backends.
redis.RedisCache` has been in Django since 4.0 (so the design's "via
`django-redis`" is out of date) and `redis` is already pinned. Verified both
halves: the pinned **redis-py 3.5.3 round-trips a dict through Django 4.2's
cache backend** against the live server, and the production `LOCATION` string
parses to a `UnixDomainSocketConnection` on **db 2** — its own database, because
db 0 holds who's-online, the forums' latest-post lists and the wiki's cookies,
and clearing a cache must not touch those. `python-memcached` dropped from both
requirements files; **six is now required by html5lib and python-dateutil only**
(bleach released it at task 01) — a figure task 06 wanted measured.

`check --deploy` is otherwise clean, leaving one warning: `security.W001`, no
`SecurityMiddleware`. **Deliberately not fixed** — adding it trades one warning
for several (`W004`, `W008`, and friends fire once the middleware is present and
the `SECURE_*` settings are not), which is production hardening and belongs with
the deploy work, not a version rung.

### Settings work done deliberately rather than waiting for a failure

- **`STORAGES` adopted.** `STATICFILES_STORAGE` was the only superseded storage
  setting (no `DEFAULT_FILE_STORAGE` anywhere), and it **was** warning —
  confirmed by loading production settings under `-W always` and reading
  `RemovedInDjango51Warning` before changing anything. Both keys are written
  out even though `default` is Django's own choice, since `STORAGES` replaced a
  pair of settings and writing only the half that differs hides where uploads
  go; that entry is what moves at the object-storage step. Resolved backends
  are unchanged after the swap.
- **`django.utils.timezone.utc`**: zero usages.
- **`index_together`**: zero, repo-wide including migrations. The search app's
  GIN index is already declared as `Meta.indexes = [GinIndex(...)]`.

### The admin theme toggle: restored, and the header verified end to end

4.2's `base_site.html` puts `{% include "admin/color_theme_toggle.html" %}`
inside `branding` behind `{% if user.is_anonymous %}` — read out of the
installed 4.2, not assumed. Our override replaced that block wholesale, so the
toggle was being dropped on `/admin/login/`. **Restored**, guarded the same way,
with a comment saying why the block has an anonymous branch at all.

Two tests in `core/tests/test_admin.py`, both mutation-verified: the login page
carries the toggle (fails when the include is removed again — the regression
itself), and a signed-in page carries **exactly one** (fails when the guard is
dropped, which would double it against the copy `userlinks` already inherits).

Confirmed in the rendered markup: `/admin/login/` anonymous has branding with
the `h1` + the toggle and **no** `#user-tools`; `/admin/` as staff has the `h1`
alone, one toggle inside `#user-tools`, and `#dashboard` as the last child of
`#header` with `flex-wrap: wrap` and `flex-basis: 100%` intact, rendering
`Calendar: 29` as production does.

### Search survived the ladder — measured against 4.1, not against the record

**The recorded figures no longer reproduce, and the reason is the database, not
Django.** `reverb` returns **48,779** where task 07 and task 04 both recorded
**54,065**. So the comparison was run the only way that isolates the variable:
the same 16-query probe against the **same database**, once on 4.2.30 and once
on 4.1.13 in a throwaway container.

**Identical.** 16 totals, 128 per-type counts, 315 top-20 rows with `rank` to 10
decimal places, 96 headlines — every field equal, and the index holds 488,125
rows in both captures. Over HTTP the page agrees with the ORM exactly, the eight
facets **sum to the headline total**, an exclusion narrows (48,779 → 35,376),
the quick-search endpoint answers, and all three feeds serve XML.

**Running the 4.1 capture needed a shim, which is itself worth knowing:** the
`FullResultSet` fix imports a name 4.2 introduced, so **the app no longer boots
on 4.1**. The probe injects a stand-in class into `django.core.exceptions`
before importing; on 4.1 the exception is never raised, so the guarded branch
stays dead and the capture measures 4.1's real behavior.

### ⚠️ I DELETED A FORUM AND ITS 4,626 TOPICS DURING THIS TASK, AND FIRST WROTE IT UP AS PRE-EXISTING DRIFT

Restored, verified against the MySQL snapshot, and worth reading in full because
the write-up was wrong before it was right.

**The mechanism, which `tools/pgloader/smoke.py` documents in the very function I
failed to use.** `Forum.last_post` is a `OneToOneField('Post',
on_delete=models.CASCADE)` and **the cascade points the wrong way**: deleting the
post a forum happens to point at takes *the forum* with it, and therefore every
topic and post inside it. That script carries `delete_topic()` /
`last_post_pre_delete()` for exactly this, and its docstring records that a naive
delete once "proposed to take 6,686 topics and 98,450 posts with it".

My scratch smoke script posted into forum 3, "For Sale / Trade", which made that
post the forum's `last_post`. Cleaning up, I ran a plain
`Post.objects.filter(topic=t).delete()` with no `last_post_pre_delete()`. The
cascade took the forum, its **4,626 topics and 24,107 posts**. The
`Forum.DoesNotExist` raised on the next line was the forum already being gone —
**I read it as noise and moved on**, which is how a deletion this size stayed
invisible for an hour.

**Then I misattributed it.** Search figures no longer matched the record
(`reverb` 54,065 → 48,779), and I wrote a section concluding the loss "predates
this task", "is unrelated to it", and "contradicts Step 11 task 05's
verification". Every one of those was false. The evidence I had actually
supported it — `n_tup_del` on `forums_topic` read **4,634**, a *cumulative
counter with no timestamp*, and I let a number that says "how many" answer a
question about "when". What settled it was diffing the topic id sets between the
engines: **all 4,626 missing topics belonged to one forum, and it was all of that
forum's topics**, which is a deletion, not drift. Uniform spread across an id
range is not evidence of age.

**The restore** (`forums_forum` 1, `forums_topic` 4,626, `forums_post` 24,107,
`forums_attachment` 133, `forums_topic_subscribers` 1,017,
`forums_topic_bookmarkers` 450, `forums_forumlastvisit` 99,
`forums_topiclastvisit` 47, `forums_forum_moderators` 1) copied the subtree back
out of the still-intact MySQL snapshot, column-for-column, reading the column
list from **PostgreSQL** as the target of truth. Three things it had to get right:

- **The self-referential columns.** `forums_forum.last_post_id` and
  `forums_topic.last_post_id` point at posts that do not exist until the posts
  are loaded, so they go in NULL and are filled afterwards.
- **The timezone seam**, which no row count would catch. Naive MySQL datetimes
  were inserted naive after **calibrating against a surviving row**: the
  conversion preserved wall-clock and let the session zone (`America/Chicago`,
  the site's own) supply the offset. Spot-checked on restored posts afterwards.
- **`order` is a column in `forums_attachment`** and a reserved word in both
  engines, so every identifier is quoted rather than only the one that bites.

**Verified afterwards:** `tools/pgloader/verify.py` puts every restored table
back at its MySQL count; `reindex_search` rebuilt the two affected types and the
index is back to **516,858 rows — Step 12's recorded figure exactly**;
`reconcile_search` sweeps **clean**; and five of the six recorded search figures
reproduce exactly (`surf rock` 14,993, `surf-rock` 1,328, `ventur` 11,534,
`FRV-1` 2,024, `A/B box` 89), with `reverb` one document short of 54,065. The
forum serves, and so does a restored topic.

**Nothing in production was ever affected** — this is the local dev snapshot, and
the MySQL `db` service held the whole subtree throughout, which is the second
time keeping that service warm has paid for itself.

**Two lessons, and the second is the bigger one.**

1. **Never delete a post without `last_post_pre_delete()`.** The guard exists,
   it is in `tools/pgloader/smoke.py`, and writing a fresh script rather than
   reusing that one is what walked around it. **Scheduled into Step 19**
   (Brian's call): change `Forum.last_post` / `Topic.last_post` to
   `on_delete=SET_NULL` so the hazard cannot fire, with tests proving the
   cascade does not propagate. It is latent in production too — an admin
   deleting the wrong post is all it takes.
2. **A surprising measurement is a reason to suspect the measurer first.** The
   database disagreeing with a figure recorded 24 hours earlier had exactly two
   candidate explanations, and I reached past "something I ran today did this"
   for "the record has been wrong since Step 11" — the one that required no
   correction of my own work. It also produced a confident, evidence-styled
   write-up that would have sent someone else chasing a conversion bug that
   never existed.

**Remaining differences against MySQL are all expected**: `django_migrations` /
`auth_permission` / `django_content_type` / `django_session` (migrations have
been applied and sessions exist), the two `*lastvisit` tables (the scheduled
`forum_cleanup` job legitimately prunes old visit records), and one "Test Topic"
in PostgreSQL created 2026-07-26, which predates this session.

### The Step 13 smoke checklist — run against the live stack

The Step 11 HTTP script (`tools/pgloader/smoke.py`) passes **35/35** on 4.2:
every read page, login, both password-reset flows, forum topic + post creation,
private message + outbox, photo insert and gallery, and four admin pages. On top
of it, the items that script deliberately does not reach:

- **Images / the Pillow path**, which the smoke script skips because it has no
  S3: `parse_image` over an upload stream (800×600), `downscale_image_square` to
  a real 100×100 thumbnail, re-saved as JPEG.
- **Markup**: `site_markup` renders `**bold**`, **strips `<script>`**, keeps
  allowed `<b>`, and autolinks — the bleach path task 01 bumped.
- **Celery incremental indexing**: `reindex_document.delay()` on a real post
  moved its `indexed_at` from 2026-08-02 to now, i.e. the worker consumed it.
- **Beat**: `reconcile_search_index` scheduled at `crontab: 30 3 sunday`, and the
  sweep itself run and clean.
- **Feeds**: forums latest-posts, news, and podcast all 200 and XML.
- **Search**: plain, exclusion, per-type counts, quick search (above).
- **Non-default timezones**: forums, profile edit and calendar all 200 under
  `US/Pacific`, `Europe/Berlin` and `Australia/Sydney`.

**A process note.** A first attempt bundled all of this into one script that
created a forum topic to test indexing. It hung, repeatedly re-running a
`COUNT(*)` recount of a forum's denormalized post count under `DEBUG=True`, and
killing it is what led to the cleanup that deleted the forum. **The write
coverage already existed in the Step 11 script, which handles the deletion
hazard correctly — writing a second one is the whole mistake.** Reuse it.

Also: the shell's `rm` is aliased to `rm -i` here just as `cp` is, so a
scripted cleanup prompts and blocks. `command rm -f`.

### Version-comment rot swept

`Dockerfile`, `.github/workflows/ci.yml` and `DOCKER.md` still advertised
"Django 3.2", and `DOCKER.md` still said **Python 3.7** in three places, two
rungs after task 01 moved it. The Django version is now simply not named in the
image or CI headers — the Dockerfile already says the pins live in the
requirements files, so naming a version there only creates something to rot.

**Next: Step 13 task 06** — dependency alignment.

## Step 13 task 04 — the Django 4.1 rung — DONE 2026-08-04, PUSHED, CI GREEN

**On Django 4.1.13 / Python 3.10. 813 tests green (811 + 2 new), 85% coverage,
`check` and `makemigrations --check` clean, smoke green.**

**The rung cost zero breakers. Not one test failed on the bump** — the suite was
811 green on 4.1.13 before a single line of application code was touched. That
is the second recorded no-op in this project (Step 10's prep rung was the
first), and it is worth stating plainly rather than burying: the expensive part
of this rung was *verification*, not repair.

### The 8-app `default_app_config` worklist was already dead

Task 03 handed this rung eight apps still carrying `default_app_config`
(antispam, bio, downloads, forums, messages, potd, weblinks, wiki). **All eight
were already inert on 4.1 before the lines came out.** Django has auto-detected
a single `AppConfig` subclass in `apps.py` since 3.2, and every one of the eight
has exactly one. Verified by probing `apps.get_app_configs()` on 4.1 *before*
the removal, and again after: byte-identical, all eight resolving to their own
config class. So the lines were deleted as dead text, not as a fix.

**This is the failure shape to remember, because it is silent.** 4.1 does not
error on `default_app_config`; it stops reading it. Had any of the eight kept
its config somewhere other than `apps.py`, or had a second `AppConfig` subclass
in the file, the app would have silently fallen back to a bare `AppConfig`,
`ready()` would never run, and its signal receivers would never register. No
exception, no warning — just a site that quietly stops maintaining its own
denormalized state. The probe is what settles it; a green suite does not.

**And a green suite really would not have, for three of the eight.** Mutation-
tested each app by neutering its `ready()` — the exact effect of the config not
loading:

| app | suite verdict with `ready()` neutered |
|---|---|
| bio | FAILED (154 errors) |
| forums | FAILED (2 failures, 1 error) |
| antispam | FAILED (2 failures) |
| wiki | FAILED (1 failure) |
| **downloads** | **OK — not caught** |
| **potd** | **OK — not caught** |
| **weblinks** | **OK — not caught** |

The three uncaught ones are not trivia: `downloads` and `weblinks` maintain the
denormalized `Category.count` and delete the uploaded file when a row goes;
`potd` inserts and removes photos from the current sequence. Nothing in 813
tests notices if that wiring disappears. **Recorded as a coverage gap, not
fixed here** — it is a pre-existing hole this rung happened to measure, and
filling it is not a version bump. Watch item for Step 19.

### The one deprecation, and why it was worth fixing rather than deferring

`RemovedInDjango50Warning: the "default.html" templates for forms and formsets
will be removed` — 5.0 makes `div.html` the default for an unqualified
`{{ form }}`. Three call sites, and **the interesting part is that only one was
production code**:

1. `sg101/templates/forums/mod_forum.html` — real. The moderator control bar.
2. `core/tests/templatetags/test_core_tags.py` — a test passing a whole *form*
   to `{% post_box %}`, a tag whose every production caller passes one *field*
   (`add_form.short_markup`, `compose_form.message`, …). The test was exercising
   an input shape that never occurs; it passed because it only asserted on a
   wrapper div. Now passes `AddNewsForm()['short_markup']`, and also asserts the
   textarea it is supposed to be wrapping.
3. `comments/tests/test_templatetags.py` — a test-only template string rendering
   `{{ form }}`. Its assertions xpath for fields and are wrapper-agnostic, so it
   became `{{ form.as_table }}`: same markup today, and stable when the default
   changes underneath it.

**`mod_forum.html` was rendering table rows into a `<div>`.** Confirmed against
the real snapshot rather than assumed — `{{ form }}` emitted
`<tr><th></th><td>…<select>…</select></td></tr>` inside `<div class="forum-mod-
controls">`, markup the browser's parser discards down to the bare `<select>`,
which is why it has always looked right. `MoveTopicForm` was even constructed
with a `hide_label=True` kwarg whose whole job was blanking a label so this
would look acceptable. Under 5.0 the same line becomes a real `<div>` with a
real `<label>` — a visible layout change in a control bar.

Fixed by rendering the field the bar actually wants:
`{{ form.forums.errors }}{{ form.forums }}`, matching the idiom already used in
`show_form.html`, `contact_form.html` and `messages/options.html`. `hide_label`
went with it (no label is rendered now, so nothing is left to hide) — it had
exactly two callers, both here. **The errors half is not decoration:** the
whole-form render was displaying "This field is required." when a moderator hits
"Move To:" with no destination picked, and rendering the field alone would have
silently dropped it.

Two tests added, and **each was mutation-tested against the fault it names**:
reverting to `{{ form }}` fails `test_the_move_control_is_a_bare_select` only;
dropping `.errors` fails `test_a_move_with_no_destination_shows_the_error` only.
Neither test catches the other's mutation, so both earn their place.

**The first version of the fix shipped a bug that the new test caught
immediately: `{# … #}` is a single-line comment token.** A multi-line `{# #}`
does not comment anything out — the whole thing rendered into the page as
literal text. `{% comment %}` is the multi-line form.

### The deprecation gate was lying, and had been giving a clean bill of health

**`python -W error::django.utils.deprecation.RemovedInDjango50Warning` is
silently ignored.** Python cannot resolve a dotted category path there and
prints `Invalid -W option ignored: invalid module name` — one line, to stderr,
before the test output. A full suite ran **813 green under that flag with the
deprecation still present in the tree**, and it looked exactly like a pass.

Caught only by deliberately re-running the gate against a *known* deprecation
(the un-fixed template) and noticing it did not fire. **A gate has to be proven
to fail before a pass from it means anything** — the same lesson as task 01's
`print('ok')` probe on an interpreter that aborted at exit, now in its warning-
filter form.

**The recipe that works on this rung:**

```
python -W error::PendingDeprecationWarning manage.py test --noinput \
    --settings=sg101.settings.docker_test
```

`RemovedInDjango50Warning` subclasses `PendingDeprecationWarning` on 4.1, the
builtin name resolves, and nothing else in the tree raises one (everything else
deprecated here — Pillow's ANTIALIAS, kombu, pkg_resources, the `assertEquals`
calls — is a plain `DeprecationWarning`). Verified to fail on the un-fixed
template and to pass on the fixed one. **On 4.2 this changes**: Django promotes
`RemovedInDjango50Warning` to a `DeprecationWarning` subclass, so task 05 needs
`-W error::DeprecationWarning` plus ignores for the third-party noise — and must
re-prove the gate fires before trusting it.

### Search: byte-identical, measured before and after on production data

The task named the search app as the thing to watch, since it is the only code
talking to `django.contrib.postgres` and Step 12 spent nine tasks fixing what
its output should be. **Nothing moved.**

A probe captured 16 queries on 4.0.10 before the bump and replayed them on
4.1.13 — per-query total, all 8 per-type counts, and the **top-20 rows with
`rank` to 10 decimal places**, plus the exclusion-stripped query string. The two
JSON captures compare **exactly equal**. The queries are Step 12 task 07's
measured set, and every recorded figure reproduced (`reverb` 54,065; `surf rock`
14,993 vs `surf-rock` 1,328; `ventur` 11,534; `FRV-1` 2,024; `A/B box` 89),
which is also what says the probe is measuring the real index.

- **Exclusion ranking still meaningful.** `reverb -fender` returns 38,340 rows
  across 5 distinct ranks in the top 20 — not the constant score that Step 12
  task 04 found looks entirely normal from the outside.
- **Per-type counts still sum to the total** on all 16 queries, and none
  collapses to 1. On the rendered page, `backing track` shows
  `Downloads (115)` beside `Forum Posts (2,830)`, summing to the `3,481 hits`
  headline — exactly what task 09 shipped.
- **Headline escaping holds.** 302 headlines drawn from real rows whose stored
  summary contains `<`: the only tag rendered in any of them is `span`, the one
  the code writes. Snippets for 6 queries are byte-identical across 4.0 and 4.1,
  40 highlight spans among them, still only `span`.

**One thing that looks alarming in a smoke and is not:** the top hits for
`backing track` render *empty* snippets, and the raw `[[[hl]]]` sentinel appears
in the page source. Both are expected. The top rows are `forums.topic`, whose
document summary is zero characters by design (a topic *is* its title, per task
07), so `ts_headline` has nothing to highlight; and the sentinel occurrences are
inside the **debug toolbar's SQL panel**, printing the query text, not in a
result row.

### Forms: 23 cases, measured against 4.0 rather than trusted

4.1 tightened form and model validation, and this site's most bespoke code is in
its forms — so a green suite was not accepted as the answer. A probe binds the
four forms the task names (registration, profile edit, private message, calendar
event) plus `MoveTopicForm`, with valid **and** invalid input across 23 cases,
and reports `is_valid()`, the full `errors.as_json()`, and the field list. Run
on 4.1.13, then on 4.0.10 in a throwaway `docker compose run --rm` container
with Django downgraded in place: **all 23 identical**, same verdicts, same error
codes, same messages.

The constraint-validation change 4.1 brought has essentially no surface here:
the tree contains exactly one `UniqueConstraint` (`search.SearchDocument`'s
`content_type`/`object_id`), which has no ModelForm, and **no application code
calls `full_clean()` anywhere**. The `LOWER(username)` uniqueness from Step 11
is a raw functional index, not a `Meta` constraint, so it is untouched by this.

**Two probe cases initially failed for reasons that were not Django** — the
registration form carries an antispam question (`question1`), and `country`
takes lowercase ISO codes (`us`, not `US`). Worth noting because both looked
like findings for a moment, and an A/B probe whose "valid" case is not actually
valid quietly tests only the reject path.

### Not needed, with the reason

`CSRF_COOKIE_MASKED` — 4.1's transitional setting exists for a site running 4.0
and 4.1 instances side by side during a rollout. This site deploys once, at the
end, at 5.2 (R14/R15), so there is no window in which two versions serve the
same cookies. Deliberately not set.

`django-debug-toolbar==3.2.4` is past its supported Django range (2.2–3.2) but
loads and panels correctly on 4.1 — verified by the SQL panel rendering the
search query. Its bump belongs to task 06, with the rest of the dependency
alignment; pulling it forward would have put two variables in this rung.

`requirements_dev.txt` still had a `Python 3.7 / Django 3.2 LTS` header, missed
by tasks 01 and 03, which both updated the other two requirements files. Fixed.

### Carried into task 05: two items in the admin header override

Found after the rung closed, by comparing the running admin against production
side by side — see the dashboard fix below, which came out of the same look.
Both live in `sg101/templates/admin/base_site.html`, and both are consequences
of its `{% block branding %}` override replacing Django's version wholesale.

1. **4.2 — the admin login page loses the light/dark theme toggle.** 4.2 adds
   `{% include "admin/color_theme_toggle.html" %}` inside `base_site.html`'s
   `branding` block, guarded on `user.is_anonymous`. Our override supplies its
   own `branding` and would drop it.

   **To be clear about what "anonymous" means here, because the phrasing
   invites the wrong reading:** nobody browses the admin anonymously. The one
   admin page an anonymous visitor sees is the **login form** at
   `/admin/login/` — `admin/login.html` extends `admin/base_site.html`, and
   `base.html` renders `{% block header %}` for anyone not in a popup, with no
   reference to authentication. What *is* gated is `usertools`, on
   `has_permission`. Confirmed by fetching `/admin/login/` anonymously from the
   running site: branding header present, `#user-tools` absent. That is exactly
   why 4.2 ships the toggle **twice** — in `userlinks` for logged-in staff, and
   in `branding` for the one page where `userlinks` does not render. So the
   loss is real but small: a theme toggle on the login screen.

   **Also worth knowing before someone reads a status code wrong:** `/admin/`
   answers **302 → `/admin/login/?next=/admin/`**, not 200. Task 04's smoke
   recorded 200 for an anonymous curl — that was the **debug toolbar's
   Redirects Panel** rendering a page in place of the 302, a dev-only artifact
   of `INTERCEPT_REDIRECTS`. And `docker_test` settings answer the bare test
   client **400**, since `ALLOWED_HOSTS` has no `testserver` outside the real
   runner.
2. **5.0 — `site-name` stops being a heading.** 5.0 changes branding from
   `<h1 id="site-name">` to `<div id="site-name">` for accessibility: the
   page's `<h1>` is meant to be the content title, not the site name. Our
   override still emits `<h1 id="site-name">`. Not a 4.2 item; recorded here
   so it is not rediscovered at Step 14.

**The dashboard mechanism itself is safe the whole way.**
`{% block nav-global %}`, which `base_site.html` uses to hang the moderation
dashboard in the header, still exists in the same place inside
`{% block header %}` in **4.2.30, 5.0.14, 5.1.15 and 5.2.17** — checked by
grepping each release's `admin/base.html`, not assumed.

**Next: Step 13 task 05** — the Django 4.2 rung. (Done 2026-08-05; see the
task 05 section above.)

## Admin dashboard layout fix — DONE 2026-08-04, `1b968a4` (own commit, not part of a rung), PUSHED, CI GREEN

**The moderation dashboard had been rendering at the far right of the admin
header, level with the user tools, instead of on its own row under the
branding. It has been that way since Step 10.** Brian caught it by putting a
production screenshot beside the modernization site; the suite could not see it
and neither could a version bump.

Django's `#header` became `display: flex` with `justify-content: space-between`
in **3.2** (confirmed absent in 1.9.13, present in 3.2.25), which turns
branding, user tools and whatever `nav-global` adds into three flex items
spread across one row. **The wrapper was a `<div class="clear">`** — exactly
right under the floated header 1.9 shipped, and completely inert here, because
**floats and clears do not apply to a flex item**. So it rode through four
rungs unremarked.

Fixed by giving the wrapper its own id and a full-width flex basis, with the
header allowed to wrap — the same intent expressed in the layout model the
admin now uses. The rule sits after `base.css` in the cascade at equal
specificity (`#header` vs `#header`), so it wins on source order; verified from
the served page rather than assumed.

Three tests in `core/tests/test_admin.py`, each verified to fail on the fault
it names. **The third needed a second attempt, and the reason is the recurring
one:** the first mutation flipped an inner per-count `{% if %}` that the outer
"is anything pending at all" condition makes unreachable, so the suite stayed
green and looked like a test without teeth. Mutating the outer guard reproduced
the fault and the test caught it. Also worth keeping: asserting on
`dashboard-list` alone cannot work, because `#dashboard-list` is a selector in
the stylesheet above and is on every admin page whether or not anything is
pending — the assertion has to name the rendered element.

**Confirmed in the browser, since a layout fix verified only by markup is not
verified.** It now renders on its own row beneath the branding as production
does, inset by the 40px of header padding modern Django adds where 1.9 had it
flush left. 816 tests green.

**Not a defect, and worth recording so it is not chased:** production showed
`News: 1` where the local site showed only `Calendar: 29`. Local
`PendingStory.objects.count()` is 0 against 29 event requests — the snapshot
simply predates that submission. The dashboard hides a zero by design.

## Step 13 task 03 — the Django 4.0 rung — DONE 2026-08-04, PUSHED, CI GREEN

## Step 13 task 03 — the Django 4.0 rung — DONE 2026-08-04, PUSHED, CI GREEN

**On Django 4.0.10 / Python 3.10. 811 tests green (unchanged), `check` and
`makemigrations --check` clean, smoke green.**

**The rung itself cost exactly one breaker, and it was a dependency, not the
application.** Task 02's backlog work paid off: not one `ifequal`, `is_ajax`,
`providing_args`, `force_text`, `urlquote` or `ugettext_lazy` surfaced, and
`django.conf.urls.url` was confirmed free as predicted. The single failure was
`django-tagging==0.5.0` importing `smart_text`, removed in 4.0 — and it fails at
*import*, so `django.setup()` aborts and nothing runs at all until it is fixed.
That is worth noting as a shape: a rung can look catastrophic (zero tests
runnable) and be three lines.

### `USE_TZ`: decided on evidence, and the plan was wrong about which release forces it

**Set to `False` explicitly** in `sg101/settings/base.py`, with the conversion
scheduled as new **task 09** (see below).

**The database was never the problem.** Measured across the whole history: a
2006 post the app reads as `19:24:30` is stored as `2006-02-27 01:24:30 UTC`;
the 2011 and 2026 samples line up the same way. Django sets the connection's
`TimeZone` to `TIME_ZONE` while `USE_TZ` is off, so PostgreSQL puts every naive
value on the real timeline. **Turning `USE_TZ` on is a settings change, not a
data migration** — luck the PostgreSQL move bought, since MySQL's offsetless
`datetime` would have forced rewriting every column.

**The application is the problem**, which is why it is deferred: 79 naive
builders (75 `datetime.now()`, 3 `utcnow()`, 1 `datetime.today()`, and **zero**
uses of `timezone.now()`), 3 `pytz.localize()` calls that break outright, and
8 lines of month/year rollup in `donations`/`news` that would silently file a
7pm-Chicago record under the next month. Cross-cutting behavior work does not
belong on a version rung.

**Two corrections to the task file and plan, both from reading 4.0's source
rather than trusting the write-up:**

1. **The `USE_TZ` default flips in 5.0, not 4.0.** 4.0 only *warns*, and only
   while the setting is unset (`conf/__init__.py:205`) — so setting it silences
   the warning outright.
2. **`USE_L10N`'s default *does* flip in 4.0** (`global_settings.USE_L10N` is
   `True`), and nothing in the plan mentioned it. **Measured rather than
   assumed, and it is a no-op here**: with `USE_I18N = False` and
   `LANGUAGE_CODE = 'en-us'`, every format constant is unchanged except
   `DATETIME_INPUT_FORMATS`, which only *widens* (adds date-only `%Y-%m-%d`),
   and numbers render identically because `USE_THOUSAND_SEPARATOR` is off.
   **Deliberately left unset** — setting it buys nothing and adds a
   `RemovedInDjango50Warning`, since the setting is itself deprecated in 4.0.

Verified by diffing a characterization script (storage, ORM values, and output
rendered through the real `forum_date`/`current_forum_time` tags for both an
anonymous visitor and a user on `US/Pacific`) before and after: **byte-identical
except `USE_L10N` and the wall clock.** No repeat of Step 11 task 05's 5–6 hour
shift.

### django-tagging is vendored — the fix was 3 lines, the decision was not

0.5.0 is the final release (upstream stopped 2018) and it breaks on 4.0
(`smart_text`) and again on 4.1 (`default_app_config`). Brian's call: **vendor
now, explore replacements later.** Copied in as `tagging/` under its original
package name, so the app label, its three migrations and their tables all still
match — verified: 1,006 tags and 4,561 tagged items intact, `TaggingConfig`
still auto-detected without `default_app_config`, and `/news/story/1831/`
renders its three tag links. Its own `tests/` (1,371 of 3,020 lines) is **not**
vendored: it ships its own `settings.py` and `urls.py`, and `manage.py test`
would discover and fail it.

**Retirement is scheduled into Step 19**, beside the deferred `elsewhere`
rework. Surface is fully mapped and small — only `news` uses it. `django-taggit`
is the like-for-like, but **a Postgres `ArrayField` is the more interesting
candidate**: the `TaggedItem` join table and its content-type indirection exist
to support tagging *any* model, and this site tags exactly one. Also noted for
that step: `sg101/templates/fixed/colophon.html:14` credits django-tagging with
a long-dead `code.google.com` link, on a live page.

### pytz: all 17 sites audited, all deferred — and the audit found a 93.6% problem

Full register in `research/pytz-audit.md`. **The plan had `zoneinfo` pencilled
against the 4.1 rung; that sequencing is wrong** — nothing forces it (the app
uses pytz *directly*, not through Django, so no rung breaks), and while `USE_TZ`
is `False` the `localize()` idiom is correct and load-bearing rather than
legacy. Converting before task 09 means converting twice. **Moved to task 09.**

**The finding that matters: `zoneinfo` cannot resolve the timezone names 93.6%
of users have stored.** `tools/tz.py` built the profile dropdown from
`pytz.common_timezones`, which carries legacy names a stock slim image's tzdata
does not — `ZoneInfo('US/Pacific')` raises. **14,248 of 15,227 profiles** are on
one of those 17 names, `US/Pacific` alone being 12,619. And
`forum_tags.py:33` hardcodes `DEFAULT_TZ = timezone('US/Pacific')` at *module
level*, so a naive swap raises at import and the forums stop rendering for
everyone, not just the 93.6%. The PyPI **`tzdata`** package fixes all of it
(486 → 599 zones available) — **and the lesson under that is the durable one:
`zoneinfo` reads the host's tzdata while pytz bundles its own**, so swapping
makes timezone correctness depend on image packaging that can differ between
dev, CI and the Step 21 deploy host, with no test that would catch it.

Two more, both measured: **`pytz.NonExistentTimeError` has no `zoneinfo`
equivalent** — on 2:30 AM of a spring-forward date pytz raises and `zoneinfo`
silently returns `-06:00`, so `forums/latest.py:317` currently *detects* the DST
gap and a swap deletes that detection invisibly. And **`zoneinfo` raises two
exception types for bad zone names**, so a one-to-one port of
`except pytz.UnknownTimeZoneError` turns path-shaped input like
`'../etc/passwd'` (a `ValueError`, not `ZoneInfoNotFoundError`) into an
unhandled 500 on a user-controlled field in `bio/forms.py`.

### `CSRF_TRUSTED_ORIGINS` is genuinely free

Not merely absent from the repo: no settings module defines *or reads* it, the
chain is `production.py` → `base.py` with **no local-override escape hatch**,
and `env.read_env()` feeds a fixed key set (DB creds, `SECRET_KEY`, AWS, GCal,
reCAPTCHA) that does not include it. So there is no mechanism by which
production could be setting it, and 4.0's new scheme requirement costs nothing.

### New task 09 — turn `USE_TZ` on

Written this rung, scheduled **last in Step 13, on 4.2, with no version bump in
flight**. Django 5.0 flips the default, so Step 14 cannot start with it open,
and pooling timezone semantics with a version bump is exactly what the
one-variable-per-rung discipline exists to prevent. It also inherits the pytz
work. All measurements above are carried into the task file so nothing needs
re-deriving — with an instruction to re-measure anyway, since tasks 04–08 land
in between.

### Noted, deliberately not fixed here

`core/functions.py:120` emits `DeprecationWarning: invalid escape sequence '\d'`
— a missing raw-string prefix that predates this work and is unrelated to 4.0.
It becomes a `SyntaxError` in a future Python. Left alone to keep every fix in
this rung attributable to it; it is noise in the deprecation gate until someone
takes it.

**The 4.1 backlog is 9 apps, not 1.** Task 02 recorded `default_app_config` as a
single item (`django-tagging`); running 4.0 with warnings visible names
**antispam, bio, downloads, forums, messages, potd, weblinks, wiki** as well.
Vendoring tagging already cleared its one, so **8 remain for task 04.**

## Step 13 task 02 — the RemovedInDjango40 backlog — DONE 2026-08-03, committed

Cleared on Django 3.2.25 where every one of these is still a warning. **811 tests
green** (802 + 9 new), `check` and `makemigrations --check` clean, and the suite
passes with **`RemovedInDjango40Warning` promoted to an error**. 50 files,
+124/−67.

The mechanical part went as written: 19 `ifequal`/`ifnotequal` tags, the seven
pure renames (`providing_args`, `force_text`→`force_str`,
`urlquote`→`urllib.parse.quote`, `ugettext_lazy`→`gettext_lazy`), the four
`is_ajax` guards, and all 32 `from __future__` lines. Three things were not as
written.

**The inventory was missing an item, and it is the one that would have broken
task 03.** Running the suite with the warning promoted to an error surfaced
**`Passing None for the middleware get_response argument`** — 11 tests across
`core/tests/test_middleware.py` (×2) and `wiki/tests/test_middleware.py`, all
constructing middleware bare. Django 3.2's `MiddlewareMixin` carries the comment
`# RemovedInDjango40Warning: when the deprecation ends, replace with: def
__init__(self, get_response):`, so in 4.0 it becomes a **required positional
argument** and a bare `WhosOnline()` is a `TypeError` at construction.

**Why no grep would have found it:** every other item in this task is an
app-code API *usage* with a name to search for. This one is a test-construction
pattern, triggered by the **absence** of an argument. Nothing in the source text
says "deprecated." It exists only in tests because Django's own handler always
passes the real next-link as `get_response`; production was never affected. The
fix passes `lambda request: HttpResponse()` — never invoked, since these tests
drive `process_response`/`process_view` directly, and commented as such. **This
is the argument for running the deprecation gate as a real gate rather than a
formality**, and for doing it on a stable rung: had it waited, task 03 would have
opened with 11 broken tests pooled in with 4.0's genuine breakers.

**`ifequal` is 19 lines across 7 files, not 17 across 6.** The plan's grep
searched `ifequal`, and **`ifnotequal` does not contain it as a substring** —
neither does `endifnotequal` contain `endifequal` — so
`sg101/templates/bio/members.html` was invisible to the count. Worth remembering
as a grep shape, not just a miscount.

**The `is_ajax` swap is a pure refactor, contrary to the task file's warning.**
Django 3.2's method is *literally* `self.META.get('HTTP_X_REQUESTED_WITH') ==
'XMLHttpRequest'`, and `request.headers` is an `HttpHeaders`
(`CaseInsensitiveMapping`) built from META by stripping `HTTP_` and mapping
`_`→`-`. Same key, same comparison. The removal rationale — that the method
detects jQuery rather than AJAX — is a statement about the *method's* honesty,
not about the replacement's equivalence. That design concern is real but
**pre-existing and unchanged**: all three photo endpoints are driven by jQuery
Form Plugin's `ajaxForm()` through `$.ajax`, which sets the header. A future
port to `fetch()` breaks those guards, but it would have broken them under
`is_ajax()` too. Noted in the helper's docstring so whoever modernizes that JS
trips over it. The helper lives in `core/functions.py` beside `get_ip(request)` —
same shape, same module both callers already import from — rather than repeating
the magic string four times.

**`from __future__`: migrations included** (16 app files + 16 migrations). On
Python 3 `unicode_literals` is definitionally a no-op, so the edit cannot change
migration behavior, and the suite rebuilds the test DB from scratch on every run,
applying all of them. Leaving 16 behind would make every future sweep re-triage
the same 32 hits.

**AC6 exposed a coverage gap that had nothing to do with this change.** Dropping
`created=` from a `notify_*` helper left the suite green across 297 forums+search
tests. The receivers in `forums/latest.py` read `kwargs['created']` directly and
the helpers send with **`send_robust`, which swallows the resulting `KeyError`** —
so a dropped argument costs a queued Celery task and reports nothing. Added four
tests pinning which task each helper reaches; both mutations now caught.
(`providing_args` itself was never the risk: it appears **3 times in all of
`dispatcher.py`** — signature, `is not None` check, warning text — and is never
stored or read. Django's own words: "purely documentational.")

**Two dead templates converted anyway.** `core/pagination_query.html` has **zero
references anywhere**, and `ygroup/pagination.html` is reachable only from
`ygroup/thread.html`/`thread_list.html`, which the views bypass in favor of the
`v3/` variants. Converted so they cannot fail a later grep, but no test exercises
them — which is why the conversion was verified by rendering old-vs-new directly
(38 comparisons, 0 differences, harness mutation-checked) rather than by the
suite. Prune candidates for Step 19/20.

**Two findings left alone, both pre-existing.** `tools/filter_posts.py` and
`tools/translate_yahoo_group.py` are **still Python 2** — `print` statements,
they do not compile on Py3 (verified against HEAD, so not caused here). One-time
historical import scripts; prune candidates. And the **Django 4.1 backlog is
exactly one item**: `django-tagging` sets `default_app_config`, which aborts at
`django.setup()` under a 4.1 gate. It is site-packages, so it is a dependency
bump for task 04/06.

**Two process traps, each of which cost a run and produced convincing garbage.**
`manage.py test` under a wrapper script needs
`os.environ['DJANGO_SETTINGS_MODULE'] = ...` — **`setdefault` is a no-op**
because the container already exports `sg101.settings.docker`, so `django.setup()`
binds dev settings before `--settings` can apply, and the debug toolbar produces
**58 failures / 351 errors** that look exactly like the noise recorded at Step 12
task 07. Separately, **zsh does not word-split unquoted parameters**: a
`$TEST_LABELS` variable holding three labels is passed as one bogus label, so
baseline and all three mutants failed *identically* — a mutation run that proves
nothing while looking like it proved something.

## Step 13 task 01 — Python 3.7 → 3.10 — DONE 2026-08-03, PUSHED, CI GREEN

Base image on `python:3.10` with `Django==3.2.25` untouched. **802 tests green**
(798 + 4, see below), `check` and `makemigrations --check` clean, live smoke
green. Cold build 26s vs the 3.7 image's 30s. `cc0ea88` (code) + `27d8bc6`
(planning); **CI green on the first run against the 3.10 image**, which also
settled the one thing local work could not: the Pillow abort had been reproduced
on x86_64 only under emulation, and CI is the real thing. Built from sdist: `mysqlclient`,
`psycopg2`, `ftfy`, `repoze.timeago`, `coverage`; everything else came from
wheels, **including Pillow and lxml**.

**Two dependency bumps, not the one the plan predicted.**

`bleach==3.1.5 → 6.4.0` was the expected gate, and it behaved exactly as
written up: import-time `cannot import name 'Mapping' from 'collections'`. The
`styles=` removal was as small as the plan argued. **Verified rather than
asserted**: a 19-case adversarial corpus (script tags, event handlers, inline
CSS, `javascript:` hrefs, entities, malformed markup) run through both profiles
on 3.7/bleach-3.1.5-with-`styles=[]` and on 3.10/bleach-6.4.0-without-it came
back **byte-identical across all 38 outputs** — only the version banner differs.
6.4.0 is the final release; upstream archived bleach in 2023 for `nh3`.

**`Pillow==6.2.2 → 9.5.0`, which the plan said would not be necessary — this is
the real finding.** 6.2.2 installs on 3.10 *and imports* on 3.10, and then
**aborts the interpreter at shutdown**: `free(): invalid pointer`, exit 134.
Reproduced on arm64 and, under emulation, on **amd64 — so CI and production
would both have hit it**. `from PIL import Image` and nothing else is enough to
trigger it; oddly, doing real image work first sometimes exits clean, which is
what makes it easy to miss. Impact is that any process importing PIL and
returning normally dies on a signal: a Celery worker looks crashed to its
supervisor, a management command fails a shell's `&&`. 9.5.0 is quiet, ships a
cp310 wheel, and **keeps `Image.ANTIALIAS`** — so task 07 still owns the
`ANTIALIAS` removal, now starting from 9.5.0 instead of 6.2.2, with the
DeprecationWarning at all 7 sites making that work visible.

**The measurement lesson generalizes past this project.** The 2026-08-02 pass
checked *installs*. A follow-up caught that **installing is not importing**
(bleach). This task found the third rung: **importing is not exiting.** The
import is silent, the work succeeds, and the process dies on the way out — so a
probe that ends in `print('ok')` reports success on a build that is broken.
Check the exit status, not the output.

**The libjpeg hazard the task file warned about did not fire, and the reason is
worth keeping.** 6.2.2's sdist build *did* find libjpeg on the 3.10 base
(`features.check('jpg')` was True), so the predicted silent-codec-loss never
happened — but only by luck of what the Debian base ships. Moving to 9.5.0
removes the exposure properly, since it installs from a wheel and never
compiles. The Dockerfile comment now names the check instead of asserting the
outcome. Also corrected there: the base is **Trixie**, not Bullseye, so the
`archive.debian.org` note and the "Bullseye's psql would be older" aside are
both gone, along with the `pip<24.1` cap.

**A pre-existing test bug surfaced while editing those exact lines.**
`core/tests/test_html.py` had **two methods both named `test_comments`** — the
second shadowed the first, so the `comments` profile assertion had never run.
Renamed to `test_news`, which is what it always was. That plus three new
behavioral tests (disallowed tags, style attribute, event handler) is the
798 → 802 delta. One of the three failed on first write and **the code was
right**: `strip=True` drops the tag and keeps its text, so
`<script>alert(1)</script>` yields the inert string `alert(1)`, identical on
old and new bleach. The assertion was corrected to the real behavior.

**Pillow 6 → 9 audit, prompted by Brian asking what a three-major-version jump
could break that no test would catch. Answer: exactly one thing, and it did.**
The whole PIL surface the non-test code touches was diffed across 6.2.2 and
9.5.0 against a byte-identical fixture — `Image.open`, `thumbnail`, `resize`,
the four `transpose` constants, `ImageFile.Parser`, `_getexif`, JPEG re-save,
truncation and corrupt-input handling, and CMYK/grayscale/progressive/palette/
16-bit/LA modes.

**`thumbnail()` pixel output changed. Nothing else did, and nothing broke.**

| Size | max channel Δ | mean Δ | pixels differing |
|---|---|---|---|
| 120×120 | 25/255 | 0.74 | 23.3% |
| 64×64 | 9/255 | 0.63 | 33.3% |
| 32×32 | 7/255 | 0.63 | 49.7% |

Sub-perceptual, on a deliberately harsh fixture (high-frequency noise; real
photos drift less). **`resize()` was byte-identical** — so this touches
`core/images/upload.py:96,104,138,146` and `ssl_images.py:101`, and not
`potd`/`utils`. No test could have caught it: the image tests mock PIL
wholesale, which is the same blind spot that makes the six `ANTIALIAS`
assertions useless.

**Two causes, and the obvious one is only half the story.** `reducing_gap`
(Pillow 7.0, a `reduce()` pre-pass) accounts for 64×64 and 32×32 — passing
`reducing_gap=None` restores the old hash there. It does **not** account for
120×120, where default and `reducing_gap=None` agree and both differ from 6.2.2.
Worth remembering before attributing a future shift to `reducing_gap`.

**Verified unchanged**, which is the more useful half of the result: `_getexif()`
still present and returning the orientation tag, so `orient_image` still rotates
uploads; all four `transpose()` constants byte-identical; `ImageFile.Parser`
identical including `.format`; JPEG re-save byte-identical; `MAX_IMAGE_PIXELS`
unchanged; truncated files rejected identically at 90% and 50%; and CMYK,
progressive, 16-bit and palette images all still round-trip. `Image.open()` now
raises `UnidentifiedImageError` rather than bare `OSError` on garbage — it
subclasses `OSError` and `bio/forms.py:94` catches `IOError`, so it is still
caught, and the only way to break it is to narrow that clause.

**Consequence for task 07, applied:** its AC4 said thumbnails should come back
"byte-identical or near it, since `ANTIALIAS` aliased `LANCZOS`." The premise is
right and the test is wrong — the rename cannot move a pixel, but a version jump
can and just did, so a hash check fails for reasons that do not matter. AC4 now
asks for a **tolerance** (max channel Δ ≤ 25/255, mean ≤ 1.0 — the band this
jump produced) and requirement 5 says measure perceptually rather than by hash.

**A related find on the same question, also folded into task 07:** `.format` is
`None` after `crop()`/`resize()` (new objects) but survives `thumbnail()` (in
place). `potd/models.py:66` and `bio/forms.py:98` each capture the format one
line *before* the scale to work around it, with no comment saying why — and the
ANTIALIAS edits land right beside both. That is the likeliest source of the
past PNG/JPEG trouble Brian mentioned: it presents as one format breaking and
the other not, depending purely on which helper the path used.

**Smoke note, so the next person doesn't repeat it:** `/news/` 404s because
**there is no such route** — `news/urls.py` mounts only subpaths (`date/`,
`archive/`, `categories/`, `tags/`, `story/<id>/`, …) and has no empty pattern,
so the 404 is correct. The news app was then smoked properly at `/news/date/`,
`/news/archive/`, `/news/categories/` and `/news/tags/`, all 200.

## PLANNING — Step 13 task files generated, and four plan corrections (2026-08-03)

Eight task files in `.agents/tasks/2026-07-04-modernizing-sg101/step13/`:
01 Python 3.10 base image (+ the forced bleach bump), 02 the `RemovedInDjango40`
backlog, 03/04/05 the Django 4.0 → 4.1 → 4.2 rungs one apiece, 06 dependency
alignment, 07 Pillow/ANTIALIAS, 08 Markdown. Brian settled three scope calls
during generation: **three separate rung tasks** rather than one traversal (the
one-variable-per-rung discipline, and how Step 10 was actually executed);
**Pillow and Markdown stay in Step 13** rather than drifting to Step 14; and
**`USE_TZ` gets investigated and decided inside the 4.0 task**, not pinned
blindly nor split out.

**Generating the files re-counted the plan's inventory against the tree, and
four things came back different.** Recording them because a task file is where
a wrong number becomes wasted work:

- **`is_ajax` is 4 sites, not 7.** Three of the seven grep hits are in
  `forums/templatetags/forum_tags.py:117,125`, where `is_ajax` is a **parameter
  name on the `show_form` tag** — nothing to do with the removed `HttpRequest`
  method. The real four are `core/middleware.py:49` and
  `user_photos/views.py:64,103,219`. Worth noticing that **three of the four
  guard POST endpoints**, so this is an access-control change wearing a
  refactor's clothes: get the header check wrong and photo upload breaks rather
  than degrades. Also `providing_args` is **2**, not 3 (`forums/signals.py:13,20`).
- **`django.conf.urls.url` costs nothing** — zero usages. The one `conf.urls`
  import is `conf.urls.static.static` (`sg101/urls.py:1`), never removed; 89
  modules already use `django.urls`. That rung item can come off the list.
- **The Markdown bump is the biggest single item in Step 13, and the plan had
  it as a footnote to the logger question.** Both custom extensions use the
  pre-3.0 API and cannot load on 3.x: `extendMarkdown(self, md, md_globals)`,
  `md.inlinePatterns.add('del', tag, '>not_strong')`, registry item assignment,
  and `markdown.util.etree`. The `'>not_strong'` relative placement has **no
  numeric equivalent** in `Registry.register()`, so the priority has to be
  re-derived from output. These render `---struck---` and all site autolinking
  on every post, and a mis-registered pattern **does not raise** — it silently
  stops working.
- **The six `ANTIALIAS` test assertions cannot catch the `ANTIALIAS` bug.** Four
  of them assert against `image_mock.ANTIALIAS`, and a `Mock` returns any
  attribute asked of it, so they stay green against a Pillow that removed the
  constant. The bump's real deliverable is a test on a real `PIL.Image`, seen to
  fail before the swap. Same lesson as Step 12's template comment: **a
  regression test that has not been watched to fail proves nothing.**

**One new risk, not a correction.** `USE_TZ` **is not set anywhere in
`sg101/settings/`** — `base.py` has `TIME_ZONE = 'America/Chicago'` (line 28)
and `CELERY_TIMEZONE` (line 220), and nothing else. So the site runs on Django's
`False` default, naive datetimes, against the `timestamptz` columns Step 11
created — the same seam **Step 11 task 05 found every datetime 5–6 hours early
in**. Task 03 has to characterize what the columns hold before choosing, and set
it explicitly either way so a later default flip cannot move it silently. pytz
is genuinely entangled too: 17 sites across 6 modules, including
`pytz.NonExistentTimeError` and `pytz.common_timezones`, neither of which
`zoneinfo` has an equivalent for, plus user-supplied zone validation in
`bio/forms.py`.

**And one caveat on the 2026-08-02 measurement below.** "Builds from sdist" is
not "installs from a wheel." The Dockerfile dropped the image/XML `-dev` headers
because Py3.7 got manylinux wheels; a source build on 3.10 needs those libraries
to link against, and **Pillow built without `libjpeg-dev` builds clean, imports
clean, and fails on the first JPEG.** The measurement said the pins install — it
did not say the resulting Pillow can decode anything. Task 01 verifies codec
support explicitly.

## PLANNING — Step 13 resequenced interpreter-first (2026-08-02)

The step was written as a pure Django traversal, with the Python move sitting in
Step 14. That cannot work: **Django 4.0 requires Python 3.8+**, so the first rung
of Step 13 is unreachable from the frozen `python:3.7` image, and Step 14 is
downstream of the rung that needs the interpreter it owns.

**3.10 is the waypoint**, not the 3.8 minimum. It is the only version supported
by Django 3.2 *and* by everything through 5.2, which is what lets the interpreter
move by itself with `Django==3.2.25` untouched — one variable per rung, the
discipline that has found the real breaker in every upgrade step so far. 3.8
would buy a second interpreter move later; 3.12 cannot be a solo move at all,
since Django 3.2 tops out at 3.10.

**The measurement, taken before the plan was rewritten rather than after.** The
expectation — stated to Brian in the same conversation — was that the interpreter
would force several dependency bumps, because Step 14's venv note had identified
four pins that "predate modern wheels and want C libraries to compile":
`mysqlclient`, `Pillow==6.2.2`, `lxml==4.9.4`, `psycopg2==2.9.9`. **All four
build fine on `python:3.10`**, from sdist, with nothing beyond the apt packages
the Dockerfile already installs, and the entire pin set installs unmodified. The
prediction was wrong, and wrong in the direction that would have oversized the
step. Guessing at build outcomes reads exactly like knowing them; the difference
took one `docker run`.

**Installing is not importing, and that is where the one real breaker is:
`bleach==3.1.5` cannot be imported on 3.10** — `cannot import name 'Mapping'
from 'collections'`, the ABC aliases 3.10 removed. Every other third-party
package imports clean (`debug_toolbar` "fails" only by wanting
`DJANGO_SETTINGS_MODULE`, which is not a version problem). So the bleach bump
deferred since Step 10 is now the gate on the interpreter — and it is much
smaller than its own pin comment implies. That comment calls 3.1.5 "the last
line keeping the `styles=` kwarg `core/html.py` passes," which sounds like a
real CSS allowlist is at stake; in fact **both `_CLEAN_PROFILES` entries pass
`[]`**, and neither allows a `style` attribute anyway, so the kwarg is redundant
twice over and modern bleach's no-`css_sanitizer` default already strips exactly
what it asks to strip. The change is deleting the kwarg, the empty third tuple
element, and two assertions in `core/tests/test_html.py`.

**Consequence worth carrying:** Pillow is now decoupled from the interpreter, so
the `Image.ANTIALIAS` removal across its seven call sites should be its own
change on its own evidence rather than a passenger on the 3.10 move.

### Task 09 — per-type result counts — DONE (2026-08-02)

**18 tests, 798 green**, `check` and `makemigrations --check` clean. New
`search/tests/test_counts.py`; `search/query.py` split; `SearchForm.show_counts`;
`CountedPaginator` in `search/views.py`. **This is the last of Step 12's nine
tasks.**

**It closes the loop on task 07.** That pass measured `backing track` burying the
first of 115 matching downloads at rank #47. The same search now renders
`Downloads (115)` beside `Forum Posts (2,830)`, so the member sees where the
answer lives instead of paging through five screens of forum chatter. The
recommendation task 07 made is now the thing that shipped.

**The change is the split in `search/query.py`; everything else is
presentation.** `matching_documents(query)` is the match set with no type filter
and no order. `search_documents(query, keys)` filters, ranks and orders it for
the page; `type_counts(query)` groups the same set without filtering. The counts
must come from the *unfiltered* set — otherwise narrowing to News Stories zeroes
every other count and destroys the only information that makes narrowing an
informed choice. Verified: a search narrowed to Downloads still shows
`Forum Posts (47,004)`.

**Counts verified against reality rather than against constants**, because both
known failure modes return plausible numbers. For six queries × all eight types,
every facet equals what that query returns with only that type checked —
including the collision the task flagged: `reverb` gives 47,004 forum posts and
4,539 archive posts, which merge to the 51,543 that grouping on
`content_type__model` would have reported as a single number for both.

**Cost reproduces the task's estimate once measured properly.** Medians of seven
runs, warm, against the full 516,858-document index:

| query | hits | count + page | facets + page | delta |
|---|---:|---:|---:|---:|
| `surf` | 156,517 | 0.159s | 0.161s | **+0.9%** |
| `reverb` | 54,065 | 0.129s | 0.130s | **+1.3%** |
| `-fender` | 470,846 | 0.192s | 0.197s | **+2.5%** |
| `backing track` | 3,481 | 0.009s | 0.009s | −1.4% |

And the arrangement the task warns against — facets *added* to the paginator's
`COUNT` rather than replacing it — costs **+36.6%** and **+40.7%** on the first
two. A single un-repeated run had earlier put `reverb` at +8.7%; that was noise,
and worth re-measuring rather than reporting.

**A search still issues two index statements, not three**, asserted in the tests
and confirmed on the live page: one `GROUP BY` for the facets, one for the page.
The paginator is handed its total instead of counting, since the facets sum to
it. `CountedPaginator` works because `Paginator.count` is a `cached_property`,
which is a *non-data* descriptor, so an instance attribute shadows it.

**THE MUTATION TESTING MISLED ME FIRST TIME, AND THE REASON IS WORTH KEEPING.**
Two mutations "passed" — removing the `.order_by()` guard, and aggregating over
the ranked queryset — suggesting the tests had no teeth. Neither mutation
actually reproduced the trap. It needs *both* conditions at once: an ordered
source **and** no `.order_by()` to clear it. With both applied the documented
failure appears exactly as described — **every count comes back as 1** on the
live index — and **eight tests catch it**, including
`test_no_count_comes_back_as_one`, which exists for precisely that. The lesson is
that a mutation which does not reproduce the bug proves nothing about the test,
and reads identically to one that does.

**A consequence worth recording honestly: the `.order_by()` is defensive, not
load-bearing.** The counts aggregate over `matching_documents()`, which carries
no ordering, so removing the guard changes nothing *today*. It earns its keep
only if someone later rebuilds the counts from `search_documents()` — which is
what its comment says, and why it stays.

**Counts are folded into the choice labels** rather than passed to the template
beside them, because a Django template cannot index a dict by a variable without
a filter written for the purpose, and the checkbox loop already renders
`choice_label`. The template's only change is `|intcomma` on the headline hit
count, which had been reading `54065 hits` next to `Forum Posts (47,004)`.

**Nothing else moved:** ranking, the login gate, query logging, page size, page
links and the out-of-range 404 are untouched, and the landing page renders labels
with no counts and issues no counts query.

### Task 08 — the weekly index reconcile sweep — DONE (2026-08-02)

**19 tests, 780 green**, `check` and `makemigrations --check` clean. New:
`search/reconcile.py`, `search/management/commands/reconcile_search.py`,
`search/tests/test_reconcile.py`; `search.tasks.reconcile_index` and a Beat entry
at Sunday 03:30. Reports drift, repairs nothing.

**THE TRAP, AND IT IS THE ORM'S DEFAULT SPELLING.** `missing` reads naturally as
`indexable.exclude(pk__in=rows.values('object_id'))`. That compiles to
`NOT IN (subquery)`, which PostgreSQL **cannot** answer with an anti-join —
three-valued logic means one NULL would change the result, so it materializes the
subquery and rechecks per row. **It had not finished after five minutes on
forums.Post and had to be cancelled from `pg_stat_activity`.** `~Exists(...)`
compiles to `NOT EXISTS` and the same check runs in **567 ms**. Recorded in the
module docstring, because the fast spelling is the less obvious one and someone
will eventually "simplify" it back.

**Baseline against the full index: clean, 8 types, 2.6 s** (2.32 s of query time).
`forums.post` is 2.2 s of that; every other type is single-digit milliseconds.
Per-check on forums.post: missing 567 ms, orphaned 705 ms, deleted 72 ms, stale
882 ms. **No sequential scan of `forums_post` in any plan.** The staleness check
*is* a nested loop — 444k correlated lookups — but each is an index scan on
`search_document_unique_source` at 0.001 ms, which is the right plan rather than
a degradation, and three spellings (correlated `Subquery`, `Exists` from the
source side, `Exists` from the index side) all landed within 750–805 ms.

**`get_task_logger()` would have sent the report to the wrong file.** Celery
reparents the logger it returns onto `celery.task`, so `search.tasks`'s existing
lines do **not** reach `logs/search.log`. The sweep uses
`logging.getLogger('search')` — the same name `search/views.py` uses — so its
findings interleave with the query lines, which is what the task asked for.
Verified in the file, not assumed: INFO on a clean run, WARNING per drifting type.

**Proved on real data, and the interesting part is what did *not* self-heal.**
Stopped the worker; edited post 484428 through `save()` (queueing a task nobody
was draining) and deleted the index row for link 580 outright. The sweep reported
exactly those two and nothing else — `1 (484428) stale`, `1 (580) missing`. On
restarting the worker, **the queued task survived in Redis and repaired the post
by itself**, while the lost row stayed missing until `reindex_search` was run by
hand. That distinction is the argument for the job existing: the drift that
matters is the drift no queued task will ever fix. Snapshot restored afterwards
(update_date put back, weblinks reindexed, sweep clean).

**Orphans are split into deleted vs still-present, which the task did not ask
for.** An index row can fail two ways — its source is gone, or its source exists
but is no longer indexable — and one count merges them. The second is exactly
what task 03's backfill found in production (43 unapproved downloads, 57 links,
1,637 deactivated profiles), so a sweep that cannot name that class would miss
the defect this codebase has actually had. One extra `~Exists` against the
unfiltered manager, ~72 ms on the largest type.

**Every test was mutation-checked**, per the lesson from task 05 that a
regression test which passes against the bug is worthless. Six mutations — each
detection blinded in turn, the deleted/excluded split collapsed, and a write
injected into the sweep — and **each was caught by its intended test**. Worth
noting: the injected write was caught **only** by
`test_the_sweep_issues_no_write_statements`, not by the before/after state
comparison, because the mutation wrote to a row matching nothing. Both tests
earn their place.

**`ygroup.Post` is detected, not hardcoded.** `tracks_updates()` reads
`_meta.get_fields()` rather than naming the model, so the archive's lack of an
`update_date` cannot silently become a special case that outlives the reason
for it. Missing and orphaned are still checked for it.

**Next:** task 09, per-type result counts — which task 07 recommended as the fix
for cross-type burial.

### Task 07 — search verification against production data — DONE (2026-08-02)

**No code changed and no reindex is needed.** A verification pass, not a feature:
34 queries against all 516,858 documents, timings, plans, and one real ranking
defect. Full write-up in `research/search-verification.md`; the load-bearing
findings are below. 761 tests still green — nothing here touched the suite.

**`normalization=Value(1)` is a document-length sort in disguise, and the comment
in `search/query.py` justifying it is wrong in both halves.** It reads "so a
900-word forum post does not outrank a tight news headline on bulk alone."
`ts_rank` does not reward bulk — eight documents matching `Sundazed Music` in
their titles all score `0.9910322` at `normalization=0`, whether they are 0 or
677 characters long. And the tight document here is not a news headline: it is
`forums.topic`, whose summary is **exactly zero characters** because a topic
document *is* its title. Measured average vector lengths: topic **71** bytes,
weblink 318, download 373, post 480, podcast item **1,635**. So normalization is
not protecting brevity from bulk — it is *manufacturing* an ordering where
`ts_rank` saw a tie, and that ordering is length, ascending. The clean
demonstration is a forum topic and a weblink carrying byte-identical titles: same
weight-A match, and the weblink places fifth at `0.2678` against the topic's
`0.4955` solely because it has a 96-character description.

**The cost is that categorical queries bury the curated types — exactly
backwards.** `backing track` → first download at **#47** (of 115 matching);
`Treble Spankers` → first weblink at **#36**; `space surf podcast` → the podcast
item at **#29**; `surf guitar tabs` → first weblink at **#26**. Specific queries
are fine: `Ali Baba backing track` and `Link Wray Creepy tablature` both put the
download at #1. `space surf podcast` compounds two causes — podcast titles are
literally "Episode 7" with the show name in the summary at weight B, so the forum
posts *announcing* the episode carry "Space Surf" at weight A and outrank the
episode itself.

**Kept `normalization=1` anyway, and this is the judgement to revisit if Brian
disagrees.** `normalization=0` lifts that download from #47 to #2, but over the
20-query comparison the top-10 type mix goes topic **121 → 5** and post 71 → 177:
it rescues 11 curated rows by all but eliminating thread titles, which are the
site's natural navigational answer. **The recommended fix is task 09** — per-type
counts let a member searching `backing track` click `Downloads (115)` directly,
and the burial is a *volume* problem between types (444,134 posts vs 673
downloads), not a ranking error within one. If a per-type boost is wanted anyway,
the measured magnitude is **≈1.21×** and it is query-time, so cheap to try.

**`'english'` stays, decisively.** Band names here are overwhelmingly plural
nouns and stemming unifies them (`ventur`, `bombora`, `tornado`); it also folds
surfing/surfed/surf, tabs/tab, and **silently fixes the typo `reverbe` → all
54,065 reverb documents**, which `'simple'` returns nothing for. `'simple'` would
index the stop words (a `the` lexeme covering most of the table) and manufacture
junk (`Satan's Pilgrims` → a bare `s`). Contamination from the worst-case stem
was measured, not assumed: of 11,534 documents matching `ventur`, **10,990
(95.3%) contain the literal "Ventures"**. No reindex.

**The `FRV-1` limitation is gone — but the design's stated reason for it is
wrong, and the difference is visible.** `FRV-1` finds **2,024** against the old
tips' `FRV 1` workaround at **114** (18×). The design said the parser "emits both
the whole hyphenated token and its parts" — true for letter–letter (`surf-rock`
also emits `surf`, `rock`), **false for word–digit**: `FRV-1` parses as an
asciiword plus a *signed integer* `-1`, and websearch makes them adjacent
(`'frv' <-> '-1'`). It works because it is a phrase match on an adjacency, not
because a compound token is indexed. Two consequences: a document written `FRV 1`
will never match a query for `FRV-1` (`1` and `-1` are different lexemes), and
`surf-rock` finds **1,328** where `surf rock` finds **14,993**, because the
hyphenated query demands the compound token. Correct behavior, but hyphenating
*narrows*. The tips block needed no edit — task 04 retired the apology early —
and every other claim in it was re-verified, including `A/B box` (89 hits, `a/b`
survives as one `file` token) and author search.

**Performance: the GIN index is used in every plan** (`Bitmap Index Scan on
search_sear_search__b5d516_gin`), no sequential scan anywhere, index scan for the
worst term returning 166,388 rows in **7.9 ms**. Warm medians, counting the
paginator `COUNT` and the top-10 slice separately because a page pays both:
typical queries **1.3–10 ms**, worst case `surf` (156,517 hits, 30% of the
corpus) **159 ms**, `"surf music"` **168 ms**. Incidental confirmation from the
plans: `ts_headline` projects in a `Result` node *above* the sort, so it runs for
ten rows rather than 156,517 — because `rank` is the sort key and `headline` is
not.

**The rate-limiting deferral stands, but not for the reason the design gave.**
"A GIN lookup should be milliseconds" holds for typical queries and is off by two
orders of magnitude for the broadest ones — one core saturates at roughly **6
req/s** of `?q=surf`. What actually carries the load is that `/search/` is
login-gated, the defence adopted after bots were killing the site. **If that gate
is ever relaxed, rate limiting has to be reconsidered in the same change.**

**Deferred to Step 20 with numbers: Misirlou / Miserlou.** The site's signature
tune is split across two spellings and neither query finds the other — 1,416
documents match `misirlou`, 2,131 match `miserlou`, **only 148 match both**. The
misspelling is the *more* common form on the site. Either spelling reaches at
most 63% of the ~3,400 documents about the song. Stemming does not bridge it and
`'simple'` would not either; it needs a synonym dictionary (config change + full
reindex) or `pg_trgm` similarity as a low-result fallback. Real features, not
tuning.

**Next:** task 08, the index reconcile sweep.

### Task 06 — the `ajax_users` ordering fix — DONE (2026-08-01)

**Two tests added, one corrected; 761 green**, `check` clean. Commits `c87fc27`
(the fix) and `a95f2c3` (a dead-code deletion it uncovered).

**THE ENGINE CHANGE IS WHAT MADE THIS REAL, AND MEASURING SHOWED WHY.** The task
recorded that the view takes a `LIMIT`ed slice with no `ORDER BY`. What it did not
say is that on MySQL the results were alphabetical *anyway*: `username__istartswith`
compiles to `username LIKE 'x%'`, which MySQL answers with a **range scan on the
unique `username` index** (`type: range`, `key: username`, confirmed by `EXPLAIN`
against the still-running MySQL container), and an index range scan returns rows
in key order. Brian spotted this from the other end — he compared against the
live site and got the same results he was getting from the fix.

PostgreSQL cannot inherit that accident. Django compiles the same lookup to
`UPPER(username::text) LIKE UPPER(...)`, a function of the column that the plain
btree cannot serve, so the plan is a **Seq Scan** and the order is heap order:

| | first five for `bri` |
|---|---|
| MySQL (production today) | Brian, Brian-C, Brian123_surf, brianblaut, Briandean335 |
| Postgres, no `ORDER BY` | brianeharmonjr, Brian-C, bridgeman, Briantime, brianmckenna1111 |
| Postgres, with the fix | Brian, Brian123_surf, Brian_66, brianblaut, Brian-C |

So this was not tidying a theoretical wart: it restores behavior MySQL had been
providing for free and Postgres had quietly stopped providing at the migration.
Ordering under `en_US.utf8` is linguistic rather than ASCII, which is the better
reading for a member-facing list — mixed case interleaves instead of every
capitalized name sorting ahead of the lowercase ones.

**Both ordering tests were verified to fail with the `order_by` removed**, per the
task's own acceptance criterion 2 — the point being that the old test passed by
query-plan luck, so a replacement that did the same would be no better.

**The autocomplete's third "caller" turned out not to exist.** `messages/forms.py`
and `bio/forms.py` wire it; `core/widgets.py`'s `AutoCompleteUserInput` looked like
a third but had no importers at all. History dated its death exactly: it lost the
member search on **2016-04-22** (`4d208c0`) and the private message form on
**2016-10-23** (`a2d6c5e`), each replaced by a CSS class the site's own JavaScript
binds — superseded deliberately, twice, then never deleted. **Deleted here**
(`a95f2c3`) rather than waiting for Step 19; the three forward-pointers to that
step are marked resolved above.

**Deferred to Step 20, with numbers:** every keystroke seq-scans all 15,227 users.
A functional index on `UPPER(username)` turns that into a bitmap index scan —
**2.7 ms → 0.48 ms** on the worst realistic prefix — but it needs
`varchar_pattern_ops`, and neither existing index on the column covers it,
including the `lower(username)` unique index from Step 11, which still seq-scans a
prefix `LIKE` at 3.3 ms. All measured in rolled-back transactions. Not done now
because 2.7 ms is invisible and a third index on one column is a tuning decision,
not a correctness one.

**Next:** task 07, verification against production data.

### Task 05 — the forums' duplicate-topic quick search — DONE (2026-08-01)

**The last stubbed search route is gone.** 17 new tests, 759 green, `check` and
`makemigrations --check` clean. Commit `06b61f9`. New: `search.views.search_topics`
and `search/tests/test_quick_search.py`; `search_ajax.html` renamed to
`search_topics.html`. Exercised from the real new-topic form on the running
stack, not only in tests.

**BRIAN SUPERSEDED TWO REQUIREMENTS, AND THE REASONING GENERALIZES.** The task
said to keep the path at `/search/ajax/` *because the JavaScript hardcodes it*,
and not to touch `forums.js` beyond the minimum. He observed that the view forces
`forums.Topic` anyway, so the JS sending `models=forums.topic` advertises an
interface that does not exist — and once the JS is being edited to drop it, the
only argument for freezing the path has evaporated. **The constraint was
self-justifying**: "don't change the path because a caller hardcodes it" holds
only while that caller is not already being changed. So the endpoint is
`/search/topics/` (route `search_topics`), naming what it does rather than how it
is called, and the JS sends a bare `q`. He has no plans to offer quick searches
over the other seven types, which is now recorded in the view rather than implied.

**The trap in dropping `models`:** the fragment's "visit the search page" link
built its query string by forwarding `q` *and* `models` from the request. With
nothing left to forward it would have silently widened the full search page to
all eight types. It pins `models=forums.topic` itself now — which is more correct
regardless, since the link should describe what was searched rather than echo the
caller. Caught before shipping; pinned by a test.

**THE MARKUP BUG WAS REAL AND PRE-DATED THE PRUNE.** `</fieldset>` and `</div>`
sat inside the `{% else %}` branch, so neither closed when there *were* results —
precisely the case a member sees when the feature works. Fixed, and the test was
**verified to fail against the old markup** rather than merely pass against the
new; the no-results test correctly still passes, that branch never being broken.

**A BUG I INTRODUCED AND BRIAN CAUGHT IN THE BROWSER:** Django's `{# #}` is
**single-line only**. A three-line one is not a comment at all and renders
verbatim, so an explanatory note appeared on the page. `{% comment %}` is the
multi-line form. The instructive part is the test: the one written to catch it
*passed against the broken template*, because the comment lives inside
`{% if page.paginator.num_pages > 1 %}` and the test indexed a single topic, so
the block never rendered. Only checking that the regression test actually fails
against the bug exposed it. It now indexes 25 and asserts no `{#`/`{%`/`{{`
survives in either branch.

**Quick searches are logged, marked.** An earlier draft skipped logging on the
grounds that the check fires while a member types — **Brian corrected this: it is
an explicit button click**, `forums.js` binds only `topicSearchButton.click(...)`
with no `keyup` or `input` handler anywhere. So each request is deliberate and
worth recording, and the line reads `Forum topics quick search: <q> by <user>
[<ip>]` — distinct from a real search, because it records what a member was about
to post rather than what they went looking for. The task file's Background said
"as a member types a new topic title", which is where the error came from; it has
been corrected in place.

**`core/tests/test_pruned.py` lost its search assertion entirely.** Both search
URLs now serve real views, so "the stub still serves" has no subject; the module
docstring notes that search is the one pruned thing that came back, rebuilt rather
than resurrected.

**THE DEAD-METHOD PRUNE IS NOW UNBLOCKED.** Nothing outside the models defines or
calls `search_title`/`search_summary` except two live callers:
`search/documents.py:283` needs `bio.UserProfile.search_title()`, and
`podcast/detail.html:79` needs `podcast.Item.search_title()` for social sharing.
The other 14 methods across `forums`, `news`, `ygroup`, `downloads` and `weblinks`
are dead, and **no test references any of them**. Left for the end-of-Step-12
prune as planned.

**Next:** task 06, the `core.views.ajax_users` ordering fix.

### Task 04 — the search page, restored — DONE (2026-08-01)

**`/search/` works again, for the first time since Step 4 stubbed it.** 64 new
tests, 743 green, `check` and `makemigrations --check` clean. Commit `2622943`.
New: `search/query.py` (the read path, as `search/indexer.py` is the write
path), `search/forms.py`, `search/views.py`, `search/urls.py`, and four test
modules including `test_xss.py`.

**Verified end to end against the real 516,858-document index**, not only in
tests: ranked blended results, working snippets, and a 470,846-hit exclusion
query answered in 0.13s.

**THE DEFECT THIS TASK FOUND, ONE: ts_rank cannot rank a query that excludes
anything.** The moment a tsquery holds a negated term, `ts_rank` returns
`6.3092975e-21` — the same constant for every row, regardless of length or where
the match fell. So `reverb -fender` came back ordered by nothing but the date
tiebreak, across all 38,340 of its hits, while looking perfectly normal. This
matters more than it sounds because requirement 7 has the tips block actively
*teaching* `-exclusion`: the one syntax we advertise was the one that silently
turned ranking off.

Fixed by ranking against the query with its exclusions stripped
(`search.query.positive_terms`) while filtering keeps the whole query. Confirmed
on real data — a title hit now leads at 0.4027 where every row previously tied.
**Brian chose this over documenting the limitation or dropping the syntax from
the tips.**

**THE DEFECT THIS TASK FOUND, TWO: the obvious way to render a snippet is
stored XSS.** `SearchHeadline` returns the summary with the match wrapped, and
PostgreSQL escapes none of the text around it — so `{{ result.headline|safe }}`,
which is what the annotation invites, publishes stored input as HTML.

The summaries genuinely contain live markup. `body_text()` is
`html.unescape(strip_tags(...))`, so a stored `&lt;` — which is how every
`news.Story` and much of the ygroup archive holds a typed angle bracket —
survives `strip_tags` and then *unescapes into a real tag*. `ts_headline` drops
some tags but by no means all: `<img src=x onerror=alert(1)>` comes back through
it **intact**, verified in psql.

Fixed by having the database mark hits with sentinels that escaping cannot
touch (`[[[hl]]]`), escaping in Python, and inserting the real markup after.
Residual and deliberate: a member who types the sentinel earns themselves a
highlight `<span>` and nothing else, since the replacement is a fixed literal —
pinned by a test. `test_xss.py` covers both stored and reflected paths by
asserting **every tag in a result row is one the template wrote**, which is the
assertion that works; an earlier substring blocklist produced nine false alarms
on payloads that were inert text.

**THE FRV-1 TIP WAS XAPIAN'S PROBLEM, NOT POSTGRES'S.** The task file said to
leave the claim alone for task 07 to judge. One query settled it: `FRV-1`
returns **2,024** documents, while the tip's advice to search `FRV 1` instead
returns **114**. PostgreSQL splits the token into `'frv'` and `'-1'` at adjacent
positions and reads the query as a phrase over them; `surf-music` indexes as the
compound *and* both halves; `A/B` survives whole. The apology became a tip that
says the true thing, with two behavioral tests behind it.

**BRIAN REVERSED REQUIREMENT 1 AND AC4.** They specified all eight boxes checked
on render, reasoning that it made the implicit "none means all" convention
visible. He asked for them to start **unchecked**, matching the old site, so a
member picks their areas rather than being handed a whole-site search. The
submit-nothing-means-everything rule stays: a browser sends nothing for an
untouched checkbox group, so the masthead box — which posts a bare `q` — is
indistinguishable from a form nobody touched, and both have to mean everything.
Consequence worth knowing: unchecked boxes do not *force* a choice, they only
stop suggesting one.

**Two errors in the task file, corrected:** it says "eight callers across seven
templates" and then lists seven references across six files — seven is right,
and `haystack_search_ajax` has **zero** callers, nothing reverses it anywhere.
And "delete the `FixedView` stub" cannot mean the class, which still serves
about/colophon/privacy/tos; it means the two stub routes. The quick-search route
keeps its placeholder until task 05 supplies the view, and
`core/tests/test_pruned.py` was narrowed to assert that rather than the search
page.

**Still deferred: the models' `search_title`/`search_summary` methods.** Task 01
parked this until task 04 settled what was dead, and it is still not settled —
`search_ajax.html:7` renders `result.object.search_title` until task 05 rewrites
it, and `podcast.Item.search_title()` must survive regardless (social sharing,
`podcast/detail.html:79`). Also untouched: `fixed/colophon.html` still credits
Haystack and xapian-haystack in prose, and the dead Xapian index templates in
`sg101/templates/search/indexes/` remain, cited by `search/documents.py` as the
provenance of its field lists.

**Task 09 came out of reviewing this one.** Measuring `reverb` showed 95% of its
54,065 hits are forum posts, which buries the 243 news stories — so the member
is being asked to pre-filter without evidence of where their answer lives. Per-
type counts beside each checkbox would supply it, and the single-table index
makes them a `GROUP BY` over a query already running. Costed at **+0.9%** if the
facets replace the paginator's `COUNT(*)` (they sum to it), **+36%** if merely
added alongside. Two traps found while prototyping, both yielding plausible
wrong numbers rather than errors: an uncleared `order_by` puts the ordering
columns in the `GROUP BY` and returns 1 for every type, and grouping on
`content_type__model` merges `forums.Post` with `ygroup.Post`. Both are written
into the task file.

**Next:** task 05, the forums' duplicate-topic quick search.

### Task 03 — incremental indexing through Celery — DONE (2026-07-30)

**The index now maintains itself from ordinary site activity.** 44 new tests,
679 green, `check` and `makemigrations --check` clean. New: `search/tasks.py`,
`search/receivers.py`, `search/apps.py`, `search/indexer.py`; `search/tests/
test_receivers.py` and `test_tasks.py`.

**End to end on the running stack with real data:** a forum post became
findable **0.61s** after being posted, through the real worker and Redis, and
its rows were gone **0.73s** after the topic was deleted.

**THE DEFECT THIS TASK FOUND: three of the eight documents were indexing
content the site does not show.** Requirement 6 asked for the other seven
documents' visibility rules to be confirmed rather than assumed, and the
assumption was wrong. Task 01 built every queryset from `_default_manager.all()`
and only `forums.Topic`/`Post` narrowed it. Measured in the backfilled index:

| Document | Rule that was missing | Rows wrongly indexed |
|---|---|---|
| `downloads.Download` | `is_public` (an admin's approval) | **43** of 716 |
| `weblinks.Link` | `is_public` | **57** of 571 |
| `bio.UserProfile` | `user__is_active` | **1,637** of 15,227 |

The downloads case is the worst of the three: `downloads-details` is
`get_object_or_404(Download.public_objects, ...)`, so each of those 43 would
have produced a search hit that **404s on click** while showing the title and
description of something an admin has not approved. The 1,637 profiles are
deactivated accounts, which are mostly spammers — `bio/views.py:40` already
keeps them out of the member list that exists for finding people.

The profile exclusion was the one product call in the three, since it also makes
a *resigned* member unfindable rather than only a spammer. **Confirmed by Brian
2026-07-30: "deactivated users can be removed from the index."**

**All three rules were recovered from the pruned stack rather than invented** —
`pre-step-4-prune`'s `downloads/search_indexes.py` and `weblinks/search_indexes.py`
both used `index_queryset() → Model.public_objects.all()`, and `bio`'s used
`UserProfile.objects.filter(user__is_active=True)`. The old
`QueuedSignalProcessor` went further and had an `enqueue_public_save` that
enqueued a *delete* when `is_public` was false, "in case the flag just went from
True to False". Same lesson as Q1–Q11: the old behavior is in the repo, and
checking beats remembering.

Fixed in the registry querysets, where task 02 put the private-category filter,
so the per-object task inherits all four rules for free. Index repaired with
`reindex_search --model` for the three types: **1,737 rows removed, corpus now
516,858**. Verified by SQL join that zero non-public downloads, non-public
links, deactivated profiles or `Kahunas` rows remain. The remaining three
documents genuinely have no rule (`news.Story`, `downloads.Download` and
`weblinks.Link` keep unapproved submissions in separate `Pending*` models;
`podcast.Item` has no flag; `ygroup.Post` is a frozen archive) — recorded in
`search/documents.py`'s docstring so it need not be re-derived, and asserted by
`test_the_types_without_a_visibility_rule_index_everything`.

**REQUIREMENT 8 IS MOOT, AND MEASURING SAID SO.** The task file warned that
attaching `post_delete` to `forums.Post` disables Django's fast-delete path.
It was already disabled: `forums/receivers.py` has connected `on_post_delete` to
`Post` and `Topic` for years, and `downloads.Download`/`weblinks.Link` likewise.
Confirmed directly — `Collector.can_fast_delete(Post.objects.all())` is `False`
with the search receivers disconnected. Timed on the biggest topic in the
snapshot (**7,649 posts**) inside a rolled-back transaction:

| | Wall clock | on_commit callbacks |
|---|---|---|
| Without the search receivers | 105.65s | 7,650 |
| With them | 106.51s | 15,300 |

**CORRECTED 2026-07-30 — that +0.86s is not the production cost.** The
measurement wrapped `_delete_topic` in `transaction.atomic()` so it could be
rolled back, which made `in_atomic_block` true, so the callbacks were *appended
to a list* rather than run. In production nothing wraps that view
(`ATOMIC_REQUESTS` is unset and `save_base` opens no transaction for a model
without parents), so each callback **executes immediately** and publishes for
real. Measured separately: **0.402 ms per publish** to the local Redis, so 7,649
posts is **~3.1s**, or **~3%** on top of the 105.65s baseline. The 0.86s figure
was the cost of building and registering 7,650 partials, nothing more.

The conclusion is unchanged: 3s on a 105-second operation is still noise, and
the path was already dominated by the app's own per-post work
(`post.attachments.clear()` in a loop, plus a topic and forum recount save per
post). So **a delete queues one task per object rather than batching them.** A
batcher would have to hold pending ids on the connection and clear them on
rollback, and Django 3.2 has no `on_rollback` hook to do it with — a subtle leak
in the path where bugs are silent, bought for 3% of an admin action nobody runs.
(That 105s is pre-existing and not ours; worth a look if the forums are ever
open for other reasons.)

**The general lesson, which cost me a wrong number: a rolled-back transaction is
not a neutral harness for measuring `on_commit` work.** Wrapping something in
`atomic()` to undo it changes the very behavior under test — it converts
immediate execution into list appends. Measure the deferred work separately, as
above.

**Both privacy directions verified on real data**, on the smallest public
category (`SurfGuitar101.com Site Specific`, 337 topics / 7,991 posts) so that
genuinely private content was never indexed to test the test: assigning a group
**purged 8,328 rows in 1.1s**, removing it **restored all 8,328 in 2.1s**, and
the category finished byte-for-byte where it started. `reindex_category` needs
no idea which direction the change went — it indexes what the documents still
yield for the category and drops the rows of everything they no longer do, which
covers both.

**`transaction.on_commit` is what the tests actually assert.** Under
`CELERY_TASK_ALWAYS_EAGER` a `delay()` called straight from a handler would
index *immediately*, so the test asserts the row is **absent inside** the
`captureOnCommitCallbacks` block and present after it — a test that only checked
the end state would pass either way. A companion test rolls an atomic block back
and asserts zero callbacks were left registered. **Note the corollary: ordinary
`TestCase` tests never run on_commit callbacks at all**, so the other 600 tests
in the suite are untouched by indexing — the blast radius of this change on the
existing suite was one test module (see below).

**`instance.pk` is read in the delete handler, not in the callback.** The
collector sets it to `None` when the delete finishes, which is before the commit
that runs the callback — capturing it at signal time is not a style preference.

**WHY `on_commit` MATTERS HERE, since the member-facing paths have no
transaction to wait for** (Brian asked, 2026-07-30, and the first answer —
future-proofing — undersold it). `ATOMIC_REQUESTS` is unset and `save_base`
opens no transaction for a model without parents, so a member posting to the
forums publishes the task immediately; `on_commit` defers nothing there. **But
the Django admin wraps both `changeform_view` and `delete_view` in
`transaction.atomic`, and the admin is where a category's groups are edited.**
That is the privacy boundary, inside a real transaction. Without `on_commit`,
making `Kahunas` private would: insert the m2m row uncommitted → fire
`m2m_changed` → publish `reindex_category` → the worker reads the category on
another connection, cannot see the uncommitted row under READ COMMITTED, judges
the category public, and **indexes all 487 topics and 19,088 posts** → the admin
transaction then commits. Silent, no error, and nothing fixes it until someone
reindexes by hand. The same race runs the other way through `delete_view` (a row
re-indexed just before its object is deleted, left orphaned) and through
`auth.User` (a deactivation the worker cannot see yet, so the spammer's profile
stays searchable). One uniform rule, free when there is no transaction and
correct when there is; "queue on commit unless we think there is no transaction"
is not verifiable at a call site.

**THE OUT-OF-ORDER RACE — FOUND, THEN FIXED (Brian asked 2026-07-30 whether
autocommit lets indexing run at the wrong time, then asked for it closed).** The
fix is an optimistic guard in `SearchDocument.objects.index_object`: `read_at` is
taken **before** the source is read, becomes the row's `indexed_at`, and the
write is `WHERE indexed_at < read_at`, so a row already built from a later read
is left alone. Either interleaving now yields the fresher snapshot. Falls back to
an insert when there is no row, inside `atomic()` so that losing the insert race
to a concurrent task leaves a usable transaction rather than an aborted one.
Proven by removing the guard and watching
`StaleWriteTestCase.test_a_stale_read_does_not_overwrite_a_fresher_row` and
`..._does_not_roll_indexed_at_backwards` go red. **The bulk path in
`search/indexer.py` deliberately keeps no guard** — a reindex is the repair tool
and must be able to overwrite a row however fresh that row claims to be.

Everything below is the analysis that led there, kept because the reasoning
matters more than the conclusion.

A
member posting is safe *because* there is no transaction: in autocommit the
INSERT commits as it executes, and `post_save` fires after it, so the row is
durable before the task is published. The real hazard is **two tasks for the
same object processed out of order** — the worker runs at concurrency 10, so
tasks queued a millisecond apart land in different child processes.
`bio.edit_profile` is the case, and the duplicate is **unconditional**: the
edit-profile page is one form over two models — `first_name`, `last_name` and
`email` live on `auth.User`, everything else on `bio.UserProfile` — so every
valid POST saves both rows (`ModelForm.save()` does not diff), and each save
queues `reindex_document(UserProfile, 42)`. If the first reads the profile
before the second's save commits but writes after the second has written, the
index keeps the pre-edit text. The redundant task is therefore 100% of profile
edits; only the stale *outcome* needs the unlucky interleave — which is what
tipped the decision from "record it" to "fix it": a race run on every profile
edit is a different proposition from one run incidentally. **Task 08's reconcile sweep cannot see this** —
the stale write stamps `indexed_at = now`, so the row looks fresh against the
source's `update_date`. Needs an unlucky interleave in a ~1ms window; self-heals
on the next edit of that profile; `reindex_search --model bio.userprofile` is
the manual remedy. **Fixed, as above** — the read-timestamp option; the
alternative considered was locking the index row and reading the source *inside*
the lock, which is also correct and needs no clock, but costs a row lock on every
write and still needs insert-race handling for a brand-new object, so it buys a
lock for nothing.

**The delete case is immune, and by design rather than luck.** `_delete_topic`
saves the topic (queueing a reindex) and then deletes it (queueing a removal);
if those are processed out of order and the reindex lands last, it looks the
topic up in the document's queryset, does not find it, and **deletes the row**
instead of recreating it. A late reindex for a vanished object cleans up after
itself. Only the case where both tasks find the object present — a profile edit
— can settle on stale data.

**Rejected: the old stack's content-update signals.** `forums/signals.py` and
`bio/signals.py` still ship `topic_content_update`, `post_content_update` and
`profile_content_update`, which the Xapian processor used instead of `post_save`
so that saves changing no text (`profile.save(content_update=False)`, which fires
on every forum post to bump `forum_post_count`) did not reindex. Not adopted:
those are sent by hand from a handful of call sites, and one that someone forgets
to add is an index that goes quietly stale — the exact failure this task exists
to prevent. `post_save` cannot be bypassed. The cost is two extra cheap tasks per
post (the topic's row and the author's profile row) at 134 posts a month.

**Three senders beyond the eight models, all for the same reason** — the
searchable object is never saved when the thing that changed is, so `post_save`
on the document's own model cannot see it. `forums.Category` (its groups decide
whether the topics and posts may be indexed at all) is the one the task file
asked for; the other two came out of checking:

- **`post_save` on `User`.** A profile document holds the full name at weight A
  and is indexed only while the account is active, and *both of those live on
  `User`*, which the auth admin edits on its own. The site's own
  `bio.edit_profile` saves the profile too, so the member-facing path was
  already covered, but an admin rename or deactivation from `/admin/auth/user/`
  rebuilt nothing. Skips `created` (bio's receiver creates the profile, which
  queues its own reindex) and `update_fields == {'last_login'}`, every login.
- **`post_save`/`post_delete` on `elsewhere.WebsiteProfile`** (added 2026-07-30
  at Brian's prompting — see the content-update-signal note below). A member's
  website links are indexed at weight B, name and url, exactly as the old
  `userprofile_text.txt` template had them, but they live in their own model, so
  adding or removing one never saves the profile whose document holds them. 549
  rows across 377 members. Verified live through the worker on the vendored
  `elsewhere` fork: adding a link reached the profile's `summary` and deleting
  it took the link back out.

**THE CONTENT-UPDATE SIGNALS: two are load-bearing, one is dead, and the dead
one found the gap above.** Brian asked whether the signals he had built for
Haystack should come out now or later. Checking who receives them:

- **`topic_content_update` / `post_content_update` are NOT search code and must
  stay.** `forums/latest.py:94` and `:324` have live `@receiver`s — the Redis
  "latest posts" datastore behind the RSS feeds, covered by
  `forums/tests/test_feeds_latest.py`. Search was only ever their *second*
  consumer.
- **`profile_content_update` is dead**: sent from `bio/models.py:140` and
  `bio/views.py:236`, received by nobody since Step 4 pruned `custom_search`.
  Step 4 removed the receiver and left the signal and both senders standing.
- **But `bio/views.py:236` sends it when a member edits their website links** —
  i.e. the dead signal was an accurate note that the profile's *indexed* content
  can change without the profile being saved. That is what prompted the
  `WebsiteProfile` handler. It was fixed with `post_save`/`post_delete` on the
  model rather than by connecting to the signal, because the signal fires from
  that one view only and would miss an admin edit.
- **Decision: `profile_content_update` and its two senders go in the
  end-of-Step-12 prune**, with the 6 `search_title()`, 8 `search_summary()` and
  8 `templates/search/indexes/*.txt` — one coherent "remove what the old search
  left behind" commit, once task 04 has settled what is actually dead. The
  `content_update` kwarg on `UserProfile.save()` stays regardless: it also gates
  `update_date`, the markup conversion and the avatar cache delete.

**CARRIED OUT TO STEP 21: pin the celery worker's concurrency explicitly.**
`docker-compose.yml` runs `celery -A sg101 worker -l info` with no
`--concurrency`, so the prefork pool defaults to the host's CPU count — one
worker node, **10 child processes** on the dev Mac today (verified via `celery
inspect stats`), and whatever the deploy VM has tomorrow. That number was never
chosen by anyone, and it is the number that decides whether two tasks for the
same object can run at once — the thing `indexed_at`'s guard defends against. It
is not a throughput question at 134 posts a month. Recorded in `plan.md`'s Step
21 section too. **Brian asked to revisit this at deploy time, 2026-07-30.**

**KNOWN GAP, deliberate: moving a `Forum` between categories does not reindex.**
It is the same privacy boundary, but detecting it needs the old category, and a
`pre_save` probe would cost a query on **every** forum save — and `forums/
receivers.py` saves the forum on every post. The remedy is
`reindex_search --model forums.topic --model forums.post` after an admin moves a
forum. **Owner decision, Brian 2026-07-30: accepted — moving a forum between
categories is "very very rare" and he will run the reindex by hand.** So this
is settled, not a deferred item; nothing downstream needs to pick it up. Also unhandled:
`m2m_changed` with `action='post_clear'` from the *group* side, where Django has
already forgotten which categories were attached; nothing in the admin clears
from that side.

**Task 02's batching is now shared, not duplicated** (requirement 5): `batched`,
`index_batch`, `index_queryset` and `discard_stale` moved out of the management
command into **`search/indexer.py`**, which the command and `reindex_category`
both call. `discard_stale` grew a `scope` argument so a caller working on one
category does not sweep the whole type.

**One test outside the search app needed changing:** `bio/tests/test_receivers.py`
sends `post_save` by hand with `namedtuple` stand-ins that have no `pk`, to
exercise bio's badge handlers. It already disconnected three other apps'
receivers by `dispatch_uid` for the same reason; it now disconnects
`search.receivers` for `Link`, `Download` and `Story` too.

### Task 02 — the reindex command and the backfill — DONE (2026-07-29)

**`manage.py reindex_search` exists and the index is populated: 518,595
documents, built in 1m17s.** 17 new tests, 635 green, `check` and
`makemigrations --check` clean.

**The backfill, measured against the converted snapshot:**

| Document | Rows | Build | Rebuild |
|---|---|---|---|
| `forums.post` | 444,134 | 1:04 | 3:53 |
| `forums.topic` | 35,206 | 0:03 | 0:15 |
| `ygroup.post` | 21,032 | 0:06 | 0:14 |
| `bio.userprofile` | 15,227 | 0:02 | 0:07 |
| `news.story` | 1,694 | 0:01 | 0:01 |
| `downloads.download` | 716 | <1s | <1s |
| `weblinks.link` | 571 | <1s | <1s |
| `podcast.item` | 15 | <1s | <1s |
| **Total** | **518,595** | **1:17** | **4:32** |

Counts match the source tables exactly, less private content: 35,693 − 487
topics and 463,222 − 19,088 posts. The search table is **881 MB** with its GIN
index, against a 544 MB database — the doubling task 01 predicted, now measured.

**The corpus is 518,595, not the ~490k every planning document says.** The
estimate omitted the Yahoo Group archive (21,032) and rounded the rest down. No
consequence beyond the number itself; task 07 should compare against 518,595.

**A rebuild costs 3.5× a build (4:32 vs 1:17), and that is the update path, not
the CASE statement.** Re-running writes the same values to rows that already
exist: every row is rewritten and every GIN entry churned, where the first run
inserted into an index that started empty. It only shows up on `forums.post`
(1:04 → 3:53), the one type whose rows carry large `summary` text. Left alone —
this is a maintenance command run when the weights change or the worker was
down, and five minutes is not a number worth optimizing against.

**Private-category exclusion lives in the registry's querysets, not in the
command.** `TopicDocument`/`PostDocument.get_queryset()` filter on
`category__groups__isnull=True`, which makes "the objects to index" one
definition that the bulk path, the stale-row pass and (next) task 03's
per-object check all read from. The payoff is that a category *becoming*
private needs no special handling: its topics and posts simply leave the
queryset, and the end-of-type sweep deletes rows the queryset no longer yields.
Verified against `Kahunas` in the real data by SQL join, not by row count —
zero index rows reference any of its 487 topics or 19,088 posts.

**`iterator()` silently drops `prefetch_related` on Django 3.2** (the support
landed in 4.1), which would have turned `bio.UserProfile`'s
`user__website_profiles` into a query per row over 15,227 profiles — invisible,
since the results would still be correct. Documents now declare
`prefetch = (...)` and the command applies it per batch with
`prefetch_related_objects()`, so both the batched path and the single-object
path prefetch properly.

**Shape of the command:** `--model app.model` (repeatable) for a selective
rebuild, `--batch-size` (default 1000), one transaction per batch, four queries
per batch regardless of batch contents — read the existing rows, `bulk_create`,
`bulk_update`, then one `UPDATE` that builds the vectors server-side from the
columns just written. Rows are matched by `(content_type, object_id)` and
updated in place, so a run is safe to repeat; a re-run of the full snapshot left
the row count at 518,595 with no duplicates. A full run also drops rows whose
content type is no longer registered. `order_by()` clears the model's `Meta`
ordering — a sweep does not care what order it walks the table in, and sorting
444k rows to ignore the result is pure cost.

### Task 01 — the search app, the document model, and the registry — DONE (2026-07-28)

**25 new tests, 618 green, `check` and `makemigrations --check` clean.** `django.contrib.postgres` and `search` added to `INSTALLED_APPS`.

**The design decision this task settled: the vector is built from the row's own
columns.** `title` (A), `summary` (B) and `author` (C) hold the text to be
indexed, and `search_vector` is a function of the three. The alternative —
keeping `search_title()`/`search_summary()` for display and passing the index
text in from Python as `Value()` literals — was walked through with Brian in
detail and rejected on "keep it standard and simple" grounds: **column-derived is
the pattern in the Django FTS docs**, and the literals variant is the unusual one.
Notably, the argument I had led with (a weight or config retune becomes one
`UPDATE`) **Brian discounted** — he does not expect to retune weights or leave
`'english'` — which was correct, and it left the idiom argument carrying the
decision on its own. Cost: one column beyond the design doc's table, `author`.

**Consequences, all accepted and recorded in `search-design.md` §3:**
- `search_title`/`search_summary` go unused except on `bio.UserProfile`. They do
  not survive weighting — `forums.Topic`/`Post` embed the username *and* a
  formatted date in their titles, which would put the author at A instead of C
  and make `2020` match half the forum at top weight.
- Result lines get composed by task 04's template from `title` + `author` +
  `date`, uniformly across the eight types. A forum topic loses "; 3 posts";
  news, links, downloads and podcasts gain a visible author. **Brian explicitly
  did not want byte-identical parity with the Xapian result lines.**
- Defining `summary` as *what should be indexed* closed three parity gaps
  `search_summary()` had: `news` regains `tags`, `weblinks` regains `url`, `bio`
  sheds the username/full name that belong at A — which also dissolves the
  "display summary is the index blob" gotcha the task file flagged.

**Found while building, all verified against the converted production data:**
- **Body text is often rendered HTML, so it gets stripped on the way in.** All
  1,694 news stories store HTML in `short_text`/`long_text` — and 989 of them are
  version 0, with no markup source to index instead. 8,392 of 21,032 Yahoo Group
  posts likewise, plus ~1,100 forum posts. Since this text is both indexed and
  snippet source, tags would otherwise show up in both places.
- **Django emits a redundant btree on `content_type_id`**, duplicating the unique
  constraint's leading column. `db_index=False` on the FK; two indexes on the
  table, the GIN and the unique.
- **Nothing indexes `date`.** `ORDER BY rank, -date` sorts on a computed
  expression first, so the sort runs over the matched set regardless.
- **`title` must be a `TextField`.** A profile's is `"username (Full Name)"`,
  which can reach 453 chars, and overflowing a varchar is a `DataError` on
  PostgreSQL rather than the silent truncation MySQL used to do.
- **`bio.UserProfile` has no natural date**; `user.date_joined` is used — stable
  and meaning "member since", where `update_date` would let the most recently
  edited profile win every relevance tie.
- **`ygroup.Post.poster` is now indexed** at weight C. The old index ignored it;
  it costs nothing on a frozen archive and gives those posts an author.

**Storage measured and accepted (Brian asked whether the table duplicates data —
it does).** ~196 MB of source text copied into `summary`, a tsvector at ~110% of
the text it covers, plus a GIN index, against a 544 MB database: the search table
roughly doubles it. **Kept as built, revisit only if it becomes a problem.** The
proportion is the point — the vector and GIN are unavoidable in any Postgres FTS
design, and **Xapian already held the same text copy**, on local disk outside
MySQL, which is the persistent-disk hosting constraint this step dissolves. The
one place this goes further than Haystack is storing title/url/date, which Haystack
refetched per result (`result.object` at `search.html:91`); that is what buys a
single-query results page. Escape hatch if it ever matters: drop `summary`, fetch
result objects for snippets and highlight in Python, Haystack-style — which also
puts the weight-B text back to `Value()` literals. Full numbers in
`search-design.md` §5.

**Pending cleanup, deferred to the end of Step 12** (Brian spotted the dead code
during task 01): the models' now-unused search-display methods. **Not done yet
because task 04 rewrites `search.html` / `search_ajax.html`, which are what still
reference them** — `result.object.search_title` at `search.html:91` and
`search_ajax.html:7`, `search_summary` at `search.html:94` — so until it lands the
true dead set is a guess. The sweep is 6 `search_title()` + 8 `search_summary()`
+ the 8 recovered index templates under `sg101/templates/search/indexes/` (whose
only remaining caller is `bio.UserProfile.search_summary()`; the other seven are
already unreferenced), as one commit, once `documents.py` is unambiguously the
authority on what gets indexed. **Two must survive it:**
`bio.UserProfile.search_title()`, used by the registry, and
**`podcast.Item.search_title()`, which is not search code at all** — it feeds the
social-sharing tag at `templates/podcast/detail.html:79`, and a naive sweep would
break the podcast detail page.

Task 01 also supplies `SearchDocument.objects.index_object(obj)` — one
`update_or_create` for the values, one `UPDATE` for the vector. The task said to
write no rows *automatically*, but acceptance criterion 6 needs idempotent
reindexing demonstrable now, and tasks 02 (batching) and 03 (Celery) should wrap
one implementation rather than each growing their own.

**Next:** task 03, Celery incremental indexing and the privacy boundary on write.

## EXECUTION — Step 11 (MySQL → PostgreSQL) — **DONE** (2026-07-24 → 2026-07-26)

**All six tasks complete.** SG101 runs on PostgreSQL 16: the site, the converted
production data, the test suite, and CI. MySQL remains in the Compose file
behind a profile, as the source the cutover conversion reads from.

**Task order changed:** 04 ran before 02 and 03. Task 01 found that nothing can
create a fresh database on Postgres until every app has migrations (below), so
04 is a prerequisite, not a successor. Its own spec expected the converted
database from 03 to diff against; the real production schema in MySQL is what
pgloader will convert, so the audit was done there instead and got re-verified
against the converted tables at 03/05.

### Task 06 — CI on Postgres + the test-database decision — DONE (2026-07-26)

**The suite runs on PostgreSQL from here on, everywhere, and the sqlite path is
gone.** This was the question Step 11 deliberately deferred until there was real
data, so it was measured first, on 593 tests, in-container, on one machine:

| | Django-reported | wall clock |
|---|---|---|
| sqlite (cold) | 5.17–5.22 s | 7.21–7.27 s |
| PostgreSQL (cold) | ~6.9 s | 9.11–9.17 s |
| PostgreSQL (`--keepdb`) | 6.82 s | 8.30–8.33 s |

**The whole price is ~1.9 s on a 7-second suite (+27%)** — much less than the
plan assumed when it proposed keeping sqlite for local runs. Two details worth
recording: `--keepdb` does nothing for sqlite (its test database is in-memory
already), and it saves Postgres only ~0.85 s, so building the schema from 26
apps' migrations is nearly free. Task 01's earlier figures (4.93 s / 6.30 s) were
567 tests and timed Postgres with `--keepdb`, which flattered it; these are
cold-to-cold and comparable.

Against those two seconds: Step 12 is Postgres full-text search — `SearchVector`,
GIN, `SearchQuery`, `SearchRank` — **none of which exist on sqlite**, so a split
policy would have left the entire search implementation untestable locally and
its tests needing `skipUnless` guards to keep a sqlite run green. And task 04
established that schema drift between build paths is a live risk in this
codebase, precisely the class of bug a sqlite suite cannot see. One engine, one
schema, from the developer's terminal through to CI.

**No test needed changing.** The suite was already engine-portable: no
`connection.vendor` branches, no `skipUnless`, nothing engine-specific — task 01
had already flushed out the sqlite-shaped assumptions (predictable pks, courtesy
of rowids that roll back where Postgres sequences do not).

- `docker_test.py` now **is** the Postgres test settings; `docker_test_pg.py` is
  deleted rather than kept as an alias, so there is only one name to type.
- `test.py` no longer names a database, matching `base.py` — the module that runs
  the tests picks the engine, which is what `databases.py` was built for. Its
  sqlite `legacy_alter_table` shim went too: it existed for Django 1.9's schema
  editor and has been dead since Step 10.

**CI runs the identical command against the Compose `postgres` service**, not a
GitHub-hosted service container, keeping the parity the workflow was built on.
`docker compose run --rm web` starts `postgres` and waits on its healthcheck via
`depends_on`. Coverage measurement and artifact upload are unchanged: 593 tests,
5 skipped, **85% coverage**.

**One real snag, caught locally rather than in CI:** a leftover test database
makes Django *prompt* before dropping it, and a prompt with no terminal is an
`EOFError`, not a wait — the run dies before a single test executes. CI now
passes `--noinput`. A fresh CI checkout would not have hit it; a re-run against a
warm volume, or any developer who had once used `--keepdb`, would.

**Compose defaults to Postgres, and MySQL moved behind a `mysql` profile.** The
`db` service is *kept* — the cutover converts a fresh production snapshot the
same way, and that procedure needs a MySQL source, so it cannot go until then —
but it no longer starts with the stack, and `web`/`worker` no longer `depends_on`
it. Leaving that dependency in place would have dragged an amd64-emulated MySQL
into every `up` and made the app block on the healthcheck of a database it no
longer uses (and CI wait for it on every run). `docker compose up` is five
services on Postgres; `docker compose --profile mysql up` is the conversion
stack. `.env.example` ships `DB_ENGINE=postgresql`.

**A profile filters `down` as well as `up`, which is the one sharp edge.** Found
by noticing the `db` container had been up 8 days *through* a `docker compose
down` — and that the same `down` had reported "Network sg101_default Resource is
still in use", which was this, unread at the time. A plain `docker compose down
-v` removes `postgres_data`, leaves `db_data` and a running MySQL container, and
then cannot remove the network; `docker compose --profile mysql down -v` takes
everything. DOCKER.md's command table and §6 both say so now. CI is unaffected,
since `db` never starts there, but the documented "stop and wipe the DB" would
have half-worked on a developer's machine.

**Pushed as `cf334b7`; CI green on GitHub 2026-07-26** — the first CI run on
Postgres, which is what acceptance criterion 1 actually asked for. **It came in
*faster* than the sqlite run before it: 1m57s against 2m18s for `3114b4f`.**
Losing the `depends_on: db` wait for MySQL 5.7 to go healthy more than paid for
the suite's extra 1.9s. Single runs either side, so an observation rather than a
benchmark, but it settles any worry that the engine change slowed CI down.

**Verified on this machine:** fresh `docker compose up` → 5 services, no MySQL,
Django resolving `django.db.backends.postgresql` with no `DB_ENGINE` set
anywhere; site serves the converted snapshot (463,221 posts, 35,692 topics,
15,227 users; home and forums 200); `check` and `makemigrations --check` clean;
593 tests green through the exact CI invocation.

**DOCKER.md rewritten** for the new default: five services, the schema-creation
and snapshot paths, the test command with the policy and its cost stated, a new
§6 on MySQL and engine switching, the `--profile mysql` requirement threaded
through the §7 conversion procedure, and a `no such service: db` troubleshooting
entry for the profile's one sharp edge.

**Also corrected at close-out:** `detailed-design.md` and `database-migration.md`
both still recommended `CITEXT`, which task 02's deprecation finding superseded
(deprecated in Django 4.2, removed in 5.1 — Steps 13/14 walk into it). Both now
point at the `__iexact` + functional-index approach that actually landed.

#### Carried forward out of Step 11

Nothing here was forgotten; each has a destination.

- **`elsewhere`: real migrations + data-migration seeding, and `network_id` →
  FK → Step 19.** Task 04 gave the app an initial migration like the other 20,
  which is all Postgres required. The deeper rework — seeding the network tables
  from a data migration instead of the `post_migrate` hook, and making
  `network_id` a real foreign key — is app modernization, not an engine switch,
  and the plan's "Step 11 or 19" is hereby settled as **19**.
- **The 7 model-less legacy tables → Step 19** (`auth_message`,
  `core_anonlastvisit`, `core_userlastvisit`, `gcalendar_accesstoken`,
  `irc_ircchannel`, `mailer_message`, `membermap_mapentry`, ~1,540 rows). They
  came across deliberately: conversion is not the place to prune.
- **The 12 duplicate-email account pairs → Step 19** (data hygiene; note the trap
  that a naive uniqueness check locks those 26 members out of profile edits).
- **`bio_tags.flag_icon` leaves `name` unbound on an unrecognised country code**
  — a latent crash on either engine, masked because `''` is falsy. Not scheduled;
  fix when someone is next in that file.
- **`forums_topic_subscribers(topic_id)`** is redundant with the leading column
  of the composite unique index. Cosmetic; no destination.
- **`AGENTS.md` at the repo root is badly stale** (Python 2, Django 1.8,
  Mercurial, `custom_search`) → Step 19, or sooner if it starts misleading
  someone.
- **Resolved by the engine switch, needing no further work:** the environmental
  `mysql.W002` strict-mode warning is simply gone.

### Task 05 — data integrity verification — DONE (2026-07-25)

The conversion is now verified rather than merely run, and **four defects that
would have shipped were found by doing it** — all invisible to row counts, to
the column-level schema diff, and to the test suite.

**1. Every datetime in the database was 5–6 hours early.** MySQL `datetime`
carries no offset and, with `USE_TZ` off, Django wrote local wall-clock time
into it. Django maps `DateTimeField` to `timestamptz` on PostgreSQL, so every
value has to be placed on the timeline as it loads, using the session
timezone — which was the server default, UTC. Django then read them back in
`America/Chicago`. The same ORM query returned `2006-02-26 19:24:30` on MySQL
and `13:24:30` on Postgres, for all 1.25 million datetime values. The stored
values really are local time and this is not an assumption: **the 02:00 hour
is empty on every DST spring-forward day across twenty years of posts**, the
gap only local time has. `convert.sh` now sets the timezone on the target
database before loading and reads it from Django so the two cannot drift.

**2. All 91 foreign keys were `RESTRICT`, where Django builds `NO ACTION
DEFERRABLE INITIALLY DEFERRED`.** Django's ORM performs cascades in Python and
lets its deletion collector remove rows in whatever order suits it, leaving
the database to confirm consistency once, at commit. pgloader carried InnoDB's
semantics across instead. RESTRICT is checked immediately and **cannot be
deferred** — deferring them first was tried and changed nothing, which is what
pointed at the action rather than the timing. Ordinary operations therefore
failed against the converted database while working against a migrated one:
**deleting a forum topic was enough**, because the topic's own `last_post`
points at a post being removed in the same transaction. `post_convert.py` now
drops and recreates all 91 with Django's semantics.

**3 and 4, found by asking the question generally.** The foreign keys were
caught by chasing a specific failure, which prompted the obvious follow-up:
where *else* does pgloader produce a faithful conversion of MySQL rather than
the schema Django would have built? Two more. **Every `CHECK` constraint was
missing** — `PositiveIntegerField` and `PositiveSmallIntegerField` are plain
integers plus a `>= 0` check on PostgreSQL, where MySQL said UNSIGNED, which
has no equivalent to carry across; the converted database accepted a negative
`tagging_taggeditem.object_id` and now rejects it. And **two columns kept a
`DEFAULT 0`** from MySQL, where Django applies field defaults in Python and
leaves the database with none. Both are repaired in `post_convert.py`, derived
from Django's own field definitions rather than hardcoded.

**That question is now a tool.** `compare_schema.py` diffs the converted
schema against one the migrations build, across columns, indexes,
constraints, foreign keys — action and deferrability included — defaults and
sequence ownership. Names are deliberately excluded: pgloader's
`idx_393735_username` against Django's
`forums_topic_last_post_id_ed000e17_fk` would bury everything that matters.
It reports **522 columns, 88 foreign keys and 0 unowned sequences matching**,
with two differences understood: the redundant
`forums_topic_subscribers(topic_id)` index, and 25 uniqueness rules Django
declares as `UNIQUE` constraints that pgloader created as unique indexes —
which PostgreSQL enforces identically and Django finds by introspection, so
the tool reconciles them by columns rather than accepting them by name. It was
tested by breaking the database on purpose — one foreign key back to RESTRICT,
one CHECK dropped, one default restored — and it named all three and exited 1.

**Everything else matches.** 91 tables, 699,435 rows, exact counts;
`forums_post` 463,221, `forums_topic` 35,692, `auth_user` 15,227, `news_story`
1,694. Column by column: **543 columns, 5.7M values**, checksummed on both
engines with datetimes compared as the application sees them and NULL held
distinct from `''`. 91 foreign keys valid, **zero orphaned rows**, enforcement
proved by a rejected insert rather than read off the catalog. Twelve models
dumped through Django's serializer on both engines are byte-identical. Beyond
columns, the converted schema was compared to a migrations-built one for
uniqueness and nullability too: the only differences are the 7 legacy
model-less tables and the single known `forums_topic_subscribers(topic_id)`
index.

**Four differences from the source are expected, and each is pinned to a row
count** so corruption arriving alongside one still fails: `auth_permission` and
`django_migrations` grow when migrations are applied; `auth_user.email` differs
in exactly 1 row (`accounts.0003` folding the case-variant address);
`forums_post.user_ip` in exactly 370 (`''` → NULL, since `inet` has no empty
value).

**Live smoke: 35 checks, reads and writes.** The full checklist plus the pages
this conversion put at risk — a profile with no country set, the cp1252 band
name (`The Chi-Tones™`) coming back out of the map endpoint. Writes go through
the running server: a forum topic, a private message and a photo were created,
checked to display, and removed again. Both password flows work. **The Celery
worker and beat ran all five scheduled tasks clean against the converted
database**, and beat dispatched `max_users` on its own schedule, which the
worker executed 23ms later; the private message raised a real `send_mail` task
organically.

**AC 6 is met in substance, not as written.** It asks for the suite green
against the converted production database. The suite is written against an
empty one, and 566 tests run with 27 failures and 98 errors there — every one
of them a fixture colliding with real data: 89 unique-constraint violations
(the fixtures create a user named `Gremmie`, who exists), 27 assertions about
global counts (`potd` expects 3 photos and finds 575), and 9 slug collisions.
**Zero engine-level errors** — no `DataError`, no encoding or interface
trouble — which is the finding that matters. The pass/fail gate stays the
clean-schema run: **593 green on Postgres and on sqlite**, `check` and
`makemigrations --check` clean. The stale "567 tests" in the task's AC 6
predates task 02.

**Repeatable end to end.** After the scheduled tasks mutated data, the whole
pipeline was re-run from the pristine MySQL snapshot — convert, verify,
post_convert, verify_data, crosscheck, smoke — and every check passed again.
`smoke.py` recovers from a previous run that died part way through, which was
tested by planting the wreckage: an orphaned topic plus a reply that had become
both its topic's and its forum's `last_post`. It repointed both, removed the
content and put `forums_forum.surf-music` back to 6,685 topics / 98,449 posts
and its original `last_post` — the source values exactly.

**Order matters: verify before smoking.** Using the site writes sessions and
raises topic view counters, so a comparison against the untouched MySQL source
has to happen before anything browses. DOCKER.md §7 numbers the steps
accordingly.

**Artifacts:** `tools/pgloader/{verify_data.py,compare_schema.py,
crosscheck_dumpdata.sh,smoke.py}`, additions to
`verify.py`/`convert.sh`/`post_convert.py`, procedure in DOCKER.md §7.

**Also fixed:** `verify.py` reported nonsense non-ASCII tallies. MySQL 5.7's
`REGEXP` has no `\x` escape, so `[^\x00-\x7F]` is a class of literal
backslash/x/digits that matches ordinary ASCII — and only on the latin1
columns, the ones the check exists for. It claimed 931 non-ASCII values in
`bandmap_bandentry.name` where there are 23. Now measured by byte length. The
md5 comparison that decides pass/fail was never affected.

**Watch items, neither caused by the conversion:**

- **`Forum.last_post` and `Topic.last_post` are `OneToOneField(..., on_delete=
  CASCADE)` pointing at `Post`.** Deleting the post a forum happens to point
  at takes the forum — and every topic and post inside it — with it. Deleting
  one scratch account proposed to cascade to **6,686 topics and 98,450
  posts**. The app has carried `last_post_pre_delete()` for years to step
  around this, so its own paths are safe, but a plain `User.delete()` from the
  admin is not. Pre-existing, and worth a real fix when the forums app is next
  open.
- **Index names are pgloader's (`idx_393735_username`), not Django's.** Django
  resolves indexes by introspection, so this works, but a migration written
  against a name would not.

### Task 03 — pgloader snapshot conversion — DONE (2026-07-25)

The production snapshot now runs on PostgreSQL. **699,435 rows across 91
tables, zero rejections**, exact row-count match on every table, and the
converted schema differs from one Django's own migrations build by **zero
columns** (522 compared). Repeatable from empty: the wrapper drops and
recreates the target every run, and it was run start-to-finish five times.

**Converted from the *pristine* dump, not the working database.** Brian still
had `sg10120260712.sql.bz2` (it was in the frozen hg backup, not the git
repo). It is loaded as a separate `sg101_pristine` database alongside the
working one, so MySQL is only ever read — verified afterwards: 15,227 users,
`first_name` still `varchar(30)`, 29 migration rows, untouched. That choice
matters: the working database already had task 02's migrations applied, so
converting it would have skipped the very steps requirements 9 and 10 ask to
prove.

**The snapshot is Django 1.8-era, not 1.9.** Brian pointed out that he had
bumped the repo to 1.9 himself but production still runs 1.8, and the data
agrees: the dump has `auth` at `0006` and `sites` at `0001`, and it was 1.9
that added `auth.0007` and `sites.0002`. Cutover will start from this same
state, so this is a true rehearsal rather than a data copy.

**Four findings, three of which would have shipped silently.**

1. **MySQL's `latin1` is cp1252, not ISO-8859-1.** Declaring `AS latin1` — the
   obvious reading of the task — corrupted 8 of 1,066 `bandmap_bandentry`
   rows: bytes `0x92`/`0x93`/`0x94`/`0x99` are printable in Windows-1252
   (`’ “ ” ™`) but C1 controls in the ISO standard, and pgloader's `LATIN-1`
   is the strict standard. Only rows using smart quotes were affected, which
   is exactly how this goes unnoticed. Now `AS cp1252`, and `verify.py`
   compares **all 84,279 text values** in those tables by md5 against MySQL's
   own decoding so it cannot recur.
2. **`int(11)` arrives as `bigint`.** MySQL reports precision 10 and
   pgloader's default sends >= 10 to bigint, so **204 columns including every
   primary key** were 64-bit where the migrations build them 32-bit — against
   Step 10's deliberate `DEFAULT_AUTO_FIELD = AutoField`. Explicit CAST rules
   fix it; safe because no int value anywhere exceeds 2,147,483,647.
3. **`char(2)` is a live bug on Postgres, not vintage drift.**
   `bio_userprofile.country` is `char(2)` in production where models.py says
   `varchar`. The schema diff flagged it and it was nearly written off —
   **the live smoke test is what caught it**. MySQL strips trailing spaces
   reading CHAR, so an unset country returns `''`; PostgreSQL pads and returns
   `'  '`, which is **truthy**, so templates guarding on `{% if
   profile.country %}` call `flag_icon('  ')` and raise `UnboundLocalError`.
   **12,854 of 15,227 profiles have no country set** — every one of those
   pages 500'd until the column was cast to `varchar`.
4. **Requirement 9's prescribed mechanism does not work.** The task says to
   widen the three `varchar(75)` email columns with an `AlterField`
   re-asserting the field. Both migrations reported `OK` and **changed
   nothing**: task 04 generated `0001_initial` from the models, so it already
   declares 254, and it was applied with `--fake-initial` against tables that
   are really 75 — Django believes they are already wide and emits no SQL.
   `accounts/0004` and `podcast/0002` now correct the recorded state to 75 via
   `SeparateDatabaseAndState` (no database operation) and *then* widen, which
   Django can see. Caught by checking the columns rather than trusting `OK`.

**Also resolved:** the 4 IP columns become `inet` to match
`GenericIPAddressField`; 370 empty strings in `forums_post.user_ip` become
NULL (Brian's call — 636 rows were already NULL, so 1,006 total, exactly as
predicted). The 22 `varchar_pattern_ops` indexes Django creates for prefix
matching are missing after `--fake-initial` and pgloader has nothing to copy
them from, so they are generated into `tools/pgloader/pattern_ops_indexes.sql`
and applied post-conversion — without them `username__istartswith` over 15,227
users is a sequential scan, since a plain btree cannot serve `LIKE 'prefix%'`
under `en_US.utf8`.

**Requirements 9 and 10 verified on real data:** all three email columns now
254, `auth_user.first_name` 150, and the task 02 migrations exercised properly
— `accounts/0002` built the functional unique index across 15,227 usernames on
Postgres, and `accounts/0003` folded the real `Joey`/`SurfBeat` collision.

**AC 4 (zero dates) is not applicable and that is a finding, not a skip.** All
79 date/datetime/timestamp columns were probed two ways — a range comparison
and a cast-to-text pattern match — and the database contains no `0000-00-00`
value. The permissive `sql_mode=''` in compose is needed to *load* the dump,
but the data is clean.

**Remaining differences from a migrations-built schema, both explained:** the
7 model-less legacy tables (`auth_message`, `core_anonlastvisit`,
`core_userlastvisit`, `gcalendar_accesstoken`, `irc_ircchannel`,
`mailer_message`, `membermap_mapentry`, ~1,540 rows) come across by Brian's
decision — conversion is not the place to prune, Step 19 is. And one index,
`forums_topic_subscribers(topic_id)`, which is served by the leading column of
the composite unique index that is present.

**Live smoke on the converted data:** home, forums index, a real topic, news,
podcast, links, downloads, bandmap, search, calendar, a profile, and
specifically a profile with no country set — all 200. The cp1252 band name
renders as `Chi-Tones™`. Suite still 593 green on sqlite and Postgres;
`check` and `makemigrations --check` clean.

**Artifacts:** `tools/pgloader/{sg101.load,convert.sh,verify.py,post_convert.py,
pattern_ops_indexes.sql}`, procedure in DOCKER.md §7.

**Watch item for later:** `bio.templatetags.bio_tags.flag_icon` leaves `name`
unbound on any unrecognised country code — a latent crash on either engine,
not caused by the conversion, currently masked because `''` is falsy. Worth a
fix when someone is next in that file.

### Task 02 — case-insensitive lookup parity — DONE (2026-07-25)

**593 tests green (was 567) on sqlite and on Postgres**; `check` and
`makemigrations --check` clean; both migrations applied to the real MySQL
snapshot and verified row by row; live smoke on real data.

**The audit found 14 collation-dependent lookups that matter, not 8.** Method:
AST scan, not grep (the Step 9 lesson). Two refinements mattered — template-tag
`register.filter(name=...)` calls are not ORM calls, and **`get_object_or_404`
is a plain function, not an attribute call, so the first pass missed it
entirely**. That is where four of the real findings live. Full audit in
`research/collation-audit.md`.

Beyond the eight sites the task named: `messages/forms.py:47` (PM to a
hand-typed recipient), `accounts/views.py:109` (registration confirmation),
`donations/views.py:183` (PayPal donation → user linking), and three
URL-driven username lookups — `bio/views.py:83`, `forums/views/main.py:918`,
`user_photos/views.py:142`. **7,006 of 15,227 usernames carry uppercase**, so
those URLs are case-bearing in practice; a mis-cased profile bookmark resolves
today and would have started 404ing. Plus `news/views.py:184`, the tag lookup.

**Two corrections to the task file's framing.**

1. `accounts/forms.py:243` is **`ForgotUsernameForm`, not password reset**.
   Django's own `PasswordResetForm.get_users()` already uses `email__iexact`,
   so password reset was engine-independent all along — pinned with a test
   rather than fixed.
2. **The "13 email case-collision groups" are almost all not case collisions.**
   `GROUP BY email` on a `*_ci` column groups case-insensitively — the very
   trap this task is about, and it produced a wrong first answer here. Forcing
   `BINARY`: **12 groups are byte-identical duplicates** (two accounts holding
   the same address, e.g. `Drippy`/`Hydronaught`), which exist today on MySQL,
   are untouched by the engine change, and would defeat a *plain* unique index
   just as surely as a case-insensitive one. **Exactly one group is a true case
   variant** — `SurfBeat` (inactive, id 2373) vs `Joey` (active, id 2947) on
   `eight_til_midnight@{y,Y}ahoo.com`.

**Live bug found and fixed:** `ForgotUsernameForm` called `.get(email=...)`
with no `MultipleObjectsReturned` handler, so all 13 groups got a 500 and could
never recover a username — **today, on MySQL**. Not caused by the engine move
and not fixed by it; fixed here because it is the same line.

**Decisions (Brian, 2026-07-25):** no unique index on email (the data cannot
satisfy one in either direction) but normalize the single genuine case variant;
fix the forgot-username bug here; add the functional unique index on
`LOWER(username)`; convert the tag and URL-username lookups too.

**Shipped:** 12 lookups → `__iexact` across 9 files, plus two migrations in
`accounts`. `0002` creates `CREATE UNIQUE INDEX ... ON auth_user
(LOWER(username))`. `UniqueConstraint(Lower(...))` is Django 4.0+ and
`auth_user` is not our model, so raw SQL in a `RunPython` is the only route on
3.2. **The guard skips MySQL, not "everything but Postgres"** — Postgres and
SQLite both support functional indexes, and MySQL needs none because its
collation already makes the column's existing `UNIQUE` case-insensitive. So the
index is exercised by the default sqlite suite as well as the Postgres one.
`0003` lowercases addresses that collide with another account only by case:
**exactly one row today**, verified on the snapshot (non-lowercase emails
1043 → 1042, 15,227 users unchanged, case-variant groups 1 → 0). It **groups
and compares in Python on purpose** — an `exclude(email=x)` would compare on
the very engine whose semantics are in question, and on MySQL would match the
case variants too and silently do nothing.

**`FORCE_LOWERCASE_TAGS` was already `True`** (`base.py:196`) — found late,
after an earlier grep for `TAGGING` missed it (the setting has no such prefix).
Tag *creation* was therefore already engine-independent, and that half of the
planned change was a no-op. Only the tag **lookup** needed `name__iexact`. The
1,006 all-lowercase tags are that setting's doing, not the collation's.

**Discrimination, and why it is better than the task assumed:** SQLite's `=` is
case-sensitive for ASCII, so every one of these tests fails without the fix on
**sqlite as well as Postgres**, and is vacuously green on MySQL. The fast
default suite catches a regression here, not just the Postgres job. RED was
verified on sqlite before any implementation landed — 17 failures, one per
changed site.

**Checked and clear** (recorded so nobody re-checks): `antispam.contains_spam`
matches in Python, not SQL, so the other abuse control was never at risk; no
`__contains`/`__startswith`/`__endswith` anywhere in application code; no raw
SQL or `.extra()`; admin `search_fields` generate `__icontains`. Deliberately
left case-sensitive: PayPal `txn_id`, md5 photo signatures, IP-to-IP
comparisons, the oembed URL cache (case-sensitivity is *more* correct there),
and every `slug=` lookup (all production slugs are lowercase).

**Pre-existing failure surfaced, not fixed — FOLDED INTO STEP 12** (Brian's
call, 2026-07-25; see that step in `implementation/plan.md`). On **MySQL** the
full suite has one failure,
`core.tests.test_views.AjaxUsersTestCase.test_happy_path`.
`core.views.ajax_users` has **no `ORDER BY`** and takes a `[:limit]` slice, so
its row order is undefined; sqlite and Postgres happen to return insertion
order and MySQL does not. Confirmed pre-existing by running the suite on
unmodified code (567 tests, same single failure). Unrelated to collations, and
**the engine move does not fix it** — the test asserts an order SQL guarantees
on no engine, and users typing a common prefix (`j` matches 884 active
accounts) get an arbitrary ten with no way to tell. Parked with Step 12 because
the autocomplete is search-adjacent; fix is `.order_by('username')` plus an
alphabetical assertion.

**Also noted for task 03:** the Postgres dev database still carries the
migration history from task 01, i.e. **before** the backfill — no `oembed` or
`accounts` records at all — so `makemigrations --check` against it raises
`InconsistentMigrationHistory`. Harmless (the suite builds its own database)
and moot once task 03 replaces that database with the converted one.

**Where the duplicate addresses came from** (asked during review, worth
recording). The registration form has always checked — the check dates to the
2009 initial import, and commit `892b847` (2012) reworked it from `.get()` to
`.filter().count()` precisely because `get()` raised `MultipleObjectsReturned`
once duplicates existed, the same defect just fixed in `ForgotUsernameForm`.
The duplicates arrived by two routes. **`date_joined` shows a clean bulk-import
boundary** — 4,170 accounts have a midnight (`00:00:00`) timestamp and stop at
2011-02-24; the 11,057 after 2011-02-25 have real times. That is the phpBB →
SG101 migration, and `legacy/management/commands/import_old_users.py`
(deleted in Step 4, readable at tag `pre-step-4-prune`) deduplicated on
**username only** — it never looked at the email, took `user_email` straight
from the CSV, and preserved the old `user_id` as the Django pk. **Seven of the
13 pairs have both accounts inside that imported set**, so they are inherited
from the old platform. The other six (4 both-post-import, 2 mixed) were created
while the Django check was live and must have gone through the profile-edit
gap below. Caveat: `date_joined` records when the *account* was created, not
when its *email* was set, and there is no audit trail — so "both imported" is
the most economical explanation, not proof.

**REVISIT — editing an email address is unverified and unchecked.** Recorded in
`implementation/plan.md` under **Step 16** (the email step, where the
confirm-link flow would naturally be built). `bio.forms.EditUserForm` has no
`clean_email` and `User.email` has no `unique=True`, so any member can point
`/profile/edit/` at an address already in use, or one they do not control, with
no confirmation. Not a takeover path, but it can publish someone else's address
(the profile page, member list, and every forum post render it when
`hide_email` is unticked), it damages the other account's recovery, and a typo
silently costs you your own password reset. Full detail and fix order in
plan.md; note the trap that a naive uniqueness check would lock the 26 existing
duplicate-pair members out of saving any profile edit.

**Carried forward:** the 12 duplicate-address account pairs are data hygiene
for Step 19. `detailed-design.md` and `database-migration.md` both still say
"add `CITEXT`" — superseded by the deprecation finding, correct at close-out.
`AGENTS.md` at the repo root is badly stale (Python 2, Django 1.8, Mercurial,
`custom_search`).

### Task 04 — backfill initial migrations for the 21 unmigrated apps — DONE

Initial migrations generated for all 21; **all 26 apps now have a `migrations/`
package** and nothing relies on `run-syncdb`. No bytes-literal regression (the
`c76f920` problem); no model changed.

**The audit found no structural drift** — full report in
`research/schema-drift-audit.md`. Method: build `sg101_frommigrations` from the
migrations on the *same* MySQL server and diff `information_schema` against the
production snapshot, avoiding hand-rolled cross-engine type mapping. Result:
**0 missing columns, 0 extra columns, foreign keys identical**. That is a
genuinely good outcome for fifteen years of hand-run `ALTER`s. The 75 column
differences are vintage, not drift: 69 are `datetime`→`datetime(6)` (MySQL 5.6+
microseconds — hits migrated apps and Django's own tables equally, and vanishes
on Postgres), 1 is `char(2)`/`varchar(2)` on `bio_userprofile.country`, 2 are
database-level defaults on `news_*.priority` that Django never emits. The 14
extra production indexes are all a redundant index on the leading column of a
composite unique index (old Django did that for FK columns on MySQL). **Two
items were escalated:**

1. **`varchar(75)` vs `varchar(254)` on 3 email columns** (`accounts_illegalemail
   .email`, `accounts_pendinguser.email`, `podcast_channel.owner_email`) — real
   drift. Django widened `EmailField` 75→254 in 1.8; `auth_user.email` got it
   via Django's own migration, these three never did because their apps had no
   migrations. Nothing at risk today (0/1/1 rows, longest 25 chars; longest
   address in the whole database is 47) but truncation is silent. **RESOLVED
   2026-07-24 — Brian: widen during the conversion.** pgloader copies the MySQL
   width, so it needs an explicit step; carried into task 03 as requirement 9,
   via a hand-written `AlterField` rather than a pgloader `CAST` rule (engine-
   agnostic, survives a re-run, leaves the reason in the migration history).
2. **`auth.0012_alter_user_first_name_max_length` is unapplied** on the
   production database (`first_name` still `varchar(30)`). Not drift and not from
   this task — it shipped with Django 3.2 and was missed in Step 10. Left pending
   deliberately so "faking changes nothing" stayed literally true. It's a real
   `ALTER` on 15,227 rows. **RESOLVED 2026-07-24 — Brian: apply it during the
   conversion**, via a plain `migrate` against the converted database (task 03
   requirement 10) — the same run that applies the email widening. That run is
   consistent only because the backfill preceded the conversion: MySQL's
   `django_migrations` now carries the 21 initials and the `oembed` record, so
   pgloader brings them across.

**Cutover gotcha, now in the runbook:** `forums/0001_initial` has declared
`('oembed', '__first__')` since 2015 — inert while oembed had no migrations, and
the moment oembed got one Django's `check_consistent_history` refused **every**
`migrate` command on the existing database (`InconsistentMigrationHistory`).
`--fake` can't fix it (the check runs first); the one-time unlock is
`MigrationRecorder(connection).record_applied('oembed', '0001_initial')`, safe
because oembed's tables were verified against the models first. Any database
carrying the old history needs the same step.

**Faking changed nothing, demonstrated not asserted:** column definitions
identical before/after (551 compared), indexes identical (261 compared), and
across all 91 tables **the only row-count change is `django_migrations` 40 → 61**
— exactly the 21 initials. Data intact (15,227 users / 463,221 posts / 35,692
topics).

**Both build paths agree:** on Postgres, a syncdb-built schema and a
migrations-built one are **identical** — 0 column differences, 0 index
differences. And a fresh Postgres database now builds from a **single plain
`migrate`**, so task 01's phase-ordering helper (`tools/create_pg_schema.py`) and
the clone-plus-`--keepdb` test-database dance are both **deleted**; the suite
creates its own test database normally now. 567 tests green on Postgres and on
sqlite.

**`makemigrations --check` finally means something** — it was silently covering
5 apps of 26. Verified clean project-wide and per-app, and **added to CI** as its
own step with a comment recording that its coverage is now whole-project.

### Task 01 — stand up PostgreSQL and run the suite against it — DONE

**Shipped:** `postgres:16` service in Compose (named volume, healthcheck, 5432 on
the host, `POSTGRES_INITDB_ARGS=--encoding=UTF8`, snapshot mount) running
*alongside* MySQL; `psycopg2==2.9.9` in both requirements files (verified as the
last release supporting Python 3.7 — 2.9.10 requires 3.8+) built from source via
`libpq-dev` in the Dockerfile; `sg101/settings/databases.py`, a small engine map
so no settings module hardcodes an engine; `DB_ENGINE` (`mysql` default |
`postgresql`) as the single switch, with host/port defaulting to the matching
Compose service; `sg101/settings/docker_test_pg.py`; `.env.example` and DOCKER.md
updated. **Version rationale:** PG 16 is what the target architecture names and
its support window (Nov 2028) covers every remaining Django rung (3.2 needs 9.6+,
5.2 needs 14+); it also has an arm64 image, so the MySQL emulation penalty is
gone.

**The finding that matters — schema creation cannot be done in one pass.**
`migrate --run-syncdb` runs its **syncdb phase first**, and Postgres (unlike
SQLite) requires an FK's target table to exist when the constraint is created.
The real dependency picture: **24 columns in the 21 unmigrated apps reference
`auth_user`** (so syncdb can't go first) and **`forums.0001_initial` references
`oembed_oembed`** (so the migrations can't go first). Not circular — oembed has
no FKs of its own — so ordered phases work, and `tools/create_pg_schema.py` does
it: detach elsewhere's `post_migrate` hook (it queries its own tables on every
migrate call), `migrate auth`, `migrate oembed --run-syncdb`, `migrate`,
`migrate --run-syncdb`, reattach + seed. 84 tables, reproducible from empty.

**Consequence for sequencing:** Django's test runner builds its test database
with a *single* `migrate --run-syncdb` call, so it hits the same wall — the suite
can only run on Postgres against a database cloned from the phased build
(`CREATE DATABASE test_sg101 TEMPLATE sg101` + `--keepdb`). **Backfilling
initial migrations for the 21 apps (task 04) is therefore a prerequisite for
anything that creates a fresh database — including the Postgres CI job (task
06) — not a successor to it.** Both workarounds (the script, the clone) delete
themselves once task 04 lands.

**Suite: 567 tests green on PostgreSQL** (5 skipped), and still green on sqlite.
**8 tests had to change, all one root cause:** they relied on SQLite reusing
rowids after a rollback, which made PKs predictable (`pk=1`, or `user.pk` ==
`profile.pk`); Postgres sequences don't roll back, so the assumed ids were wrong.
Fixed by using the real ids — `bandmap` (`get(pk=1)` → `first()`), `donations`
×2 (→ `get()`, the idiom already used elsewhere in that file), `forums`
(hardcoded topic/post ids 1–3 → the created objects' pks), `polls` ×2 (voted for
`choices: 1`), `bio` (passed a **User** pk where the view takes a **UserProfile**
pk — they only ever matched by coincidence), `comments` ×3. No app code changed.

**Watch-item handed to tasks 03/05:** the `comments` failures traced to
`potd.CurrentManager`/`SequenceManager` fetching their singleton row with
`get(pk=1)`. Production holds exactly one row in each of `potd_current` and
`potd_sequence`, both with `id = 1`, so the conversion **must preserve those
ids** or the POTD stops working. The test now pins `Current(pk=1, ...)`.

**Table diff vs. the MySQL snapshot:** 84 (PG) vs 91 (MySQL). All 84 match; the
7 MySQL-only tables are dead legacy with no models left — `auth_message`
(Django ≤1.3), `core_anonlastvisit`, `core_userlastvisit`, `gcalendar_accesstoken`
(returns when gcalendar is revived), `irc_ircchannel`, `mailer_message`
(django-mailer), `membermap_mapentry`.

**Measurement for task 06 (no policy decided here):** 567 tests — **sqlite
4.93–4.96 s**, **Postgres 6.30–6.59 s** (≈ +30 %), both in-container on the same
machine, Postgres timed with `--keepdb` (so DB creation is excluded on that
side). Stable across repeat runs on a reused test database.

**Also verified:** MySQL path untouched (site serves the snapshot — 463,221
forum posts, pages 200), `check` clean on both engines, `makemigrations --check`
clean, and the site renders on Postgres against the empty schema.

**Not committed yet.** Remaining Step 11 tasks: 02 (case-insensitive lookup
parity), 03 (pgloader conversion), 04 (backfill migrations — see resequencing
above), 05 (data-integrity verification), 06 (CI + test-DB policy).

## INTERLUDE — drop the `six` compatibility shim from application code (2026-07-24)

Standalone cleanup between Steps 10 and 11 — Step 7 residue, not part of either. All
17 application imports of `six` were `six.moves.urllib.{parse,request,error}` and
`six.StringIO`, which on Python 3 alias the standard library exactly; swapped to
`urllib.*` / `io.StringIO` and merged into each file's stdlib import group. No
behavior change. 567 tests green on a fresh image, `check` + `makemigrations --check`
clean, all 17 touched modules import clean.

**The `six==1.16.0` pin stays** — four installed packages still require it
(`bleach`, `html5lib`, `python-dateutil`, `python-memcached`), so removing the pin
doesn't remove the package, it just lets it float (a rebuild without it drifted to
1.17.0). Same reasoning as the `sqlparse` pin: transitive, but pinned for a
reproducible build. The comment now marks it transitive-only. six leaves the image
for good when those four are bumped or dropped — `bleach`/`html5lib` are the
deliberately-deferred Step 10 pins (Step 13), `python-memcached` disappears at the
memcached→Redis consolidation.

**Related residue still present, deliberately not touched here:** several modules
keep a `from __future__ import print_function` line (inert on Py3). Sweep it with
the Step 13 deprecation backlog.

## EXECUTION — Step 10 (Django 2.2 → 3.2 LTS + Celery 5, Python 3) — DONE (2026-07-24)

Staged 2.2→3.0→3.1→3.2 (same doctrine as Steps 6/9), then Celery 4.4→5.2. Now on
**Django 3.2.25 LTS + celery 5.2.7**, still Python 3.7. **567 tests green, 5
skipped** on the freshly-built image; `manage.py check` + `makemigrations --check`
clean; full live smoke (site, forums, news, podcast, links, search, admin, both
password-reset flows, debug toolbar, celery worker + beat) all serve. **Pushed to
`modernize`; CI green on GitHub (2026-07-24).**

**Prep was a no-op for the 3.0 removals** (static scan + runtime warning capture on
2.2 found nothing: no `django.utils.six`, no `cookie_date`/`xreadlines`, staticfiles
tags already swept in Step 9, no removed settings). Each rung surfaced its own
breakers instead — a good argument for the rung-by-rung method.

**`python_2_unicode_compatible` removal (`bce37e7`) — prep, its own commit.** All 26
models.py imported `django.utils.encoding.python_2_unicode_compatible`, **removed in
3.0** (I'd mis-filed it as a 4.0 removal; the 3.0 rung caught it). It's a no-op under
Py3 and the classes already have real `__str__`, so a scripted removal of the
decorator + import across all 26 (the Step 9 watch-item, now forced). elsewhere's
vendoring note updated to match.

**Rung 1 — 3.0.14 (`800da53`):** two behavior changes. (1) `django.utils.html.escape()`
now defers to stdlib `html.escape()`, rendering `'` as `&#x27;` not `&#39;` — updated
3 test assertions (messages self-send/report, accounts password mismatch); output is
equivalent. (2) **3.0 enforces a model field's `choices` even when the list is empty**
(2.2 treated empty as "no choices"). The elsewhere app froze
`SocialNetworkProfile`/`InstantMessengerProfile.network_id` choices at import time —
*before* its `post_migrate` hook (`fill_db`) populates the network tables — so on a
fresh DB they froze `[]` and every valid network was rejected (`ModelForm._post_clean`
→ `instance.full_clean()` validates against the frozen model-field choices, which the
form-field override couldn't fix). Fix: **choices are dynamic data, so move them off
the model field and onto the form**, populated from the live data in `__init__`
(idiomatic). No schema/migration impact (elsewhere has no migrations). **Deeper
elsewhere modernization — real migrations + data-migration seeding, maybe
`network_id`→FK — deferred to Step 11/19** (see the task; do NOT smuggle a schema
refactor into an upgrade rung, and it collides with the Postgres move).

**Rung 2 — 3.1.14 (`d33552d`):** debug-toolbar 2.2→3.2.4 (2.2 caps at Django 3.0).
Three fixes. (1) `django.core.paginator.QuerySetPaginator` (a deprecated Paginator
alias) **removed in 3.1** — `core/paginator.py` used it only as a base of
`QuerySetDiggPaginator`, which already inherits Paginator via DiggPaginator, so dropped
the redundant base (public name kept). (2) **3.1 defaults `DEFAULT_HASHING_ALGORITHM`
to sha256**, so the password-reset token's hash half is now 32 chars (half a sha256
hexdigest) not 20 (sha1) — widened the reset-confirm URL token regex `{1,20}`→`{1,32}`.
(3) **debug-toolbar 3.x builds its URLconf — and reads settings — at package-import
time**; `local.py` probed availability with `import debug_toolbar` *while the settings
module was still loading*, so that settings access re-entered settings construction and
tripped 3.1's new empty-`SECRET_KEY` check, crashing the dev server. Probe with
`importlib.util.find_spec` instead (never executes the package). **Prod-cutover note:**
the sha256 default invalidates old sessions/reset-tokens signed under sha1 at deploy —
fine for the single Step-21 cutover (users re-login); the transitional
`DEFAULT_HASHING_ALGORITHM='sha1'` exists if a rolling deploy is ever needed.

**Rung 3 — 3.2.25 LTS (`6326ef5`):** two fixes. (1) 3.2 warns (`models.W042`) on every
implicit PK and would default new models to `BigAutoField` — set
`DEFAULT_AUTO_FIELD='django.db.models.AutoField'` in base settings to keep the existing
32-bit integer PKs (widening is a deliberate schema call for later, not upgrade churn).
(2) **3.2 gives the admin a catch-all view** that redirects anonymous users to login
for any unknown `/admin/` path, so `core/tests/test_urls.py`'s "retired admin reset
route 404s" check saw a 302 — log the test in as staff (the catch-all raises the real
404 for authenticated users). `makemigrations --check` stays clean.

**Celery 4.4→5.2 (`fd1aebd`):** celery 5.2.7 (last line on Py3.7; 5.3 needs 3.8+) +
kombu 5.2.4/amqp 5.1.1/vine 5.0.0. **celery 5 drops the uppercase-settings compat**
(the deferred Step-8 item), so config moved to the **`CELERY_` namespace**:
`celery.py` uses `config_from_object(..., namespace='CELERY')` and every key renamed to
its lowercase-with-prefix form (`CELERY_BROKER_URL`→`broker_url`,
`CELERYBEAT_SCHEDULE`→`CELERY_BEAT_SCHEDULE`→`beat_schedule`,
`CELERY_ALWAYS_EAGER`→`CELERY_TASK_ALWAYS_EAGER`,
`CELERY_IGNORE_RESULT`→`CELERY_TASK_IGNORE_RESULT`,
`CELERY_DISABLE_RATE_LIMITS`→`CELERY_WORKER_DISABLE_RATE_LIMITS`, BROKER_* keys gain the
prefix). Dropped `CELERY_SEND_TASK_ERROR_EMAILS` (removed in celery 4) and the unused
`CELERY_REDIS_DB`. **`pytz`→2021.3** (celery 5.2 needs ≥2021.3). **importlib-metadata
stays capped <5.0**: kombu 5.2's entry-point shim still calls `entry_points().get()`,
removed in importlib-metadata 5 (same class of bug as Step 8's kombu 4.6; kombu 5.3
fixes it but needs Py3.8+). Verified worker+beat boot and every namespaced setting
resolves to its lowercase key.

**Deliberately NOT done (orthogonal to the LTS climb, left at working pins):** Pillow
6.2.2, Markdown 2.6.11, bleach 3.1.5. Each is a real behavioral/API change (bleach 3.1
is the last line keeping the `styles=` kwarg `core/html.py` passes; Markdown 3 changes
rendering) and belongs in its own deliberate step, not this upgrade.

**Watch items beyond Step 10:** RemovedInDjango40Warnings are the Step-13 (4.x) backlog
— `request.is_ajax()` (user_photos/views, core/middleware), `{% ifequal %}`/
`{% ifnotequal %}` templates, `Signal(providing_args=...)` (forums/bio signals),
`force_text`/`ugettext_lazy`/`urlquote` (core/markup, elsewhere, messages tags), and
passing None for middleware `get_response` (tests). elsewhere migrations/FK refactor at
Step 11/19; `AutoCompleteUserInput` dead-code deletion (~~Step 19~~ done 2026-08-01, Step 12 task 06); `mysql.W002`
strict-mode (Step 11). **Pushed; CI green (2026-07-24).**

## EXECUTION — Step 9 (Django 1.11 → 2.2 LTS, Python 3) — DONE (2026-07-22)

Staged 1.11→2.0→2.1→2.2 (same doctrine as Step 6; Brian confirmed). **All four
rungs done and committed, plus the deferred `url()`→`path()` migration — Step 9
is complete.** Now on **Django 2.2.28**, 567 tests green, 5 skipped. **Pushed; CI
green on GitHub (2026-07-22) — this cleared the whole unpushed backlog, Steps 6–9.**

**Prep done first, on 1.11, so each version bump stayed a clean isolated diff:**
- **A (`226d4e6`)** — 49 `is_authenticated()` call sites across 21 files → property
  access. `CallableBool` (which allowed both forms) is removed in 2.0. Templates
  already used the property form.
- **B — NO-OP.** All 85 FK/O2O calls (55 models, 30 migrations) already pass
  `on_delete`; added back in `3fc659e` "Update to Django 1.9", predating this
  project. **A line-based grep said 17 were missing — all were false positives from
  wrapped definitions with `on_delete` on the continuation line.** An AST scan
  settled it. Lesson: multi-line call signatures need AST, not grep.
- **C (`1edcb4d`)** — the 7 function-based auth views → CBVs (deleted in 2.1).
  Config moves from URL `kwargs` into `as_view()`; `post_*_redirect`→`success_url`.
  **Gotcha: `success_url` is used verbatim, not through `resolve_url()`** — so
  `LOGIN_REDIRECT_URL` (the URL *name* `'bio-me'`) needed `reverse_lazy()`, else
  password-change would redirect to the literal string `"bio-me"` (silent, no
  exception). `PasswordResetConfirmView` now answers the emailed link with a
  redirect to a `set-password` placeholder route, keeping the token in the session;
  the existing token regex already matches it, so only the test needed the extra
  hop. antispam's `log_auth_failures` monkeypatch of `auth.views.login` (in
  `AppConfig.ready()`) had nothing left to patch → wraps the view in `urls.py`
  instead; **it had zero coverage**, so added `antispam/tests/test_decorators.py`
  and **verified by mutation** that removing the wrapper fails it.

**Rung 1 — 2.0.13 (`3fa865e`): zero application code changed.** Suite emitted no
`RemovedInDjango20Warning`; `manage.py check` clean. Only the two requirements
files (+ stale comments).

**Rung 2 — 2.1.15 (`49a047e`):**
- **`sg101/urls.py` blocked the import** — it referenced `auth.views.password_reset`
  &c., which 2.1 deletes. Prep C only covered `accounts/urls.py`; this second set
  was missed. **That admin flow was already broken**: its companion routes were
  never *named*, so submitting raised `NoReverseMatch: 'password_reset_done'`
  (verified by probe on 2.0), and its confirm URL still used the pre-1.6 `uidb36`
  format. Resolution (Brian chose): `admin_password_reset` → `RedirectView` to the
  site's real flow, other 3 routes deleted. Admin login keeps its "Forgotten your
  password?" link (that template renders it only if the name resolves). New
  `core/tests/test_urls.py` (3 tests) — nothing covered these before.
- **`bio/admin.py` `KeyError: 'delete_selected'`** — 2.1's `get_actions()` removes
  that action itself when `has_delete_permission` is False, so the explicit `del`
  hit an absent key → `pop(..., None)`.
- **`core/widgets.py`** — `Widget.render()` must accept `renderer` in 2.1. Note
  `AutoCompleteUserInput` is **dead code** (defined, referenced nowhere, no tests;
  orphaned when PM autocomplete was reworked) — fixed rather than pruned; deletion
  candidate for Step 19. **Deleted 2026-08-01 during Step 12 task 06**, which was
  already in `core/views.py` for the autocomplete's ordering; history showed it
  had been dead since 2016-10-23.
- **Cookie expiry format** — 2.1 emits RFC 7231 (`01 Jan 1970`) not the obsolete
  dashed form; `wiki/tests/test_middleware.py` pinned the old string.

**Migration-state cleanup (`c76f920`) — the big hygiene win.** `makemigrations`
had been reporting **28 phantom `AlterField` ops** across comments/downloads/
forums/news. Root cause: **34 Python-2 bytes literals** (`verbose_name=b'IP
Address'`, `help_text=b'...'`, `default=b''`, `upload_to=b'...'`) frozen into
2015-era migrations — on Py3 `b'x' != 'x'`, so those fields could never compare
equal. The 4 apps holding such literals were *exactly* the 4 apps reporting drift.
**Confirmed pre-existing, not caused by the upgrade: `makemigrations --check` on
the same code under 1.11 and 2.0 produced byte-identical output.** All values are
plain ASCII metadata and `default` is applied in Python, so rewriting alters no
schema. After the fix, drift collapsed to **2 genuine ops**.
- Those 2: **2.1 stopped forcing `blank=True` on `BooleanField`**, so
  `Topic.locked`/`.sticky`'s explicit `blank=True` now serializes →
  `forums/0003_topic_boolean_blank`. **`blank` is validation-only: `sqlmigrate`
  emits NO SQL on MySQL.** (SQLite shows a full table rebuild, but that's SQLite
  doing that for *any* `AlterField` — nearly wrote a wrong comment before checking
  both backends.)
- **`makemigrations --check` is now clean ("No changes detected") for the first
  time in this project** — it's now usable as a CI gate.

**Verified on the real prod snapshot:** migrations applied clean (Django's own
`admin.0003_logentry_add_action_flag_choices` + `auth.0009_alter_user_last_name_max_length`,
plus `forums.0003`); site/forums/news/podcast/links/search, both password-reset
flows, and admin login all 200; celery worker + beat boot clean on 2.1.
`/news/` 404 is correct and pre-existing (no `^$` pattern — the news front page is
the site home `/`; the paginated index is `/news/date/`).

**Rung 3 — 2.2.28 (`f3b93ac`): zero application code changed.** The only Django
warning was a `RemovedInDjango30Warning` that *predates* the bump (dates to 2.1):
`{% load static from staticfiles %}` is deprecated → `{% load static %}` (equivalent
since 2.1 — the built-in tag routes through `STATICFILES_STORAGE` when staticfiles is
installed); swept across **84 templates**. Requirements: Django→2.2.28, **`sqlparse`
now a hard Django runtime dep** so pinned in `requirements.txt`, **django-debug-toolbar
1.11→2.2** (1.x caps at 2.1); mysqlclient 1.4.6 already clears 2.2's raised 1.3.13
floor. `migrate` applied Django's own `auth.0010` (Group.name 80→150) + `auth.0011`
(proxy-perm rebuild — a no-op here, no proxy models) to the prod snapshot clean;
`makemigrations --check` stays clean. Checked the `Meta.ordering`→`GROUP BY`
`RemovedInDjango31Warning` (pending; only fires on `.values().annotate()` over a
Meta.ordering model): **non-issue** — the app's only GROUP BY query
(`donations.top_donors`) is on stock auth User (no Meta.ordering) AND already has an
explicit `.order_by()`. Remaining suite deprecations are third-party only (bleach's
vendored html5lib collections-ABC; kombu SelectableGroups — celery-5 step).

**Docker debug-toolbar fix (`4059cb1`, separate commit):** the toolbar was silently
hidden in Docker since Step 8 — its default gate needs `REMOTE_ADDR in INTERNAL_IPS`
(127.0.0.1), but host→container requests arrive NAT'd from the bridge gateway
(172.18.0.x). Fix in `docker.py`: `SHOW_TOOLBAR_CALLBACK = lambda r: DEBUG` (guarded
on debug_toolbar installed; inert under DEBUG=False). Per `research/docker-strategy.md`
prod WILL be Docker (same image, env-differentiated; deploy = Step 21), so this
dev-only setting moves into the dev compose override at the split — no prod debt.

**`url()`→`path()` migration (5 commits) — `django.conf.urls.url` is now GONE from the
project** (only the non-deprecated `django.conf.urls.static.static` remains). Deferred
until 2.2 was green (Brian's call) so the version bumps stayed clean diffs; `url()` is
a deprecated alias of `re_path()` removed in Django 4.0, so this is a hard prereq for
the future 4.x rung. Approach: **mixed `path()`/`re_path()`** — `path()` with typed
converters where clean, `re_path()` only where the regex does real work. Built a
classifier (196 routes: 136 static, 18 clean-param, 33 unnamed-`(\d+)`, 9 keep-re_path).
Commits: `d5d39cf` news (pilot — one of each shape), `dd34403` forums (biggest, 28
routes), `52d3b03` batch A (21 leaf apps + gcalendar's custom admin `get_urls()`),
`21c251d` batch B (root `sg101/urls.py`). **Key gotchas:** (1) `path()` only produces
KEYWORD captures — each unnamed `(\d+)` had to be NAMED to match the view parameter;
**ygroup `ThreadView` reads the id positionally via `self.args[0]`, so its route MUST
stay `re_path()` with an unnamed group** (path() would leave `self.args` empty →
IndexError; view untouched). (2) Stock converters don't enforce width/format, so
`\d{4}` year, `{20}` reg key, the reset token, the `user|date`/`title|date|rating|hits`
enums, and `[\w.@+-]{1,30}` usernames all stay `re_path()` (verified: a 5-digit year is
still rejected). (3) `<int:>` hands the view a real int (was str) — harmless for pk
lookups. (4) comments `/cr/` points at Django's `contenttypes.shortcut` (params
`content_type_id`, `object_id`). (5) route NAMES unchanged throughout, so
`reverse()`/`{% url %}` callers (args= or kwargs=) all still work; djdt namespace still
reverses after the root's DEBUG-guarded `__debug__` include moved to `path()`.

**Verified across the whole step:** 567 tests green / 5 skipped on the freshly-built
2.2.28 image; migrations apply clean to the prod snapshot; full live smoke (site,
forums, news, podcast, links, search, feeds, admin, both password-reset flows, debug
toolbar) all serve; celery worker + beat boot clean.

**Watch items beyond Step 9:** `mysql.W002` strict-mode warning still environmental
(Step 11); `@python_2_unicode_compatible` removable once Py2 support is formally
dropped; celery uppercase-settings rename at the celery-5 step; `AutoCompleteUserInput`
dead-code deletion (~~Step 19~~ done 2026-08-01, Step 12 task 06);
bleach/kombu third-party deprecations at their deps steps.
**Pushed; CI green (2026-07-22).**

## EXECUTION — Step 8 (flip interpreter to Python 3.7, Django 1.11) ⭐ — DONE (2026-07-19)

The central milestone: SG101 runs on **Python 3** for the first time, still on the
Django 1.11 LTS rung. **559 tests green under Py3.7, 5 skipped (S3), 84% coverage**
via the exact CI command; live smoke green on the real production snapshot (site +
celery worker + beat). Pushed with the Step 9 backlog; CI green (2026-07-22).

**Image / deps:**
- Dockerfile `python:2.7` → `python:3.7`; dropped the Debian-archive / `pip<21` /
  `git` / `--src` machinery (no editable git dep anymore).
- Requirements re-pinned for Py3.7: dateutil 1.5→2.8.2, Pillow 2.7→6.2.2, lxml
  3.4→4.9.4, bleach 1.4→3.1.5 (last line keeping the `styles=` kwarg), Markdown
  2.5→2.6.11, docutils 0.10→0.16, ftfy→5.9, six→1.16, redis 2.10→3.5.3,
  simplejson/requests/pytz bumps. python-memcached→1.59 (prod-only).
- **Celery 3.1.23 → 4.4.7** (+kombu 4.6.11/billiard/amqp/vine). **Gotcha: pinned
  `importlib-metadata==4.13.0`** — kombu 4.6's `entry_points().get()` shim breaks on
  importlib-metadata ≥5.0's `.get()`-less `EntryPoints` (celery imported but
  `from celery import Celery` failed via the lazy loader until pinned). Old
  uppercase celery settings (BROKER_URL/CELERYBEAT_SCHEDULE/…) still work in
  celery-4 compat mode — rename deferred to the celery-5 step.

**Vendored django-elsewhere** in-tree (was an editable git dep): 5 `.py` + 62 static
icons + a provenance docstring (upstream `github.com/leah/django-elsewhere`, fork
`github.com/gremmie/django-elsewhere@c8c6f5e`; neither ships a license). Py3-patched
(urlresolvers→django.urls, `__unicode__`, has_key). Trimmed to models+admin+data+
static; dropped the fork's dead views/urls/example template. **Static icons matter**
— SG101's `bio/elsewhere_links` templates reference `{% static 'elsewhere/*.png' %}`;
an initial trim dropped them (would've broken profile icons) — caught + restored.
No migrations (unchanged); tables come via run-syncdb, matching the prod DB.

**Graceful-guarded stubs** (module imports, real op raises NotImplementedError):
`core/s3.py` (boto2 → Cloudflare R2/boto3 at Step 15) and `gcalendar` calendar/oauth
(apiclient/oauth2client/httplib2 → google-auth at Step 18). Public `/calendar/` and
existing-photo display keep working; only new S3 uploads + admin Google-sync go
inert. Their tests skip cleanly (5 S3 tests).

**Runtime Py3 fixes:** redis-py 3.x — `zadd(mapping)`, `zincrby(amount, value)`,
`hmset`→`hset(mapping)`, `decode_responses=True` (whos_online, forums.latest, wiki;
the wiki `zadd` was a 4th one missed by the first grep). DiggPaginator: materialize
`map()`/`range()` → lists (subscripting + the `reduce` concat). `force_unicode`→
`force_text`; hashlib `.update()` needs bytes (wiki cookies — also kept username/
email as str for the `#`.join so the hash bytes match the external wiki);
`b64encode` bytes; text-mode file write (make_fixed_page); forums index
`sorted(key=)` (bare `cmp` + positional-cmp — Step-7 batch E missed it); isinstance
`long`/`unicode`; smiley implicit-relative import; `except (KeyError, X)`.

**Tests updated for library-driven output changes** (not regressions): bleach 3.1 +
html5lib 1.1 **alphabetize HTML attributes**; Py3.7 dicts render OpenGraph tags in
**insertion order**; Markdown 2.6's internal `IMAGE_LINK_RE` no longer matches one
malformed nested-bracket case (ssl_images leaves it unchanged vs `{bad image}`);
`response.content` is bytes (decode); `__builtin__`→`builtins`; `assert_called_once`
→`_with`; doctest `IGNORE_EXCEPTION_DETAIL` (Py3 fully-qualifies exception names);
`decode_responses=True` in the services call asserts; uuid `.bytes` mock → bytes.

**Method note / lesson:** the host runs **Python 3.14**, which accepts syntax that
**Py3.7 rejects** (e.g. `except A, b:`) — so Step 7's host-side `python3 -m
py_compile` gave false-green and missed a straggler. **Verify against the container
(3.7), not the host.** Used an in-container import-probe + `compileall` to surface
all import/syntax breakers at once instead of one-per-test-run.

**Follow-up (2026-07-19, post-flip):** true-division sweep. Brian noticed
`/messages/inbox/` rendering "46.666666666666664% used" — Py3's `/` is true
division where Py2 floored int/int. Swept product code for the whole category and
fixed 6 sites with `//`: `messages/views.py` (the reported percent), `forums/
views/main.py` `_goto_post` page number, `core/images/utils.py` square-crop offsets
(x2), **`downloads/models.py` upload-path `hex(... microsecond/1000)` — this one
CRASHED on Py3 since `hex()` needs an int**, and two `ygroup` sync commands' page
numbers. (Decimal/`float()`-wrapped and `x/2.0` sites left alone — unchanged
across Py2/3.) Added `messages` test pinning inbox/outbox pct as `int` (the
function had zero coverage, which is why the flip's suite stayed green). 560 tests.
Lesson reinforced: Step 7 chose not to add `from __future__ import division`, so
the flip surfaced these only via real use.

**Watch items forward:** celery uppercase-settings rename at the celery-5 step;
`@python_2_unicode_compatible` becomes removable once Py2 is fully dropped;
DOCKER.md §1 corrected to `.env` (Step-3 leftover). Step 9 (Django 1.11→2.2) is
next; the django-elsewhere fork no longer imports urlresolvers (that Step-9 watch
item is resolved by the vendoring).

## EXECUTION — Step 7 (Python 2/3-compatible source, still Py2.7) — DONE (2026-07-18)

Dual-runtime source on Django 1.11, still **executing under Python 2.7**. Method:
targeted manual batches (not a blanket `python-modernize`/`futurize` run — chose
reviewable diffs over auto-injected six/`__future__` noise), each ending green +
its own commit. **559 tests green**; **`python3 -m py_compile` clean across the
whole app + migrations** (proves zero Py2-only *syntax* remains — the semantic
str/bytes work is Step 8).

- **Batch A** (`1f3c63a`) — trivial syntax: `print`→`print()` (+`from __future__
  import print_function`), `except X, e:`→`except X as e:`, `raise X, "msg"`→
  `raise X("msg")`, `0644`→`0o644`, `xrange`→`range`, `reduce`→`functools.reduce`.
- **Batch B** (`c5bf802`) — **`__unicode__`→`@python_2_unicode_compatible`** across
  25 models.py (rename to `__str__` + decorator, via a host transform script) and
  11 admin.py `list_display '__unicode__'`→`'__str__'`. Also fixed a Step-6
  straggler: `from django.core import urlresolvers` (module form the sed missed;
  its warning had been masked by the elsewhere fork importing it first).
- **Batch C** (`8834989`) — `.iteritems()`/`.itervalues()`→`.items()`/`.values()`
  (small/non-hot, plain methods over six); `accounts._make_key` rewritten dual-safe
  (`b64encode(str)`/`unicode()`/`sha1(unicode)` all need bytes on Py3) with
  **byte-for-byte identical Py2 hash output** so registration keys don't change,
  + new `accounts/tests/test_models.py`; `avatar_cleanup`/`dlorphan` `unicode(path,
  'utf-8')`→decode-only-if-bytes.
- **Batch D1** (`d614766`) — `StringIO`→`io.BytesIO` (binary image data) /
  `six.StringIO` (Django command-output capture in tests); `urlparse`/`urlsplit`/
  `parse_qs`/`urllib.urlencode`→`six.moves.urllib.parse`.
- **Batch D2** (`a922552`) — network fetches. oembed/bandmap/oembed_refresh/
  fix_news→`six.moves.urllib` (kept six.moves to preserve the `HTTPError`/`URLError`
  types callers catch). **donations IPN `verify_request`→`requests`** per the plan:
  besides the library swap it fixes a **latent Py3 bug** (old `response.read()`
  returned bytes, `b'VERIFIED' != 'VERIFIED'` on Py3 → every verification would
  have failed; `response.text` is correct on both), adds a **20s timeout** (urllib2
  had none), and `raise_for_status()`. `hasattr(settings,…)`→`getattr(…,None)` to
  make it testable; +3 `VerifyRequestTestCase` tests (mocked `requests.post`).
- **Batch E** (`1e9952d`) — residual grep-sweep breakers: `sorted(cmp=…)`→
  `sorted(key=functools.cmp_to_key(…))` (bio/flags; cmp kwarg gone in Py3);
  `dict.values()[0]`→`list(dict.values())[0]` (forums/main, comments; dict views
  aren't subscriptable on Py3); `json.load(encoding=)`→`io.open(encoding='utf-8')`
  (arg removed in Py3.9; also fixes a latent locale-decode bug).

**Watch items for Step 8 (the ⭐ Py3 flip):**
- **Deep str/bytes + dict-ordering** work is Step 8's core (this step only made
  syntax + the obvious semantics dual-safe).
- **Celery 3.1.23 must bump** at the flip — not for Django but for Python: kombu's
  `async` module name is a reserved word in Py3.7. Plan → celery 3→4.4 (last
  Py2.7)→5. See [[modernizing-sg101-planning]].
- **django-elsewhere fork** must become Py3-compatible for the flip (it's the last
  suite deprecation warning on 1.11 via its `urlresolvers` import; on Py3 it must
  actually run) — patch the fork + re-pin.
- **Stub-on-flip apps** (per plan Step 8): `gcalendar` (old apiclient/oauth2client/
  httplib2) and `core/s3.py` boto usage — Py3-incompatible libs, temporarily
  disabled at the flip, revived at Steps 18/15.
- **Deferred formatting pass:** run `isort` (+ maybe `black`) as its own commit
  right after the flip (black dropped Py2; a whole-repo reformat now would bury the
  migration). A few import-placement nits from the batch scripts are parked for it.
- `@python_2_unicode_compatible` becomes a no-op on Py3; removable once Py2 is
  dropped (~Step 10).

## EXECUTION — Step 6 (Django 1.9 → 1.11 LTS, still Py2.7) — DONE (2026-07-18)

Reached the last Django that supports both Py2 and Py3. **1.9.13 → 1.11.29**,
**staged through 1.10.8** (Django's own advice: one feature release at a time —
isolates which rung a failure belongs to; 1.11's headline change is form-widget
template rendering). **549 tests green** on 1.10.8 and again on 1.11.29; live
smoke green on real prod data.

**Version-agnostic code changes (identical for 1.10 & 1.11):**
- **Hard breaks** (dotted-path URL reversing removed in 1.10): `news/views.py`
  `reverse('news.views.email_thanks')`→`'news-email_thanks'` (the Step-5 watch
  item); templates `register_success.html` (×2)→`'accounts-login'`,
  `register_failure.html`→`'accounts-register'`.
- **Middleware:** `MIDDLEWARE_CLASSES`→`MIDDLEWARE` in `base.py` (+ `local.py`
  debug-toolbar insert); dropped `SessionAuthenticationMiddleware` (always-on in
  1.10+); added `MiddlewareMixin` to the 3 custom middleware (`InactiveUserMiddleware`,
  `WhosOnline`, `WikiMiddleware`).
- **`django.core.urlresolvers`→`django.urls`** — 55 sites (all `reverse`/
  `NoReverseMatch`), mechanical sed.
- **`allow_tags`→`format_html`/`mark_safe`** — 14 admin display methods across
  forums/comments/messages/bio/user_photos/gcalendar/smiley/banners/shoutbox/
  potd/weblinks (RemovedInDjango20). `message_text` uses `mark_safe` (pre-rendered
  markdown); the rest `format_html` (XSS-safe interpolation).

**1.10-specific breakages surfaced by the staged run:**
- **`NoArgsCommand` removed + `optparse` `option_list`/`make_option` removed** →
  **17 management commands** converted to `BaseCommand`/`LabelCommand` +
  `add_arguments()`/argparse, `handle_noargs`→`handle(self, *args, **options)`.
  **Only 3 were caught by the test suite** (`max_users`, `ssl_images`,
  `purge_messages`); the other **14 have no tests** and stayed green — they
  surfaced only when the live **celery worker/beat** booted and fired scheduled
  tasks (`core.tasks.cleanup`→`forum_cleanup` crashed with
  `ImportError: cannot import name NoArgsCommand`). Full list: `forum_cleanup`,
  `sync_forums`, `oembed_refresh`, `avatar_cleanup`, `bio_image_check`,
  `fix_news_embeds`, `sync_ygroup_threads`, `sync_ygroup_posts`, `pick_potd`,
  `dlorphan`, `update_bands` (all `NoArgsCommand`), plus `topic_export`,
  `top_donors`, `dlcatreport` (`option_list` on `BaseCommand`/`LabelCommand`; the
  `LabelCommand` two call `super().add_arguments()` to keep the label positional).
  **Two celery task wrappers** were invoking commands via `Command().execute()`
  (KeyError `no_color` under BaseCommand, since options aren't populated) →
  switched to `call_command`: `messages.tasks.purge_messages` and
  `core.tasks.cleanup` (`clearsessions` + `forum_cleanup`). Verified by
  load-building the parser for all **27** project commands + running each affected
  path. (`tools/*.py` standalone scripts use stdlib `optparse` directly — fine.)
  **Lesson: the green unit suite is necessary but not sufficient — booting the
  worker/beat and the live dev server is what catches untested command/task code.**
  **Safety net added** (follow-up commit, +5 tests → 554): `core/tests/test_commands.py`
  loads every registered command + builds its parser (would have caught all 14 at
  once); `forums/tests/test_commands.py` (forum_cleanup), `potd/tests/test_commands.py`
  (pick_potd command), and the long-abandoned `core.tasks.cleanup` task test are now
  real; `messages` purge task test `.get()`s the result so a task exception fails
  loudly. These guard the command surface for the harder rungs ahead (the Py3 flip
  will break command bodies: print/urllib2/cStringIO/iteritems).
- **django-tagging 0.4.3 incompatible with 1.10** → **bumped to 0.5.0** (last line
  supporting Py2.7 **and** Django 1.11). Root cause: `TagField` installs itself as
  a class descriptor, so its attname is never in `instance.__dict__`; Django 1.10's
  new "auto update_fields for deferred fields on save" saw `tags` as deferred and
  set `update_fields` on a brand-new (pk-less) object → `ValueError: Cannot force
  an update in save() with no primary key`. 0.5.0 fixes it and ships one forward
  migration `0003_adapt_max_tag_length` (widens `Tag.name` to `MAX_TAG_LENGTH`,
  default 50; applied cleanly to the real DB).

**Other deprecation cleanups (kept the rung warning-clean):**
- `potd.Sequence.seq` `CommaSeparatedIntegerField`→`CharField(validators=
  [validate_comma_separated_integer_list])` (system-check W901; potd is a
  syncdb/unmigrated app so **no migration needed**, both are varchar).

**Dev-tooling the 1.11 dev server forced (dev/test-only, not in requirements.txt):**
- **django-debug-toolbar 1.4→1.11** (+ `sqlparse 0.1.14→0.2.4`): 1.4 is broken on
  1.11. And 1.11 requires the toolbar's URLs be wired explicitly — added a
  DEBUG-guarded `include(debug_toolbar.urls)` at `^__debug__/` in `sg101/urls.py`
  (matches `local.py`'s app+middleware guard). Without it every dev page 500'd with
  `NoReverseMatch: 'djdt' is not a registered namespace`.

**Migrations applied to the prod-snapshot dev DB** (all clean on real data):
admin `0002_logentry_remove_auto_add`, auth `0007_alter_validators…` +
`0008_alter_user_username_max_length` (30→150 on 15k users), sites
`0002_alter_domain_unique`, tagging `0002_on_delete` + `0003_adapt_max_tag_length`.

**Watch items for later rungs:**
- **django-elsewhere fork** (vendored `-e git+…gremmie/django-elsewhere`) still
  `import`s `django.core.urlresolvers` → the **only** remaining deprecation
  warning in the suite. Harmless on 1.11; **must patch the fork + re-pin before
  Django 2.0 (Step 9)** where urlresolvers is removed.
- **Function-based auth views** (`accounts/urls.py` + `antispam/apps.py` monkeypatch
  of `auth.views.login`) are **fine on 1.11** (class-based-view deprecation lands
  in 2.1) — the Step 9 CBV migration handles them.
- `mysql.W002` (strict mode off) — environmental, tied to Step 11 (Postgres).
- The `docker_test` `PRAGMA legacy_alter_table` SQLite shim is still required on
  1.11 (Django's SQLite schema editor keeps old ALTER-TABLE semantics until 2.0).

**Files:** 90 changed (+323/−243); most are the 1-line urlresolvers swap and the
17 management-command conversions.
**Committed + pushed, CI GREEN on GitHub:** `14793f0` (the 1.11 upgrade) +
`a637b75` (management-command smoke + scheduled-job tests, 549→554).
**Next real-world action: Step 7** — make the code Python 2/3 compatible on
Django 1.11 (still executing under Py2.7): `print()`, `except X as e`, octals,
`iteritems`/`xrange`, `__unicode__`→`__str__` shim, `urllib2`→`requests`.

## EXECUTION — Step 5 (regression safety net) — DONE (2026-07-17)

Characterization/functional tests that lock in **current** behavior of critical
journeys, so the Django upgrade ladder (Steps 6+) surfaces regressions loudly.
**+179 tests (370 → 549), total coverage 75% → 83%.** Full suite green in-container.

Opened by running a fresh per-file coverage report to target real gaps (not a
blanket unit sweep). The already-strong apps from the earlier manual pass
(accounts/login-registration, comments, messages/PMs) were left as-is; new tests
went to the thin, high-risk journeys:

- **forums permissions** — `forums/tests/test_permissions.py` (16). Anon→login vs
  403 on AJAX; member can't edit/delete others' posts or moderate; locked-topic
  reply refused; superuser + group-moderator powers; private-category access.
  `permissions.py` 83%→93%.
- **forums read/unread tracking** — `forums/tests/test_unread.py` (25). The whole
  `forums.unread` algorithm branch-by-branch (get_post/topic/forum_unread_status,
  get_unread_topics) + journeys (topic_unread jump-to-first-unread, forum_catchup/
  catchup_all, visit writes ForumLastVisit). **`unread.py` 15%→78%** (was the
  worst-covered core module).
- **donations PayPal-IPN** — appended to `donations/tests.py` (15). The IPN
  listener's defensive branches: unverified, non-Completed, non-donation item,
  **duplicate txn_id**, **wrong business email**, wrong txn_type, missing/invalid
  amounts & payment_date; edge saves (unknown custom user → unlinked, test_ipn
  flag); index/thanks pages. **`donations/views.py` 62%→90%.**
- **user_photos upload** — `user_photos/tests/test_upload_views.py` (26). upload
  (form/503-disabled/redirect), upload_ajax (v2 JSON), upload_ajax_v3 (status-code
  semantics incl. save-error 500), GalleryView, PhotoView, delete (own vs another
  user's photo). Mocked at the app's seams (UploadForm, delete_photos) — no Pillow
  or S3. **`user_photos/views.py` 39%→97%.**
- **admin smoke** — `core/tests/test_admin.py` (3). Walks `admin.site._registry`
  and loads every changelist + add form (and the index) as a superuser over all
  **60** registered models. Cheap insurance the admin still boots after upgrades.
- **forums moderation + spam tools** — `forums/tests/test_moderation.py` (17).
  Topic stick/move/split/split-at (effects, not just gates), bulk mod_forum
  (sticky/lock/delete/move), and the spam tools: deactivate a stranger spammer
  (account off, STA_SPAMMER, posts deleted), can't-deactivate-non-stranger,
  non-moderator blocked, nailed-confirmation, promote-stranger. **`spam.py`
  40%→98%.**
- **forums subscriptions + favorites** — `forums/tests/test_subscriptions.py`
  (16). subscribe/unsubscribe/status/manage for both features, incl. the
  asymmetry: subscribing to an inaccessible topic 404s while favoriting 403s.
  subscriptions.py 37%→79%, favorites.py 34%→89%.
- **forums latest-posts datastore + RSS feeds** — `forums/tests/test_feeds_latest.py`
  (9). Drives the real Redis-backed `forums.latest` (process a post → combined/
  per-forum feeds, updated-topics list, get_stats, notify_topic_delete) and the
  syndication feed (renders combined/per-forum/empty, excludes private forums).
  Real Redis DB 14 with `forums:*` flush + page-cache clear per test.
  **feeds.py 46%→100%, latest.py 48%→69%.**
- **forums/views/main.py** rose 38%→73% (permissions + unread + moderation).
- **news display + email** — `news/tests/test_display_views.py` (15). Front-page
  index, archives, category index/page, story, tag cloud/page (+404s), and the
  email-story-to-a-friend flow. **news/views.py 39%→93%.** Watch item for Step 6:
  email_story redirects via legacy `reverse('news.views.email_thanks')` (dotted
  view-path form — works in 1.9, removed in 1.10+); the test will flag it.
- **downloads** — `downloads/tests/test_views.py` (18). index/category(all sorts)/
  new/popular/rating/details (login-gated, 404 non-public), add form, and the AJAX
  rate (login/bad-params/duplicate-vote) + request (hit-count) endpoints.
  **downloads/views.py 28%→85%.**
- **weblinks** — `weblinks/tests/test_views.py` (19). Public browse (index/new/
  popular/category/detail + 404s), visit (hit-count redirect), random link, report-
  broken-link (anon gets friendly 200, not 403), login-gated add → PendingLink.
  **weblinks/views.py 31%→92%.**

Also **swept modernization step-number references out of shipped code/comments**
(test_pruned.py, docker.py, urls.py, requirements-docker.txt, and the two new
forums test docstrings): comments describe the code, not the plan; step history
lives here in `.agents/planning/`. No functional change; touched tests stay green.

**Not committed yet** (awaiting the go-ahead to bundle). Push remains the user's.
**Next real-world action: Step 6** — upgrade Django 1.9 → 1.11 LTS (still Py2.7),
with this safety net as the regression gate.

## EXECUTION — Step 4 (prune dead/disabled code) — DONE (2026-07-16)

Removed code that should not be carried up the upgrade ladder. **54 files
deleted, ~3,090 lines removed.** Tagged **`pre-step-4-prune`** before deleting
(recoverable ref).

- **Apps removed** (all had no migrations → clean): `irc` (chat status page),
  `legacy` (one-off phpBB→SG101 importers: 13 mgmt commands + `phpbb.py`/
  `html2md.py`; `models.py` was empty), `membermap` (user location map),
  `custom_search` (Haystack signal-processor glue).
- **Disabled search stack removed** per the Step 1 Postgres-FTS decision: 7
  `search_indexes.py` (downloads, weblinks, forums, bio, news, ygroup, podcast),
  `HAYSTACK_CONNECTIONS`, the `search_queue` Celery-beat entry,
  `SEARCH_QUEUE_ENABLED`, and the `QUEUE_*` async block (base/docker/test).
  **`/search/` stays a stub** (`FixedView`) — native PG FTS is built in Step 12.
- **Wiring cleaned:** `INSTALLED_APPS` (incl. the commented `#haystack`/
  `#queued_search`/`#custom_search`); `urls.py` (`/irc/`, `/member_map/` includes
  + commented haystack view/import cruft); templates — irc `{% load %}`/nav link/
  `irc_status` block pulled from `base.html` **and** `v3/base.html`; orphaned
  `sg101/templates/{irc,membermap}/` dirs deleted.
- **membermap wasn't fully unlinked** (contra the initial assumption): a live
  `{% url 'membermap-index' %}` remained in `user_stats_tag.html`, which renders
  on the **forums index** via `{% user_stats %}` → would have been a
  `NoReverseMatch` 500. Reworded to plain text.
- **Requirements slimmed:** dropped `django-haystack`, `queued-search`, `queues`
  (private `hg+ssh://bobcat/...`), `xapian-haystack`, and `django-picklefield`
  (was a queued_search dep; zero usage in the tree). `requirements-docker.txt`
  header comment updated (the two omitted deps are now formally pruned).
- **Left intentionally:** `colophon.html` still credits Xapian/Apache/MySQL in
  prose — cosmetic, describes the still-legacy stack; revisit at Step 20.
- **Test:** new `core/tests/test_pruned.py` guards against reintroduction (removed
  apps not in INSTALLED_APPS; `/irc/`+`/member_map/` → 404; `irc-main`/
  `membermap-index` reverse raises; `/search/` stub still 200).
- **Verified:** suite **370 pass** (was 369: −3 `legacy/tests.py`, +4 new); image
  rebuilt; live smoke test — `/`,`/forums/`,`/search/` = 200, `/irc/`,
  `/member_map/` = 404.

## EXECUTION — Step 3 (12-factor env-var config) — DONE (2026-07-15)

`secrets.json` is retired; **all config/secrets come from environment variables.**

- **Library:** `django-environ==0.4.5` (last Py2.7-compatible line; verified on the
  container) added to `requirements.txt` + `requirements-docker.txt`.
- **Loader:** `base.py` replaces the `json.load(secrets.json)` with
  `environ.Env()` + `read_env(DOTENV_PATH or repo-root .env)`. Every
  `SECRETS['X']` → `env('X')`: `SECRET_KEY` is **required** (missing ⇒
  `ImproperlyConfigured`); `GCAL_*`/`AWS_*`/`RECAPTCHA_*` default to `''`; DB
  creds via `env('DB_*')` in `local.py`/`production.py`.
- **Env files:** git-ignored **`.env`** (real values, migrated from the old
  `secrets.json`; DB creds = the `sg101` container creds) + committed
  **`.env.example`** template. `secrets.json`(.example) deleted.
- **Compose:** app services load `env_file: .env` (SECRET_KEY, DB_*, API keys);
  only topology (`DJANGO_SETTINGS_MODULE`, `DB_HOST`, `REDIS_HOST`) stays inline.
- **Hostname logic removed** (the plan's "platform.node()=='jaguar'" item — it
  lived in `celery.py`, not settings): `celery.py` now just
  `os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sg101.settings.local')` and
  drops the hardcoded `/svr/...` sys.path; `test.py` drops its Darwin Redis-socket
  branch; **`mac.py` deleted** (Intel-Mac-only, unused). Legacy deploy artifacts
  with `/svr` paths (`fabfile.py`, `apache/sg101.wsgi`) intentionally deferred to
  the deploy step (Step 21).
- **CI:** the `cp secrets.json.example secrets.json` shim is replaced by
  `cp .env.example .env` (standard env mechanism, not a JSON side-channel).
- **Test:** new `core/tests/test_settings.py` (subprocess boot tests: env value
  reaches the setting; missing `SECRET_KEY` fails loudly).
- **Verified:** full suite **369 pass** (70% cov); stack rebuilt (all 3 app
  images) and boots from `.env` only — web/worker/beat healthy, site serves 200s,
  no `secrets.json` present.

## EXECUTION — Step 2 (hg → git, private GitHub, CI) — DONE (2026-07-15)

**The repo now lives in git.** Canonical working copy: `sg101-git/` (pushed to
private `github.com/gremmie/sg101`, default branch `modernize`). The old hg repo
(`sg101/`) is a frozen backup.

- **Conversion tool:** git-cinnabar (hg-fast-export dropped the anonymous heads —
  no bookmark support). Faithful: 1268 commits, identical file trees, `rollout`
  tag. **All 4 heads preserved as branches:** `main` (←hg 1260), `modernize`
  (active), `v3-dev` (←1171), `abandoned-2015` (←960). Authors cleaned via
  git-filter-repo mailmap (gremmie→Brian, convert-repo→convert-repo@localhost).
- **Secret audit #1:** gitleaks (5 historical hits) + trufflehog (**0 verified
  live**). All old (2009–2015): 4 client-side Google Maps keys (public by design)
  + one dead 2011 OAuth consumer key (no committed secret material). Nothing
  rotated; re-check at audit #2 before any public flip.
- **CI:** `.github/workflows/ci.yml` builds the Py2.7 image + runs the suite on
  push/PR to `modernize`. **GREEN: 367 tests, coverage 70%.** (Fixed 4
  test_receivers modules: removed dead custom_search coupling — pulled a slice of
  Step 4 forward for a green baseline. CI also seeds secrets.json from the
  committed example since base.py still requires it pre-Step-3.)
- **GitHub's own "Dependency Graph / update-pip-graph" workflow** runs too
  (dynamic, not ours) — benign.
- **Transition DONE (2026-07-15):** the git repo now lives at the canonical path
  `/Users/brianneal/workspaces/bgn/sg101/` (dirs swapped: old hg repo → frozen
  backup `sg101-hg-backup/`). Directory basename `sg101` = compose project name,
  so the existing `sg101_db_data` volume reattached with zero reload (verified:
  15,227 users / 463,221 posts; `/`, `/forums/`, `/podcast/` all 200). Next real
  step: **Step 3** (12-factor env-var config, retire secrets.json — which also
  removes the CI placeholder shim).

## EXECUTION — Step 1 (Dockerized legacy env) — ~DONE (2026-07-12)

Legacy stack (Python 2.7 / Django 1.9.13 / MySQL / Redis) runs in Docker on the
Mac, seeded with a real production snapshot.

- **Runtime:** Docker Desktop installed. `docker compose` stack: `web`, `worker`,
  `beat`, `db` (MySQL 5.7, permissive `sql_mode=`), `redis`. Files: `Dockerfile`,
  `docker-compose.yml`, `requirements-docker.txt`, `sg101/settings/docker.py` +
  `docker_test.py`, `.dockerignore`, `DOCKER.md` (new-to-Docker walkthrough).
- **Image build:** faithful legacy pins compiled first try on `python:2.7`
  (archive.debian.org fix for EOL Buster). Dropped only the unreachable/native
  deps (private hg `queues`, native `xapian-haystack`) — both unused (search
  disabled) and formally pruned in Step 4. Pinned `sqlparse==0.1.14` (debug
  toolbar compat).
- **Snapshot:** `sg10120260712.sql.bz2` loaded cleanly (91 tables; 15.2k users,
  463k forum posts). DB findings recorded in `research/database-migration.md` →
  **Postgres decision holds**; Step 11 watch-items = latin1→UTF8 for 8 tables +
  CI uniqueness constraints. (Search decision: drop stack → Postgres FTS, as planned.)
- **Demo:** site serves real content (`/`, `/forums/`, `/podcast/`, `/links/`
  all HTTP 200) on Py2.7 in Docker.
- **Tests:** existing suite runs in-container — **349 pass / 353**. Fixed via
  settings-only shims (SQLite `legacy_alter_table` pragma for Django-1.9-vs-modern
  -SQLite; Redis→`redis` service over TCP) + one env-agnostic fix to
  `core/tests/test_services.py`. **Remaining 4 errors** = orphaned
  `*/tests/test_receivers.py` importing the disabled search stack
  (`custom_search`→`queued_search`, uninstalled) — pre-existing on `modernize`,
  slated for removal in **Step 4**. OPEN: pull that pruning forward for a 100%
  green baseline, or defer to Step 4 (see below).

## Where we are in the PDD process

- [x] Step 1 — Project structure created
- [x] Step 2 — Initial process planning (chose: requirements clarification first)
- [x] Step 3 — **Requirements clarification (Q1–Q11) COMPLETE** → see `idea-honing.md`
- [x] Step 4 — **Research COMPLETE** (static + web). 8 files in `research/`.
- [x] Step 5 — **Iteration checkpoint** — revisited requirements (AWS now allowed;
      hosting stays late-binding). Proceeding to design.
- [x] Step 6 — **Detailed design COMPLETE** → `design/detailed-design.md`
- [x] Step 7 — **Implementation plan COMPLETE** (21 steps) → `implementation/plan.md`
- [x] Step 8 — **Summary COMPLETE** → `summary.md`

## Step 2 prep (2026-07-13, before starting Step 2)

- **VCS heads:** repo has 4 topological heads; bookmarked the 2 loose ones so
  they convert to git branches — `v3-dev` (rev 1171, 2018 anon head),
  `abandoned-2015` (rev 960, closed 2015). Branch tips `modernize`/`default`
  convert automatically. Step 2 must head-parity-check after conversion.
- **Repo visibility:** decided **private initially, public later** (amends the
  Q7 "public GitHub" decision). Secret audit now runs **twice**: audit #1 during
  Step 2 (private, rotate live findings immediately) + audit #2 as the gate
  before flipping to public. Details in `research/vcs-migration.md`.

## ✅ PLANNING COMPLETE (2026-07-04)
All PDD steps done. Next real-world action: **execute Step 1** of
`implementation/plan.md` (Dockerized legacy environment + load a prod snapshot).
Track progress via the checklist at the top of the plan.

## How to resume

1. Re-open this project by adding its files to context:
   `/context add .agents/planning/2026-07-04-modernizing-sg101/**/*.md`
2. Tell me: **"Resume the SG101 modernization planning — start the research phase."**
   (Optionally re-invoke `/agent-sops:pdd` if you want the full SOP framing again;
   not required — the state below is enough for me to continue.)
3. I'll propose the research plan (seeded below) for your input, then investigate.

## Requirements summary (decisions locked in Step 3)

- **Scope:** Lift + prune (modernize stack, remove dead/expensive legacy, no new features).
- **Apps:** Drop `irc`. Revive `gcalendar` with modern Google client libs. Keep
  haystack+xapian search *if feasible* (open to replacing). Triage remaining apps
  in research.
- **Target:** Latest Django LTS (~5.2) on a modern Python 3, via an LTS ladder:
  `1.9 → 1.11 → 2.2 (Py3 migration here) → 3.2 → 4.2 → 5.2`. Make code Py2/Py3-
  compatible on 1.11, flip interpreter, then continue. 4.2 is an acceptable pause.
- **Testing:** Risk-based coverage; integration/functional-first, unit backfill.
  Current coverage unknown (measure in research). Clear deprecation warnings each
  rung (CI-enforced).
- **Dev env:** Docker for legacy stack (user new to Docker — needs clear guidance).
  Faithful legacy reproduction first; vendor/pin only if needed. Real production
  DB snapshots available for test data. Design container for prod parity from day 1.
- **VCS/CI:** Convert hg → git preserving branch history (incl. `modernize`).
  Public GitHub. GitHub Actions CI. Vendor private deps (`queues`; reuse existing
  `django-elsewhere` fork).
- **Sequencing:** Modernize locally in Docker first; **deploy to a new host once
  at the end** (no 2nd server during iteration — cost reasons). Leave current
  prod (Ubuntu 14.04) running untouched; accepted unpatched-OS risk (low traffic).
  Keep option to cut over at an intermediate rung. Short maintenance-window
  cutover acceptable; keep old box warm as fallback ~1–2 weeks.
- **Database:** Decide in research; **lean PostgreSQL** if it lets us delete the
  xapian/haystack/`queues` search stack (via Postgres FTS) and simplify hosting.
  Engine switch is its own deliberate step.
- **Hosting:** ~$94/mo donations + some out-of-pocket (hobby budget). Wants
  *simpler* than a hand-managed dedicated box; Linode-familiar; **no AWS** (no
  time to learn). Return to **S3** (or hosted object store) for user files.
  Xapian's persistent-disk need is a key hosting constraint (may vanish if we go
  Postgres FTS).
- **External services:** Email **critical** (currently local mail server — a
  headache; open to a **transactional email provider**). Google APIs important
  (gcalendar). **PayPal IPN** for donations (legacy — may need updating; verify).
  **Consolidate Redis + memcached → Redis only** (cache + broker). CAPTCHA desired
  (open to modern alternatives). Secrets: replace uncontrolled `secrets.json` with
  **env-var / 12-factor** config; **audit git history for secrets** before going
  public and rotate.

## Seeded research plan (Step 4 — to refine with user before executing)

Proposed research topics (each → a file in `research/`):

1. **Codebase state & test coverage** (`research/codebase-and-coverage.md`)
   - Run the suite (once Dockerized) and measure coverage per app; identify
     critical untested paths. Inventory apps, URLs, models, management commands.
2. **App usage triage** (`research/app-triage.md`)
   - Confirm keep/prune for `ygroup`, `oembed`, `legacy`, `countdown`, `contests`,
     `banners`, `bulletins`, `donations`, etc. via URL wiring, DB tables, templates.
3. **Search subsystem entanglement** (`research/search-stack.md`)
   - How xapian/haystack/`queues`/queued-search are used; whether Postgres FTS can
     replace them without losing behavior; migration effort.
4. **Database: MySQL → PostgreSQL** (`research/database-migration.md`)
   - MySQL-specific schema/queries; charset/collation (utf8 vs utf8mb4); data
     migration tooling and effort; Django ORM portability.
5. **Django/Python upgrade path & dependencies** (`research/upgrade-path.md`)
   - Per-rung breaking changes; dependency modernization map (celery 3→5,
     boto→boto3, google-api-python-client/oauth2client → current, Markdown,
     django-tagging, django-picklefield, python-dateutil 1.5→current, six removal,
     Pillow, mysqlclient/psycopg, etc.). Celery: what jobs actually run.
6. **Containerization & dev/prod parity** (`research/docker-strategy.md`)
   - Legacy Py2.7 image feasibility; compose for MySQL/Redis/(memcached)/xapian;
     how the setup evolves up the ladder into a deploy artifact.
7. **Hosting options** (`research/hosting.md`)
   - Compare simpler-than-dedicated options (esp. Linode/Akamai ecosystem, plus
     PaaS/container hosts) against: hobby budget, no-AWS, xapian-or-Postgres,
     managed DB/cache, S3, transactional email, container-friendliness.
8. **hg → git migration & going public** (`research/vcs-migration.md`)
   - History-preserving conversion (branches incl. `modernize`); secret-history
     audit/rotation; vendoring private deps; GitHub Actions matrix CI design.

**Note:** Item 1 (and much of the rest) depends on first standing up the legacy
Docker environment — so the very first *implementation* step, and an early
research enabler, is the Dockerized legacy stack.
