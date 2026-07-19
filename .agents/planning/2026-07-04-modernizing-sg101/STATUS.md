# Project Status — Modernizing SG101

**Last updated:** 2026-07-19
**Methodology:** Prompt-Driven Development (`/agent-sops:pdd`)

## EXECUTION — Step 8 (flip interpreter to Python 3.7, Django 1.11) ⭐ — DONE (2026-07-19)

The central milestone: SG101 runs on **Python 3** for the first time, still on the
Django 1.11 LTS rung. **559 tests green under Py3.7, 5 skipped (S3), 84% coverage**
via the exact CI command; live smoke green on the real production snapshot (site +
celery worker + beat). NOT pushed yet (Brian pushes his own remotes).

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
