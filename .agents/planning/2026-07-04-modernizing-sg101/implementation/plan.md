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
- [x] **Step 13** — Python 3.7 → 3.10, then Django 3.2 → 4.2. **DONE 2026-08-09** (all nine tasks). **The interpreter moves first and is not optional** — Django 4.0 requires Python 3.8+, so the step cannot begin on the frozen `python:3.7` image; Step 14 used to own the Python move and cannot, being downstream of the rung that needs it. **3.10 rather than the 3.8 minimum**, because it is the only version Django 3.2 *and* everything through 5.2 support, which lets the interpreter move alone with `Django==3.2.25` untouched before any Django rung starts. **Measured 2026-08-02: the interpreter move costs exactly one dependency bump, and not one of the four this plan expected.** Every pin installs unmodified on `python:3.10` — `Pillow==6.2.2`, `mysqlclient==1.4.6`, `psycopg2==2.9.9` and `lxml==4.9.4` all build cp310 wheels from sdist. The real breaker is at import: **`bleach==3.1.5` cannot import on 3.10** (`cannot import name 'Mapping' from 'collections'`), so the long-deferred bleach bump becomes the gate. It is small — the pin comment calls 3.1.5 "the last line keeping the `styles=` kwarg," but both `_CLEAN_PROFILES` entries pass `[]` and neither allows a `style` attribute, so the kwarg is redundant twice over and modern bleach's default already does what it asks for. **Pillow is therefore decoupled from the interpreter**, and its `Image.ANTIALIAS` removal (7 call sites) should be its own change on its own evidence. **`mysqlclient` stays** (settled 2026-08-02): it looks like dead weight in a Postgres project, but `tools/pgloader/verify.py` and `verify_data.py` import `MySQLdb` to read both engines side by side — pgloader and the `mysql` CLI do the converting, and only the *verification* needs the Python driver. Dropping it would leave Step 21's fresh-snapshot conversion unverifiable, and since neither tool is in the suite, nothing would go red until the maintenance window. **EIGHT task files generated 2026-08-03** in `.agents/tasks/2026-07-04-modernizing-sg101/step13/` (01 interpreter + bleach, 02 the `RemovedInDjango40` backlog, 03/04/05 the Django rungs one apiece, 06 dependency alignment, 07 Pillow, 08 Markdown). Generating them corrected four things in the detail below — `is_ajax` is **4** sites not 7 (three matches are a same-named tag parameter) and `providing_args` is **2** not 3; `django.conf.urls.url` has **zero** usages so that rung item is free; the **Markdown bump is the step's largest single item**, since both custom extensions use the pre-3.0 API; and the six `ANTIALIAS` test assertions are mock-based and **cannot fail on this bug**. It also surfaced one thing the plan never had: **`USE_TZ` is not set anywhere in `sg101/settings/`**, so the site runs naive against Step 11's `timestamptz` columns — decided inside task 03. **Task 01 DONE 2026-08-03** (`cc0ea88`), pushed, CI green — the interpreter move cost *two* bumps, not one: bleach as predicted, plus `Pillow 6.2.2 → 9.5.0`, which installs and imports on 3.10 and then **aborts the interpreter at shutdown** (exit 134). **Task 02 DONE 2026-08-03** — the `RemovedInDjango40` backlog, 811 tests green with the warning promoted to an error. It corrected two more counts (`ifequal` is **19** across **7** files, not 17 across 6 — `ifnotequal` is not a substring of `ifequal`) and **found an item the inventory never had**: `Passing None for the middleware get_response argument`, 11 tests in 3 files, invisible to grep because it is triggered by an *absent* argument rather than a named API. Also settled: the 16 `from __future__` lines in migrations **are** in scope. **Task 03 DONE 2026-08-04** (`92c993d`), pushed, CI green — the 4.0 rung, on Django 4.0.10, 811 green and unchanged. Task 02's backlog work paid off: **not one application breaker**. The only failure was `django-tagging==0.5.0` importing `smart_text`, which fails at *import* so `django.setup()` aborts and zero tests run — a rung can look total and be three lines. **Vendored into the repo as `tagging/`** (Brian's call: vendor now, replace later; 0.5.0 is the final release and it breaks again at 4.1), keeping the app label and its three migrations so the 1,006 tags and 4,561 tagged items are untouched; **retirement scheduled into Step 19**, where a Postgres `ArrayField` is the more interesting candidate than `django-taggit`, since the content-type indirection exists to tag *any* model and this site tags one. **`USE_TZ` decided on evidence and set to `False` explicitly**: the `timestamptz` columns already hold correct absolute instants across the whole history, so turning it on is a settings change and **not** a data migration — but 79 naive builders, 3 `pytz.localize()` calls and 8 lines of month/year rollup make it cross-cutting behavior work, so it became **new task 09**, last in the step, on 4.2 with no version bump in flight. **Two plan corrections from reading 4.0's source:** the `USE_TZ` default flips in **5.0, not 4.0** (4.0 only warns, and only while unset), while **`USE_L10N`'s default *does* flip in 4.0** — measured a no-op here and deliberately left unset. **All 17 pytz sites audited and deferred to task 09** (`research/pytz-audit.md`), which corrected the plan's sequencing — nothing forces `zoneinfo` at 4.1, and the audit found that **`zoneinfo` cannot resolve the timezone names 93.6% of users have stored** (14,248 of 15,227 profiles, `US/Pacific` alone 12,619; also hardcoded at module level in `forum_tags.py:33`, so a naive swap breaks the forums for everyone). `CSRF_TRUSTED_ORIGINS` confirmed genuinely unset — no settings module reads it and there is no local-override hatch. The 4.1 `default_app_config` backlog is **9 apps, not the 1 recorded** — vendoring tagging cleared its own, leaving **8**. **Task 04 DONE 2026-08-04** — the 4.1 rung, on Django 4.1.13, **813 green (811 + 2 new), 85% coverage, and zero breakers**: the suite was green on the bump before any application code was touched, the project's second recorded no-op rung. **The 8-app `default_app_config` worklist turned out to be already dead** — Django has auto-detected a single `AppConfig` in `apps.py` since 3.2, and probing `apps.get_app_configs()` before *and* after the removal showed all eight already resolving to their own config class, so the lines came out as dead text. That removal is the rung's silent-failure shape: 4.1 does not error on `default_app_config`, it stops reading it, and a mis-placed config would leave `ready()` unrun and receivers unregistered with no warning. **Mutation-testing each app's `ready()` found the suite would not catch three of them** — `downloads`, `potd` and `weblinks` stay green with their signal wiring gone, though it maintains denormalized category counts, deletes files on delete, and keeps the photo-of-the-day sequence; recorded as a pre-existing coverage gap for Step 19, not fixed inside a version bump. **One deprecation, and only one of its three call sites was production code**: `{{ form }}` renders `default.html` (a proxy to `table.html`) which becomes `div.html` in 5.0 — `mod_forum.html` had been emitting `<tr>/<th>/<td>` into a `<div>` all along, markup the browser silently discards, which is why it looked fine; now renders the single field and its errors directly, and `MoveTopicForm`'s `hide_label` kwarg went with it. The other two were tests, one of which passed a whole form to a tag every real caller hands a single field. **The deprecation gate had been lying**: `-W error::django.utils.deprecation.RemovedInDjango50Warning` is silently ignored (`Invalid -W option ignored: invalid module name`), and a full 813-green run under it meant nothing; `-W error::PendingDeprecationWarning` works on 4.1 and was proven to fail on a known deprecation before being trusted — **task 05 needs a different filter**, since 4.2 promotes that warning to a `DeprecationWarning` subclass. **Search verified byte-identical on production data**, not merely green: 16 queries captured on 4.0.10 and replayed on 4.1.13 compare exactly equal on totals, all eight per-type counts, and top-20 ordering with `rank` to 10 decimal places; exclusion ranking still spreads across 5 distinct ranks rather than collapsing to a constant; 302 real headlines render `span` and nothing else. **Forms verified the same way** — 23 valid-and-invalid cases across registration, profile, private message, calendar event and move-topic, run on 4.1.13 and again on 4.0.10 in a throwaway container: identical verdicts, error codes and messages. 4.1's constraint validation has no surface here (one `UniqueConstraint`, no ModelForm, and nothing calls `full_clean()`). `CSRF_COOKIE_MASKED` deliberately unset — it exists for running two versions side by side during a rollout, and this site deploys once at the end. **Next: task 05**, the 4.2 rung. Nine task files now, task 09 added 2026-08-04. **Task 05 DONE 2026-08-05, pushed, CI green** — the 4.2 rung, on **Django 4.2.30**, **821 tests green**, `check`/`check --deploy`/`makemigrations --check` clean, full Step 13 smoke checklist run. Three breakers, **none of them application code**: `sqlparse==0.2.4` blocked the install (4.2's floor is 0.3.1) → 0.5.5, proven byte-identical through the debug toolbar's formatter; the **vendored `tagging` fork**, where 4.2 made an all-matching WHERE **raise `FullResultSet`** instead of compiling to empty SQL, 500'ing the news tag cloud; and `MemcachedCache` in `production.py`, **removed in 4.1**, so production settings had been unimportable for a rung and a half with nothing loading them to notice — **Brian chose to pull R21's memcached→Redis consolidation forward** (no new dependency: the Redis backend has been in Django since 4.0, so the design's "via `django-redis`" is stale; `python-memcached` dropped, leaving six required by html5lib and python-dateutil only). Beside the tagging fix, a **latent `add_filter()` arity break dating to 4.0** that no caller in the project reaches. **The predicted gate trap landed**: 4.2 promotes `RemovedInDjango50Warning` to a `DeprecationWarning`, so task 04's filter reports `OK` on a live 5.0 deprecation — demonstrated, not reasoned about. The working gate needs **both** warning categories plus **message-based** ignores (the module field matches the attributed frame, so `-W ...:pkg_resources` silently fails to bind), and **both halves were proven to fire before anything was recorded**. **The 5.x inventory for Step 14 is empty**, backed by a static sweep of the known 5.0/5.1 removals since a suite only covers what it runs. The gate also caught **17 Pillow `ANTIALIAS` failures** — the deprecation whose six assertions task 01 proved *cannot* fail, being mock-based — left for task 07. `STORAGES` adopted; the **admin theme toggle restored** on `/admin/login/` with two mutation-verified tests. **Search verified against 4.1 rather than against the record**, by replaying a 16-query probe on both versions against the same database — 16 totals, 128 per-type counts, 315 top-20 rows with rank to 10dp and 96 headlines all **identical**. The reason the recorded figures did not reproduce is that **a scratch smoke script deleted forum 3 and its 4,626 topics / 24,107 posts during this task**: `Forum.last_post` is a `OneToOneField(on_delete=CASCADE)` pointing the wrong way, so deleting the post a forum points at takes the forum with it — the hazard `tools/pgloader/smoke.py` guards against and a freshly-written script walked around. **Restored from the still-intact MySQL snapshot and verified**: every table back at its source count, the index back to 516,858 rows (Step 12's figure exactly), `reconcile_search` clean, 5 of 6 recorded search figures exact. It was **first written up as pre-existing drift, which was wrong** — a cumulative `n_tup_del` counter was allowed to answer a question about *when*. **Task 06 DONE 2026-08-07** — dependency alignment, **823 green (821 + 2 new), 86% coverage**, checks clean, Celery verified end to end, still Django 4.2.30 / Py3.10. celery/kombu went to the **current** line (5.6.3 / 5.6.2) rather than the 5.3 the task file named, which pulls **redis-py 3.5.3 -> 6.4.0** in with them (Brian's call, to collect the chain here rather than meet it at the interpreter move): kombu's runtime guard would not have raised on 3.5.3, but kombu 5.6 imports `CredentialProvider` and `sentinel` from redis under one `try/except`, so the missing `CredentialProvider` takes **sentinel down with it, silently, to None**. All three redis-py consumers verified (cache backend, application datastore, broker). **The `importlib-metadata` cap was already inert and had been since task 01** — kombu's shim tries `from importlib import metadata` first and on 3.10 that *succeeds*, so the pinned backport was installed and never imported; it came out as dead weight, not as a fix. What made the bump necessary is that `.get()` was reaching the **standard library's** `SelectableGroups`, removed in **3.12** — a Step 14 prerequisite wearing a Step 13 label. **psycopg 3 evaluated and declined**, on the structural reason rather than caution: the three `tools/pgloader/` scripts import psycopg2 directly, so it stays in the image either way and adopting psycopg 3 would mean running *two* drivers; psycopg2 went to 2.9.12 and the live search queries were replayed under 2.9.9 to prove the driver moved nothing. **six keeps its pin** (two requirers left, not four). Two pins whose comments named this work as their trigger came along: **debug-toolbar 3.2.4 -> 6.3.0** and **coverage <5 -> 7.15.4**. **The toolbar bump exposed a real defect it did not cause**: importing a settings module reconfigures the running one, because `from base import *` binds base's own mutable objects and both `local.py` (MIDDLEWARE/INSTALLED_APPS) and `production.py` (TEMPLATES) edited them in place — 105 errors once the toolbar shipped a model, and `production.py`'s half had been silently changing template loading mid-suite without ever going red. `local.py` fixed by copying, with a mutation-verified test; **`production.py`'s block was deleted outright** — Brian asked why it still dropped `APP_DIRS`, and measuring both engines showed the five lines reproduce a Django default exactly (`Engine.__init__` wraps in `cached.Loader` by itself when debug is off, and the `del` was only ever the price of hand-specifying `loaders`), so production.py now does no in-place mutation at all. **Found and deliberately not fixed:** `production.py` and `local.py` still declare `django.db.backends.mysql`, five steps after the PostgreSQL move — a deploy decision, recommended into Step 21. **Next: task 07** (Pillow and `ANTIALIAS`). **Tooling added 2026-08-05** (Brian's suggestion, out of the deletion above): `tools/pg_snapshot.sh` — `dump`/`list`/`restore`/`scratch` PostgreSQL snapshots, DOCKER.md §8, and a "take one first" note in the remaining task files. **Round trip exercised, not just written**: dump 8s/128MB, full restore ~1min with every row count identical, `reindex_search` 1m35s back to 516,858 documents, sweep clean, smoke 35/35. The index is dumped schema-only — 1,104 MB of the 1,681 MB database, and derived. The `scratch` mode is the one that matters: restore tables into a scratch database beside the real one and `\copy` rows across, which keeps column types intact where the cross-engine copy had to reconstruct them by hand. **Task 07 DONE 2026-08-08** (Pillow): `Pillow==9.5.0` -> **12.3.0**, current line, Brian's call from three clean candidates. The seven call sites now name `Image.Resampling.LANCZOS`. **The used PIL surface was diffed empirically across 9.5.0 / 10.4.0 / 11.3.0 / 12.3.0 rather than read off a changelog, and is identical throughout** except `ANTIALIAS` itself; **thumbnail output is byte-identical too, so the drift measured over 6.2.2 -> 9.5.0 did not recur** and the tolerance AC4 asks for was never needed. **The task's real find is a coverage hole it predicted but under-counted:** reverting the constant in `core/images/upload.py` *together with* its mock assertions left 41 tests green while a real upload raised `AttributeError`, and `ssl_images.resize_image()` was wholly uncovered — 201 tests stayed green with it reverted. Closed with 29 real-`PIL.Image` tests (853 green, from 824). All five mutations now fail. **Task 08 DONE 2026-08-08** (Markdown): `Markdown==2.6.11` -> **3.10.3**, **872 green (853 + 19)**, checks clean, site and worker and beat smoked. Both custom extensions ported to the 3.x API, and **a third consumer the plan never listed** — `ssl_images` borrowed Markdown's own `IMAGE_LINK_RE`/`IMAGE_REFERENCE_RE` and indexed groups 1 and 8 out of them, but 3.0 replaced regex link parsing with hand-written bracket matching so both constants are now just `\!\[`; 14 tests failed with `IndexError`, and the command now owns the patterns, rebuilt byte-identical to 2.6.11's. **The `'>not_strong'` priority was re-derived from output**, not transliterated: rendering all 1,516 `---`-bearing corpus posts at 35 priorities shows **61..119 all reproduce the archive**, above `autolink` (120) URLs containing `---x---` get struck through and their href corrupted, and at or below `em_strong` (60) emphasis claims the hyphens first. **76 of 6,001 real documents render differently and a control run proves none of it is ours** — stock Markdown with both extensions unloaded flags the same 62 post ids exactly; archive-wide the rate is **0.33%, 1 in 300**, four fifths of it Markdown 3.3's emphasis conformance fix (`**bold **` with a trailing space is now literal), and stored HTML means it only surfaces when a post is edited. **The caching the plan asked for was measured and NOT done**: the parser build is 0.047 ms of a 0.737 ms render, rendering is a write path at ~36 renders/day, so caching buys **~6 ms/day** — and in production the *smiley* regex build (0.128 ms from Redis) is 2.7x the parser's, so dev profiling points at the wrong half. A shared instance leaking a `[secret]: url` definition from one post into the next was reproduced. **`Markdown.convert()` now calls `reset()` (0.0002 ms) instead**, making an instance safe to hold for the bulk re-render where caching would actually pay (~19% of such a job). **The `MARKDOWN` logger stays in `local.py`** — still 4 DEBUG records per parser build on 3.10.3, and local's root is DEBUG — and is **inert in `production.py`** where root is INFO; both now say which they are. **Task 09 DONE 2026-08-09** (`USE_TZ`), which closes the step: **884 green (872 + 12)**, green again under `-W error::RuntimeWarning`, checks clean, and a before/after characterization on the production snapshot showing no displayed time moved. **No stored value was rewritten** — Step 11's `timestamptz` columns already held correct instants, so this was a settings change and not a data migration. **The premise it was scoped on was wrong**: the month rollups do *not* resolve in UTC when nothing is activated, they resolve in `TIME_ZONE`, so they were already correct and the real hazard is that they follow any zone that *is* activated — which ruled out this plan's own suggestion of activating the user's timezone in middleware, and made Brian's choice of explicit `timezone.localtime()` in the tag the one that keeps donations reporting the same totals to every reader. The five rollups are pinned with `ExtractYear/ExtractMonth(tzinfo=...)` rather than `timezone.override()`, because the querysets are lazy and an override can exit before the SQL runs. **The `RuntimeWarning` gate carried the task** — 148 errors to 0 — and **two of the pytz audit's three "hard" cases dissolved rather than being solved** (`common_timezones` was never a runtime dependency, and `NonExistentTimeError` sat in a 2019 shim whose timezone lines discarded their return values); **`pytz` is gone from the project**, `tzdata` pinned in its place. Three latent host-clock-dependent bugs fixed in passing, a fourth (**PayPal `payment_date` truncation**, all 1,421 donations stored 2 hours early) deferred to Step 19. **Next: Step 14** — Django 4.2 → 5.2 LTS, Python 3.10 → 3.12.
- [x] **Step 14** — Upgrade Django 4.2 → 5.2 LTS (Python 3.10 → 3.12) ⭐ target reached. **SIX task files generated 2026-08-12** in `.agents/tasks/2026-07-04-modernizing-sg101/step14/` (01 Python 3.12 base image, 02/03/04 the Django 5.0/5.1/5.2 rungs one apiece, 05 dependency alignment, 06 the host venv). Two scope calls: **the interpreter moves first and alone** with `Django==4.2.30` held — 3.12 is again the version supported by both the current and target Django, so Step 13's shape repeats — and **the venv is in scope**, written last so it can be cut. Generating them measured four things the detail below did not have. **The 3.12 move costs no dependency bumps at all**, the reverse of Step 13's interpreter move: the whole pin set installs, imports *and* exits 0 on 3.12 with Django untouched, because task 06 aligned to the current line rather than the minimum that worked. **`mysqlclient==1.4.6` still builds** despite 3.12 removing `distutils` and the slim image shipping no `setuptools`, because PEP 517 build isolation supplies it — recorded so a future build failure is not "fixed" with a global setuptools pin. **Two pins are dead weight**: `html5lib==1.1` and `simplejson==3.17.6` have zero requirers and zero imports, `html5lib` orphaned since bleach dropped it at 6.4.0 in Step 13 task 01; dropping it leaves `six` with one requirer (`python-dateutil`, via celery) so six still does not leave the image. **5.1's positional-`Model.save()` deprecation is a non-item** — all ten positional `.save(` hits are `PIL.Image.save()` or `FieldFile.save()`. And **5.0's form-renderer change has zero surface**, since all six whole-form renders are explicit `as_p`/`as_table` and the one `as_table` is correctly inside a `<table>`. The **vendored `tagging` fork** is threaded through all three rung tasks as the first place to look: `tagging/models.py:178-186` is the only private-SQL-compiler consumer in the tree and has broken on two of the last three rungs, and only the news tag cloud reaches it. **Task 01 DONE 2026-08-12** — `python:3.12` (3.12.13), Django held at 4.2.30, **884 green, and the predicted zero dependency bumps held**: the image built on the first `FROM` edit with nothing else touched. The suite got *faster* (13.03s → 11.62s) and the cold build moved 26.05s → 28.70s, the whole +2.65s being `simplejson`, the one pin with a cp310 wheel and no cp312 wheel — and one of the two orphans task 05 drops. Celery was verified end to end (transport resolved, tasks round-tripped the real broker, beat up), which is the `SelectableGroups` payoff Step 13 task 06 paid for in advance. A whole-tree compile sweep found **zero invalid-escape `SyntaxWarning`s** but did find **five `tools/` scripts still written in Python 2** — pre-existing, since Step 7's `py_compile` claim covered app and migrations only, and now **scheduled into Step 19** as triage rather than porting. **Task 02 DONE 2026-08-13** (`0713e15` + `8aacd65`) — **Django 5.0.14, 884 green under a gate proven to fire, zero breakers and zero dependency bumps**: the suite was green on the first run with no fixes, which is what the empty 5.x inventory from Step 13 task 05 predicted. Search and the vendored `tagging` fork are byte-identical to captures taken on 4.2 before the bump against the same database, and the admin's `site-name` is now a `<div>` with exactly one `<h1>` per page. **All the work was in the gate**: 5.0 re-parents on schedule, so the 4.2 filter's *shape* survived — a first — but **all four of its ignores are dead where the task predicted two**, the celery pins from Step 13 task 06 having quietly retired the other two. Four new ignores replace them and **three are Python 3.12/3.14 deprecations from third parties** (`repoze.timeago`, `dateutil`, `django-environ`), invisible until now only because the gate last ran an interpreter ago — **task 01 moved Python without running it**, so a gate skipped for one rung hid everything that rung introduced. Two of the three retire with task 05's bumps, which is also when putting the gate in CI becomes worth doing — **now written into task 05 as requirements 9–11 and ACs 9–10 rather than left as prose**, since a recommendation carried in two write-ups and named in no task file is one nobody is obliged to do. The one code decision was `forms.URLField`'s implicit scheme: **the transitional `FORMS_URLFIELD_ASSUME_HTTPS` announces its own deprecation, so it relocates the warning rather than clearing it**, making both available paths cost exactly one ignore and reducing the choice to pure behavior — Brian took https now. Asking about it surfaced the `weblinks` add form, **scheduled into Step 19**. **Task 03 DONE 2026-08-13** — **Django 5.1.15, 884 green under a re-proven gate, a second free rung and this one predicted**: no breakers, no dependency bumps, no application code, the only edits being version strings in comments. Every 5.1 removal re-swept to zero (`CIText` family, `index_together`, `make_random_password`, `length_is`, `get_storage_class`, the two storage settings), and no positional `Model.save()` warnings, which the gate settles better than the grep could. **The task file's gate prediction was wrong and the correction is the finding**: 5.1 does *not* re-parent `RemovedInDjango60Warning`, because 6.0 is two releases away from 5.1 rather than one — the pattern held and only the arithmetic was off, so **the re-parent lands at 5.2**. On 5.1 the near class is named generically (`RemovedInNextVersionWarning`, since there is no `RemovedInDjango52Warning`) and **nothing raises it — 5.1 schedules zero removals for 5.2** — so the gate's `DeprecationWarning` half has nothing Django-side to catch here and its probe had to be synthetic. `production.py` was checked from both directions, since `check --deploy` proves the import and not that the `STORAGES` backends resolve; both do. **Pushed and CI green 2026-08-13.** Two things surfaced right after, both recorded: **logging out had been broken since the 5.0 rung** (Django 5.0 removed logout-via-GET, both navbars used a plain link, every Logout answered 405) — fixed in `39aceca` with three mutation-verified tests, and the reason nothing caught it is that **no test had ever requested that URL**, so a warning the 4.2 gate would have failed on never fired; and the **ORDER BY collation** difference Brian noticed on the member list, audited in `4d5104a` and scheduled into Step 19. The logout fix also exposed that **the v3 Sass toolchain cannot be rebuilt**, now written up under Step 20. **Task 04 DONE 2026-08-15 — TARGET STACK REACHED**: **Django 5.2.17 LTS / Python 3.12.14 / PostgreSQL 16, 887 green** under a gate proven to fire, checks clean, all 17 site pages hash-identical to 5.1 captures, search and the `tagging` fork identical for the third and fourth rung running, full smoke green. A third free rung on the application side — no breakers, no application code — with `django-debug-toolbar 6.3.0 -> 7.1.1` the only dependency move, and it is a dev dependency whose pin comment had **named this exact rung as its trigger** (7.x requires `django>=5.2`); the constraint now runs the other way, since 7.1.1 will not install against 5.1. **The predicted gate trap landed for the fourth time and in the silent direction**: 5.2 re-parents `RemovedInDjango60Warning` to `DeprecationWarning` and introduces `RemovedInDjango61Warning` as pending, so the inherited filter's `FORMS_URLFIELD_ASSUME_HTTPS` ignore — spelled `PendingDeprecationWarning` — stopped binding and aborted the run at settings load; the fix is one category word, and **both halves were then proven live with real Django warnings for the first time** (`format_html()` no-args and `StringAgg(ordering=)`), run against the full ignore list and again without the gate. **The Django 6.0 inventory is EMPTY and both legs are stated**: the gated suite emits exactly one Django warning, our own deliberate `FORMS_URLFIELD_ASSUME_HTTPS`, and a static sweep covers **32 deprecation points AST-extracted from the installed 5.2.17** rather than recalled — zero hits everywhere, the only near-miss being two `UniqueConstraint`s that are keyword-only. **The page probe turned out to have been measuring the debug toolbar for two rungs** (its payload carries timings and a request id, and the probe also picked its member by `-last_login`, which `force_login()` itself sets); stripping the toolbar made `/admin/` report its true 302, and a newly added per-page sha256 immediately caught the forums index coming back **same length, different hash** — a constant-width wall clock, proven to be the entire difference by rebuilding down to 5.1.15 and back. One dead setting removed (`JQUERY_URL`, inert since Step 13 task 06, and **nearly recorded backwards because a `grep | head` pipeline always exits 0**). **The toolbar's `RedirectsPanel` is disabled and the middleware moved to index 0** — Brian's call, after noticing 7.x ships a History panel and warns the Redirects panel is deprecated; both observations were right, and the deprecation message names HistoryPanel as its own replacement. The finding underneath is that **the toolbar disables `RedirectsPanel` and `ProfilingPanel` by default, so this project's `DISABLE_PANELS: set()` was not "leave the defaults alone" but "turn both on"** — the interstitial that made the middleware position load-bearing for years was self-inflicted config, the mirror of the `JQUERY_URL` key in the same block (one silently reproduced a default, the other silently overrode one). Measured in both directions with a control (panel re-enabled at index 0 reproduces the interstitial), and **the authors' rule was read rather than recalled**: the docs ask for it as early as possible with one exception, content-encoding middleware, which is also the only ordering rule `check_middleware()` enforces — so index 0 is correct here and **adding a GZipMiddleware later is the one thing that would change that**. The move is also what makes redirect monitoring honest: from index 1 the toolbar sits inside `CommonMiddleware` and an `APPEND_SLASH` request records as the inner 404 it really is, never reaching the panel; from index 0 HistoryPanel records the 301. All 17 pages verified identical between the two positions. **A third volatile element in the page probe surfaced here** — Who's Online is Redis-backed with a TTL and fed by the probe's own `force_login()`, so the capture was perturbing what it measured, one layer below the `-last_login` bug; normalized. **Task 05 DONE 2026-08-15** — final dependency alignment, **887 green under the gate**, checks clean, smoke 35/35, worker and beat clean. Two orphan pins removed (`html5lib`, `simplejson`) after verifying by removal rather than grep; seven never-moved pins bumped one at a time with the suite between each (`django-environ` 0.4.5→0.14.0, `python-dateutil`→2.9, `lxml`→6.1.1, `requests`→2.34.2, `ftfy`→6.3.1, `docutils`→0.23, `testfixtures`→12.3.0), **none of which broke anything**; and the `mock` backport removed outright rather than bumped (Brian's call — 30 test files to `unittest.mock`, proven by the package being *absent* from the image, so a missed import cannot pass). **psycopg 3 re-decided, not inherited**: still deferred, because all three `tools/pgloader/` scripts still import psycopg2 directly and the Step 21 cutover that would retire them has not happened. **The `html5lib` story is older than the task file had it** — bleach had already vendored html5lib by 3.1.5, so the pin was a fossil of the pre-vendoring era rather than of Step 13 task 01 (Brian recalled the bleach connection independently). **`lxml` got a back-comparison** over 210 real fragments + 10 edge cases because two uncovered management commands slice `tostring(root)[5:-6]` by index — identical on both versions, **but the corpus turned out not to exercise the risky line at all** (every real fragment passes through unchanged), so the slice is covered only by the synthetic nested-div case: a probe over real data can still miss what it was written for. **The gate caught a deprecation this task itself introduced** — docutils 0.23 deprecates `writer_name=`, which `make_fixed_page` passed — which is the argument for the gate in one line. **The gate now runs in CI** from `tools/deprecation_gate.sh`, one source for CI and developers, using `PYTHONWARNINGS` (demonstrated: a child process exits 0 under `-W` and 1 under `PYTHONWARNINGS`) passed in with `-e` because the suite runs under `docker compose run`. **The ignore list is down to two**, both retirements earned by this task's bumps and confirmed absent from an unfiltered inventory, both survivors re-proven by deletion. **Next: task 06** (host venv), which closes the step. **DONE 2026-08-15** (all six tasks). Task 06 closed it: `.venv` on Python 3.12.14 matching the image, `pyright` errors 892 -> 241, `django-types` chosen over `django-stubs` because the latter needs a mypy plugin pyright cannot run, `.tool-versions` committed, 887 tests still green. Four of the task file's premises measured wrong; see STATUS.
- [x] **Step 15** — User photo uploads → back to S3 (boto3). **DONE 2026-08-16, all five tasks.** **RESCOPED 2026-08-15, direction reversed: R2 is out.** The `/pdd` session chose R2 believing S3 was unusable; the real cause was Py2.7 TLS against AWS's TLS 1.0/1.1 deprecation, and Steps 13-14 already fixed it. The buckets never went away and still serve reads. Measured: 26,331 `user_photos.Photo` rows storing absolute URLs, split 21,754 on S3 (to 2023-05-07) and 4,577 on local disk (from 2023-05-08). **NOTHING migrates in this step** (revised 2026-08-15, superseding an earlier draft that had the 4,577 local files moving into the bucket): rewrites made in dev cannot survive Step 21's fresh production snapshot, the local set keeps growing until the DNS flip, and production's Py2.7 cannot perform the upload — so the 4,577 ride Step 21's media rsync and their URLs keep working because the new host serves the same path. Consolidating them into S3 is optional, windowless, and post-cutover. Also carries: retiring `ssl_images` on seven counts of evidence (-42 tests, and its `gen_key()` Py2 bug dies with it; `make_key()` was already correct), and rewriting `core/tests/test_s3.py`'s 5 boto-v2 mocks for boto3. **`sg101.forum.photos` must keep serving regardless** -- 15,690 posts embed its URLs. Local `/media` deferred to Step 20, with `downloads` (716 MP3 rows) the only part worth revisiting. **FIVE task files generated 2026-08-16** at `.agents/tasks/2026-07-04-modernizing-sg101/step15/` (01 retire `ssl_images`, 02 the boto3 rewrite, 03 settings/env + the upload flip, 04 the delete path, 05 the S3 smoke tool). Reading the code first corrected six things: the **credentials were already env-driven since Step 3**, so only bucket/base-URL/region remain (and the region is not a setting at all -- it is a default argument in `S3Bucket`'s signature); `USER_PHOTOS_LOCAL_UPLOAD = True` is **committed** at `production.py:74`, so the flip is one tracked line, though the Step 21 working-copy audit still stands on its own reasoning; **deleting a photo raises on this branch today**, since `user_photos/s3.py:20` builds the bucket before reading any URL and all three call sites are unguarded -- invisible for six steps because all three tests mock `delete_photos`; **`delete_keys()` miscounts** and its existing test pins the bug, which once boto3 works would delete a local photo's row, leave its file, and log success; 42 `ssl_images` tests confirmed (887 -> 845); and `HOT_LINK_PHOTOS_*` retire with the command while `USER_IMAGES_SOURCES` stays. `ssl_images` goes **first**, since removing an `S3Bucket` consumer narrows the API task 02 must hold fixed. Brian's calls: **`unittest.mock` over `moto`** (no new dependency -- so the suite cannot catch a wrong boto3 kwarg or the miscount, making task 05's real-bucket run load-bearing and every new test mutation-verified), and **task 04 unlinks local files** rather than skipping them, which is the delete path working rather than a migration. Verification is a **tool, not a test**: `tools/image_smoke.py` already drives real uploads and its docstring already names the S3 gap, so it gains an opt-in `--s3` branch -- CI has no AWS credentials and should not, what is verified is environmental rather than behavioral, and **Step 21 must rerun exactly this on the new host before the DNS flip**. **TASK 01 DONE 2026-08-16** (`afe32ca` + `cc9bb99` planning, PUSHED, CI GREEN): `ssl_images` retired, **887 -> 845**, gate green, checks clean, 1,045 lines deleted. The evidence re-verified stronger than recorded — the last commit touching it (`69717f7`) is dated **2015-11-27, the same day as production's cache file**, so the code's last change and the tool's last completed run agree from two independent directions. **The orphan sweep found nothing**: `core/download.py` and `core/functions.py` keep live callers in `user_photos/forms.py`, and the four models were used through stock fields only. The bucket was verified still serving (HEAD 200 `image/jpeg`; a real post renders with the URL present, in a rolled-back transaction). `HOT_LINK_PHOTOS_*` retired; `USER_IMAGES_SOURCES` kept and commented — **Brian caught that the first comment was ambiguously placed**, since `s3.amazonaws.com` (`sg101.forum.photos`, write-retired) and `s3-us-west-1.amazonaws.com` (`sg101.user.photos`, which **task 03 starts writing to again**) are both in that list; it now names both and states the invariant task 03 must preserve. **That invariant was stated wrongly on 2026-08-16 and corrected in task 03 after Brian queried the wording**: `USER_IMAGES_SOURCES` is the whitelist of hosts *user-authored content* may reference in `<img>` tags, enforced by `core.html.image_check()` at submit time. The gallery and detail pages render the stored URL directly and are unaffected by it, so a mismatch is **not** "uploads fine, fails to display" — it is a photo that uploads, appears in its gallery, and then cannot be **posted**, because the markup the detail page hands the member is rejected as "Invalid image source". **TASK 02 DONE 2026-08-16** (`219e4be` + `1609fca` planning, PUSHED, CI GREEN): `core/s3.py` rewritten on **`boto3==1.43.72`**, the Step 8 stub resolved, **845 -> 851 and the suite now has zero skipped tests**; gate green with no new warning, checks clean (`check --deploy`'s `security.W001` is pre-existing, verified at HEAD, and belongs to Step 20). Neither caller changed. **`client` not `resource`**, chosen for mock-call-list legibility, which given the no-`moto` decision *is* the coverage. **THE FIND: `DeleteObjects` caps at 1000 keys and boto3 does not chunk where boto v2 did** — and three members own enough photos to exceed it in one delete (largest 1,233 photos = 2,466 keys), reachable from the admin bulk action and antispam deactivation, so a naive port would have passed every test and failed on exactly those accounts. **The `delete_keys` miscount is fixed here**, not deferred: it returns what was deleted from this bucket and the test asserts 2 where the old asserted 3, leaving task 04 to sum S3 against local. **All 17 mutations caught** — including one that first reported "pattern missing" because my replacement string didn't match the source, correctly scored as a hole rather than a pass. URL format verified against a real snapshot row, not a test literal. **TASK 03 DONE 2026-08-16** (`816b95a` + `4576e28` planning, PUSHED, CI GREEN): `USER_PHOTOS_BUCKET` / `BASE_URL` / a new `USER_PHOTOS_REGION` are env-read with the old hardcoded values as defaults, both call sites pass the region explicitly, and **`production.py` sets `USER_PHOTOS_LOCAL_UPLOAD = False` — uploads go to `sg101.user.photos` again**. 851 -> **854**, gate green, checks clean, **all 11 mutations caught** (mutation testing found a hole in my own tests: only the base URL's env read was covered, so hardcoding the bucket back passed). Settings now **refuse to boot** if the upload host is missing from `USER_IMAGES_SOURCES` — a hard raise rather than a system check, since `core` has no `apps.py` and adding one exceeds a settings task's blast radius. **Found mid-task: `docker compose build web` rebuilds only `sg101-web`, and `restart` reuses the old image**, so worker and beat ran without `boto3` and crashed at import while the suite stayed green — Step 6's "boot worker and beat" lesson recurring, and a live demonstration that task 02's removal of the import guard fails loudly as intended. **TASK 04 DONE 2026-08-16** (`b324774` + `d7eb7f3` planning, PUSHED, CI GREEN): `delete_photos()` now routes each URL to the backend holding it — S3 to the bucket, local to `os.unlink` under a `realpath` containment guard — building the bucket only when there is something in it to delete, and counting files actually removed across both. 854 -> **866**, gate green, checks clean, `image_smoke.py` 7/7, snapshot data intact at 26,331 photos. Module renamed `user_photos/s3.py` -> `storage.py`; `core.s3` gained `bucket_url_prefix()` so both modules share one definition of "a URL in this bucket". **All 13 mutations caught, after mutation testing found two holes in my own tests** (the blank-URL and empty-key-name cases each passed whether or not the code was right). **Brian caught a fabricated justification**: I had written into a comment *and* a test docstring that rows predate the https move and that `www.` forms occur, having measured neither — **all 52,662 URLs are https on exactly two hosts, no `http:`, no `www.`**. Path-based matching is still right, but because `SITE_SCHEME` and the `Site` row make scheme and host environment-dependent (dev writes `http://`), not because the archive is mixed. Also found: **`assertLogs` is useless in this suite**, since `settings/test.py:15` disables logging globally. **⭐ TASK 05 DONE 2026-08-16 — STEP COMPLETE** (`5576aa7` + `52cb62f` planning, PUSHED, CI GREEN): `tools/image_smoke.py` gained an opt-in `--s3` round trip, **12/12 against the real bucket** (7/7 default unchanged). **The step's open question is answered: the credentials still authenticate after three years dormant, and `public-read` still succeeds** — HTTP 200 fetched with no credentials, so no Block Public Access or bucket-owner-enforced ownership; metadata survives; `delete_photos` removes both keys via the app's own path. **The first run failed 8/12 because `UploadForm.save()` returns an existing `Photo` on a matching image signature**, so reusing the local checks' bytes uploaded nothing — and the delete check *passed anyway*, since refetching a local path production does not serve returns 404, indistinguishable from a deleted S3 object. Fixed with distinct bytes, a new-row assertion and an early bail. Interrupted-run cleanup exercised deliberately, not assumed. **Bucket measured: 43,511 objects / 1.78 GB / 2013-09-02 → 2023-05-07** — its newest object is the cutover date, a third independent confirmation of the local-upload switch, and **3 orphaned objects** against 43,508 stored URLs, predating 2023 and consistent with the silent-failure delete that task 04 fixed.
- [ ] **Step 16** — Email → transactional provider. **Provider decided 2026-08-16: Postmark Basic, $15/mo**, on volume (**re-measured 2026-08-17: ~900/mo typical, ~1,675 peak month, ~30/day, peak day 207** — superseding an inferred "~1,000–1,800/mo, peak day 239") and on a diagnosis that only came out of auditing the live host — reverse DNS stopped forward-confirming when the apex A record was proxied by Cloudflare, the HELO hostname is a dead domain with no MX or SPF, and no DMARC record exists anywhere. **NINE task files** in `.agents/tasks/2026-07-04-modernizing-sg101/step16/`: 01 settings→env (finds `SERVER_EMAIL` unset, i.e. error mail from `root@localhost` that Postmark will reject), 02 the Postmark backend (whose substance is that a local MTA was a durable retry queue and an external provider is not), 03 the DNS remediation, 04 **delete** email-a-friend (Brian's call; hardening was the earlier plan), 05 the verified email change carried from Step 11, 06 inbound → Cloudflare Email Routing, 07 the smoke tool whose acceptance criterion is an Outlook inbox rather than a green suite, 08 `secrets`-based tokens, 09 per-send logging. Also corrected here: password reset uses Django's stock `PasswordResetView` and does **not** go through the site's mail wrapper or Celery. **Deliverability is worse than the audit found, measured 2026-08-18: Comcast refuses every message from `173.255.245.115`** (`554 … found on one or more DNSBLs`, their internal list — the IP is on none of six public ones), with 23 site notifications to a single member queued behind it and expiring at Postfix's 5-day limit. The Outlook capture's reading of "authentication perfect, reputation neutral" understates it: one major consumer ISP is refusing outright. Delisting request tracked in task 10; it is also the sharpest argument for moving member mail onto Postmark's IPs sooner. **Task 03 partially executed 2026-08-17** (started first for its mandatory week-long DMARC wait): `_dmarc` published at `p=none` with a Cloudflare `rua` — the reporting clock starts here — Postmark's DKIM and Return-Path verified, `mail.surfguitar101.com` unproxied to the Linode IP, `smtp_helo_name` aligned; the PTR was accepted by Linode but had not propagated at end of session. **Four audit claims corrected against measurement**, the headline being that **Postmark issued a 1024-bit DKIM key**, not the 2048-bit one the plan promised. **Tasks 01 and 02 done 2026-08-17** (`b5b5686`, `72e823d`, `7f316dd`, `d7fefb5`, pushed, CI green): mail settings moved to the environment — which found `SERVER_EMAIL` unset, i.e. `AdminEmailHandler` error mail sent from `root@localhost`, and `EMAIL_TIMEOUT` unbounded — and the backend task, **whose diff contains no provider-specific code at all**, since the cutover is now environment variables. Its substance was retry with jittered backoff and permanent-vs-transient classification (the `except` order is the mechanism: `SMTPRecipientsRefused` subclasses `SMTPException`), and **routing password reset through the site's mail wrapper**, which no site email had done. Delivery-side criteria — real send, header proof, rollback demo, SPF rewrite — are unmet by design and belong to the cutover. **Tasks 04, 08, 09 and 05 done 2026-08-18/19/21/22**: email-a-friend deleted, registration tokens moved to `secrets` (which found the confirm route rejecting the very tokens it now mints), one log line per email carrying the send's outcome, and the Step 11 REVISIT closed — an email address change is now confirmed from the new address before it takes effect. **951 tests green.** **Task 06 DONE 2026-08-23/26**: inbound mail for both zones is Cloudflare's -- `surfguitar101.com` in Phase 1, `themadeira.net` in Phase 2, **7 of 7 addresses confirmed end-to-end, tested per address rather than sampled**; only Phase 3 (Postfix keeps *receiving* on jaguar for a week past the 08-25 flip, since senders cache MX beyond the 300s TTL) remains. **Task 07's tooling DONE 2026-08-26** (`4d77b672`, pushed): `tools/email_smoke.py`, `tools/live_mail.sh` and 21 tests, **951 -> 972 green**, and **the acceptance criterion for the whole step is met** -- a message built by the site, sent through Postmark, landing in an Outlook **inbox** (`dest:I`) with `spf=pass dkim=pass dmarc=pass compauth=pass`, Return-Path aligned on `pm-bounces.surfguitar101.com`. **Two corrections this produced.** The `Message-ID` finding is closed **by substitution, not repair** -- Postmark rewrites the header to `@mtasv.net` while Django still builds one from the sending host's FQDN, which is exactly what task 07 requirement 11 predicted a pass here would mean. And **the SCL comparison this step planned to judge the move by is still open**: the capture reads `SCL=-1`, which is not an improvement on the baseline's 3 because it is not a score -- Exchange stamps -1 when filtering was *skipped* because the receiver already trusts the sender, and that mailbox has been receiving these tests since 08-17. Closing it needs a Microsoft address that has never been told to trust this sender. Remaining: task 06 Phase 3, the SCL measurement, and the two-week bounce-dashboard watch that replaced the graduated warm-up (dropped 2026-08-20 on measurement). **The DMARC reading item is closed — corrected 2026-08-30, this line had been carrying it as outstanding since before it was answered.** The twelfth reading ran 2026-08-27 and did not settle it cleanly: two of three reports read `p=quarantine` and `yahoo.com` read `p=none` from the same filing run, which the thirteenth reading resolved as a per-receiving-domain cache lag in `policy_published` rather than a fault in the zone. `p=quarantine` is now live at five reporting organizations and eleven reporting endpoints. Every row in every report is `disposition=none`, and **exactly one message in fifteen readings aligned on neither mechanism** — a forwarded message on 2026-08-26 that Google delivered under a discretionary forwarding exemption, which is the open exposure against `p=reject` rather than a fault in the configuration. The log is at **fifteen readings** in `research/dmarc-readings.md`.
- [ ] **Step 17** — reCAPTCHA → Cloudflare Turnstile, on contact **and registration**. **Re-scoped 2026-08-27:** the cost rationale is dead (71 assessments in the busiest month vs a 10k cap); proceeds on privacy and friction. **Tasks 01 (helper), 02 (contact form), 05 (the log file and the no-token line) and 03 (registration widget) done**; 02 removed the last reCAPTCHA reference from the codebase 2026-08-28, and 03 put the widget on registration stage one 2026-08-29 while removing nothing. **Task 04 done 2026-08-30** — registration is `register` -> `thanks` plus the emailed confirmation, and the browser pass on it is done. *(An earlier version of this line said task 04 retires "both honeypots"; it retires `question1` and `question3`, the visible one, and keeps `question2`, the hidden one, which the layer measurement made the best discriminator of the five.)* **What remains is the *after* measurement, which cannot exist until the Step 21 cutover.** The *before* was read 2026-08-30 from `UserProfile.status` — 1,601 spam deactivations back to 2011, corroborating ~1.4/month — and was never perishable: it was recorded against `sg101.log`, which holds none of it
- [ ] **Step 18** — Revive `gcalendar` with modern Google libraries
- [ ] **Step 19** — Retire `wiki`/MoinMoin; verify-then-prune `banners`/`oembed` (`contests`/`countdown`/`bandmap` confirmed KEEP 2026-07-24; `membermap` already pruned in Step 4). Also carries: the `elsewhere` rework, the `last_post` CASCADE hazard, retiring vendored `django-tagging`, the `downloads`/`potd`/`weblinks` `ready()` coverage gap, and — added 2026-08-07 from Step 13 task 06 — the **settings-module cleanup** (extract `LOGGING` to its own module; move the search-logging assertions onto the subprocess helper), and — added 2026-08-09 from Step 13 task 09 — the **PayPal `payment_date` timezone truncation** (the IPN handler discards PayPal's `PST`/`PDT` instead of converting it, so all 1,421 donations are stored 2 hours early; 5 rows would change month, 0 would change year). Also carries the **timezone dropdown** (`static/js/timezone.js` is frozen 2010 pytz data and the form field behind it is a hidden free-text `CharField`, not a choice field — leave it, regenerate it, or move the choices into Python), and — added 2026-08-12 from Step 14 task 01 — **five `tools/` scripts that are still Python 2 and compile on no Python 3** (`filter_posts.py`, `flag_data.py`, `load_ygroup.py`, `post_sub.py`, `translate_yahoo_group.py`; pre-existing, since Step 7's `py_compile` claim covered app and migrations only — nothing imports them, three feed the `mysqlimport` path Step 21 retires, and `flag_data.py` is the one plausible survivor, so the work is triage rather than porting). Also carries — added 2026-08-15 from Step 14 task 05, **corrected the same day** — **replacing `repoze.timeago`** (0.5 is the last release, upstream stopped in 2011, and it owns the one third-party ignore the deprecation gate still carries, its module-level `_NOW = datetime.utcnow`). The reason first recorded here was **wrong and is worth noting as a process failure**: it said replacement was application work *because `core_tags.py` monkeypatches `_NOW`*, but **Step 13 task 09 removed that monkeypatch** and there is no `_NOW` assignment left in the tree — the claim came from the task file and went into three files unchecked. **The real obstacle is that every alternative changes what the site displays**: repoze rounds to nearest and stops at days (90s = "2 minutes ago", 400d = "400 days ago"), while `timeago` and `django.utils.timesince` both truncate and escalate to weeks/years ("1 minute ago", "1 year ago") — and those strings render on every forum topic and post listing, so a swap restyles the archive. **Vendoring is the recommendation** (79 BSD-licensed lines, one function used, `tagging` and `elsewhere` already vendored, and the deprecation becomes a one-line fix that empties the gate's third-party ignore list); `timeago` on PyPI was considered and last released 2022-08-18. Decision belongs to this step, not to task 05. Also carries, added 2026-08-16 from Step 15 task 05 (Brian's call): **choose a linter, and possibly a formatter — and note this has now been deferred three times without ever being scheduled.** Step 7/8 parked an `isort` (+ maybe `black`) pass as "its own commit right after the flip", on the sound reasoning that a whole-repo reformat would bury the Py2→Py3 migration; Step 14 task 05 hit it again and left `mock`/`unittest.mock` import placement alone for the same reason; and Step 15 task 05 found the third face of it — **the project carries `# noqa: E402` markers but has no linter at all**: no flake8 config, nothing in `requirements_dev.txt`, no lint step in CI. So those suppressions have never been validated against a run, and some may be for rules nothing checks (one was added in that task for an import that did not need it, and removed on inspection). The work is: pick the linter (flake8 vs ruff — ruff subsumes isort and is fast enough to run in CI), decide whether a formatter is wanted at all given this codebase's deliberate hand-wrapped comment style, wire whatever is chosen into CI so it is enforced rather than advisory, and only then run the reformat as its own separately-verified commit. **The "burying the migration" objection expires with Step 14** — the ladder is finished, so the reason for deferral no longer holds, which is exactly why it should stop being deferred. Also carries, added 2026-08-15 from Step 14 task 06: **`Post.delete()` returns `None` where `Model.delete()` returns a tuple** (`forums/models.py:311`, latent -- nothing reads the value), and a test for the queryset delete at `forums/tools.py:71` that bypasses that override entirely.
- [ ] **Step 20** — Production hardening (gunicorn/WhiteNoise/prod compose/backups) + Cloudflare front **Corrected 2026-08-15:** media is NOT going to R2 -- Step 21 chose a single VM, so `/media` stays on the server's disk as it always has, and no `ImageField`/`FileField` changes shape. Backups still go to object storage. `downloads` (716 MP3 rows) is the one category worth measuring egress on before leaving it on disk.
- [ ] **Step 21** — Deploy to new host + cutover + fallback. **CARRIED IN 2026-08-30: fail2ban's Cloudflare edge blocking must be rebuilt, and after the real-IP rewrite, not before.** jaguar's fail2ban pushes bans into a Cloudflare IP list that a WAF rule drops at the edge (`ip.src in $block_list`, built 2025-08-10); it is host configuration and Cloudflare credentials, so nothing in this repo recreates it. It is what holds spam registrations at ~1.25/month — not the registration form — so losing it at cutover raises spam for reasons Turnstile will be blamed for. **Ordering is load-bearing:** enabling fail2ban before Step 20's `ngx_http_realip_module` is working repeats the 2025-06-19→08-10 mistake, where the host saw only Cloudflare edge IPs and banning them would have banned Cloudflare. See STATUS, *Cloudflare dated, and 35% of the layer measurement had no client IPs*. **Carried in 2026-08-05: bound Redis's memory and set `maxmemory-policy volatile-lru`** — one Redis now serves the cache (db 2), the broker (db 1) and the site's kept state (db 0), and the policy is server-wide, so `allkeys-lru` would evict broker messages and kept keys; `volatile-lru` evicts only the TTL-carrying cache keys. Also: the Redis cache backend fails hard where memcached failed soft. **Also carried in 2026-08-07 from Step 13 task 06: decide the dev/prod settings split.** `docker-strategy.md` records both "the dev override owns the debug toolbar" and "one image runs dev and prod", and those cannot both hold — one image means the prod image either carries `django-debug-toolbar` or it does not. Recommended: a **multi-target Dockerfile** (`prod` from `requirements.txt`, `dev` layering `requirements_dev.txt`), which lets a dev-only settings module drop the `if DEBUG and find_spec(...)` guard entirely. Neither half of that guard protects production today — `production.py` never goes through `local.py`. **Do the whole chain at once**: `local.py` and `production.py` both still declare `django.db.backends.mysql` five steps after the PostgreSQL move. **Preserve the toolbar's MIDDLEWARE position** — after `CommonMiddleware` deliberately, measured, and commented in place. **Tail item: retire the MySQL conversion chain, gated on decommissioning the old box** — not on the site looking fine, because while the old box stays warm a DNS flip makes its MySQL authoritative again and any second roll-forward is another convert-and-verify. Preconditions: tag the cutover commit (`verify_data.py`'s canonicalization is worth keeping findable) and archive the final snapshot (git restores the tooling; nothing restores the data). Out: `mysqlclient` + the Dockerfile's MySQL apt packages, the `db` service and `mysql` profile, `verify.py` / `verify_data.py` / `convert.sh` / `sg101.load` / `crosscheck_dumpdata.sh`, `DOCKER.md` §6–§7, and the four keep-this comments added 2026-08-02, which become wrong at exactly that moment. Stays: `compare_schema.py` (psycopg2 only — compares a converted schema against a Django-built one, useful beyond MySQL). **Carried in 2026-08-15 from the Step 15 rescope: audit the old box's working copy (`hg status` / `hg diff`) before cutover.** Production ran `USER_PHOTOS_LOCAL_UPLOAD = True` as an uncommitted edit to `production.py` for ~20 months (live 2023-05-08, committed 2025-01-04); `hg pull --update` preserves such edits silently, and a fresh clone drops them, so any second instance would surface after cutover rather than during. **RUN 2026-08-16: the working copy is CLEAN, no second edit exists** — consistent with `e53aa1f` having committed the first one. **Downgraded to a cutover-day re-run rather than closed**: production stays live on the old code for six more steps, and an edit made in that window is exactly what this check is for. **HOST DECIDED 2026-08-15: single VM with persistent disk** (Linode/Lightsail class), no longer late-binding -- the media strategy is downstream of it. Render priced at ~$80-115/mo against ~$24, would mean re-architecting a working six-service compose stack at the riskiest moment, and its persistent disks remove zero-downtime deploys and offer only all-or-nothing snapshot restore, which is unusable for user uploads. PaaS revisit deferred to its own `/pdd` after modernization. **Also carried in 2026-08-18, found while tracing a stray cron mail: the backup box is undocumented.** `bobcat.gremmielabs.dev` (198.58.104.73) is a second Linode that rsyncs the production host nightly at 03:15 — the `sg101<date>.sql.bz2` dumps, the media tree, the moin wiki, `.hg`, and Brian's other sites — and **nothing in this plan mentions it.** At cutover that job keeps backing up a machine nobody uses while the new VM has no backup at all, and the failure mode is silence: the backup appears to be running because it is, just of the wrong host. Repointing it belongs with the cutover, not after it. It also mails its output to Brian, which is how it surfaced at all — **and that alarm is almost entirely deaf**: 54 bounce log lines against 4 deliveries in the retained logs, measured 2026-08-18 — and since each failed message logs one line per MX host tried (Gmail is reached over both IPv6 and IPv4), that is roughly 27 messages, i.e. about one a day, which is exactly the backup job's cadence. Nearly every night's report has been refused. Causes are jaguar's own, on another machine: the IP's PTR names `gremmielabs.com`, which has no A record, so reverse DNS cannot forward-confirm and Gmail refuses with `5.7.25`; the HELO name `bobcat.gremmielabs.dev` has no A record either; and Postfix also attempts IPv6, where Gmail's stricter rules refuse with `5.7.1` for the same missing PTR — so one nightly message generates two rejections. **The consequence is not the mail, it is the alarm: a backup that starts failing would announce it through a channel that already fails 93% of the time.** Fix mirrors task 03 — an unproxied A record for the HELO name, Linode reverse DNS repointed at it, and `inet_protocols = ipv4` so it stops trying IPv6. Out of this repo's scope, but the cutover depends on that box. **Also added: a media-transfer step, which this plan had entirely missing** -- two-pass rsync, the delta running AFTER the final DB snapshot so no row arrives without its file. **Corrected 2026-08-23: the decommission inventory is now its own PDD project** (`~/workspaces/bgn/planning/2026-08-23-jaguar-decommission/`, its `STATUS.md` authoritative) -- **three** sites move, not the six vhosts on the box, because `tmensurf.com` and `briananddebra.com` have lapsed entirely and `deathofagremmie.com` serves 403; `bravenewsurf.com` is **Django 1.3.7 not 1.8** and *also* still MXes to jaguar (previously unrecorded); `edtaxidermy.com` needs no crawl at all since it rebuilds from source; and **the warm window no longer has a fixed 1-2 week length** -- it ends when that project does. **Also carried in 2026-08-24, from the decommission project's completed research pass: a public IRC server is running on jaguar and this plan retired the wrong thing.** `ngircd` on `0.0.0.0:6667`/`:6697` plus `/svr/irc/sg101bot/` as root, live since Apr 23 — Step 4 pruned the Django app *named* `irc` (the chat status page), which does not touch the daemon. sg101's by content, so this step's to resolve; the decommission cannot complete around a live public service. **Also: `wiki.surfguitar101.com` is still an enabled vhost** despite Step 19 retiring the wiki. **And jaguar's Apache logs have never been backed up at all** — `jaguar_exclude.txt` excludes every `access.log*`/`error.log*` and the rsync runs `--delete`, so `bobcat:/svr/backups/jaguar/www/*/log/` is empty; the other project archived its three sites' logs on 2026-08-24, but **sg101's and the wiki's remain unarchived** and this cutover has the same evidentiary dependency.

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
   **DONE 2026-08-07, and the chain was one link longer than written here.**
   celery/kombu went to the current line (**5.6.3 / 5.6.2**) rather than 5.3,
   which pulls **redis-py 3.5.3 → 6.4.0** in with them: kombu's redis extra asks
   for ≥ 4.5.2, and while kombu's *runtime* guard only checks ≥ 3.2.0 and so
   would not have raised, kombu 5.6 imports `CredentialProvider` and `sentinel`
   from redis under one `try/except ImportError` — on 3.5.3 the missing
   `CredentialProvider` takes `sentinel` down with it, silently, to `None`.
   redis-py serves three consumers here (the application datastore, Django's
   cache backend, the broker transport) and all three were verified.
   **The `importlib-metadata` cap turned out to be already inert**, which the
   plan could not have known: kombu's shim does `from importlib import metadata`
   first, and on 3.10 that *succeeds*, so the pinned backport was installed and
   never imported (`'importlib_metadata' in sys.modules` → `False`). The cap was
   removed as dead weight rather than as a fix. What made the kombu bump
   necessary is the other half of that shim — `entry_points().get()` reaches the
   **standard library's** `SelectableGroups`, deprecated on 3.10 and **removed in
   3.12**, so this was a Step 14 prerequisite wearing a Step 13 label.
   **psycopg 3 evaluated and deferred, on a reason that is not timidity**: it
   would not be a swap. `tools/pgloader/verify.py`, `verify_data.py` and
   `compare_schema.py` import psycopg2 directly, so psycopg2 stays in the image
   either way and adopting psycopg 3 means running *two* PostgreSQL drivers.
   psycopg2 went to 2.9.12 instead, and the three live search queries were
   re-run under 2.9.9 in a throwaway container to prove the driver moved nothing
   — identical totals and all eight per-type counts. **six keeps its pin, with a
   corrected comment**: two requirers left (html5lib, python-dateutil), down
   from four. Two further pins came along because their own comments named this
   work as their trigger: **debug-toolbar 3.2.4 → 6.3.0** (the newest supporting
   Django 4.2 — 7.0 requires 5.2) and **coverage <5 → 7.15.4** (the cap was for
   Python 3.7). See STATUS.md for the settings-isolation defect the toolbar bump
   exposed.

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

**Task 09 (`USE_TZ`) closed the step on 2026-08-09 and corrected the premise it
was scoped on.** The plan and the task file both said the month/year rollups
would resolve in UTC once `USE_TZ` was on, quietly filing an evening record
under the following month. **They resolve in `TIME_ZONE`**: date lookups read
the *active* timezone, and with nothing activated that is the default, which is
`TIME_ZONE`. So the five rollups were correct at the moment of the flip and the
hazard is the mirror image of the recorded one — they follow *any* zone that
gets activated, which made the display decision load-bearing and ruled out this
plan's own suggestion of activating the user's timezone in middleware. They are
pinned with `ExtractYear/ExtractMonth(tzinfo=...)` rather than a
`timezone.override()` block, because the querysets are lazy and an override can
exit before the SQL runs. **The `RuntimeWarning` gate was the technique that
carried the task**, exactly as the task file promised: 148 errors down to 0, and
the 108 that came from `search` traced back to 11 datetime literals in
fixtures.

**Two of the pytz audit's three "hard" cases dissolved on inspection rather
than being solved.** `common_timezones` is not a runtime dependency — the
dropdown is a static committed asset generated once in 2010 by `tools/tz.py`,
which had been unrunnable Python 2 since the Step 8 flip. `NonExistentTimeError`
lived in a 2019 Redis-format shim whose two timezone-aware lines discarded their
return values. Only the "catch `ValueError` too" case was real, and it is the
one that would have turned user input into a 500. **`pytz` is now gone from the
project**; `tzdata` is pinned in its place.

**Three latent bugs surfaced, all the same shape**: code that only worked while
the host clock agreed with `TIME_ZONE` — true on the production box, false in a
container, and therefore false for the Step 20/21 deploy. Two were
`mktime(timetuple())` epoch conversions; the third was the `repoze.timeago`
monkeypatch, whose own comment said it was waiting for the decision this task
made. **A fourth is deferred to Step 19**: the PayPal IPN handler discards the
`PST`/`PDT` PayPal sends instead of converting it, so all 1,421 donations are
stored two hours early.

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
it from 4.2); it came back **"defer,"** so this is where it lands, and the reason
is already written down: psycopg2 stays in the image regardless, because the
three `tools/pgloader/` scripts import it directly, so adopting psycopg 3 adds a
second driver rather than replacing one. What changes that arithmetic is the
MySQL box being decommissioned (Step 21), which retires those tools and psycopg2
with them — so if the cutover has happened by the time this step runs, the
decision is worth re-taking rather than inheriting.
**Task 06 also cleared the interpreter-facing caps ahead of this step**: celery
5.6.3 / kombu 5.6.2 / redis-py 6.4.0 / psycopg2 2.9.12, and
`importlib-metadata` removed. The kombu bump was in fact a **3.12 prerequisite** —
kombu 5.2 read its transport registry through the standard library's
`SelectableGroups`, which 3.12 removes — so that breaker is already paid for
here rather than waiting in the interpreter move. **debug-toolbar will need
bumping again in this step**: 6.3.0 is the newest release supporting Django 4.2,
and 7.0 requires 5.2.
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

**Six task files generated 2026-08-12**, in
`.agents/tasks/2026-07-04-modernizing-sg101/step14/`: **01** Python 3.12 base
image, **02/03/04** the Django 5.0 → 5.1 → 5.2 rungs one apiece, **05**
dependency alignment, **06** the host venv. Two scope calls settled during
generation. The interpreter **moves first and alone**, with `Django==4.2.30`
held: this section offers either order, and 3.12 turns out to be the version
supported by both the Django we are on and the Django we are going to, exactly
as 3.10 was for Step 13 — so the same one-variable move is available and worth
taking. And the venv **is** in scope, as task 06, written last so it can be cut
without touching the rung tasks.

**Four corrections and confirmations from measuring rather than predicting.**
First, this section says the 3.12 move "can be skipped entirely if 3.10 is good
enough." True, and now beside the point: **the move is free.** The whole pin set
— runtime and dev — installs, imports, and exits 0 on `python:3.12-slim` with
Django held at 4.2.30, `Pillow` decodes JPEG, and only `ftfy`, `simplejson` and
`repoze.timeago` need an sdist build. The reason is written into the section
above without its consequence being drawn: task 06 took celery/kombu/redis-py
and psycopg2 to the *current* line, so the interpreter's bill was already
settled. `mysqlclient==1.4.6` builds too, despite 3.12 removing `distutils` and
the slim image carrying no `setuptools`, because PEP 517 build isolation
supplies one.

Second, **two pins are dead weight and the alignment task now has concrete
scope**: `html5lib==1.1` and `simplejson==3.17.6` have zero requirers and zero
imports, `html5lib` having been orphaned when bleach moved to 6.4.0 in Step 13
task 01. Removing it leaves `six` with a single requirer, `python-dateutil` via
celery, so **six still does not leave the image** — and `requirements.txt`'s
comment naming two requirers has to move with the pin. Third, **5.1's
positional-`Model.save()` deprecation has no bite here** (all ten positional
`.save(` call sites are `PIL.Image.save()` or `FieldFile.save()`), and **5.0's
form-renderer default change has no surface** (all six whole-form renders are
explicit `as_p`/`as_table`) — both of which strengthen the inherited "5.x
inventory is empty" rather than merely repeating it.

Fourth, on the **psycopg 3 re-decision this section hands to the step**: the
condition it names — the MySQL box being decommissioned — is Step 21 and **has
not happened**, so the structural reason to defer still holds and task 05 is
written to expect that outcome. What it also requires is that the re-decision be
*recorded* with its date and reason rather than silently carried, since a
decision nobody re-states is indistinguishable from one nobody revisited.

**Two things the rung tasks carry that this section did not name.** The
**vendored `tagging` fork** is the first place to look on every rung:
`tagging/models.py:178-186` is the only code in the tree reaching into Django's
private SQL-compiler API, it has broken on two of the last three rungs, upstream
is dead, and **only the news tag cloud reaches it** — so a green suite says
nothing about it. And **`django-debug-toolbar` moves on the 5.2 rung** (7.1.0
current; 7.0 is the release requiring Django ≥ 5.2), which
`requirements_dev.txt:11-15` already schedules by name.

**Task 06's premise re-checked against the actual host:** `mysql_config` and
`pg_config` are both absent, Homebrew is present, and the host's default
interpreter is **Python 3.14.2** via asdf — so the venv must be built on 3.12 to
match the image rather than on whatever `python3` resolves to, or it type-checks
against a different standard library than the code runs on. `.venv` is in
neither `.gitignore` (which carries `.env`, a different entry) nor
`.dockerignore`.

---

## Phase E — Modernize subsystems (resolve the Step 8 stubs, adopt Cloudflare)

### Step 15: User photo uploads → back to S3 (boto3)
**Objective:** Restore uploading to the existing S3 bucket; resolve the Step 8
`boto` stub; move the local-disk photos of the last three years into it.

**RESCOPED 2026-08-15, and the direction reversed — R2 is out, S3 is back.**
This section previously said Cloudflare R2. That recommendation came out of the
`/pdd` session under the assumption that S3 was no longer usable, and **the
assumption was wrong** — or rather, it stopped being true two steps ago.

**What actually happened, from Brian plus the data.** Media for `bio`,
`downloads`, `smiley` and the rest has lived on the dedicated server's own disk
since day one, by design; that was never S3. The `user_photos` app came later,
when https became a necessity, and it alone uploaded to S3. Then AWS stopped
accepting production's uploads — **Py2.7-era TLS against AWS's TLS 1.0/1.1
deprecation**, which S3 completed in mid-2023 — and Brian worked around it by
switching new photos to local disk (`3e655db`, `e53aa1f` on `main`). The buckets
were never turned off and still serve reads.

**So the blocker was the interpreter, and Steps 13–14 already removed it.** The
site runs Python 3.12 on OpenSSL 3.6.3. Going back to S3 costs no new account,
no new credentials, and no migration of the historical photos.

**Measured in the snapshot 2026-08-15**, and it corroborates the account to the
day — `user_photos.Photo` stores absolute URLs, 26,331 rows:

| rows | host | `upload_date` range |
|---|---|---|
| 21,754 | `s3-us-west-1.amazonaws.com/sg101.user.photos` | 2013-09-15 → **2023-05-07** |
| 4,577 | `surfguitar101.com` (local disk) | **2023-05-08** → 2026-07-11 |

A one-day cutover, landing the day after `3e655db` added the local-upload option.

**And the twenty-month gap is explained, 2026-08-15.** `e53aa1f` "Turn on user
photos local upload in prod" is dated 2025-01-04, long after local uploads
demonstrably began on 2023-05-08. Brian's recollection — offered as probable, not
certain — is that he ran the switch in production for a while before putting it
under version control. **The code constrains this to one mechanism**:
`USER_PHOTOS_LOCAL_UPLOAD` is a plain assignment in `base.py`/`production.py`,
not env-driven, and there is no `local_settings.py` override, so the only way to
have had it on was editing `production.py` on the server. `fab update` is
`hg pull --update`, which preserves an uncommitted working-copy edit across
deploys — so it would have survived indefinitely and silently.

**This is a Step 21 hazard, not a curiosity.** Production's working copy has
carried at least one uncommitted modification for roughly twenty months, and
nothing in the repo would reveal a second one. A fresh clone onto the new host
drops any such edit on the floor, and the resulting behavior change would surface
after the cutover rather than during it. See Step 21.

**Guidance:** Rewrite `core/s3.py` for `boto3` (dropping the dead boto v2 import
guard); env-configure `USER_PHOTOS_*`; set `USER_PHOTOS_LOCAL_UPLOAD = False`
again. `USER_IMAGES_SOURCES` needs no new host if the destination stays
`s3-us-west-1.amazonaws.com`. **Leave the 21,754 existing S3 rows alone** —
Brian's call.

**MIGRATE NOTHING HERE, revised 2026-08-15.** An earlier draft of this section
said to upload the 4,577 local files into the bucket and rewrite their rows.
**That was wrong on three counts**, all raised by Brian asking what happens to
these files at cutover:

1. **The rewrites would not survive.** Step 21 loads a *fresh production
   snapshot*. Anything rewritten here happens in the dev database; production's
   database never sees it, so the fresh snapshot arrives with every row still
   pointing at `surfguitar101.com`. The whole migration would have to be re-run
   at cutover regardless — this is the same shape as Step 11, whose `pgloader`
   tooling exists precisely because the real conversion happens at Step 21.
2. **The set keeps growing.** Production stays live on the old code until the DNS
   flip, so members keep adding local-disk photos the entire time.
3. **Production cannot perform the upload.** Its Py2.7 cannot talk to S3 — that
   is the whole reason this step exists. The migration can only run from a
   machine that has both the files and a working modern client, i.e. the new
   host. Dev cannot even rehearse it fully: `media/user_photos` does not exist in
   the checkout, so those files live only on production.

**So the local photos ride the Step 21 media rsync**, which has to happen anyway
for badges, smiley, potd, downloads and the rest. Their URLs keep working because
the new host serves the same path. Zero row rewrites, nothing lost to the fresh
snapshot, and zero added minutes in the maintenance window.

**Consolidating them into S3 later is optional and windowless** — it can run any
time after cutover, from the new host, with no downtime and no time pressure.
Worth doing eventually for one URL form; worth doing *then*, not now.

**This depends on the Step 21 host decision** (single VM, decided 2026-08-15). On
a PaaS with an ephemeral or snapshot-restore-only filesystem, none of the above
holds and **all nine upload fields** would need object storage before cutover.

**`make_key()` is already correct** — `core/images/upload.py:51` does
`b64encode(uuid.uuid4().bytes, b'-_').rstrip(b'=').decode('ascii')`, with bytes
altchars and a decode. The Py2 `gen_key()` this section used to schedule a fix
for lives only in `ssl_images.py`, which is being retired instead (below). Those
are two separate upload paths and only the retired one was broken.

**Retire `ssl_images` rather than porting it, added 2026-08-15.** It rewrote
http images in old posts to https, rehosting non-SG101 ones into
`sg101.forum.photos`. Brian says it has not been used in years, and the evidence
agrees on seven counts: absent from `CELERY_BEAT_SCHEDULE` (6 entries), absent
from every `call_command` in the tree (7 sites), absent from `fabfile.py`,
compose, the Dockerfile, CI and `tools/`; no `ssl_images.log` or
`ssl_images_cache.json` anywhere; last code change on `main` **2015-11-27**; and
its output signature in the data stops dead — posts containing
`sg101.forum.photos` run 966 in 2015, 323 in 2016, then 22, 3, 5, 3 and single
digits through 2025, a tail consistent with members pasting existing URLs rather
than the tool running. It also could not have succeeded since May 2023 anyway,
since it uploads to S3. **Measured directly on production 2026-08-16, which
settles it**: two untracked cache artifacts sit in `PROJ_DIR`, both owned
`brian:brian` — `ssl_images_cache.json` (2,720 bytes, **2015-11-27**) and
`ssl_images_cache.json.bz2` (306,180 bytes, 2015-10-29). `save_cache()` writes the
`.json` at the end of a run, so that mtime is the last *completed* run, **the same
day as the command's last code change**. **The pair brackets the tool's whole
working life inside autumn 2015**: runs through October built a large cache, it was
archived to `.bz2`, a fresh cache started from empty and stopped a month later —
matching the independent data signature (966 posts in 2015, 323 in 2016, single
digits after). Run by hand from `PROJ_DIR`, not by a daemon. Production's
crontab is the one count that cannot be seen from the repo and **was deliberately
not checked** — a command that uploads to S3 from Py2.7 has been failing since May
2023 regardless, so any entry would be a dead entry and no answer argues for
keeping it.

**Retiring the command is NOT retiring the bucket.** 15,690 posts and 16
comments carry `sg101.forum.photos` URLs inside their stored HTML.
`sg101.forum.photos` has to keep serving indefinitely or a decade of forum images
breaks. Deleting the command removes **42 tests** (`core/tests/management/
commands/test_ssl_images.py`), which is a real dent in the suite count and wants
its own separately-verified commit. Check `news` and `UserProfile` before
deleting — its history includes "Modify ssl_images to update news models" and
"Prevent mixed content in UserProfiles".

**Tests:** `core/tests/test_s3.py`'s 5 tests mock boto v2 names
(`connect_to_region`, `Key`, `OrdinaryCallingFormat`) and all get rewritten for
boto3's shape — the "its callers import cleanly and their tests keep mocking it"
bargain Step 8 struck, coming due. Upload/serve/delete against moto or a test
bucket; the photo-upload journey re-enabled.
**Demo:** Upload a user photo → stored in `sg101.user.photos` → served, from the
same host the other 21,754 already use.

**Local `/media` is explicitly NOT this step.** It has been on the server's disk
since day one and works; `bio` badges (10 files), `smiley` (87), `news` (22),
`podcast`, `potd` (575 rows), `banners` and 2,837 avatars are small and
admin-managed. The one worth revisiting is **`downloads` — 716 rows of MP3s**,
the only category where size and egress could justify object storage. Deferred
to Step 20 with WhiteNoise and the Cloudflare front, where it belongs.

### Step 16: Email → transactional provider
**Objective:** Replace the local mail server with a deliverable provider.
**Guidance:** Point Django's email backend at Postmark/Brevo (SMTP or API) via env
config; set up sending domain + SPF/DKIM/DMARC; wire `DEFAULT_FROM_EMAIL` and
admin error mail. (Cloudflare Email Routing handles inbound only.)
**Tests:** Email-send tests (locmem/backends in unit tests; a staging smoke send);
registration/notification flows assert mail is dispatched.
**Demo:** Trigger a registration/notification in staging → email arrives in inbox.

**PROVIDER DECIDED 2026-08-16: Postmark, Basic plan, $15/mo.** Volume
**re-measured 2026-08-17** against the snapshot, replacing figures that had been
inferred from posts × subscriber counts: **~900 emails/month typical**, busiest
month ~1,675. In the 12 months to 2026-07-26, **4,487 forum posts generated 9,819
notification emails** (~2.2 recipients per post), plus 376 registrations and 419
private messages sent, plus contact/flag/error mail. **Mean ~30/day; peak day 207
over 12 months, 233 over 24; none over 300.** *(Superseded: "~1,000–1,800/month,
peak day 239" — that range was really average-month-to-peak-month, and Brian
caught it as too high. Method and caveats in STATUS.md.)* Cost is therefore not
the deciding factor and deliverability is. Postmark was chosen over the
alternatives because its IP pools are transactional-only and actively policed,
which is the specific failure being fixed. **Rejected:** Resend (free 3,000/mo but
capped 100/day — breached on ~5% of days, and the breach lands on a registration
confirmation); Brevo (free
300/day fits, but the free plan stamps its logo in the footer and removing it
costs more than Postmark); Amazon SES (~$0.15/mo and now plausible since Step 15
restored working AWS credentials — rejected because it keeps bounce/complaint
handling and reputation monitoring in-house, i.e. it keeps the headache this step
exists to remove).

**Diagnosis FOUND 2026-08-16, and it is neither of the first two hypotheses.**
Not "the DNS records are subtly wrong" (Brian's), and not "pure IP reputation,
nothing is misconfigured" (mine — superseded; Microsoft's May 2025 mandate binds
senders above 5,000/day and this site sends ~37, so that part still holds).
Auditing the live Postfix config alongside DNS found **three independent silent
failures**:
1. **Reverse DNS does not forward-confirm.** `PTR` for `173.255.245.115` is
   `surfguitar101.com`, which now resolves to Cloudflare's proxy IPs. It used to
   match; enabling the Cloudflare orange cloud on the apex — a *web* change —
   broke it invisibly.
2. **The HELO hostname doesn't resolve to the sender either.**
   `myhostname = jaguar.deathofagremmie.com` → Cloudflare proxy IPs, on a domain
   with no MX and no SPF.
3. **No DMARC record on any domain**, which is why neither of the above was ever
   reported back to us.

A fourth item was claimed here — that the DKIM milter sat on an impossible port
(`inet:localhost:88888`) and mail was going out unsigned. **A captured message
header disproved it on 2026-08-16: `dkim=pass`, signature valid and aligned.**
SPF and DKIM both pass; the three items above are the whole story. That capture
also independently confirmed items 1 and 2 from the receiver's side — Gmail
logged an empty reverse-DNS parenthetical, and emitted no `dmarc=` clause.

**This explains the receiver split**: Gmail accepts the mail (it weights SPF and
DKIM, both passing) while Microsoft rejects it (it weights connecting-IP
reputation and reverse DNS, both failing). **Postmark owns the IP, PTR and HELO,
so all three are fixed by the move** — see task 03, which also carries an
optional interim FCrDNS fix and an instruction to leave the working milter alone.

**Task 03 PARTIALLY EXECUTED 2026-08-17** — started first because it embeds a
mandatory week-long DMARC reporting wait. Live: `_dmarc` at `p=none` with a
Cloudflare-hosted `rua` (**the clock starts here**), Postmark's DKIM and
Return-Path records verified, `mail.surfguitar101.com` unproxied to the Linode
IP, and `smtp_helo_name` aligned. Outstanding: the PTR was accepted by Linode but
had not propagated at end of session, so **item 1 above is not yet closed**. The
SPF rewrite stays with the task 02 cutover. Full record, and four corrections to
the audit, in STATUS.md.

**DNS audited 2026-08-16** against `ada.ns.cloudflare.com`; findings and
remediation in `.agents/tasks/.../step16/task-03-dns-email-authentication.code-task.md`.
Headline: **there is no DMARC record at all** — so there has also never been any
aggregate reporting, which is why the rejections were undiagnosable from this
side. The DKIM key is **1024-bit** — *and so is the one Postmark issued on
2026-08-17, measured; the plan's earlier claim that the move fixes this was
wrong. Not a blocker, and never implicated in the rejections.* The SPF `a`
mechanism now resolves to
Cloudflare's shared proxy IPs, since the apex is proxied. The suspected duplicate
TXT records **do not exist** — one apex SPF, one DKIM at `dkim._domainkey`, which
is correct. DNS is already fully on Cloudflare, so Step 20's front is partly in
place and Email Routing is one toggle away.

**Inbound needs no Postfix.** Postmark is send-only; receiving at `admin@` and
`no_reply@` moves to Cloudflare Email Routing (free, forward-only, 200 verified
destinations/account, 25 MiB max). The new VM keeps no MX, no inbound port 25,
and at most a send-only null-client relay for cron/root mail. **Also carries the
migration of the existing Postfix aliases for Brian's other domains** on the
dedicated server — inventory not yet taken.
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
**DONE 2026-08-22 as task 05.** A requested address goes into a new
`accounts.PendingEmailChange` (`OneToOneField`, so the last request wins in the
schema rather than in code) and reaches `User.email` only when the emailed link
is followed; the old address gets a courtesy note with no action link. **945
tests green** (904 before). Two things the task file had wrong or unspecified,
both settled by Brian: **requirement 3's premise was backwards** — it called a
scheduled sweep "more consistent with the codebase" when
`PendingUser.purge_expired()`'s only caller is *on use* — so expiry is now both,
the confirm view checking `is_expired` (which lets an expired link say so, where
`register_confirm` can only hedge) and `core.tasks.cleanup` sweeping abandoned
rows; and **requirement 4's guard could not see the race** where two members
request the same free address and both confirm, so `clean_email` also rejects an
address pending for another account and the confirm view re-checks uniqueness
before writing. The 26-account trap above is guarded by `clean_email` returning
before doing any work when the address is unchanged, verified both by a test
watched to fail against the naive implementation and by a read-only probe over
the dev database: 13 groups, 26 accounts, 0 that could not save. `unique=True`
on `User.email` stays a follow-on — those 26 rows would fail the migration.
**And the lesson that outlived the task: ten minutes of browser testing found
six defects the 946-test suite could not see**, every one of them because the
tests asserted state and never what a person would see — a template comment
rendered as text, flashes with nowhere to display, buttons no test knew were on
the page. One of the six was not this code at all: the Celery worker had been
running since before task 09 and was failing every deferred send, which
`CELERY_TASK_ALWAYS_EAGER` hides from the suite by construction. Full account in
`STATUS.md`.

### Step 17: reCAPTCHA → Cloudflare Turnstile
**Objective:** Swap CAPTCHA to a free, privacy-preserving solution, on the contact
form **and registration**.

**Re-evaluated 2026-08-27 — the rationale changed; see the Step 17 section of
`STATUS.md` for the measurements.** R23 justified this step on reCAPTCHA's 10k/mo
cap. That cap is real, but this site's busiest month is **71 assessments** — 0.7%
of it — so cost is not a reason. The step proceeds on privacy and user friction,
and the current classic key was verified healthy rather than degraded.

**Two corrections to this entry, both found 2026-08-27:**
1. **The work is not in the `antispam` app.** That app is a spam-phrase filter and
   auth-failure logger with no CAPTCHA in it. `contact/` is the only reCAPTCHA
   caller in the repo — `contact/forms.py`, `contact/views.py`, one template, and
   three settings.
2. **Scope now includes registration**, which has no CAPTCHA today. It relies on a
   static knowledge question, two honeypots and an emailed code word, and **~1.4
   spam accounts/month complete registration anyway** (measured, caught-only).

**Guidance:** Render the Turnstile widget and verify tokens server-side
(env-configured site/secret keys); follow Cloudflare's reCAPTCHA→Turnstile
migration guide; remove reCAPTCHA config. Turnstile's siteverify takes the same
`remoteip` the contact form already passes — which depends on the
`CF-Connecting-IP` rewrite hung on Step 20.
**Tests:** Form-validation tests for pass/fail Turnstile verification (mock the
verify endpoint), on both forms.
**Demo:** Contact and registration both show Turnstile and reject a
missing/invalid token.
**Open for task generation:** whether Turnstile replaces the registration
question or joins it, and which stage of the two-stage registration flow carries
the widget.

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

**Also carries the `last_post` cascade hazard, added 2026-08-05 after it fired.**
`Forum.last_post` and `Topic.last_post` are `OneToOneField('Post',
on_delete=models.CASCADE)` and the cascade **points the wrong way**: deleting
the post a forum happens to point at deletes *the forum*, and with it every
topic and post inside. It cost the dev database forum 3 and its 4,626 topics /
24,107 posts during Step 13 task 05 (restored from the MySQL snapshot; see
STATUS). Today the only protection is `Forum.last_post_pre_delete()`, called by
hand -- `tools/pgloader/smoke.py` does it correctly and a second script written
without it did not. **This is latent in production**: an admin deleting the
wrong post is all it takes. Fix is `on_delete=SET_NULL` on both fields plus a
migration, with tests proving a post deletion no longer propagates past the
post. Brian's call to schedule it here rather than mid-ladder, schema changes
belonging with the other model-level work.

**Also carries `Post.delete()`'s return type, found 2026-08-15** by the language
server the Step 14 venv made usable — the first defect that tooling surfaced.
`forums/models.py:311` overrides `delete()`, calls `super().delete()` and
discards its result, so it returns `None` where `Model.delete()` returns
`tuple[int, dict[str, int]]`. **Latent, not live**: nothing in the tree consumes
a `.delete()` return value, verified by grep, so it would only bite the first
caller to write `count, _ = post.delete()`. The fix is to stash the result and
return it, which cannot be a blind one-liner because the `if self.id ==
first_post_id` block has to run before the return — so it wants a test, and it
belongs beside the cascade work rather than alone.

**Worth confirming while in there, not yet a finding:** `forums/tools.py:71`
deletes posts as a queryset (`Post.objects.filter(pk__in=post_ids).delete()`),
which does **not** call `Post.delete()`, so the "first post deleted, therefore
delete the topic" rule never runs on that path. It reads as deliberate — the
function handles topics explicitly just above via `pending_delete`, and its
comment says the foreign keys are already accounted for — but it means that
override's behavior is not guaranteed merely because a post was deleted. Given
this project has already lost a forum to a delete path, the assumption is worth
writing a test around rather than leaving in a comment.

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

**Also carries the settings-module cleanup, added 2026-08-07 out of Step 13 task
06** (Brian's call to defer it rather than grow that task's diff). Three small
independent changes:

1. **Extract `LOGGING` into `sg101/settings/logging_config.py`.** `local.py` and
   `production.py` each carry a ~95-line dict, and they differ in exactly six
   places: `disable_existing_loggers` (False→True), the `auth` and `search`
   *handler* levels (DEBUG→INFO), the `auth` *logger* level, `root` level, and
   production's extra `django.request`→`mail_admins` logger. So ~190 lines to
   express six decisions. **`sg101/settings/databases.py` is the precedent** — a
   side-effect-free module exposing `for_engine(name)` / `from_env()` that the
   deployment modules call — so this follows a convention already in the package
   rather than inventing one.
2. **Move the search-logging assertions onto the subprocess helper.**
   `search/tests/test_views.py`'s `SearchLoggingSettingsTestCase` imports
   `sg101.settings.local` and `.production` into the running test process to read
   their `LOGGING` dicts, which is what detonated task 06's toolbar bump.
   `core/tests/test_settings.py` already has `_run()`, which loads settings in a
   fresh subprocess for exactly this reason. Verified 2026-08-07 that production
   settings load standalone with no env help (`REDIS_UNIX_SOCKET` defaults in
   `base.py:228`), so there is no friction to it.
   **The trap to avoid while doing item 1:** if the test is repointed at
   `logging_config` instead of at `production.LOGGING`, it stops proving that
   `production.py` *uses* the shared config, and a later `LOGGING = {...}`
   override there would pass. Reading the configuration the site actually
   deploys is the property that test exists for — keep the assertion aimed at
   the deployment module and let the subprocess supply the isolation.
3. **Keep task 06's copy fix in `local.py` regardless.** Extraction shrinks what
   sits in the blast radius; it does not remove the mine. The hazard is settings
   modules mutating objects they share with whatever is already live, and
   anything that imports `local.py` for any future reason still gets the toolbar
   spliced into its `MIDDLEWARE`. (`production.py` needs nothing here — task 06
   deleted its template-loader block once measurement showed it reproduced a
   Django default, so it performs no in-place mutation at all now.)

**Also carries the PayPal `payment_date` timezone truncation, added 2026-08-09
out of Step 13 task 09.** PayPal sends the IPN `payment_date` as a Pacific wall
clock with the zone as a trailing abbreviation —
`'04:14:08 Jan 21, 2011 PST'`. `donations/views.py` does
`payment_date = payment_date[:-4]`, commented "strip off the timezone", and
parses what is left with `PP_DATE_FMT`. **The abbreviation is not converted, it
is discarded**, so a Pacific wall clock is then recorded as though it were
`TIME_ZONE`. Every donation on file is therefore **2 hours earlier than the
instant PayPal reported** (Pacific is always 2 hours behind Chicago, so the
error is a constant and DST does not complicate it).

Measured 2026-08-09 against the production snapshot: **1,421 donations, 2011-03-01
to 2026-07-06, all affected.** Correcting them by +2 hours would move **5 rows
into a different calendar month** and **none into a different year** — so the
defect is invisible in the annual totals, and shows up only as five donations
reported in the wrong month somewhere across fifteen years of
`monthly_stats()` and `donations_report`.

Task 09 deliberately preserved the existing convention (`timezone.make_aware()`
on the parsed naive value, which is exactly what the ORM did implicitly before)
rather than fix it in passing. **Correcting new donations alone would be worse
than the defect**: the column would then hold two conventions two hours apart
with nothing recording which row is which, and the monthly reports would be
comparing them. So the fix is either nothing, or new rows *and* a backfill —
which is a data migration and belongs here.

Three things to settle before touching it:
- **Whether to correct history at all.** The amounts are right and the dates are
  right; only the times are off, by two hours, on a page that reports monthly
  sums. Doing nothing and documenting it is a legitimate answer.
- **How to parse the zone if we do.** Zone abbreviations are not uniquely
  decodable in general, but PayPal only ever sends `PST`/`PDT` here, so mapping
  those two to `America/Los_Angeles` and rejecting anything else is safe and
  fails loudly rather than silently mis-filing. Note `[:-4]` also silently
  assumes a 3-letter abbreviation.
- **What the backfill keys on.** There is no marker distinguishing corrected
  rows from uncorrected ones, so the migration has to be all-or-nothing over
  `payment_date < <cutover>` and must be idempotent enough not to double-apply.

**Also carries the timezone dropdown, `static/js/timezone.js`, added 2026-08-09
out of Step 13 task 09.** Low stakes and no deadline — recorded because task 09
touched every other part of this and deliberately left this part alone.

The two timezone pickers (profile edit, calendar event) are **not server-side
choice fields**. `bio/forms.py:31` and `gcalendar/forms.py:74` both declare
`time_zone = forms.CharField(required=False, widget=forms.HiddenInput())`, and
`static/js/timezone.js` builds a pair of area/location `<select>`s in the
browser that write into that hidden input. So the server accepts **any string**
and the only real guard is `clean_time_zone()` — which is exactly why that
validator has to defend against path-shaped input, and why a naive
`zoneinfo` port of it would have turned `'../etc/passwd'` into a 500.

The data is frozen: generated once from pytz's `common_timezones` in 2010
(`0f0047f`) by `tools/tz.py`, which task 09 ported from Python 2 to `zoneinfo`
but deliberately did not re-run.

**Measured 2026-08-09, and it is less alarming than it looks.** Regenerating is
**purely additive** — 553 zones across 16 areas versus the committed 401 across
11, adding 152 and dropping **none**. All **95** distinct values stored across
15,227 profiles are in the current list and all of them resolve. So nothing is
broken and nothing is at risk; this is a question about quality, not
correctness.

Three ways to go, roughly in order of effort:

1. **Leave it.** A frozen list of 401 zones covers everyone who has ever picked
   one, and a generated static asset costs nothing to serve. The argument
   against is only that a 2010 list will drift further from reality every year,
   and that `tools/tz.py` is now a script nobody has a reason to run.
2. **Regenerate the file and keep the shape.** One command, purely additive per
   the measurement above. Worth asking whether 553 options across 16 areas is
   actually easier to pick from than 401 across 11 — `Etc/*`, `Brazil/*` and
   `Mexico/*` appear in the larger set, and a longer list is not obviously a
   better picker.
3. **Move it into Python and delete both the script and the static data.**
   Build the choices from `zoneinfo.available_timezones()` at import or in the
   form's `__init__`, and make `time_zone` a real `ChoiceField`. This is the
   option with an actual benefit beyond freshness: **it makes invalid input
   impossible by construction** rather than by a hand-written validator, and it
   keeps the list in step with the pinned `tzdata` automatically. Two things to
   settle first — the choices must be the **union** of the available zones and
   the values already stored, so an upstream tzdata release retiring a name
   cannot invalidate a profile nobody has touched in ten years; and the
   two-select area/location UI would need either rebuilding server-side or
   keeping its JS and feeding it JSON from the view.

**Also carries five `tools/` scripts that are still Python 2, added 2026-08-12
from Step 14 task 01.** They do not compile on any Python 3 and have not since
the flip: `filter_posts.py`, `flag_data.py` and `translate_yahoo_group.py` use
`print` statements, `load_ygroup.py` and `post_sub.py` use unparenthesized
`except` clauses. **This is pre-existing and was never regressed into** — Step
7's "`py_compile` clean" claim was scoped to *app and migrations*, and `tools/`
was never inside it, which is also how `tools/tz.py` sat unrunnable from the
Python 3 flip until Step 13 task 09 ported it.

Nothing imports any of the five — not the application, not the suite — so they
have cost nothing so far, and an interpreter rung was the wrong place to fix
them. What makes this the right step is that **the question is triage, not
porting**: all five are one-off MySQL-era scripts, and three
(`load_ygroup.py`, `translate_yahoo_group.py`, and `post_sub.py`'s
`LOAD DATA LOCAL INFILE` workflow) exist to feed `mysqlimport`, which Step 21
retires with the MySQL box. `filter_posts.py` fixes orphaned posts from a
migration that finished years ago. **`flag_data.py` is the one plausible
survivor** — it regenerates the ISO-3166 country JSON the bio flag icons use,
which is data that can still change. Decide each one: port, or delete. Deleting
four and porting one is the likely shape, and either outcome should be recorded
so the next compile sweep does not rediscover them as a surprise.

**Also carries the weblinks add form's URL field, added 2026-08-13 from Step 14
task 02.** `weblinks/forms.py`'s `AddLinkForm` declares `url` as a
`forms.CharField`, and it should be a `forms.URLField`.

**Measured before scheduling, because the obvious reading of it is wrong.** The
`CharField` is *not* skipping URL validation: the model field is a
`models.URLField`, and `ModelForm._post_clean` runs the model's validators for
any field the form carries, so `javascript:alert(1)` and plain gibberish are
already rejected today. Nothing is unsafe here.

The difference is confined to scheme-less input, and it runs the wrong way
round. Typing `example.com` is **rejected** — "Enter a valid URL.", which does
not tell a member what to fix — where a form `URLField` would normalize it.
**Staff do not have that problem**: the admin builds its form from the model
field, so it is already a `forms.URLField` and already normalizes. The
members' path is the strict one and the staff path is the forgiving one, which
is backwards for a link-submission form whose whole purpose is member
submissions.

It also reads like an accident rather than a decision. The field is declared
only to set the widget's `size: 52`, matching the `title = forms.CharField(...)`
line directly above it, and dates to `65659c3` — the 2009 initial import. Since
`FORMS_URLFIELD_ASSUME_HTTPS` landed with the Django 5.0 rung, a converted field
would resolve a bare domain to `https://`, which is also where the stored data
points: 474 `http` rows against 94 `https`, so members are submitting plain-http
links that mostly redirect.

Scheduled here rather than done in the rung it was found in for two reasons.
The remaining rungs re-verify form behavior — 5.1 removes the transitional div
form renderers — so a form change landing between them gives a bisect two
candidate causes instead of one. And doing it after 5.2 means writing it once
against settled behavior rather than re-examining it at each rung. **It needs a
test either way**: `weblinks` has no coverage of the scheme-less case at all,
which is the only case the conversion changes.

**Also carries the ORDER BY collation change, added 2026-08-13 after Brian
noticed `/profile/members/user/` listing members in a different order than
production.** He was right about the cause. It is collation, and the row sets are
identical everywhere — this changes *order*, never *membership* or *counts*.

**The gap this exposes: Step 11 task 02's collation audit was scoped to
lookups.** Its stated method was an AST scan of keyword arguments to
`get`/`filter`/`exclude`/`get_or_create`, which is what found the 12
case-sensitivity bugs in equality matching. `ORDER BY` was never in scope, so
nothing here was examined until now.

**The rule, demonstrated on six strings rather than asserted:**

| MySQL `utf8_general_ci` | PostgreSQL `en_US.utf8` | PostgreSQL `C` |
|---|---|---|
| `-Bong-` | `0zero` | `-Bong-` |
| `0zero` | `-Bong-` | `0zero` |
| `Bonham` | `Bonham` | `Bonham` |
| `mn` | `mn` | `_mo_` |
| `mp` | `_mo_` | `mn` |
| `_mo_` | `mp` | `mp` |

MySQL gives punctuation a real sort weight by code point, so `-` (0x2D) lands
before digits and `_` (0x5F) lands after every letter. PostgreSQL's `en_US.utf8`
treats punctuation as **ignorable at the primary level**, so `-Bong-` sorts as
"Bong" and `_mo_` sorts as "mo". Both are case-insensitive, so case is not the
driver here.

**A fresh AST sweep found 22 orderings on text columns — and 14 of them are
`Meta.ordering`,** which is the half no call-site grep would ever show, since it
applies to every unordered queryset for that model. Each was then measured
against both engines on the real data, same column, same rows:

| table.column | rows | positions identical | where it shows |
|---|---:|---:|---|
| `weblinks_link.title` | 571 | **1 (0%)** | `Meta.ordering` |
| `downloads_download.title` | 716 | **6 (1%)** | `Meta.ordering`, `dlcatreport`, `dlwgetcat` |
| `news_story.title` | 1,694 | **35 (2%)** | `Meta.ordering` |
| `bandmap_bandentry.name` | 1,040 | **92 (9%)** | `Meta.ordering` — the band map |
| `potd_photo.caption` | 575 | **106 (18%)** | `Meta.ordering`, descending |
| `auth_user.username` | 15,227 | **3,288 (22%)** | the member list, who's-online, admin user picker |
| `forums_forum.name` | 16 | **10 (62%)** | `forums/forms.py:226,244` |
| `tagging_tag.name` | 1,006 | **708 (70%)** | `Meta.ordering` — the tag cloud |
| `bio_userprofile.country` | 15,227 | 15,227 (100%) | flag-icon tag |
| `antispam_spamphrase.phrase` | 50 | 50 (100%) | `Meta.ordering` |
| `smiley_smiley.title` | 85 | 85 (100%) | `Meta.ordering` |
| `downloads_allowedextension.extension` | 12 | 12 (100%) | `Meta.ordering` |
| `weblinks_category.title` | 11 | 11 (100%) | `Meta.ordering` |
| `accounts_illegalusername.username` | 4 | 4 (100%) | `Meta.ordering` |
| `banners_campaign.name` | 1 | 1 (100%) | `Meta.ordering` |

**8 of 15 differ, and the 7 that do not are exactly the columns whose values
carry no leading punctuation** — country codes, spam phrases, file extensions.
The worst are the title columns, because so many titles begin with a quote:
`'"Yeti" - The Noble Gasses'` moves from #15 to #571 of 571. On the member list,
`-Bong-` moves from page 1 to page 68 and `_mo_` from the last page to the
middle.

**Recommendation: keep PostgreSQL's ordering and record the decision.** Three
reasons. It is cosmetic — same rows, same counts, same page count, and the
ordering is deterministic since these columns are unique or effectively so.
Postgres's answer is arguably the better one: a member list filing `-Bong-` under
B beats one exiling it to the first page. And **`C` is not the parity option it
looks like** — measured above, it sorts by byte, which is case-*sensitive* and
would put every capitalised name ahead of every lowercase one, a bigger change
than the one being fixed. True parity would mean pinning a custom ICU collation
on each column to reproduce a legacy tiebreak nobody chose deliberately.

What this step should do is **decide and write it down**, and check the two
places where order is closest to being load-bearing: the paginated member list
(does anyone navigate it by expecting a name on a given page?) and the tag cloud,
whose 70% figure means it is nearly stable already.

**Two measurement traps met while doing this, both worth reusing.** `mysql -B`
escapes control characters in its output while `psql -At` does not, so one news
title containing a literal tab read as a *data* difference between the engines
until the escaping was undone — the measurement, not the data. And a `while read`
loop feeding `docker compose exec` silently processes only its first line,
because `exec` consumes the loop's stdin; redirect it from `/dev/null`.

**Tests:** App-boot tests without `wiki`; adjust/trim tests for any pruned apps;
a compile sweep over the whole tree — not just app and migrations — that would
fail on a Python 2 file surviving in `tools/`; a `weblinks` add-form test
covering scheme-less, schemed and invalid URL input; suite green.
**Demo:** Site runs cleanly without the wiki bridge; INSTALLED_APPS reflects final
app set.

---

## Phase F — Productionize and ship

### Step 20: Production hardening + Cloudflare front
**Objective:** A production-grade compose the final host will run.
**Guidance:** gunicorn; WhiteNoise (or Cloudflare-cached) static via
`collectstatic`; prod compose (DEBUG off, Postgres, Redis cache+broker, **media
on the VM's disk**, provider email, secure cookies); `pg_dump` → object-storage
backup routine + retention; health checks; Cloudflare config (DNS record plan,
edge TLS/origin cert, cache rules).

**"R2 media" corrected 2026-08-15.** This line used to say media lived in R2.
Both halves of that are now settled differently: Step 15 reversed R2 to S3 for
*user photos*, and Step 21 chose a **single VM with persistent disk**, so the
rest of `/media` — badges, avatars, smiley, news, podcast, potd, banners,
downloads — simply stays on the server's own disk, where it has been since day
one. Nothing needs `django-storages` and no `ImageField`/`FileField` changes
shape. **The backup line is unaffected**: off-machine object storage for
`pg_dump` output is a good idea regardless, and either R2 or S3 serves.

**`downloads` is the one worth re-examining here** — 716 rows of MP3s, the only
media category where size and egress could justify object storage. Behind
Cloudflare it is very likely fine on disk; measure the egress before moving it.

**Also carries the Sass toolchain, added 2026-08-13 out of the logout fix
(Brian's call to place it here).** The v3 design's stylesheet cannot currently be
rebuilt, which was discovered the hard way: a one-rule CSS change had to be
hand-appended to the *minified build artifact* because no rebuild was possible.

**The pipeline, as committed.** `sg101/scss/main.scss` imports Foundation and
Motion UI, then the site's own `_sg101.scss`; `sg101/gulpfile.js` runs it through
`gulp-sass` → `autoprefixer` → `cssnano` → `rename('.min')` and writes
`sg101/static/css/v3/main.min.css`, **which is committed** and updated in the
same commits as the SCSS (`a3d54a8` is an example of both moving together).

**Three independent things stop it running, all observable rather than
suspected:**

1. **`gulp-sass` ^2.1.1 wraps `node-sass`**, which needs native bindings built
   per Node version. Node here is **v26**; node-sass stopped shipping bindings
   many majors ago.
2. **`gulpfile.js` is gulp 3 syntax** — `gulp.task('default', ['sass'], …)`, the
   array-of-dependencies form, which gulp 4 removed.
3. **Dependencies come from bower**, not npm: `sassPaths` points at
   `bower_components/foundation-sites/scss` and `bower_components/motion-ui/src`,
   and `sg101/bower.json` pins `foundation-sites ~6.3.0` and `motion-ui ~1.2.2`.
   Bower is sunset. Neither `node_modules` nor `bower_components` is present.

**There is a small outstanding debt to reconcile on the first successful
rebuild — now two rules, not one.** Each was appended to `main.min.css` by hand
at the position a rebuild would place it, matching its order in `_sg101.scss`:

| Rule | Added | Sits after |
|---|---|---|
| `.menu>li>form.logout-form{…}` | `39aceca4`, 2026-08-13, the logout fix | `.friends-logos` |
| `.cf-turnstile{margin-bottom:1rem}` | 2026-08-30, Step 17 task 04's page cleanup | the logout rules, last in the file |

So a correct rebuild should produce essentially the same file. **Diff the rebuild against the committed artifact
before replacing it**: bytes that differ *elsewhere* mean the toolchain
reconstruction changed the output (a different Sass implementation, a newer
autoprefixer target, a different minifier), which is worth seeing rather than
absorbing silently.

**The migration is not large, and the modern shape is clear:** drop bower for
npm (`foundation-sites` and `motion-ui` both publish there), drop `node-sass` for
**dart-sass** (the `sass` package, which is the reference implementation now and
needs no native build), and consider dropping gulp altogether — this is one
`sass` invocation plus a minifier, which an npm script can express directly. The
autoprefixer target is `['last 2 versions', 'ie >= 9']`, written in 2016; IE 9
can go.

**The decision this forces, and why it belongs in this step rather than earlier:
is built CSS a committed artifact or a deploy-time build step?** Committing it is
what the project has always done and it keeps deploys simple, but it is why a CSS
change needed a working toolchain at all. Building during deploy removes the
artifact from review but adds Node to the production image. It interacts directly
with the `collectstatic`/WhiteNoise decision above and with
`ManifestStaticFilesStorage`, which `production.py` already names — so it is one
decision about static assets, not two.
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

**Also carries the real-client-IP rewrite, added 2026-08-21 out of a Django
error report.** The Cloudflare front line above has a consequence that is easy to
miss: behind a proxy, `REMOTE_ADDR` is the proxy unless something rewrites it,
and **Django does not do this itself.**

jaguar already solves it — Apache `mod_remoteip`, `RemoteIPHeader
CF-Connecting-IP`, `RemoteIPTrustedProxy` carrying Cloudflare's 15 IPv4 and 7
IPv6 ranges (`conf-enabled/remoteip.conf`, verified against Cloudflare's
published list 2026-08-21: identical, no drift). **That configuration is not in
the repo and does not travel with the code.** Six apps read `REMOTE_ADDR`
directly — `antispam`, `accounts`, `forums`, `comments`, `downloads`,
`donations` — and every one of them is correct today *only* because of it.

**The requirement:** whatever fronts the new VM must set the client address from
`CF-Connecting-IP` for connections from Cloudflare's published ranges, and from
nothing else. For nginx that is `ngx_http_realip_module` (`set_real_ip_from` per
range, `real_ip_header CF-Connecting-IP`). **The trusted-range list is the
security boundary, not the header name**: without it the header is client-
supplied and anyone can claim any address. It also needs a refresh plan, since
Cloudflare adds ranges.

**Failure mode if skipped:** no error, no log line, no failing test — every IP
the site records silently becomes a proxy address, and IP-based moderation
quietly stops distinguishing members. Worth an explicit assertion in the
prod-mode smoke test: a request bearing a forged `CF-Connecting-IP` from an
untrusted source must *not* be recorded under the forged address.

**Two adjacent consequences.** `core/functions.py:get_ip()` was fixed
2026-08-21 to read `REMOTE_ADDR` only (it had preferred the client-supplied
`X-Forwarded-For`), so it now inherits whatever this step configures. And **Step
17 depends on this**: the contact form passes the client IP to the captcha's
siteverify call as `remoteip`, and Turnstile takes the same parameter, so a
wrong value degrades scoring on the endpoint that exists to stop bots.

**The origin accepts direct connections, measured 2026-08-21 — and the address
is published in the zone.** jaguar answers `https://surfguitar101.com/` with
**200 on both IPv4 (`173.255.245.115`) and IPv6
(`2600:3c01::f03c:91ff:fe70:e820`)** when reached with `curl --resolve`,
bypassing the proxied apex (`172.67.218.217` / `104.21.53.213`). **No
certificate trick is needed**: the origin serves a publicly-trusted Let's
Encrypt certificate for `surfguitar101.com`, so verification succeeds without
`-k`.

**Finding the address takes one `dig`.** It is published four times:

| record | value |
|---|---|
| `mail.surfguitar101.com` A | `173.255.245.115` |
| apex SPF | `ip4:173.255.245.115` and `ip6:2600:3c01::f03c:91ff:fe70:e820/64` |
| `mail` SPF | `ip4:173.255.245.115` |

This is the ordinary way a Cloudflare origin leaks: **an MX target cannot be
proxied**, so the mail name necessarily exposes the host, and SPF then republishes
it. The consequence is that WAF, rate limiting and bot rules are **advisory** —
anyone willing to read the zone reaches the application directly, and the
real-IP rewrite above correctly declines to trust their headers but cannot
refuse the request.

**Closing it is a Step 21 property of the new VM, not a jaguar repair**: firewall
443 to Cloudflare's published ranges (**IPv6 included** — a v4-only rule leaves
the door open, as measured here), or Cloudflare Origin CA with
`authenticated_origin_pull`. **It interacts with Step 16 task 06**: once inbound
mail moves to Cloudflare Email Routing the new VM needs no MX and no public mail
name, so the leak has no reason to be recreated — provided the host is not given
a proxy-exempt A record for some other purpose, and provided SPF names Postmark
rather than the VM.

**One inconsistency to check while here, found in the same `dig`:**
`mail.surfguitar101.com` has an **unproxied A but a Cloudflare AAAA**
(`2606:4700:3030::ac43:dad9`). Proxy state in Cloudflare is per record, so one
name can disagree with itself. For an MX target that is worth understanding
before task 06 moves the MX — related to Correction 2 in STATUS (the `_dc-mx`
alias existed because the MX target was proxied), and possibly the same knot.

**Tests:** A prod-mode boot/smoke test (DEBUG off, static served, security
settings on); CI builds the prod image.
**Integration:** Combines every prior subsystem into the deployable artifact.
**Demo:** Run the **production compose locally** end-to-end: DEBUG off, gunicorn
serving, static + media from disk, provider email, search — all green.

### Step 21: Deploy to new host + cutover + fallback
**Objective:** Go live on modern, supported infrastructure.
**Guidance:** Provision the VM (below); deploy the prod compose; load a **fresh
production snapshot**; **transfer the media tree** (below); run migrations +
rebuild the search vectors; run the smoke checklist on the new host (behind
Cloudflare, pre-cutover, via a test hostname). Schedule a **short maintenance
window**: final snapshot → restore → final media delta → **low-TTL DNS cutover**
in Cloudflare. Keep the **old Ubuntu 14.04 box warm** as an instant DNS-flip
fallback, then decommission.

**Corrected 2026-08-23: the warm window is no longer "~1–2 weeks."** Brian's
chosen ordering does the *other* websites during it (see the decommission
inventory below), so the window now has two jobs with different natural lengths:
as an sg101 fallback it ends when confidence in the new VM is high, in 1–2
weeks; as the other sites' capture window it ends when three sites are mirrored,
verified to URL parity, deployed and DNS-moved. **The second sets the length —
"then decommission" gates on that project completing, not on a duration.**

**ALSO CARRIES: a decommission inventory — jaguar is not an sg101 box (added
2026-08-23, Brian's catch).** Everything above treats the old host as if
sg101 were all it does. It is not, and *"then decommission"* is unsatisfiable
until someone enumerates what else dies with it. **The inventory is itself the
deliverable** — three items have surfaced independently, each found while
chasing something else, which is the signature of a list nobody has written.

- **Three websites move; three more vhosts were already dead. RESOLVED
  2026-08-23 — the inventory is now its own project**, at
  `~/workspaces/bgn/planning/2026-08-23-jaguar-decommission/`, whose `STATUS.md`
  is authoritative for the sites work. It remains **not this project** (different
  codebases, different target, different acceptance criteria), but this step
  cannot complete without it. What follows is the dependency plus the
  corrections to what was originally written here.

  **The original account was wrong in three ways** — all measured 2026-08-23
  from live DNS/HTTP and the local source repos:

  | vhost | what it actually is | disposition |
  |---|---|---|
  | `themadeira.net` | Django **1.8.10**, mod_wsgi | crawl → static → Pages |
  | `bravenewsurf.com` | Django **1.3.7** | crawl → static → Pages |
  | `edtaxidermy.com` | Flutter web, **already static, builds from a git repo** | **no crawl** — rebuild, retarget `deploy.sh` |
  | `tmensurf.com` | — | **retired; no NS, A or MX — domain lapsed entirely** |
  | `briananddebra.com` | — | **retired; domain lapsed entirely** |
  | `deathofagremmie.com` | returns 403; `/munin` not publicly exposed | **retired as a website** (mail below) |

  1. **`bravenewsurf.com` is Django 1.3.7, not 1.8** — `MySQL-python`,
     `gdata==2.0.15`, `wsgiref==0.1.2`, last commit 2014-09-27. That is 2011-era
     Django, which *strengthens* the crawl-don't-bake call below.
  2. **`edtaxidermy.com` needs no crawl at all.** It has a live source repo that
     already builds to static output, and a `deploy.sh` that rsyncs `build/*` to
     jaguar. Mirroring it would be strictly worse than rebuilding it.
  3. **Two of the six domains have lapsed entirely** — no nameservers, no
     records at all. Nothing to migrate, nothing to preserve, no certificates to
     worry about.

  **All three in-scope domains are already on Cloudflare and already proxied**
  (`ada`/`cash` nameservers — the same pair as `surfguitar101.com`). The move to
  Pages is a per-zone origin change; there is **no nameserver or registrar
  work**, which the original entry did not know.

  **Recommended approach: crawl, do not bake.** `django-bakery` or
  `django-distill` requires resurrecting a Django 1.8 / Python 2 codebase well
  enough to render — expensive archaeology for sites nobody edits. A
  `wget --mirror` against the *running* site produces the same static output
  with zero code changes, which reduces the job from "port two Django sites" to
  "mirror two websites."

  **Crawl the origin, not the proxy (added 2026-08-23, measured).** Cloudflare
  **Email Address Obfuscation** is active on `themadeira.net`: the contact
  page's `mailto:` links come back through the proxy as
  `/cdn-cgi/l/email-protection#<hex>` hrefs and `__cf_email__` spans, decoded in
  the browser by a script Cloudflare injects at the edge. A crawl through the
  proxy therefore mirrors **the transformation, not the site** — capturing a
  `/cdn-cgi/` link target that will not exist on Pages, and markup that renders
  as a literal "[email protected]" placeholder if the decode script is not
  injected alongside it. Same family as the cache hazard: crawl what the origin
  serves, and treat any edge feature that rewrites HTML as something to bypass
  or disable for the duration. Open questions for a honing pass, all small: forms and
  POST endpoints, feeds and sitemaps, extensionless URLs (Pages handles clean
  URLs), where media lives, absolute-vs-relative link rewriting, the 404 page.

  **Ordering constraint, and the reason this belongs in Step 21 at all: the
  crawl must happen while jaguar is still serving.** Capture, verify the mirror,
  *then* decommission. Getting that backwards means reconstructing the sites
  from bobcat's rsync instead of from a live server.

  **Confirmed satisfied 2026-08-23, not merely restated.** Brian chose to cut
  sg101 over *first* and do the sites during the warm window. That ordering
  works because this cutover moves only `surfguitar101.com`'s DNS and leaves the
  other three zones pointing at jaguar — they stay live and crawlable
  throughout. The accepted trade is that capture happens later on an
  end-of-life box rather than sooner.

  **Also settled in that project's requirements pass** (`idea-honing.md`, Q1–Q8):
  all three sites are frozen (the band is on hiatus); media is mirrored as-is
  and the videos are YouTube embeds, so nothing large is hosted; the mailing-list
  form becomes a `mailto:`; deployment is `wrangler` direct upload rather than
  Pages' Git integration, which does not support Mercurial; and the acceptance
  bar is **URL parity measured against jaguar's Apache access logs** — which
  rotate weekly, `rotate 8`, so roughly **eight weeks** of history is all that
  will exist at crawl time unless logs are archived sooner.

  **RESEARCH COMPLETE 2026-08-24 — that project closed all seven of its open
  items, and three of the findings land on *this* step, not that one.**

  1. **jaguar's Apache logs have never been backed up — including sg101's.**
     `bobcat:/svr/scripts/jaguar_exclude.txt` excludes `**/access.log`,
     `**/access.log.1`, `**/access.log.*.gz` and the `error.log` equivalents,
     and the rsync runs `--delete`.
     `bobcat:/svr/backups/jaguar/www/*/log/` is **empty**. So the nightly job
     everyone reasonably assumed covered jaguar covers, for this one class of
     file, nothing — on an eight-week rolling delete, on an EOL box. The other
     project archived **its** three sites' logs to Brian's laptop on 2026-08-24
     (`evidence/access-logs-2026-08-24/`, 57 days, 29 Jun – 24 Aug).
     **`surfguitar101.com`'s and the wiki's logs are still unarchived**, and
     this step's cutover has a comparable evidentiary dependency. Two lines
     deleted from `jaguar_exclude.txt` would fix it going forward; an archive
     before cutover would fix it retrospectively. Neither has been done.
  2. **The email-obfuscation hazard recorded above is broader than measured.**
     It affects **all three** in-scope sites, not just `themadeira.net`, and
     `themadeira.net` additionally runs **Automatic HTTPS Rewrites**, which
     silently upgrades outbound third-party `http://` links at the edge. The
     "crawl the origin" rule stands and is now validated: origin-direct fetches
     return HTTP 200 with a publicly-trusted certificate on all three
     (`ssl_verify_result=0`), so `--resolve` / an `/etc/hosts` override works
     with no certificate handling.
  3. **The MX for `bravenewsurf.com` should be deleted, not migrated.** Live
     `main.cf` on jaguar shows `virtual_alias_domains = deathofagremmie.com
     themadeira.net surfguitar101.com` — `bravenewsurf.com` absent, and absent
     from `mydestination`, so Postfix refuses mail for it. (The file was edited
     2026-08-20, so this is current state, not the stale config repo.) That also
     closes one of the two remaining unproxied records publishing jaguar's real
     IP.

  Full evidence in that project's `research/` — `live-inventory.md`,
  `backups-and-logs.md`, `crawl-mechanics.md`, `url-universe.md`,
  `media-and-limits.md`.

- **A public IRC server is running on jaguar, and this plan retired the wrong
  thing (added 2026-08-24, found by that project's uninventoried-services
  sweep).** `ngircd` is listening on **`0.0.0.0:6667` and `0.0.0.0:6697`**, with
  `/svr/irc/sg101bot/sg101Bot.py` running as root alongside it — both live since
  Apr 23, with 7:21 and 86:32 of accumulated CPU time. **Neither this plan nor
  the decommission project mentions either process.**

  The near-miss is worth naming precisely: **Step 4 pruned a Django app called
  `irc`** — the chat *status page* that rendered who was online — and every
  reference in this tree (`app-triage.md`, `idea-honing.md`, Step 4's own entry)
  is to that app. **Removing it does not touch the daemon.** The plan retired
  the window; the room is still there, and it is still answering the public
  internet.

  This is **sg101's by content** (`sg101bot`, `/svr/irc/`) and therefore this
  step's to resolve — the decommission project explicitly does not own it, but
  cannot complete around it, because switching the box off switches off a live
  public service. **Decide and record the disposition: retire it, or move it
  with the rest.** `/svr/irc` *is* inside bobcat's rsync mirror, so the bot's
  code and config survive the box either way — only the running service does
  not. Unresolved sub-question: what listens on `127.0.0.1:23352` (attribution
  needs root).

- **`wiki.surfguitar101.com` is still an enabled vhost (noted 2026-08-24).**
  `/etc/apache2/sites-enabled/wiki.surfguitar101.com.conf`, symlink dated
  Apr 25, still serving MoinMoin via mod_wsgi — though **Step 19 records the
  wiki as retired.** Confirm whether the retirement was code-only and the vhost
  was left serving deliberately; if not, it is a second live service that dies
  unannounced with the box. (For contrast, the three genuinely retired vhosts —
  `briananddebra.com`, `deathofagremmie.com`, `tmensurf.com` — are present in
  `sites-available` but correctly **not** symlinked into `sites-enabled`, which
  confirms that hypothesis from the other project's Q1.)

- **Inbound mail on two zones, not one (corrected 2026-08-23).**
  `themadeira.net` was recorded here on 2026-08-21, found in a bounce sample
  (`orig_to=<themadeira@themadeira.net>`). **`bravenewsurf.com` carries the same
  dependency and was named nowhere** — the fourth item to surface by accident,
  which is the pattern this inventory exists to break.

  | zone | MX | resolves to |
  |---|---|---|
  | `themadeira.net` | `_dc-mx.658032ac2d3a.themadeira.net` | `173.255.245.115` — jaguar |
  | `bravenewsurf.com` | `_dc-mx.78cd6718bba2.bravenewsurf.com` | `173.255.245.115` — jaguar |
  | `deathofagremmie.com` | **none** | no inbound path exists at all |

  - **`themadeira.net`** stays Step 16 task 06 Phase 2's, as recorded — **but
    its blocker is now concrete, and it has a lead time nothing else in either
    project has.** Jaguar's `virtual_alias_maps` carries ten aliases on this
    zone forwarding to **five different people**, four of them band members
    rather than Brian. Cloudflare Email Routing requires every destination to be
    verified *by its owner clicking a link* — which is exactly why "rules to an
    unverified destination cannot be created" blocks Phase 2. It is a
    human-coordination dependency on four other people, and **jaguar cannot be
    switched off until it completes. Start it early.**
  - **`bravenewsurf.com`** — jaguar's `virtual_alias_domains` does not list the
    zone, so mail for it is most likely refused already and the MX is
    vestigial. **Not proven** (see the evidence note below). One bounce test to
    any `@bravenewsurf.com` address settles it; if it bounces, the record is
    deleted rather than migrated.
  - **`deathofagremmie.com`** has four live-looking aliases in the same file but
    **no MX record at all**, so nothing reaches them from the internet
    regardless. Nothing to migrate.

  **Both `_dc-mx` records are unproxied A records publishing jaguar's real IP** —
  the same origin-leak class measured for `surfguitar101.com` above, in two more
  zones. It stops mattering once jaguar is gone; it matters while the box is
  warm as a fallback.

- **bobcat's nightly rsync** — already recorded in detail on this step's
  checklist line above (backup box undocumented, added 2026-08-18), including
  its own broken FCrDNS and the 93%-deaf alarm that follows from it. Repointing
  it at the new VM belongs with the cutover, not after it.

**The prior that more exist was correct (updated 2026-08-23).** Each original
item was found by accident chasing an unrelated symptom; the sweep that followed
found a fourth — `bravenewsurf.com` mail — and corrected three of the first
three. **The remaining sweep of the live box** — vhosts actually enabled, cron
jobs, listening ports, DNS records still pointing at `173.255.245.115` — belongs
to the sites project's research phase and is tracked in its `STATUS.md`. It must
still happen before the warm-fallback window closes.

**Evidence grade, carried deliberately.** The Apache, Postfix, logrotate and
backup-script facts above come from the `jaguar_linode_cfg` repo, which **Brian
flagged 2026-08-23 as "probably incomplete and out of date."** Every DNS and
HTTP measurement is live and dated. **Do not promote the former to the latter
without re-measuring on the box** — most of the sites project's open research
items exist precisely to do that.

**ALSO CARRIES: outgoing mail on the new VM (added 2026-08-16, Brian's catch).**
Step 16 makes the *application's* mail a matter of environment variables, but
three things are properties of the host and can only be done once it exists —
ideally while it is stood up and not yet serving:
- **A send-only null client** (`msmtp`, or Postfix in satellite mode) so cron,
  logrotate and unattended-upgrades output reaches `bgneal@gmail.com`. With no
  MTA at all this output is silently discarded, which is how a failing backup
  goes unnoticed for weeks. This reproduces `/etc/aliases` from the old box
  (`root`/`brian`/`www-data` → Gmail), which Cloudflare Email Routing does
  **not** cover — Email Routing handles inbound mail from the internet and never
  sees local system mail. A null client has no MX, opens no port, and holds no
  reputation; it is a pipe, not a mail server.
- **Verify outbound egress before trusting it.** Many VPS providers block
  outbound port 25 by default — Linode does, unless you ask — and some restrict
  587. Postmark offers **2525** as an alternative if 587 is blocked. Test the
  connection from the VM itself rather than assuming, because the failure mode
  is silent queueing.
- **Confirm nothing listens on 25**, and that the VM publishes no MX record.
  The end state is no inbound mail path on the host at all.
- **Rewrite the null client's *sender*, not just its recipients — Postmark will
  refuse it otherwise** (added 2026-08-18). Cron mail leaves as
  `root@<hostname>`, and Postmark accepts only a From address on a verified
  domain or sender signature, answering "not a Sender Signature on this account"
  to anything else. Reproducing `/etc/aliases` covers where the mail *goes*;
  this is where it *comes from*, and it is the same `sender_canonical` rewrite
  Step 16 task 10 applied to jaguar on 2026-08-18 — where the identical defect
  had been destroying Django's error reports for years. Both halves are needed,
  and only one of them was written down.
- **Prove it by breaking something, not by reading the config** (added
  2026-08-18). `tools/email_smoke.py` proves the *application's* egress; it says
  nothing about the null client. Make a cron job fail on the new VM and confirm
  the message reaches Brian's inbox. **A misconfigured null client discards
  silently and looks exactly like a quiet server** — which is precisely how
  jaguar lost every root message, every certbot warning and every Django
  traceback for years without anyone noticing.

Verification belongs to Step 16's `tools/email_smoke.py`, run *from the VM*
rather than from a laptop — the point is to prove the host's egress, not the
tool's correctness.

**HOST DECIDED 2026-08-15: a single VM with persistent disk** (Linode or
Lightsail class). This was "late-binding, recommend single VM ... or Render", and
the ambiguity turned out to be load-bearing — the media strategy is downstream of
it, so it could not stay open. **Brian's decision**, after pricing both.

**Why the VM:**

- **This project is already a compose stack.** `docker-compose.yml` runs six
  services and dev and CI run that exact file; a VM runs it unchanged. A PaaS
  means decomposing it into a web service, a worker, a scheduler, managed
  Postgres and managed Key Value, each configured separately — a re-architecture
  landing at the riskiest moment in the project.
- **Cost, measured 2026-08-15** (third-party trackers; Render's own pricing page
  would not render, so verify before committing): Render works out to roughly
  **$80–115/month** for this stack — $25 workspace fee, $25 web, $7–25 worker,
  $7 beat, ~$6–20 Postgres, $10 Key Value, plus $0.15/GB bandwidth over 25 GB —
  against **~$24/month** for a 4 GB shared-CPU Linode running everything.
  Roughly 4x, for more work.
- **Render's persistent disks are a poor fit for user uploads**, from their own
  docs: a disk prevents scaling past one instance, **removes zero-downtime
  deploys** (the old instance stops before the new one starts), can grow but
  never shrink, cannot attach to a cron job, and **snapshot restore is
  all-or-nothing** — recovering one deleted photo would roll back every upload
  since the snapshot. That last property alone would push media to object storage
  anyway, i.e. force the full nine-field migration the VM lets us skip.

**A PaaS is not ruled out forever** — Brian's framing: revisit it as its own
`/pdd` after the modernization lands. It is out of scope here because moving
hosts and re-architecting deployment at the same time is two risks, not one.

**Media transfer, added 2026-08-15 — the plan had none at all.** This step
previously moved the database and nothing else, on a site that has served media
from local disk since day one: `bio` badges and 2,837 avatars, `smiley`, `news`,
`podcast`, `potd`, `banners`, 716 `downloads` MP3s, and the 4,577+ local user
photos. **Two passes**, for the same reason the database gets two:

```
# 1. Bulk, days ahead, site still live -- no window pressure
rsync -avz --partial old-box:/path/to/media/ /srv/sg101/media/

# 2. Delta, inside the maintenance window, AFTER the final DB snapshot
rsync -avz --delete old-box:/path/to/media/ /srv/sg101/media/
```

**Order matters:** the media delta must run *after* the final database snapshot,
or a photo uploaded between the two arrives as a row with no file. Verify a
count-and-spot-check of `user_photos.Photo` rows against files on disk before
flipping DNS -- the same "verify, do not assume" the Step 11 conversion earned.

**Audit production's working copy against the repo BEFORE the cutover, added
2026-08-15.** Production is known to have run at least one uncommitted
modification for roughly twenty months: `USER_PHOTOS_LOCAL_UPLOAD = True` was
live from 2023-05-08 (proved by `upload_date` on 4,577 photo rows) but only
committed on 2025-01-04 in `e53aa1f`. The setting is a plain assignment with no
env or `local_settings.py` path, so it had to be a direct edit of
`production.py` on the server, and `fab update` being `hg pull --update` means
such an edit survives every deploy silently. **A fresh clone onto the new host
drops any edit like it**, and the behavior change surfaces *after* cutover, not
during. Nothing in the repo can reveal a second instance. The check is cheap and
belongs in the pre-cutover checklist:

```
# on the old box, in the working copy
hg status          # anything modified/untracked that the repo does not have
hg diff            # exactly what differs
```

Treat any output as a decision to make deliberately -- commit it, port it, or
consciously drop it -- rather than something to discover later. Discovered while
rescoping Step 15; see STATUS.

**RUN 2026-08-16, and production's working copy is CLEAN** -- Brian reports no
outstanding edits to the sg101 hg repo on the old box. So **no second uncommitted
modification exists**, and this is consistent with the `USER_PHOTOS_LOCAL_UPLOAD`
story rather than contradicting it: that edit was committed in `e53aa1f`
(2025-01-04), so `hg pull --update` reconciled it and the tree went clean.

**Downgraded, not deleted.** Production stays live on the old code until the DNS
flip, which is six steps away, and the entire reason this item exists is that
such an edit survives deploys *silently* -- so a clean tree today says nothing
about a clean tree on cutover day. The item stands as **re-run at cutover**,
costing one command in the maintenance window, rather than as an open
investigation.

One known untracked artifact will show as `?`: `ssl_images_cache.json` in
`PROJ_DIR`, dated 2015-11-27 (see Step 15). It is an artifact, not configuration.

**Collation is part of the host decision, added 2026-08-13 alongside the ORDER BY
finding in Step 19.** This database is collated `en_US.utf8`, which is
**glibc's** collation, not PostgreSQL's own — so the sort order of every text
column is a property of the C library on the machine running the server. glibc
has changed that order between releases (the 2.28 change is the well-known one),
and when it moves underneath an existing cluster, **every index on a text column
is silently wrong until reindexed** — queries start missing rows that are
present. PostgreSQL records a collation version and warns on mismatch, but the
warning is easy to miss in a log.

This is currently controlled by accident rather than by decision: Postgres runs
from the pinned `postgres:16` image, so its glibc is pinned with it. Two things
in this step can break that, and both are live options:

- **Managed Postgres.** The provider chooses and upgrades the OS underneath.
  Worth asking what their collation-change policy is before committing data to
  it, and preferring a provider that pins or documents it.
- **A major-version or base-image upgrade of our own container**, which is the
  same hazard wearing our own clothes.

Two ways to take it off the table if either applies, to decide here rather than
discover later: run `REINDEX` on text indexes as a standard step after any
server or base-image move, or use **ICU collations** instead of glibc ones,
which are versioned explicitly and travel with the database rather than the host.
Note the second interacts with the `varchar_pattern_ops` index Step 20 adds for
the autocomplete, so it is not a free swap — but it is the option that stops the
question recurring.
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
**Carried in from Step 13 task 05 (2026-08-05): set Redis's memory bound, and set
it to `volatile-lru`.** That task moved the production cache off memcached (its
Django backend was removed in 4.1) onto Redis, which means **one Redis server now
does three jobs**: the Django cache on db 2, the Celery broker on db 1, and the
application's own kept state on db 0 — who's-online, the forums' latest-post
lists and RSS caches, the wiki's cookie set.

memcached evicted LRU by design; Redis ships `maxmemory 0` with
`maxmemory-policy noeviction`, so it is unbounded and, when it does fill,
**refuses writes rather than evicting**. A cache wants the opposite.

**The subtlety that makes the obvious setting wrong: `maxmemory-policy` is
server-wide, not per-database.** `allkeys-lru` would let Redis evict Celery
messages and the site's kept keys to make room for cached fragments.
**`volatile-lru` is the correct choice here**, because it only evicts keys
carrying a TTL: every Django cache key has one (the `TIMEOUT` is 600 and every
`cache.set` in the codebase passes an explicit timeout), while the db 0 keys
mostly do not — measured 2026-08-05, five of six sampled read `ttl=-1`. So the
cache is evictable and the kept state is not, which is the behaviour memcached
gave for free by being a separate process.

Not urgent, and deliberately not done mid-ladder: the whole cache is a handful of
keys and Redis was using **1.15 MB** when this was measured. It matters when the
site is on a VM with a real memory ceiling, which is here.

**Also worth knowing at cutover:** Django's Redis cache backend does not swallow
connection errors the way `python-memcached` did, so a Redis outage now returns
500s where it used to mean cache misses and a slow site. Redis was already
load-bearing for the db 0 state above, so this widens an existing single point of
failure rather than adding one — but it is an argument for Redis being monitored
on the new host, not just running.

**Carried in from Step 13 task 06 (2026-08-07): decide how the dev-only settings
split, because two principles already recorded here point opposite ways.**
`research/docker-strategy.md` says the dev override
(`docker-compose.override.yml`) owns "DEBUG, console email, debug toolbar, local
volumes" — and, separately, that this is **"one image, env-driven config… same
image runs dev and prod; behavior differs only by env."** Those two cannot both
hold for the toolbar. One image means the production image either carries
`django-debug-toolbar` or it does not: today's image is built from
`requirements-docker.txt`, which includes it, while `requirements.txt` does not.
So either prod ships a dev dependency that sits unused, or the image stops being
literally one image.

**Recommended resolution: a multi-target Dockerfile** — a `prod` target from
`requirements.txt` and a `dev` target layering `requirements_dev.txt` on top.
That keeps the parity the strategy is actually after (same base, same Python,
same build path, same artifact family) while letting a dev settings module assume
its packages are present.

**What that buys, and it is the point of doing it at all:** the toolbar block in
`local.py` can stop being conditional. Today it is
`if DEBUG and importlib.util.find_spec('debug_toolbar') is not None`, and each
half guards something different — `DEBUG` decides whether the toolbar is active,
`find_spec` guards against the package being absent. **Neither is protecting
production**, which is the thing worth knowing before designing this:
`production.py` imports from `base.py` directly and never goes through
`local.py`; only `docker.py` inherits it. The probe exists for a *bare-metal dev*
install that ran `requirements.txt` without `requirements_dev.txt`. Give dev its
own settings module loaded only by the dev compose file and that scenario stops
existing — the module's existence means "toolbar on," and both halves of the
conditional go, along with `docker.py`'s `SHOW_TOOLBAR_CALLBACK` override.

**Do the whole inheritance chain at once, not the toolbar alone.** `local.py`
still declares `'ENGINE': 'django.db.backends.mysql'` with a `unix_socket`
option, as does `production.py` — five steps after the PostgreSQL move, surviving
because nothing loads either module (the same silence that let a dead
`MemcachedCache` sit in `production.py` for a rung and a half). The dev/prod
settings reorganization, the stale MySQL engines and the toolbar conditional are
one piece of work, and splitting them means touching `local.py` three times.

**One thing to preserve while moving it:** the toolbar's position in `MIDDLEWARE`
is load-bearing and is commented in place. It sits *after* `CommonMiddleware`
deliberately — middleware at index 0 wraps index 1, so moving it earlier routes
`CommonMiddleware`'s `APPEND_SLASH` redirects through `RedirectsPanel`, which is
live because `DISABLE_PANELS` is empty. Measured both ways: `/forums` answers 301
from the current position and 200 with an interstitial from index 0. A
reorganization that rebuilds `MIDDLEWARE` from scratch is exactly where that gets
lost.

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
PostgreSQL**, behind Cloudflare, on a supported VM, with user photos uploading to
S3 again and provider email — off the unpatched dedicated server.

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
