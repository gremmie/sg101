# Implementation Plan: Modernizing SG101

**Companion to:** `../design/detailed-design.md` (architecture, rationale,
requirements R1–R29) and `../research/*.md`. This plan assumes those documents are
available; it does not repeat their detail.

**Method:** Test-driven, incremental. Each step is a **working, shippable,
demoable increment**. No step changes two big variables at once. Every rung ends
green (tests pass), deprecation-clean, and with the manual smoke checklist passing
(R9). Solo, weekend-burst cadence → steps are small and resumable.

---

## Progress checklist

- [x] **Step 1** — Dockerized legacy environment + production snapshot (Postgres decision confirmed; 349/353 tests pass, 4 remaining = dead search-stack test modules deferred to Step 4) — done 2026-07-12
- [x] **Step 2** — hg → git (git-cinnabar; 4 heads preserved: main/modernize/v3-dev/abandoned-2015), private GitHub `gremmie/sg101` (default=modernize), GitHub Actions CI GREEN (367 tests), coverage baseline 70%, secret-history audit #1 clear (0 live) — done 2026-07-15
- [x] **Step 3** — 12-factor env-var configuration: `secrets.json` retired → `django-environ==0.4.5` reads all config from env vars (`.env`/`.env.example`, git-ignored `.env` loaded via Compose `env_file:`); removed hostname logic in `celery.py`/`test.py`; deleted `mac.py`; added settings boot test; stack boots from `.env` alone (369 tests pass) — done 2026-07-15
- [x] **Step 4** — Prune dead/disabled code: removed apps `irc`, `legacy`, `membermap`, `custom_search` + the disabled Xapian/Haystack stack (7 `search_indexes.py`, `HAYSTACK_CONNECTIONS`, `search_queue` beat entry, `SEARCH_QUEUE_ENABLED`, `QUEUE_*`); cleaned `INSTALLED_APPS`/`urls.py`/templates; slimmed requirements (dropped haystack/queued-search/queues/xapian-haystack/picklefield); `/search/` stub kept for Step 12; tagged `pre-step-4-prune`; 370 tests pass — done 2026-07-16
- [x] **Step 5** — Regression safety net (characterization functional tests for critical journeys) — DONE 2026-07-17. +179 tests (370→549), coverage 75%→83%. New: forums permissions (16), forums read/unread tracking (25), forums moderation/spam tools (17), forums subscriptions+favorites (16), forums latest-posts datastore + RSS feeds (9), donations PayPal-IPN rejection/edge branches (15), user_photos upload/gallery/delete (26), admin changelist/add smoke over all 60 models (3), news display+email (15), downloads browse/rate/request (18), weblinks browse/visit/report/add (19). Key module lifts: downloads/views.py 28%→85%, weblinks/views.py 31%→92%, news/views.py 39%→93%, forums/unread.py 15%→78%, forums/views/spam.py 40%→98%, forums/feeds.py 46%→100%, user_photos/views.py 39%→97%, donations/views.py 62%→90%, forums/views/main.py 38%→73%. Also swept modernization step-number references out of shipped code/comments. Latent Step-6 watch item found: news.email_story redirects via legacy dotted-path reverse('news.views.email_thanks') (works in 1.9, removed in 1.10+).
- [x] **Step 6** — Upgrade Django 1.9.13 → 1.11.29 LTS (still Python 2.7), staged through 1.10.8. MIDDLEWARE_CLASSES→MIDDLEWARE (+MiddlewareMixin on 3 custom middleware; dropped SessionAuthenticationMiddleware); django.core.urlresolvers→django.urls (55 sites); allow_tags→format_html/mark_safe (14 admin display methods); 3 hard-break dotted-path URL refs fixed; NoArgsCommand/option_list→BaseCommand+add_arguments (**17 mgmt commands** — only 3 caught by tests; the other 14 surfaced when the live celery worker/beat fired scheduled tasks; 2 task wrappers .execute()→call_command); **django-tagging 0.4.3→0.5.0** (fixes the 1.10 TagField-descriptor "Cannot force an update…" save bug); CommaSeparatedIntegerField→CharField+validator; django-debug-toolbar 1.4→1.11 + sqlparse→0.2.4 + wired djdt URLs. Migrations applied to real DB (auth username 30→150, sites domain-unique, tagging 0002/0003). 549 tests green; live smoke green; deprecation-clean except the vendored django-elsewhere fork's urlresolvers import (→ Step 9). — done 2026-07-18
- [x] **Step 7** — Make code Python 2/3 compatible (Django 1.11, still Python 2.7) — done 2026-07-18. 6 commits (batches A–E), 559 tests green, `python3 -m py_compile` clean across app + migrations. A: syntax (print()/except-as/raise/0o octal/xrange/reduce). B: `__unicode__`→`@python_2_unicode_compatible` (25 models + 11 admin list_display) + fixed a Step-6 `from django.core import urlresolvers` straggler. C: `.iteritems`→`.items`, `_make_key` dual-safe hash (identical Py2 output), fs-walk decode-if-bytes. D1: StringIO→io.BytesIO/six.StringIO, urlparse/urllib→six.moves.urllib.parse. D2: oembed/bandmap/oembed_refresh/fix_news→six.moves.urllib; **donations IPN→requests** (also fixed latent Py3 `bytes != 'VERIFIED'` bug + added timeout) +3 verify tests. E: `sort(cmp=)`→`cmp_to_key`, `dict.values()[0]`→`list(...)`, json.load utf-8 fix.
- [x] **Step 8** — Flip interpreter to **Python 3.7** (Django 1.11) ⭐ milestone — done 2026-07-19. Dockerfile python:2.7→3.7 (dropped Debian-archive/pip<21/git/--src); requirements re-pinned for Py3.7 (dateutil 1.5→2.8.2, Pillow 2.7→6.2.2, lxml 3.4→4.9.4, bleach 1.4→3.1.5, Markdown 2.5→2.6.11, redis 2.10→3.5.3, six/pytz/simplejson/requests/docutils/ftfy bumps); **celery 3.1.23→4.4.7** (+kombu/billiard/amqp/vine; pinned **importlib-metadata<5** — kombu 4.6's entry-point shim breaks on the 5.0 EntryPoints API). **Vendored django-elsewhere** in-tree (5 .py + 62 static icons + provenance docstring; Py3-patched; dropped the editable-git dep). **Graceful-guarded** core/s3.py (boto2) + gcalendar calendar/oauth (apiclient/oauth2client/httplib2) — modules import, real ops raise; public /calendar/ + photo display still work; their tests skip. Runtime Py3 fixes: redis-py 3.x zadd(mapping)/zincrby(amount,value)/hmset→hset + decode_responses=True (whos_online, forums.latest, wiki); DiggPaginator map()/range()→lists; force_unicode→force_text; hashlib bytes (wiki cookies); b64encode bytes; text-mode file write; forums index sorted(key=); isinstance long/unicode; smiley relative import; except (A,B). Tests updated for library-driven output (bleach 3.1 alphabetizes attrs; Py3.7 dict insertion order for OpenGraph tags; Markdown 2.6 IMAGE_LINK_RE; response.content bytes; __builtin__→builtins; doctest IGNORE_EXCEPTION_DETAIL). **559 tests green, 5 skipped (S3), 84%**; live smoke green on real snapshot (site + celery worker/beat on 4.4.7). **Lesson: host python3 (3.14) accepted syntax Py3.7 rejects — Step 7's host py_compile gave false confidence; verify against the container.**
- [x] **Step 9** — Upgrade Django 1.11 → 2.2 LTS (Python 3) — DONE 2026-07-22, pushed (cleared the Steps 6–9 backlog; CI green). Now on **Django 2.2.28**, 567 tests green / 5 skipped. Staged 1.11→2.0→2.1→2.2. Prep on 1.11: is_authenticated()→property (49 sites, `226d4e6`); on_delete already complete (no-op — grep false positives, settled by AST scan); function-based auth views→CBVs + antispam monkeypatch→urls.py wrapper w/ new mutation-verified tests (`1edcb4d`; gotcha: success_url bypasses resolve_url, so LOGIN_REDIRECT_URL needs reverse_lazy). **Rung 1 → 2.0.13 (`3fa865e`): zero app code changed.** **Rung 2 → 2.1.15 (`49a047e`):** sg101/urls.py admin password-reset routes (already broken — unnamed companions → NoReverseMatch, pre-1.6 uidb36) → RedirectView to the site flow + new core/tests/test_urls.py; bio/admin delete_selected KeyError; Widget.render(renderer); RFC 7231 cookie expiry. **Migration hygiene (`c76f920`): 34 Py2 bytes literals in 2015-era migrations caused 28 phantom AlterField ops — pre-existing (byte-identical on 1.11/2.0), metadata-only; makemigrations --check now clean.** forums/0003 for 2.1's BooleanField blank change (no SQL on MySQL). **Rung 3 → 2.2.28 (`f3b93ac`): zero app-code changes** — only a pre-existing `{% load static from staticfiles %}` deprecation swept across 84 templates; sqlparse pinned (hard Django dep as of 2.2); debug-toolbar 1.11→2.2. **Then the deferred `url()`→`path()` migration (5 commits: `d5d39cf` news pilot, `dd34403` forums, `52d3b03` batch A, `21c251d` root urls.py) — `django.conf.urls.url` is now GONE from the project** (a hard prereq for the 4.x rung, since `url()` is removed in Django 4.0). Mixed `path()`/`re_path()` over 196 routes; `path()` yields keyword captures only, so 33 unnamed `(\d+)` groups had to be named — except ygroup's `ThreadView`, which reads `self.args[0]` positionally and must stay `re_path()`. Route names unchanged, so all `reverse()`/`{% url %}` callers still work. Plus toolbar side-fix `4059cb1` (djdt silently hidden in Docker since Step 8 — host→container requests arrive NAT'd, so INTERNAL_IPS never matched; `SHOW_TOOLBAR_CALLBACK = lambda r: DEBUG` in docker.py). Real-snapshot migrate + live smoke + celery worker/beat green.
- [x] **Step 10** — Upgrade Django 2.2 → 3.2 LTS (Python 3) + Celery 4.4 → 5.2 — DONE 2026-07-24, pushed, CI green. Now on **Django 3.2.25 LTS + celery 5.2.7** (Py3.7), 567 tests green / 5 skipped, `check` + `makemigrations --check` clean, full live smoke green. Staged 2.2→3.0→3.1→3.2, then celery. **The 3.0-removal prep was a no-op** (Step 9's staticfiles sweep + no `django.utils.six` left nothing to do) — each rung surfaced its own breakers instead, a good argument for the rung-by-rung method. Prep commit `bce37e7`: **`python_2_unicode_compatible` is removed in 3.0** (not 4.0 as assumed), so a scripted decorator+import removal across all 26 models (no-op under Py3, real `__str__` already present). **Rung 1 → 3.0.14 (`800da53`):** `django.utils.html.escape()` now defers to stdlib (`'`→`&#x27;`, 3 test assertions updated); **3.0 enforces a model field's `choices` even when empty**, and elsewhere's `network_id` froze `[]` at import time — before its `post_migrate` hook seeds the tables — rejecting every valid network on a fresh DB → choices moved off the model onto the form, populated live in `__init__`. **Rung 2 → 3.1.14 (`d33552d`):** `QuerySetPaginator` removed (redundant base dropped from `core/paginator.py`); `DEFAULT_HASHING_ALGORITHM` now sha256 → reset-token URL regex widened `{1,20}`→`{1,32}`; debug-toolbar 2.2→3.2.4, whose import-time settings access re-entered settings construction and crashed dev boot → probe with `importlib.util.find_spec`, never `import`. **Rung 3 → 3.2.25 LTS (`6326ef5`):** `DEFAULT_AUTO_FIELD='django.db.models.AutoField'` (keep 32-bit PKs; widening is a deliberate schema call, not upgrade churn); 3.2's admin catch-all view redirects anon users on unknown `/admin/` paths, so the retired-route test logs in as staff. **Celery 5 (`fd1aebd`):** uppercase-settings compat is gone → `config_from_object(namespace='CELERY')` + every key renamed; pytz→2021.3; importlib-metadata stays <5.0 (kombu 5.2's `entry_points().get()` shim). Pillow/Markdown/bleach deliberately left at working pins. **Deferred out:** elsewhere migrations/FK refactor → Step 11/19; RemovedInDjango40 cleanups (is_ajax, ifequal, providing_args, force_text/ugettext_lazy/urlquote) → Step 13.
- [x] **Interlude** — Drop the `six` shim from application code (2026-07-24). Not a step; Step 7 residue cleared between Steps 10 and 11. All 17 application imports were `six.moves.urllib.{parse,request,error}` / `six.StringIO`, which alias the stdlib exactly on Py3 → `urllib.*` / `io.StringIO`, merged into each file's stdlib import group. No behavior change; 567 tests green, `check` + `makemigrations --check` clean. **The `six==1.16.0` pin stays** — bleach, html5lib, python-dateutil, and python-memcached still require it, so removing the pin only lets it float (drifted to 1.17.0 on a test rebuild); pinned for reproducibility like sqlparse, and now commented as transitive-only. six leaves the image when those four are bumped/dropped (Step 13; python-memcached at the memcached→Redis consolidation).
- [x] **Step 11** — Migrate MySQL → PostgreSQL (on 3.2 / Py3) — **DONE 2026-07-26**. Six code tasks at `.agents/tasks/2026-07-04-modernizing-sg101/step11/`, all complete: the site, its converted production data, and the test suite now all run on **PostgreSQL 16**. **Task order changed: 04 ran before 02/03** — task 01 proved that nothing can create a fresh Postgres database until every app has migrations, so the backfill is a prerequisite, not a successor. **Task 01:** `postgres:16` alongside MySQL, `psycopg2==2.9.9`, `DB_ENGINE` switch via `sg101/settings/databases.py`. **Task 04:** initial migrations for the 21 syncdb-era apps — all 26 now have them, no structural drift found, and `makemigrations --check` finally covers the whole project (it had been silently covering 5 apps of 26). **Task 02:** 12 collation-dependent lookups → `__iexact` across 9 files plus two `accounts` migrations (functional unique index on `LOWER(username)`; normalize the one genuine email case variant); the lookup audit is `research/collation-audit.md`. **Task 03:** pgloader conversion of the *pristine* 1.8-era snapshot — **699,435 rows, 91 tables, zero rejections**, repeatable from empty; four findings, three of which would have shipped silently (MySQL's `latin1` is really **cp1252**; `int(11)` lands as `bigint` unless cast, against Step 10's deliberate 32-bit `AutoField`; `char(2)` pads on PG and crashes the profile page for the 12,854 members with no country set). **Task 05:** verification, which found **four more defects invisible to row counts, column diffs and the suite** — every datetime 5–6h early (naive MySQL local time loaded into `timestamptz` as UTC), all 91 FKs `RESTRICT` where Django needs `NO ACTION DEFERRABLE INITIALLY DEFERRED`, every `CHECK` constraint missing, two stray column defaults. The lesson, now embodied in `compare_schema.py`: **pgloader converts MySQL faithfully ≠ pgloader builds what Django would build.** **Task 06:** CI runs the suite on Postgres using the same Compose services as local dev; **the deferred test-database question is settled — Postgres everywhere, the sqlite path retired** (measured: 593 tests, 9.1s on PG vs 7.2s on sqlite — ~1.9s, and sqlite could never cover Step 12's FTS at all); Compose now defaults to Postgres with MySQL behind a `mysql` profile, kept because the cutover converts a fresh snapshot the same way. Full detail for every task in STATUS.md.
- [x] **Step 12** — Build PostgreSQL full-text search (restore `/search/`) — **DONE 2026-08-02**. All nine tasks complete; `/search/` is restored on native PostgreSQL full-text search with no Haystack, no Xapian and no third-party search package — an eight-type index of 516,858 documents, incremental maintenance from signals through Celery, a weekly sweep that reports drift, the forums' duplicate-topic quick search, and per-type result counts. **798 tests green.** Nine task files at `.agents/tasks/2026-07-04-modernizing-sg101/step12/` — task 09 was added 2026-08-01 out of task 04's review. **Task 01** (2026-07-28, `f342415`): the `search` app, `SearchDocument` and the document registry — the vector is built from the row's own columns (`title` A / `summary` B / `author` C), so it is rebuildable from the search table alone. **Task 02** (2026-07-29, `9573d8e`): `manage.py reindex_search` and the backfill — **518,595 documents in 1m17s**, 881 MB with the GIN index; the private-category exclusion lives in the registry's querysets. **Task 03** (2026-07-30): incremental indexing through Celery on `transaction.on_commit`, and the privacy boundary on write — a post is findable **0.61s** after being posted, and a category's 8,328 rows purge in 1.1s and restore in 2.1s when its groups change. Task 03 also **found and fixed a real defect**: three documents were indexing content the site does not show (43 unapproved downloads, whose detail pages 404; 57 unapproved links; 1,637 deactivated members' profiles), all three rules recovered from `pre-step-4-prune`'s `search_indexes.py` — corpus corrected to **516,858**. **Task 04** (2026-08-01, `2622943`): the search page itself — the single-box form, relevance ranking, snippets, pagination, the login gate, the route rename off the dead `haystack_*` names, and query logging in its own `search.log`. 64 tests, 743 green. **Found two defects the design had not anticipated**: `ts_rank` returns one constant (`6.3e-21`) for any query containing an exclusion, so `reverb -fender` was ordered by nothing but the date tiebreak across all 38,340 hits — ranking now runs against the query with its exclusions stripped, while filtering keeps the whole one; and rendering a `SearchHeadline` directly would have been **stored XSS**, since `body_text()` unescapes what it strips tags from and `ts_headline` passes `<img src=x onerror=…>` through intact. **Brian reversed requirement 1 / AC4**: the type checkboxes start unchecked, as on the old site, though "none checked" must still mean "search everything" because the masthead box posts a bare `q` and is indistinguishable from an untouched form. The **FRV-1 tip was retired ahead of task 07** — it was Xapian's limitation, and `FRV-1` now finds 2,024 documents against the old advice's 114. **Task 05** (2026-08-01, `06b61f9`): the forums' duplicate-topic quick search, the last stubbed search route. 17 tests, 759 green. **Brian superseded two of the task's requirements** — the endpoint moved from `/search/ajax/` to **`/search/topics/`** and `forums.js` stopped sending `models=forums.topic`, because the view forces the type anyway and a parameter nobody reads advertises an interface that does not exist. The instruction to freeze the path existed only because the JavaScript hardcoded it, which stops being a reason the moment that JavaScript is being edited. Fixed the pre-existing markup bug (`</fieldset>`/`</div>` closed only in the no-results branch) and pinned `models=forums.topic` into the fragment's overflow link, which had been forwarding it from the request and would otherwise have quietly widened to all eight types. Checks are logged as `Forum topics quick search:` — **Brian corrected the assumption that this fires while typing; it is an explicit button click**, so each one is deliberate. **Task 06** (2026-08-01, `c87fc27`): the `ajax_users` member-autocomplete ordering fix, 761 green — **MySQL had been alphabetical by accident** (a range scan on the unique username index returns rows in key order), and Postgres cannot inherit that, because `istartswith` compiles to `UPPER(username::text) LIKE …`, a function of the column, so it seq-scans and returns heap order. The omission was invisible until the engine changed. Also deleted `core/widgets.py`, dead since 2016. **Task 07** (2026-08-02, `18bc237`): verification against production data, no reindex, findings in `research/search-verification.md`. **`normalization=Value(1)` is a document-length sort in disguise** and the comment justifying it was wrong in both halves — `ts_rank` does not reward bulk, and the "tight" document is not a news headline but `forums.topic`, whose summary is exactly 0 characters. Kept anyway, because `normalization=Value(0)` fixes the burial of curated types but swings the top-ten type mix from 121 topics/71 posts to 5/177; the real fix was task 09. `'english'` stays decisively (stemming turns the typo `reverbe` into 54,065 hits; worst-case stem contamination measured at 4.7%). The GIN index is used everywhere, typical 1.3–10 ms, worst case `surf` at 159 ms — so the rate-limiting deferral stands, but on the strength of the **login gate**, not the design's "should be milliseconds"; relaxing that gate requires rate limiting in the same change. **Task 08** (2026-08-02, `cf51dc5`): the weekly reconcile sweep — `search/reconcile.py`, `manage.py reconcile_search`, `search.tasks.reconcile_index`, Beat at Sunday 03:30. It **reports drift and repairs nothing**, which is the point: stopping the worker and hand-editing a post proved that a *queued* task survives Redis and self-repairs, while a *lost* row stays missing until someone reindexes. 19 tests, 780 green. **The trap:** the natural `exclude(pk__in=…)` compiles to `NOT IN (subquery)`, which Postgres cannot anti-join — it **did not finish in five minutes** on `forums.Post`; `~Exists` gives `NOT EXISTS` and 567 ms. **Task 09** (2026-08-02, `0327ec5`): per-type result counts, closing task 07's loop — `backing track` had buried the first of 115 downloads at rank 47 and now shows `Downloads (115)` beside `Forum Posts (2,830)`. 18 tests, 798 green. **They are nearly free only because they replace the paginator's `COUNT`**: the count and the `GROUP BY` do identical work below the aggregate, and that bitmap heap scan is ~95% of the cost, so replacing is +0.9–2.5% while adding alongside runs the scan twice at +36.6%. **The end-of-Step-12 prune, done 2026-08-02:** the 14 dead `search_title`/`search_summary` methods across seven models, leaving `bio.UserProfile.search_title()` (which `search/documents.py` calls) and `podcast.Item.search_title()` (social sharing, now commented as such since the name no longer tells the truth); and `bio`'s `profile_content_update` signal with its two senders, dead since Step 4 removed `custom_search` — `bio/signals.py` is deleted, and the profile document stays current through `post_save`/`post_delete` in `search/receivers.py` regardless. Not pruned: `forums`' `topic_content_update`/`post_content_update`, which `forums/latest.py` still receives for the RSS latest-posts datastore. The eight Haystack-era `sg101/templates/search/indexes/*_text.txt` went too — their last Python reference left with `bio`'s `search_summary()`, and the provenance they carried is better served by `pre-step-4-prune`, which holds the templates *and* the seven `search_indexes.py` classes that rendered them. Requirements clarified in `step12-idea-honing.md` (Q1–Q11), design in `research/search-design.md`. Shape: **one denormalized search table** (not per-model `SearchVectorField`s — relevance ordering plus pagination across 8 document types forces it), relevance-ranked with newest as tiebreak, **single websearch-syntax box** replacing the three keyword/exact/exclude inputs the old form was already synthesizing into that same syntax, all index writes **via Celery on `transaction.on_commit`**, **login required** (anti-bot, carried forward), **private categories never indexed** (`Kahunas`: 487 topics / 19,088 posts), query logging kept in its own `search.log`. Recovered rather than remembered: the old search was **date-ordered, not relevance-ordered**, and the surviving templates + `pre-step-4-prune` tag documented the form, the index fields, the login gate and the log line. Deferred additively: `pg_trgm` "did you mean", comments, private-category search, rate limiting, sort toggle.
- [ ] **Step 13** — Python 3.7 → 3.10, then Django 3.2 → 4.2. **The interpreter moves first and is not optional** — Django 4.0 requires Python 3.8+, so the step cannot begin on the frozen `python:3.7` image; Step 14 used to own the Python move and cannot, being downstream of the rung that needs it. **3.10 rather than the 3.8 minimum**, because it is the only version Django 3.2 *and* everything through 5.2 support, which lets the interpreter move alone with `Django==3.2.25` untouched before any Django rung starts. **Measured 2026-08-02: the interpreter move costs exactly one dependency bump, and not one of the four this plan expected.** Every pin installs unmodified on `python:3.10` — `Pillow==6.2.2`, `mysqlclient==1.4.6`, `psycopg2==2.9.9` and `lxml==4.9.4` all build cp310 wheels from sdist. The real breaker is at import: **`bleach==3.1.5` cannot import on 3.10** (`cannot import name 'Mapping' from 'collections'`), so the long-deferred bleach bump becomes the gate. It is small — the pin comment calls 3.1.5 "the last line keeping the `styles=` kwarg," but both `_CLEAN_PROFILES` entries pass `[]` and neither allows a `style` attribute, so the kwarg is redundant twice over and modern bleach's default already does what it asks for. **Pillow is therefore decoupled from the interpreter**, and its `Image.ANTIALIAS` removal (7 call sites) should be its own change on its own evidence. **`mysqlclient` stays** (settled 2026-08-02): it looks like dead weight in a Postgres project, but `tools/pgloader/verify.py` and `verify_data.py` import `MySQLdb` to read both engines side by side — pgloader and the `mysql` CLI do the converting, and only the *verification* needs the Python driver. Dropping it would leave Step 21's fresh-snapshot conversion unverifiable, and since neither tool is in the suite, nothing would go red until the maintenance window. **EIGHT task files generated 2026-08-03** in `.agents/tasks/2026-07-04-modernizing-sg101/step13/` (01 interpreter + bleach, 02 the `RemovedInDjango40` backlog, 03/04/05 the Django rungs one apiece, 06 dependency alignment, 07 Pillow, 08 Markdown). Generating them corrected four things in the detail below — `is_ajax` is **4** sites not 7 (three matches are a same-named tag parameter) and `providing_args` is **2** not 3; `django.conf.urls.url` has **zero** usages so that rung item is free; the **Markdown bump is the step's largest single item**, since both custom extensions use the pre-3.0 API; and the six `ANTIALIAS` test assertions are mock-based and **cannot fail on this bug**. It also surfaced one thing the plan never had: **`USE_TZ` is not set anywhere in `sg101/settings/`**, so the site runs naive against Step 11's `timestamptz` columns — decided inside task 03. **Task 01 DONE 2026-08-03** (`cc0ea88`), pushed, CI green — the interpreter move cost *two* bumps, not one: bleach as predicted, plus `Pillow 6.2.2 → 9.5.0`, which installs and imports on 3.10 and then **aborts the interpreter at shutdown** (exit 134). **Task 02 DONE 2026-08-03** — the `RemovedInDjango40` backlog, 811 tests green with the warning promoted to an error. It corrected two more counts (`ifequal` is **19** across **7** files, not 17 across 6 — `ifnotequal` is not a substring of `ifequal`) and **found an item the inventory never had**: `Passing None for the middleware get_response argument`, 11 tests in 3 files, invisible to grep because it is triggered by an *absent* argument rather than a named API. Also settled: the 16 `from __future__` lines in migrations **are** in scope. **Task 03 DONE 2026-08-04** (`92c993d`), pushed, CI green — the 4.0 rung, on Django 4.0.10, 811 green and unchanged. Task 02's backlog work paid off: **not one application breaker**. The only failure was `django-tagging==0.5.0` importing `smart_text`, which fails at *import* so `django.setup()` aborts and zero tests run — a rung can look total and be three lines. **Vendored into the repo as `tagging/`** (Brian's call: vendor now, replace later; 0.5.0 is the final release and it breaks again at 4.1), keeping the app label and its three migrations so the 1,006 tags and 4,561 tagged items are untouched; **retirement scheduled into Step 19**, where a Postgres `ArrayField` is the more interesting candidate than `django-taggit`, since the content-type indirection exists to tag *any* model and this site tags one. **`USE_TZ` decided on evidence and set to `False` explicitly**: the `timestamptz` columns already hold correct absolute instants across the whole history, so turning it on is a settings change and **not** a data migration — but 79 naive builders, 3 `pytz.localize()` calls and 8 lines of month/year rollup make it cross-cutting behavior work, so it became **new task 09**, last in the step, on 4.2 with no version bump in flight. **Two plan corrections from reading 4.0's source:** the `USE_TZ` default flips in **5.0, not 4.0** (4.0 only warns, and only while unset), while **`USE_L10N`'s default *does* flip in 4.0** — measured a no-op here and deliberately left unset. **All 17 pytz sites audited and deferred to task 09** (`research/pytz-audit.md`), which corrected the plan's sequencing — nothing forces `zoneinfo` at 4.1, and the audit found that **`zoneinfo` cannot resolve the timezone names 93.6% of users have stored** (14,248 of 15,227 profiles, `US/Pacific` alone 12,619; also hardcoded at module level in `forum_tags.py:33`, so a naive swap breaks the forums for everyone). `CSRF_TRUSTED_ORIGINS` confirmed genuinely unset — no settings module reads it and there is no local-override hatch. The 4.1 `default_app_config` backlog is **9 apps, not the 1 recorded** — vendoring tagging cleared its own, leaving **8**. **Next: task 04**, the 4.1 rung. Nine task files now, task 09 added 2026-08-04.
- [ ] **Step 14** — Upgrade Django 4.2 → 5.2 LTS (Python 3.10 → 3.12) ⭐ target reached
- [ ] **Step 15** — Media → Cloudflare R2 (boto3)
- [ ] **Step 16** — Email → transactional provider
- [ ] **Step 17** — reCAPTCHA → Cloudflare Turnstile
- [ ] **Step 18** — Revive `gcalendar` with modern Google libraries
- [ ] **Step 19** — Retire `wiki`/MoinMoin; verify-then-prune `banners`/`oembed` (`contests`/`countdown`/`bandmap` confirmed KEEP 2026-07-24; `membermap` already pruned in Step 4)
- [ ] **Step 20** — Production hardening (gunicorn/WhiteNoise/prod compose/backups) + Cloudflare front
- [ ] **Step 21** — Deploy to new host + cutover + fallback. **Tail item: retire the MySQL conversion chain, gated on decommissioning the old box** — not on the site looking fine, because while the old box stays warm a DNS flip makes its MySQL authoritative again and any second roll-forward is another convert-and-verify. Preconditions: tag the cutover commit (`verify_data.py`'s canonicalization is worth keeping findable) and archive the final snapshot (git restores the tooling; nothing restores the data). Out: `mysqlclient` + the Dockerfile's MySQL apt packages, the `db` service and `mysql` profile, `verify.py` / `verify_data.py` / `convert.sh` / `sg101.load` / `crosscheck_dumpdata.sh`, `DOCKER.md` §6–§7, and the four keep-this comments added 2026-08-02, which become wrong at exactly that moment. Stays: `compare_schema.py` (psycopg2 only — compares a converted schema against a Django-built one, useful beyond MySQL).

---

## Phase A — Foundation (enable local dev, CI, and the safety net)

### Step 1: Dockerized legacy environment + production snapshot
**Objective:** Run the *unmodified* legacy stack (Django 1.9.13 / Python 2.7 /
MySQL / Redis) locally in Docker on the Mac, seeded with real data.
**Guidance:** Base image `python:2.7`. `docker-compose.yml` services: `web`,
`worker` (Celery), `beat`, `db` (MySQL 5.7), `redis`. Install pinned deps
(faithful reproduction first; vendor/pin only where PyPI fails). Load a production
DB snapshot into `db`. Keep `secrets.json` as-is for now (converted in Step 3).
Xapian intentionally omitted; search stays stubbed (as on the branch). Document
every compose command (user is new to Docker).
**Tests:** Get the **existing** test suite running green in-container
(`manage.py test`, sqlite settings). This is the baseline that proves the harness
works — no new app code yet.
**Integration:** First runnable artifact; everything else builds on this compose.
**Snapshot task:** inspect the snapshot to make the **Postgres-vs-Xapian / DB**
decision (charset/utf8mb4, row counts, case-insensitive uniqueness, search
volume) — records the choice that Steps 4/11/12 depend on.
**Demo:** Browse the running SG101 site locally at `localhost`, logged in, viewing
real forum/news content from the snapshot — on a machine that can't run Python 2.7
natively.

### Step 2: hg → git, private GitHub, baseline CI, coverage baseline
**Objective:** Move to git with history preserved; get automated tests running on
every push; know the current coverage.
**Guidance:** Convert with `hg-fast-export` (preserve branches incl. `modernize`,
tags from `.hgtags`; author map). **Bookmark the loose heads first so they survive
as git branches** — done 2026-07-13: `v3-dev` (rev 1171), `abandoned-2015` (rev
960); after conversion verify git branches `main`/`modernize`/`v3-dev`/
`abandoned-2015` all exist (**head-parity check** vs `hg heads --topo --closed`).
Add `.gitignore` (mirror `.hgignore`). Push to a **private** GitHub repo
(visibility decision 2026-07-13: private initially, public later — see below).
**Secret-history audit #1** (`gitleaks`/`trufflehog`) on full converted history;
**rotate anything live immediately** (don't wait for the public flip). GitHub
Actions workflow runs the suite (current rung: Py2.7/Django 1.9 via the Step 1
image) + uploads a **coverage report**.
**Before-public gate (later, e.g. at/after Step 21 cutover):** re-run the audit on
everything added during modernization + a final full pass, confirm clean, verify
`.gitignore`, rotate stragglers — *then* change visibility to public. (Rotation
makes exposed secrets dead; optional `git filter-repo` scrub to physically remove.)
**Tests:** CI executes the existing suite; add a coverage measurement job
(`coverage run` + report). No product code changes.
**Integration:** Uses the Step 1 container as the CI test image (parity).
**Demo:** Push a commit → GitHub Actions runs the suite green and publishes a
coverage % for the codebase; the `modernize` branch history is visible on GitHub.

### Step 3: 12-factor env-var configuration
**Objective:** Read all config/secrets from environment variables instead of
`secrets.json` and hostname checks — enabling dev/prod parity.
**Guidance:** Introduce `django-environ` (or `os.environ`). Replace every
`SECRETS[...]` read (SECRET_KEY, DB_*, GCAL_*, AWS_*, RECAPTCHA_*) and the
`platform.node()=='jaguar'` / hardcoded `/svr/...` logic with env vars. Commit a
`.env.example` (placeholders only); git-ignore real `.env`; compose loads it.
**Tests:** A settings/boot test asserting the app configures correctly from env
vars (missing-required-var fails loudly); suite stays green.
**Integration:** Container from Step 1 now boots purely from env; CI from Step 2
supplies env vars.
**Demo:** Delete `secrets.json`, start the stack from a `.env` file only — the site
boots and serves normally.

### Step 4: Prune dead/disabled code
**Objective:** Remove code that should not be carried up the ladder — before the
upgrade work begins.
**Guidance:** Remove app `irc` and app `legacy` (one-off phpBB importers; tag a
git ref first for reference). Per the Step 1 decision (working hypothesis =
Postgres FTS), **remove the already-disabled search stack**: `haystack`/
`xapian`/`queued_search`/`queues`/`custom_search` deps and the dead
`search_indexes.py` files + the `custom_search` app + the dead search-queue Beat
entry. Search remains the existing stub. Update `INSTALLED_APPS`, `urls.py`,
`requirements*.txt`, `CELERYBEAT_SCHEDULE`.
**Tests:** Update/trim tests for removed apps; add assertions that pruned URLs
(`/irc/`) return 404 and that the app boots without the removed apps; suite green.
**Integration:** Slims the codebase and dependency set every later step must carry.
**Demo:** Site runs identically (minus IRC), with a noticeably smaller
`requirements.txt` and no Xapian/native-search dependencies.

### Step 5: Regression safety net (characterization tests)
**Objective:** Build functional tests that lock in current behavior of critical
user journeys, so upgrades surface regressions loudly. (These are **new tests for
pre-existing legacy behavior** — the safety net for all subsequent steps.)
**Guidance:** Using Django's test client, cover the risk-based critical paths
(R6): login/registration, view/post a forum topic & reply (+permissions), photo
upload flow, donations PayPal-IPN verification (good fixtures already exist),
private messages, comments, admin loads. Prefer URL/view-level tests. Target
enough coverage on these paths to trust the ladder; peripheral apps stay thin.
**Tests:** This step's deliverable *is* tests — but characterization tests of the
legacy baseline, not tests of new plan-authored code.
**Integration:** Runs in CI (Step 2); becomes the regression gate for Steps 6–14.
**Demo:** CI shows a materially higher coverage % on critical apps, and a green
suite of end-to-end journey tests describing how the site behaves today.

---

## Phase B — The Python 3 crossing (on Django 1.11)

### Step 6: Upgrade Django 1.9 → 1.11 LTS (still Python 2.7)
**Objective:** Reach the last Django that supports both Py2 and Py3, still on Py2.7.
**Guidance:** Bump Django to 1.11.x; fix 1.10/1.11 changes: `MIDDLEWARE_CLASSES`
→ `MIDDLEWARE`, remove `SessionAuthenticationMiddleware`, template/settings
adjustments. Bump only deps 1.11 requires.
**Tests:** Safety-net suite (Step 5) must stay green; add tests for anything that
changed behavior; run with deprecation warnings surfaced.
**Integration:** Same container, Django pin advanced.
**Demo:** Site runs on Django 1.11 (Py2.7); smoke checklist passes; suite green.

### Step 7: Make code Python 2/3 compatible (Django 1.11, still Python 2.7)
**Objective:** Dual-runtime source, still executing under Py2.7.
**Guidance:** Apply `python-modernize`/`futurize`: `print()`, `except X as e`,
`0o644` octals, `iteritems`→`items`, `xrange`→`range`, `__unicode__`→`__str__`
(with a compat shim), `urllib2`→`requests` (donations IPN),
`django.core.urlresolvers`→`django.urls`. Keep everything importable under Py2.7.
**Tests:** Full suite green **under Python 2.7** after each batch of changes;
add unit tests around touched tricky logic (IPN verification, markup).
**Integration:** No framework change — isolates the language migration.
**Demo:** The suite passes on Py2.7 with a codebase that is now Python-3-ready.

### Step 8: Flip interpreter to Python 3 ⭐ (Django 1.11)
**Objective:** Run SG101 on Python 3 for the first time — the central milestone.
**Guidance:** New `python:3.x` (3.6/3.7 for Django 1.11) `web`/`worker` image.
Resolve Py3-only issues (str/bytes, dict ordering, division). **Temporarily
disable/stub apps whose external libs aren't yet Py3-ready** — `gcalendar` (old
`apiclient`/`oauth2client`/`httplib2`) and `core/s3.py`'s `boto` usage — each
explicitly scheduled for revival/replacement (Steps 18 and 15). Update
`requirements` to Py3-compatible pins.
**Tests:** Full suite green **under Python 3**; CI matrix switched to Py3; tests
asserting stubbed features are cleanly disabled (not erroring).
**Integration:** Container base image swapped to Py3; all later steps are Py3.
**Demo:** Browse and use SG101 running on Python 3 + Django 1.11 with real data.

---

## Phase C — Climb to a modern LTS, then swap the engine

### Step 9: Upgrade Django 1.11 → 2.2 LTS (Python 3)
**Objective:** First Py3-only Django jump; clears the biggest API breakage.
**Guidance:** `url()`→`path()`/`re_path()`; function-based auth views →
class-based (`uidb36`→`uidb64` in password-reset URLs); `on_delete` on FKs; remove
`django.core.urlresolvers` remnants. Bump deps (start Celery modernization if
required). Clear all deprecation warnings.
**Tests:** Safety-net + unit tests green; add tests for changed auth/URL behavior.
**Demo:** Site on Django 2.2 LTS / Py3; login + password reset + smoke checklist pass.

### Step 10: Upgrade Django 2.2 → 3.2 LTS (Python 3)
**Objective:** Reach the stable modern LTS where the engine swap will happen.
**Guidance:** Address 3.0/3.1/3.2 changes; continue dependency bumps (Celery 5,
Pillow, Markdown 3, etc. as needed). Clear deprecations.
**Tests:** Suite green; smoke checklist.
**Demo:** Site on Django 3.2 LTS / Py3 with real data.

### Step 11: Migrate MySQL → PostgreSQL (on 3.2 / Py3)
**Objective:** Switch the database engine — a deliberate, well-tested step.
**Guidance:** Add **`psycopg2`** (NOT psycopg 3 — Django 3.2's PostgreSQL backend
imports `psycopg2` and fails without it; psycopg 3 support arrives in **Django
4.2**, so revisit at Step 13. Python 3.7 caps psycopg2 at **2.9.9**; 2.9.10
requires ≥3.8). Parameterize DB via env (Step 3). Convert a snapshot with
**`pgloader`** (well-documented, since it's new to the user); address
charset/utf8mb4, case-sensitivity (usernames/emails/tags), sequences. **For
case-insensitivity prefer `__iexact` + functional unique indexes over Django's
`CIText`/`CICharField`/`CIEmailField`/`CITextField` — those are deprecated in
Django 4.2 and removed in 5.1, which Steps 13/14 walk straight into.** Run Django
migrations on Postgres. CI gains a **Postgres service container**.
**Tests:** Full suite green on **Postgres**; data-integrity checks (row counts,
spot content) vs. the MySQL snapshot. ~~keep sqlite for fast unit runs but add a
Postgres CI job~~ — **superseded in task 06**: sqlite cost only ~1.9s of a 9s
suite and could not cover Step 12's FTS at all, so the suite runs on Postgres
everywhere and the sqlite path is gone.
**Integration:** Compose defaults to Postgres (MySQL kept behind a `mysql`
profile for snapshot conversion); all later rungs test on PG.
**Carried in from earlier steps:** the `elsewhere` app has **no migrations at all**
(syncdb-era tables, seeded by a `post_migrate` hook) — decide during Step 11 planning
whether real migrations + data-migration seeding (and possibly `network_id`→FK) must
land here or can wait for Step 19. Also: 8 latin1 tables → UTF8, case-insensitive
uniqueness constraints (Step 1 research), and the environmental `mysql.W002`
strict-mode warning disappears with the engine.
**Demo:** SG101 running on PostgreSQL with migrated production data; suite green on PG.

### Step 12: Build PostgreSQL full-text search (restore `/search/`)
**Objective:** Replace the removed Xapian search with native Postgres FTS —
restoring search functionality for the first time since it was stubbed.
**Guidance:** **Designed 2026-07-26 — see `research/search-design.md` for the
build, and `step12-idea-honing.md` (Q1–Q11) for the reasoning and the rejected
alternatives.** Headlines, which supersede this section's earlier sketch:

- **One denormalized search table**, not a `SearchVectorField` per model (the
  earlier guidance). Forced by the combination of relevance ordering and
  pagination across eight document types: a blended global ordering can't be
  assembled by merging eight per-model querysets in Python.
- **Relevance-ranked**, newest as tiebreak — the old search was date-ordered.
  `setweight` A=title / B=body / C=author, and
  `SearchRank(..., normalization=Value(1))`. Weights are baked into the stored
  vector (changing them means a full reindex); normalization is query-time.
  **Built 2026-07-28 (task 01):** the three weight bands are three columns on the
  search row — `title`, `summary`, `author` — and the vector is a function of
  them, which is the pattern in the Django FTS docs. The models' `search_title` /
  `search_summary` go unused as a result; they embed the author and a formatted
  date in the title, which weighting cannot accommodate. **Backfilled 2026-07-29
  (task 02):** `manage.py reindex_search` built 518,595 documents in 1m17s — 29k
  more than the ~490k estimated here, which left out the Yahoo Group archive.
- **Single search box** using `search_type='websearch'`, replacing the three
  keyword/exact/exclude inputs — which the old form was already synthesizing into
  exactly that syntax before handing it to Xapian. Type checkboxes stay, all
  checked by default. The masthead box at `v3/base.html:49` already fits.
- **All index writes via Celery**, queued with `transaction.on_commit` — never
  inline in `save()`, so an indexing bug can't break posting. **No rename
  fan-out** (revised 2026-07-27): `username` is immutable (written once at
  activation) and full names are indexed only on the `bio.UserProfile` document,
  so a profile rename rebuilds one row. Embedding full names in content
  documents would have made one profile edit rebuild up to 25,768 rows, and only
  19% of members set a full name at all.
- **A weekly reconcile sweep on Beat** (revised 2026-07-27 — originally
  declined). It compares sets and timestamps in SQL rather than rebuilding
  vectors, so its cost tracks the drift it finds, not the corpus: the dominant
  term, scanning `id, update_date` across all 463,222 posts, measures 170 ms.
  **Reports only, repairs nothing** — task 03's indexing is supposed to make
  drift impossible, and the sweep is how that claim gets tested rather than
  assumed. Requires an `indexed_at` column on the search table from day one.
- **Login required** (carried forward — it exists because bots were hammering
  search), and **private categories are never indexed** (`Kahunas`: 487 topics,
  19,088 posts, unfindable even for members who may read them — deliberate).
  **Task 02 put the exclusion in the registry's querysets**, so "the objects to
  index" is one definition the bulk path, the stale-row sweep and task 03's
  per-object check all share, and a category becoming private drops out of it.
  **Task 03 found three more rules that belonged there** and were missing:
  `weblinks.Link` and `downloads.Download` are only visible once an admin sets
  `is_public`, and `bio.UserProfile` only while the account is active. All three
  were in the old Xapian indexes; none had survived into task 01's registry.
- **Query logging is kept**, existing behavior, moved to its own `search.log`
  handler mirroring `auth.log`.
- Restore the forums' duplicate-topic quick search; delete the stub; rename the
  `haystack_*` routes.
- Deferred, all additive: "did you mean" (`pg_trgm`), comments in the index,
  private-category search, rate limiting, a relevance/newest sort toggle.

**Tests:** Indexing on create/update/delete; that private-category content never
enters the index (both directions — a category becoming private must lose its
rows); query relevance and the weighting; the websearch syntax paths (phrase,
exclusion); login gate; the quick-search endpoint; functional tests for the
search page. Q4's exclusion and Q5's `on_commit` queueing are the two places
where a silent bug is most likely and most costly.
**Integration:** Uses Postgres from Step 11 and Celery for (re)indexing. Every
searchable app already has migrations thanks to Step 11 task 04 — four of the
seven (`bio`, `weblinks`, `podcast`, `ygroup`) were syncdb-era until then, which
was the argument for doing that backfill inside Step 11.
**Demo:** Search the live local site and get real, relevance-ranked results
across forums/news/links, with highlighted snippets and a working duplicate-topic
check on the new-topic form.
**FOLD IN — `core.views.ajax_users` returns an arbitrary slice** (found during
Step 11 task 02, 2026-07-25; parked here because the user autocomplete is
search-adjacent). The view runs
`.values_list('username', flat=True)[:limit]` with **no `ORDER BY`**, so a
`LIMIT 10` picks an undefined 10 of the matches — and against real data the
match sets are large: `bri` 28, `su` 435, `a` 579, `j` 884 active users. If the
person you want is not in the arbitrary ten, they simply never appear and the
UI gives no hint. Postgres does not improve this and can make it less stable,
since heap order shifts as rows are updated. **`core.tests.test_views
.AjaxUsersTestCase.test_happy_path` currently asserts insertion order**, which
SQL guarantees on no engine — it passes on sqlite and Postgres by query-plan
luck and **fails on MySQL today** (confirmed pre-existing on unmodified code).
**Fix:** add `.order_by('username')` to the view and change the test to expect
alphabetical — one line each, the sort is free at 15k rows, and alphabetical is
the conventional autocomplete behavior. Weakening the test to `assertCountEqual`
is the lesser alternative if the view is to be left alone, but it leaves the
arbitrary-ten behavior in place.
— no native libraries, no separate search server.

---

## Phase D — Finish the ladder

### Step 13: Python 3.7 → 3.10, then Django 3.2 → 4.2
**Objective:** Traverse to 4.2 (a pass-through — EOL, so we don't rest here long).
**The interpreter moves first, and it is not optional: Django 4.0 requires Python
3.8+**, so nothing in this step can start on the frozen `python:3.7` image. Step
14 used to own the Python move; it cannot, because it comes after the rung that
already needs it.

**Go to 3.10, not to the 3.8 minimum.** 3.10 is the only version that Django 3.2
*and* everything through 5.2 both support, which is what lets the interpreter
move alone — bump the base image with `Django==3.2.25` untouched, get the suite
green, and only then start 4.0 → 4.1 → 4.2 with the interpreter held fixed. That
keeps one variable per rung, which is the discipline that has surfaced the real
breakers in every upgrade step so far. 3.8 would buy a second interpreter move
later; 3.12 is not reachable as a solo move at all, since Django 3.2 tops out at
3.10 (support added in 3.2.9, so the current pin already has it).

| Django | Python |
| --- | --- |
| 3.2 | 3.6 – 3.10 |
| 4.0 | 3.8 – 3.10 |
| 4.1 | 3.8 – 3.11 |
| 4.2 | 3.8 – 3.12 |
| 5.2 | 3.10 – 3.13 |

**Measured 2026-08-02, before writing any of this down: the interpreter move
costs exactly one dependency bump, and it is not any of the four this plan
expected.** Every pin in `requirements-docker.txt` installs unmodified on
`python:3.10` given the Dockerfile's existing apt packages — including all four
that Step 14's venv note called blockers. `Pillow==6.2.2`, `mysqlclient==1.4.6`,
`psycopg2==2.9.9` and `lxml==4.9.4` all build from sdist and produce cp310
wheels. The prediction that they would not was wrong, and it was wrong in the
direction that would have oversized this step.

**One caveat on that measurement, added 2026-08-03: "builds from sdist" is not
"installs from a wheel," and the difference is dangerous for Pillow.** The
Dockerfile dropped the image and XML `-dev` headers on the grounds that lxml and
Pillow install from manylinux wheels on Py3.7 — true there, but a source build
on 3.10 needs those libraries present to link against. **Pillow built without
`libjpeg-dev` builds clean, imports clean, and fails on the first JPEG**, which
on this site means every thumbnail. Verify decoded format support explicitly on
the new image rather than inferring it from a green `pip install`.

Installing is not importing, though, and that is where the one real breaker
lives: **`bleach==3.1.5` fails to import on 3.10** — `cannot import name
'Mapping' from 'collections'`, the ABC aliases that 3.10 finally removed. Every
other third-party package imports clean. So the bleach bump this plan has been
deferring since Step 10 stops being a nice-to-have and becomes the gate on the
interpreter.

**And the bleach bump is far smaller than its pin comment claims.** The comment
in both requirements files calls 3.1.5 "the last line keeping the `styles=`
kwarg `core/html.py` passes," which reads as though a real allowlist is at
stake. It is not: `_CLEAN_PROFILES` has two profiles and **both pass `[]`**, and
neither one allows a `style` attribute in the first place, so the kwarg is
redundant twice over. Modern bleach replaced `styles=` with a `css_sanitizer`
object and strips all CSS when none is given — which is already the behavior
here. The work is deleting the kwarg and the now-empty third tuple element, plus
the two `core/tests/test_html.py` assertions that name it (lines 95 and 106).
Worth knowing while in there: bleach was archived upstream in 2023 in favor of
`nh3`. Not a decision for this step, but the last time anyone will be reading
this code closely for a while.

**CORRECTION 2026-08-03, from executing task 01: Pillow was NOT decoupled, and
the claim above that bleach is the only breaker is wrong.** `Pillow==6.2.2`
installs on 3.10 and imports on 3.10 — and then **aborts the interpreter at
shutdown**: `free(): invalid pointer`, exit 134, reproduced on both arm64 and
amd64, so CI and production would both have hit it. `from PIL import Image`
followed by nothing else is enough. This is the failure mode the "installing is
not importing" note was reaching for and still didn't catch, because **importing
is not exiting**: the import prints no error, the work succeeds, and the process
dies on the way out. Anything that imports PIL and returns — a Celery worker, a
management command, a shell `&&` chain — fails on a signal while looking
correct. Task 01 therefore had to move Pillow after all, to **9.5.0**: quiet on
3.10, still has `Image.ANTIALIAS`, and ships a cp310 wheel so the sdist build
and its libjpeg hazard go away entirely.

**What survives of the decoupling claim** is the part that matters for
sequencing: the `ANTIALIAS` removal is still its own change, because 9.5.0 keeps
the constant. Task 07 now starts from 9.5.0 rather than 6.2.2 and is otherwise
unchanged. The measurement lesson is the general one: *installs* was checked,
then *imports* was checked, and **exit status** was the third thing nobody
thought to check.

**The original (now superseded) reasoning:** the Pillow bump is decoupled from
the interpreter, since 6.2.2 runs on
3.10. It still has to happen eventually, and the trap is unchanged: `Image.ANTIALIAS`
was removed in Pillow 10, and seven non-test call sites still use it —
`core/images/utils.py:42`, `core/images/upload.py` (four), `potd/models.py:25`,
plus `core/management/commands/ssl_images.py:101`. It's `Image.Resampling.LANCZOS`
now. Nothing fails until Pillow crosses 10, and then thumbnailing breaks
everywhere at once. Do it as its own change, on its own evidence, rather than
smuggling it into the interpreter rung.

**And the existing tests cannot catch it — found 2026-08-03.** Six more
`ANTIALIAS` references live in the suite (`core/tests/images/test_upload.py:43,
46,110,113` and `test_utils.py:43,51`), and four of them assert against
`image_mock.ANTIALIAS`. **A `Mock` returns any attribute you ask it for**, so
those assertions stay green against a Pillow that has removed the constant
entirely; the first real signal would be a broken thumbnail in production. The
bump's actual deliverable is therefore a test that exercises a real `PIL.Image`
through one of the site's thumbnail paths — written, and **seen to fail against
the bug**, before the constant is swapped.

**Suggested order:**
1. Base image `python:3.7` → `python:3.10`, Django pinned at 3.2.25, bleach
   bumped because it must be. Suite green. This is the whole interpreter risk,
   isolated.
2. The `RemovedInDjango40` backlog while still on 3.2, where the warnings are
   warnings and not errors: **19** `ifequal`, **4** `is_ajax`, **2**
   `providing_args`, 2 `force_text`, 2 `urlquote`, 1 `ugettext`, and the 32
   inert `from __future__` lines. **DONE 2026-08-03 — and the list above was
   still missing an item.** Running the suite with `RemovedInDjango40Warning`
   promoted to an error surfaced **`Passing None for the middleware
   get_response argument`** (11 tests, `core/tests/test_middleware.py` ×2 and
   `wiki/tests/test_middleware.py`), which in 4.0 becomes a required positional
   argument and a `TypeError` at construction. **No grep could have found it**:
   every other item here is an API usage with a name to search for, while this
   one is triggered by the *absence* of an argument in test code. That is the
   case for treating the deprecation gate as a real gate.
   **The `ifequal` count was also wrong: 19 lines across 7 files, not 17 across
   6** — the original grep searched `ifequal`, and `ifnotequal` does not contain
   it as a substring, so `sg101/templates/bio/members.html` never appeared.
   **Two of those counts were wrong — re-counted
   2026-08-03 while generating the task files.** `is_ajax` matches seven lines
   but three are in `forums/templatetags/forum_tags.py:117,125`, where `is_ajax`
   is a **parameter name on the `show_form` tag** and has nothing to do with the
   removed `HttpRequest` method; "fixing" those would be a pointless edit to
   working code. The four real sites are `core/middleware.py:49` and
   `user_photos/views.py:64,103,219` — and note that all three `user_photos`
   sites guard POST endpoints, so a wrong header check breaks uploads rather
   than degrading gracefully. `providing_args` is 2, both in `forums/signals.py`
   (lines 13 and 20). Also worth deciding deliberately: **16 of the 32
   `from __future__` lines are in migrations** (`forums`, `comments`,
   `countdown`, `news`, `downloads`) — inert and safe to edit, but churn across
   historical files. **Settled 2026-08-03: migrations included.** On Python 3
   `unicode_literals` is definitionally a no-op so the edit cannot change
   migration behavior, and leaving 16 behind would make every future sweep
   re-triage the same 32 hits.
3. Django 4.0, 4.1, 4.2 as three rungs (`USE_TZ`, `zoneinfo` replacing pytz,
   `CSRF_TRUSTED_ORIGINS` scheme). **`django.conf.urls.url` costs nothing here —
   verified 2026-08-03, the tree has zero usages.** The single `conf.urls`
   import is `from django.conf.urls.static import static` (`sg101/urls.py:1`),
   which was never removed, and 89 modules already import from `django.urls`.
   **`USE_TZ` was the one that actually needed deciding — settled on the 4.0
   rung 2026-08-03, see item 4.** It was set in `sg101/settings/` nowhere at
   all, so the site ran on Django's `False` default — naive datetimes — against
   the `timestamptz` columns Step 11 created, the same seam Step 11 task 05
   found **every datetime 5–6 hours early** in. It is now `False` *explicitly*,
   with the conversion scheduled as task 09. **Two corrections the rung made to
   this plan's assumptions:** the `USE_TZ` default flips in **5.0, not 4.0**
   (4.0 only warns, and only while the setting is unset — so setting it silences
   the warning), while **`USE_L10N`'s default *does* flip in 4.0**, which this
   plan never mentioned. That one was measured rather than assumed and is a
   no-op here: with `USE_I18N = False` and `LANGUAGE_CODE = 'en-us'` every
   format constant is unchanged except `DATETIME_INPUT_FORMATS`, which only
   *widens* (it adds date-only `%Y-%m-%d`), and numbers render identically
   because `USE_THOUSAND_SEPARATOR` is off. So `USE_L10N` is deliberately left
   unset — setting it would buy nothing and add a `RemovedInDjango50Warning`.
   pytz is not
   a find-and-replace either: 17 call sites across 6 modules, including
   `pytz.NonExistentTimeError` (`forums/latest.py:317`) and
   `pytz.common_timezones` (`tools/tz.py`), neither of which `zoneinfo` has an
   equivalent for, and `bio/forms.py` validates **user-supplied** zone names.
4. **`USE_TZ` is decided, and the conversion is scheduled as its own task
   (task 09), last in the step, on 4.2 with no version bump in flight.**
   Measured 2026-08-04 during the 4.0 rung: the `timestamptz` columns already
   hold correct absolute instants across the whole history (a 2006 post reading
   `19:24:30` to the app is stored as `01:24:30 UTC` the next day), because
   Django sets the connection's `TimeZone` to `TIME_ZONE` while `USE_TZ` is off
   and PostgreSQL places each naive value on the timeline with it. **So turning
   it on is a settings change, not a data migration** — which is luck the
   PostgreSQL move bought, since MySQL's offsetless `datetime` would have forced
   rewriting every column. What makes it real work is the application: **79
   naive builders** (75 `datetime.now()`, 3 `utcnow()`, 1 `datetime.today()`;
   **zero** sites use `timezone.now()` today), 3 `pytz.localize()` calls that
   break outright, and — the only part that can fail *silently* — **8 lines of
   month/year rollup** in `donations` and `news` that resolve in UTC unless the
   timezone is made explicit, filing a 7pm-Chicago record under the next month.
   The rungs therefore set `USE_TZ = False` explicitly rather than converting:
   it silences 4.0's warning about the coming default change without smuggling a
   cross-cutting behavior change into a version bump. **Django 5.0 flips the
   default, so Step 14 cannot start with this open.**
5. Remaining dependency alignment. Two caps lift with the interpreter and are
   worth collecting here: `psycopg2` was held at 2.9.9 because 2.9.10 needs
   ≥3.8 (Step 11), and `celery`/`kombu` were held at the 5.2 line because 5.3
   needs ≥3.8 (Step 10) — which is also what forces the `importlib-metadata<5`
   cap, since kombu 5.3 fixes the `entry_points().get()` shim that cap exists
   for. Also revisit psycopg 3, which Django supports from 4.2 (Step 11).

**`mysqlclient` stays — settled 2026-08-02, and the reason is not the obvious
one.** It builds on 3.10, so nothing forces the question, and it is tempting to
read it as leftover from the Django MySQL backend now that the site is on
Postgres. It is not: **`tools/pgloader/verify.py` and `verify_data.py` both
import `MySQLdb`**, because they read both engines side by side, and `verify.py`
documents this in its own header — "Run inside the web container, which has both
drivers." Loading a dump uses the `mysql` CLI and converting it uses pgloader, a
standalone tool; neither needs the Python driver. **Only the verification does.**

Dropping the pin would therefore not break the conversion — it would break the
*checking* of the conversion, which is strictly worse. Step 11 task 05 is where
those two tools found four defects that row counts, column diffs and the entire
suite had all passed over (every datetime 5–6h early, all 91 FKs `RESTRICT`,
every `CHECK` missing, two stray defaults), and **Step 21 runs the conversion
again on a fresh snapshot** whose data nobody has verified yet. Neither tool is
in the test suite, so nothing turns red if the driver goes; the failure would
surface during the cutover maintenance window.

The pin itself carries no comment saying any of this, which is what makes the
accidental drop plausible — a later reader sees a MySQL driver in a Postgres
project and reasonably concludes it is dead. Give it one, naming
`tools/pgloader/verify*.py` and Step 21, alongside the Dockerfile's two apt
packages and the `mysql` Compose profile, which are load-bearing for the same
reason and equally unexplained at the point of use.
**The Markdown bump is bigger than this plan assumed — checked 2026-08-03.** It
is framed below as the occasion for revisiting the logger, but the bump itself
is the larger piece: **both custom extensions use the pre-3.0 extension API and
cannot load on Markdown 3.x.** `core/mdexts/deleted.py` and
`core/mdexts/urlize.py` between them hit four separate API changes —
`extendMarkdown(self, md, md_globals)` lost its second argument;
`md.inlinePatterns.add('del', tag, '>not_strong')` became
`Registry.register(obj, name, priority)`, where a **numeric priority replaces
the relative-placement string** and so has to be re-derived from output rather
than transliterated; `md.inlinePatterns['autolink'] = …` is registry item
assignment; and `markdown.util.etree` is gone in favor of
`xml.etree.ElementTree`. (`SimpleTagPattern` is also superseded, with a
different `handleMatch` contract.) These two extensions are **user-visible
markup on every rendered post** — `---struck text---` and site-wide
autolinking — and a mis-registered pattern does not raise, it just silently
stops working across 444,000 posts. Capture rendered output from real posts
first and diff against it.

**Revisit the `MARKDOWN` logger and how often Markdown is constructed.** Both
live in the same place and the Markdown bump is when someone will be looking at
them.

The logger entry in `local.py` and `production.py` dates from 2014 (`bdc8901`),
when Markdown logged at INFO every time it loaded an extension. Upstream fixed
that — 2.6.11 has no `.info()` calls left and those messages are `debug()` now —
so the original reason is gone. It is not dead config, though: `local.py` sets
the root logger to DEBUG and `docker.py` inherits it, so removing the entry
there puts **four records into `sg101.log` for every render**. In
`production.py`, where root is INFO, it does nothing at all. Keep it in local,
and treat the production copy as symmetry rather than function. The logger name
is still `MARKDOWN` as of 3.10.3, so no bump silently disconnects it.

Those four records per render are the symptom of something worth fixing on its
own: `core/markup.py:32` builds a fresh `markdown.Markdown` for every call,
re-importing and re-registering three extensions each time, so the cost scales
with traffic instead of being paid once at startup. `SiteMarkup` does the same.
Caching the instance is the obvious move — measure it first, and note that a
`Markdown` instance carries per-conversion state (`reset()` exists for this
reason), so a cached one must be reset between conversions or made thread-local
rather than shared naively.
**Tests:** Suite green on Postgres; smoke checklist.
**Demo:** Site on Django 4.2 / Py3 with working search.

### Step 14: Upgrade Django 4.2 → 5.2 LTS (Python 3.10 → 3.12) ⭐
**Objective:** Reach the target end-state.
**Guidance:** Bump Django to 5.2 LTS; move the base image from **3.10 to 3.12**;
final dependency alignment; clear all deprecations. **Step 13 now owns the
interpreter's first move** (3.7 → 3.10), because Django 4.0 requires 3.8+ and
this step comes after it. What is left here is a second, smaller hop: 5.2
supports 3.10 through 3.13, so the Django bump and the 3.12 move are independent
and can be done in either order — or the 3.12 move can be skipped entirely if
3.10 is good enough, since it is supported for the whole 5.2 LTS window.
**Two things arrive here from Step 13 rather than being discovered here.** Its
task 05 hands over a **written inventory of the 5.x deprecation warnings**
collected on 4.2 and deliberately left unfixed, so "clear all deprecations"
starts from a list instead of a survey — the same handoff Step 10 made to Step
13's task 02. And its task 06 records a **psycopg 3 decision** (Django supports
it from 4.2); if that came back "defer," this is where it lands, and the reason
is already written down.
**Tests:** Full suite green on Django 5.2 / Py3.12 / Postgres; smoke checklist.
**Demo:** SG101 running on the **target stack (Django 5.2 LTS, Python 3.12,
PostgreSQL)** locally with real data and working search.
**Also unlocks — a local venv for editor tooling.** Everything ran in Docker on
3.7, so there was no venv on the host and an editor language server (pyright,
via ALE) could not resolve a single third-party import. Tried on 2026-07-31 and
abandoned on the belief that four pins would not build on a modern Python —
`mysqlclient`, `Pillow==6.2.2`, `lxml==4.9.4`, `psycopg2==2.9.9`. **Measured
2026-08-02: that was wrong.** All four build on 3.10 from sdist with the apt
packages the Dockerfile already installs, and the whole pin set installs
unmodified; the one package that genuinely breaks is `bleach==3.1.5`, and it
breaks on *import*, not on build. So the venv is not gated on this step's
dependency alignment at all — it needs Step 13's interpreter move and the bleach
bump, both of which are that step's task 01, plus `mysql_config` on the host for
`mysqlclient`.

**Two corrections to the above, 2026-08-03.** First: **`mysqlclient` is not
dropping, so `mysql_config` on the host is a real requirement, not an
alternative.** The earlier phrasing offered "or dropping that pin, which Step 13
also raises" — Step 13 raised it and **settled it the other way**. The pin stays
because `tools/pgloader/verify.py` and `verify_data.py` import `MySQLdb` to
verify a conversion, and its retirement is now scheduled into Step 21, gated on
decommissioning the old box. A host venv therefore needs the MySQL client
headers installed on the host (`mysql_config` on `PATH`), or must accept that
`mysqlclient` is the one import the language server cannot resolve — which is
tolerable, since nothing in the application imports it.

Second, and the reason the 2026-08-02 measurement is weaker evidence for a
*host* venv than it looks: **"builds from sdist" is not "installs from a
wheel."** Those four pins built inside the image, where the Dockerfile's apt
packages supply the headers they link against. A host venv has whatever the host
has. `Pillow==6.2.2` in particular will build without `libjpeg` present and
produce a Pillow that imports fine and cannot decode a JPEG — harmless for
editor tooling, which only needs the symbols, but not something to discover
later while assuming the venv mirrors the image. Step 13's task 07 bumps Pillow
past 10, and modern Pillow ships cp310 wheels, so doing the venv **after** that
task avoids the source build entirely.

Two notes for when it happens: `django-stubs` is not
optional —
without it pyright flags every `Model.objects` and every field access, because
both are runtime-generated descriptors — and naming the venv `.venv` in the repo
root is what makes ALE find it with no configuration, so it needs a `.gitignore`
and `.dockerignore` entry to stay out of git and out of the `.:/app` bind mount.

---

## Phase E — Modernize subsystems (resolve the Step 8 stubs, adopt Cloudflare)

### Step 15: Media → Cloudflare R2 (boto3)
**Objective:** Return user uploads to object storage; resolve the Step 8 `boto` stub.
**Guidance:** Rewrite `core/s3.py` for `boto3` (or `django-storages`) with R2's
custom `endpoint_url`; move `USER_PHOTOS_*` to env-configured R2; bulk-copy
existing local media to the bucket; update `USER_IMAGES_SOURCES`.
**One live Py2 leftover to fix here:** `gen_key()` in
`core/management/commands/ssl_images.py:110` reads
`base64.b64encode(uuid.uuid4().bytes, '-_').rstrip('=')` — on Python 3
`altchars` must be `bytes`, and `b64encode` returns `bytes`, so the `str`
argument to `rstrip` is a second `TypeError` behind the first. `upload_image`
calls it at line 123, so the whole S3 upload path is dead until both are fixed.
The Step 8 `boto` stub is why nothing has hit it yet.
**Tests:** Upload/serve/delete tests against a mock/localstack or a test bucket;
functional photo-upload journey re-enabled.
**Demo:** Upload a user photo → stored in R2 → served (via Cloudflare, zero egress).

### Step 16: Email → transactional provider
**Objective:** Replace the local mail server with a deliverable provider.
**Guidance:** Point Django's email backend at Postmark/Brevo (SMTP or API) via env
config; set up sending domain + SPF/DKIM/DMARC; wire `DEFAULT_FROM_EMAIL` and
admin error mail. (Cloudflare Email Routing handles inbound only.)
**Tests:** Email-send tests (locmem/backends in unit tests; a staging smoke send);
registration/notification flows assert mail is dispatched.
**Demo:** Trigger a registration/notification in staging → email arrives in inbox.
**REVISIT HERE — changing an email address is unverified and unchecked** (found
during Step 11 task 02, 2026-07-25). `bio.forms.EditUserForm` is a bare
`ModelForm` over `('first_name', 'last_name', 'email')` with no `clean_email`,
and `User.email` has no `unique=True`, so `/profile/edit/` lets any member set
their address to one another account already uses — or to one they do not
control — with no confirmation step. Registration goes to real trouble to verify
(`PendingUser` + emailed key + confirmation link) and this discards that
guarantee the next day. **Not an account-takeover path** (login is by username
and reset mails the link *to* the address, so claiming an address yields nothing
readable), but three real harms: (1) with `hide_email` unticked the address is
published on the profile page, the member list, and every forum post
(`bio/view_profile.html:87`, `bio/members.html:48`,
`forums/display_post.html:25`) — i.e. you can publish someone else's address;
(2) it damages the other account's recovery, which is how the 13 duplicate-email
pairs came to be unrecoverable; (3) a typo silently costs you your own password
reset, with no error and no mail. **Fix order:** verify on change (reuse the
registration confirm-link machinery) > uniqueness check > don't display an
unverified address. **Trap:** a naive uniqueness check must reject only
*changing to* a duplicate — `exclude(pk=self.instance.pk)` alone would lock all
26 members of those existing pairs out of saving any profile edit, forever. See
`research/collation-audit.md` for the 13 pairs and their origin.

### Step 17: reCAPTCHA → Cloudflare Turnstile
**Objective:** Swap CAPTCHA to a free, privacy-preserving solution.
**Guidance:** Update the `antispam` app + forms to render the Turnstile widget and
verify tokens server-side (env-configured site/secret keys); follow Cloudflare's
reCAPTCHA→Turnstile migration guide; remove reCAPTCHA config.
**Tests:** Form-validation tests for pass/fail Turnstile verification (mock the
verify endpoint).
**Demo:** A protected form (e.g., registration/contact) shows Turnstile and
rejects a missing/invalid token.

### Step 18: Revive `gcalendar` with modern Google libraries
**Objective:** Restore the event calendar; resolve the Step 8 `gcalendar` stub.
**Guidance:** Port `calendar.py`/`oauth.py` from `apiclient`/`oauth2client`/
`httplib2` to **`google-api-python-client` v2 + `google-auth`**; env-configured
credentials; re-enable the app + URLs.
**Tests:** Unit tests with mocked Google API responses (event sync, formatting);
functional test for the calendar page.
**Demo:** The event calendar renders and syncs events from Google Calendar again.

### Step 19: Retire `wiki`/MoinMoin; verify-then-prune peripheral apps
**Objective:** Complete pruning per the triage.
**Guidance:** If confirmed, archive MoinMoin content, then remove the `wiki` app,
`WikiMiddleware`, and `wiki.tasks.expire_cookies`. Verify usage of `banners` and
`oembed` against the snapshot; keep or prune each. (`contests`, `countdown`, and
`bandmap` were **confirmed KEEP on 2026-07-24** during Step 11 planning, since
they hold latin1 tables the Postgres conversion must transcode; `membermap` was
already pruned in Step 4.) Also carries the deferred `elsewhere` rework —
`post_migrate` seeding as a real data migration, and possibly `network_id`→FK.

**Also carries retiring vendored `django-tagging`** (vendored during Step 13
task 03; see `tagging/__init__.py`). 0.5.0 is the final release, upstream
stopped in 2018, and it did not import on Django 4.0 — vendoring was the move
that kept the 4.0 rung to one variable, not an endorsement. The surface is
small and fully mapped as of 2026-08-04: **only the `news` app uses it** —
`TagField` on `Story` (`news/models.py:9`), `Tag`/`TaggedItem` in
`news/views.py` and `news/utils.py`, the `tagging_tags` templatetags in
`sg101/templates/news/story.html` and `story_summary.html`, and the
`/news/tags/` + `/news/tag/<name>/` routes. Live data is **1,006 tags across
4,561 tagged items**.

Two candidate replacements, and the choice is not obvious:
`django-taggit` is the maintained like-for-like, but keeps the generic
foreign-key + content-type machinery. **A Postgres `ArrayField` (with a GIN
index) is the more interesting option**, because that machinery is sized for
tagging *any* model and this site tags exactly one — the whole `TaggedItem`
join table and its content-type indirection exist to support a generality
nothing here uses. Either way it is a schema change plus a data migration for
the existing 4,561 rows, which is why it is not a version-rung item. Measure
the tag-page query cost before choosing; `/news/tag/<name>/` is the read path
that would change shape most.

**While in there:** `sg101/templates/fixed/colophon.html:14` credits
django-tagging with a link to `code.google.com/p/django-tagging/`, which has
been dead for years. Whatever replaces it, that line needs updating — and it is
a live page.
**Tests:** App-boot tests without `wiki`; adjust/trim tests for any pruned apps;
suite green.
**Demo:** Site runs cleanly without the wiki bridge; INSTALLED_APPS reflects final
app set.

---

## Phase F — Productionize and ship

### Step 20: Production hardening + Cloudflare front
**Objective:** A production-grade compose the final host will run.
**Guidance:** gunicorn; WhiteNoise (or Cloudflare-cached) static via
`collectstatic`; prod compose (DEBUG off, Postgres, Redis cache+broker, R2 media,
provider email, secure cookies); `pg_dump`→R2 backup routine + retention; health
checks; Cloudflare config (DNS record plan, edge TLS/origin cert, cache rules).
**Candidate index — `UPPER(username)` for the autocomplete.** Every keystroke in
the username autocomplete sequentially scans all 15,227 users. `istartswith`
compiles to `UPPER(username::text) LIKE UPPER(...)`, and the plain unique index
on `username` cannot serve a function of the column, so PostgreSQL has no choice.
On MySQL this was an index range scan, which is also why the endpoint was
accidentally ordered there and unordered here.

Measured on the real user table, worst realistic prefix (`j`, 884 matches):

| | Plan | Execution |
|---|---|---|
| Today | Seq Scan, 15,227 rows | 2.7 ms |
| With the index | Bitmap Index Scan, 27 heap blocks | 0.48 ms |

**It needs `varchar_pattern_ops`** — a plain functional index will not serve a
`LIKE` prefix match in a database collated `en_US.utf8`, only in `C`. Verified in
a rolled-back transaction, not assumed.

**Do not assume an existing index covers it.** `auth_user` already carries two:
Django's own `varchar_pattern_ops` index on the raw `username`, and
`auth_user_username_lower_uniq` on `lower(username)` from Step 11's collation
work. Neither serves this query — the first because the predicate is a function
of the column, the second because it lacks `varchar_pattern_ops` (a lowered
prefix `LIKE` against it still seq-scans, measured at 3.3 ms). So this is a third
index on the same column however it is spelled, which is part of what makes it a
tuning call rather than an obvious win.

Deliberately *not* done during Step 12: 2.7 ms is invisible to a member, and an
index that exists for one endpoint is a production-tuning decision rather than a
correctness one. Revisit here with real traffic, and drop it if the autocomplete
turns out to be rare.
**Tests:** A prod-mode boot/smoke test (DEBUG off, static served, security
settings on); CI builds the prod image.
**Integration:** Combines every prior subsystem into the deployable artifact.
**Demo:** Run the **production compose locally** end-to-end: DEBUG off, gunicorn
serving, static + R2 media, provider email, search — all green.

### Step 21: Deploy to new host + cutover + fallback
**Objective:** Go live on modern, supported infrastructure.
**Guidance:** Choose the host (late-binding; recommend single VM on Linode/
Lightsail, or Render). Provision; deploy the prod compose; load a **fresh
production snapshot**; run migrations + rebuild the search vectors; run the smoke
checklist on the new host (behind Cloudflare, pre-cutover, via a test hostname).
Schedule a **short maintenance window**: final snapshot → restore → **low-TTL DNS
cutover** in Cloudflare. Keep the **old Ubuntu 14.04 box warm ~1–2 weeks** as an
instant DNS-flip fallback, then decommission.
**Carried in from Step 12 task 03 (2026-07-30): pin the celery worker's
concurrency explicitly.** `docker-compose.yml` runs `celery -A sg101 worker -l
info` with no `--concurrency`, so the prefork pool silently defaults to the
host's CPU count — 10 on the dev Mac, but whatever the deploy VM happens to have
(1 on a single-core Linode). Nobody has ever chosen that number, and it changes
under you when the machine does. It is not a throughput question at 134 forum
posts a month; it decides **whether tasks for the same object can be processed
out of order**, which is the concurrency the search index's `indexed_at` guard
exists to survive. Pin it in the prod compose so the value is visible and
reviewable, and so a one-core host does not quietly serialise everything while a
later resize quietly stops doing so.
**Tail item — retire the MySQL conversion chain, gated on the decommission.**
Everything MySQL in this project exists to convert a production snapshot and then
verify the conversion. When the old box is decommissioned there is no MySQL
source left anywhere, and the whole chain becomes dead at one identifiable
moment. Do it then, as one change.

**The gate is the decommission, not "the site looks fine."** While the old box
stays warm the rollback is live: flip DNS back and its MySQL is authoritative
again, which makes any second roll-forward another convert-and-verify. Deleting
the chain during the fallback window removes the tooling for the retry it exists
to support. So this waits out the ~1–2 weeks above, and goes with the
decommission itself.

**Two preconditions, because one of these is not recoverable.** Tag the cutover
commit, the way `pre-step-4-prune` holds the old search stack — `verify_data.py`'s
canonicalization encodes real knowledge about how a MySQL→Postgres port goes
wrong quietly (naive datetimes needing a timezone to be placed on the timeline,
booleans losing their sense, decimal scale, NULL becoming empty string), and that
should stay findable rather than resident. Then **archive the final snapshot**.
Git can reconstitute the tooling; nothing can reconstitute the data once the old
server is gone, and a data question six months later needs the dump far more than
it needs the scripts.

**What comes out** — narrower than it looks, since only two files actually bind
the driver:

- `mysqlclient` from `requirements.txt` and `requirements-docker.txt`, and
  `default-libmysqlclient-dev` / `default-mysql-client` / `pkg-config` from the
  Dockerfile. These exist for `tools/pgloader/verify.py` and `verify_data.py`,
  the only two files that `import MySQLdb`.
- The `db` service and the `mysql` profile from `docker-compose.yml`.
- The MySQL-sourced tooling: `verify.py`, `verify_data.py`, `convert.sh`,
  `sg101.load`, `crosscheck_dumpdata.sh`. Note that `convert.sh` and `sg101.load`
  read MySQL through pgloader rather than the driver, so they are dead by loss of
  source, not by loss of dependency.
- `DOCKER.md` §6 (MySQL, and switching engines) and §7 (Converting MySQL data to
  PostgreSQL) — the largest piece, and the one most likely to be left behind.
- **The four comments added 2026-08-02** to the requirements files, Dockerfile
  and compose, which argue for keeping this chain. They are correct until this
  moment and wrong immediately after, and they will read persuasively either way.

**What stays:** `compare_schema.py` imports only psycopg2 and compares a
converted database against a Django-built reference, both Postgres. It answers
"does this schema match what the migrations would build," which outlives MySQL
entirely. `post_convert.py` and `smoke.py` are Django-only; judge them on their
own merit rather than sweeping them up with the driver.

**Tests:** Post-deploy smoke checklist on the new host; monitor logs/error mail.
**Integration:** Final wiring of the whole system onto real infrastructure.
**Demo:** SurfGuitar101.com serving live traffic on **Django 5.2 / Python 3.12 /
PostgreSQL**, behind Cloudflare, with R2 media and provider email — off the
unpatched dedicated server.

---

## Notes on sequencing & safety
- **Shippable at every rung:** after any of Steps 6–14 the app is a
  coherent, testable increment; the project can pause without being stranded.
- **Optional early cutover (R14):** because the container is deploy-ready, the
  user *may* cut over after Step 14 (target reached) even before the subsystem
  polish of Steps 15–19, if they want the security/hosting win sooner. Default is
  deploy-at-end (Step 21).
- **Stubs always have a resolving step:** Step 8's temporary stubs (gcalendar,
  boto/media) are resolved in Steps 18 and 15 — no orphaned code.
- **Decisions resolved in-flight:** Postgres-vs-Xapian & DB specifics (Step 1),
  peripheral-app prune & wiki retirement (Step 19), host choice (Step 21).
