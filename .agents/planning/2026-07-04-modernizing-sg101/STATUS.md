# Project Status — Modernizing SG101

**Last updated:** 2026-07-26
**Methodology:** Prompt-Driven Development (`/agent-sops:pdd`)

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
Step 11/19; `AutoCompleteUserInput` dead-code deletion (Step 19); `mysql.W002`
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
  candidate for Step 19.
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
dead-code deletion (Step 19); bleach/kombu third-party deprecations at their deps steps.
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
