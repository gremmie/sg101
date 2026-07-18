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
- [ ] **Step 7** — Make code Python 2/3 compatible (Django 1.11, still Python 2.7)
- [ ] **Step 8** — Flip interpreter to Python 3 (Django 1.11) ⭐ milestone
- [ ] **Step 9** — Upgrade Django 1.11 → 2.2 LTS (Python 3)
- [ ] **Step 10** — Upgrade Django 2.2 → 3.2 LTS (Python 3)
- [ ] **Step 11** — Migrate MySQL → PostgreSQL (on 3.2 / Py3)
- [ ] **Step 12** — Build PostgreSQL full-text search (restore `/search/`)
- [ ] **Step 13** — Upgrade Django 3.2 → 4.2 (Python 3)
- [ ] **Step 14** — Upgrade Django 4.2 → 5.2 LTS (Python 3.12) ⭐ target reached
- [ ] **Step 15** — Media → Cloudflare R2 (boto3)
- [ ] **Step 16** — Email → transactional provider
- [ ] **Step 17** — reCAPTCHA → Cloudflare Turnstile
- [ ] **Step 18** — Revive `gcalendar` with modern Google libraries
- [ ] **Step 19** — Retire `wiki`/MoinMoin; verify-then-prune `contests`/`banners`/`membermap`/`oembed`
- [ ] **Step 20** — Production hardening (gunicorn/WhiteNoise/prod compose/backups) + Cloudflare front
- [ ] **Step 21** — Deploy to new host + cutover + fallback

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
**Guidance:** Add `psycopg` 3; parameterize DB via env (Step 3). Convert a
snapshot with **`pgloader`** (well-documented, since it's new to the user);
address charset/utf8mb4, case-sensitivity (usernames/emails/tags — add `CITEXT`/
constraints), sequences. Run Django migrations on Postgres. CI gains a **Postgres
service container**.
**Tests:** Full suite green on **Postgres**; data-integrity checks (row counts,
spot content) vs. the MySQL snapshot; keep sqlite for fast unit runs but add a
Postgres CI job.
**Integration:** Compose `db` service becomes Postgres; all later rungs test on PG.
**Demo:** SG101 running on PostgreSQL with migrated production data; suite green on PG.

### Step 12: Build PostgreSQL full-text search (restore `/search/`)
**Objective:** Replace the removed Xapian search with native Postgres FTS —
restoring search functionality for the first time since it was stubbed.
**Guidance:** Add `SearchVectorField` + GIN indexes to the searchable models
(forum topics/posts, bios, news, weblinks, podcast, downloads, ygroup); implement
the `/search/` and `/search/ajax/` views with `SearchQuery`/`SearchRank`;
maintain vectors via `save()`/signals or a periodic Celery task; delete the stub.
Validate against the current-behavior notes documented in Step 1.
**Tests:** New search tests (indexing on create/update, query relevance,
permissions/public-only results); functional tests for the search pages.
**Integration:** Uses Postgres from Step 11 and Celery for (re)indexing.
**Demo:** Search the live local site and get real results across forums/news/etc.
— no native libraries, no separate search server.

---

## Phase D — Finish the ladder

### Step 13: Upgrade Django 3.2 → 4.2 (Python 3)
**Objective:** Traverse to 4.2 (a pass-through — EOL, so we don't rest here long).
**Guidance:** Address 4.0/4.1/4.2 changes (`USE_TZ` defaults, `zoneinfo` replacing
pytz, `django.conf.urls.url` fully removed, `CSRF_TRUSTED_ORIGINS` scheme).
Continue dep bumps. Clear deprecations.
**Tests:** Suite green on Postgres; smoke checklist.
**Demo:** Site on Django 4.2 / Py3 with working search.

### Step 14: Upgrade Django 4.2 → 5.2 LTS (Python 3.12) ⭐
**Objective:** Reach the target end-state.
**Guidance:** Move base image to **Python 3.12**; bump Django to 5.2 LTS; final
dependency alignment; clear all deprecations.
**Tests:** Full suite green on Django 5.2 / Py3.12 / Postgres; smoke checklist.
**Demo:** SG101 running on the **target stack (Django 5.2 LTS, Python 3.12,
PostgreSQL)** locally with real data and working search.

---

## Phase E — Modernize subsystems (resolve the Step 8 stubs, adopt Cloudflare)

### Step 15: Media → Cloudflare R2 (boto3)
**Objective:** Return user uploads to object storage; resolve the Step 8 `boto` stub.
**Guidance:** Rewrite `core/s3.py` for `boto3` (or `django-storages`) with R2's
custom `endpoint_url`; move `USER_PHOTOS_*` to env-configured R2; bulk-copy
existing local media to the bucket; update `USER_IMAGES_SOURCES`.
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
`WikiMiddleware`, and `wiki.tasks.expire_cookies`. Verify usage of `contests`,
`banners`, `membermap`, `oembed` against the snapshot; keep or prune each.
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
