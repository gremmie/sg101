# Task: Serve the Application with gunicorn and WhiteNoise

## Description
Replace Django's development server with gunicorn in the production image, and
give static files a real home through WhiteNoise and a `STATIC_ROOT` that is not
a temporary directory.

**Amended 2026-09-17.** As generated, requirement 1 told gunicorn to serve
`sg101.wsgi`, **which does not exist**; and the static-assets decision `plan.md`
ties to the Sass toolchain was not referenced. See *Amendment record* at the end.

## Background
The production image currently ends in
`CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]`. `runserver` is
Django's development server — single-threaded, auto-reloading, and documented as
unsuitable for production use. Neither `gunicorn` nor `whitenoise` appears
anywhere in the repository today: not in `requirements.txt`,
`requirements-docker.txt`, the `Dockerfile`, or any settings module.

**`sg101/settings/base.py:95` sets `STATIC_ROOT = '/tmp/test_static_root'`** — a
test value living in the base module, so `collectstatic` has no real destination.

On jaguar, Apache serves static files from a `static_serve` directory via the
config in `sg101/apache/`. That configuration does not travel with the code.

**There is no `sg101/wsgi.py`.** Verified 2026-09-17: the settings package has
`__init__`, `base`, `databases`, `docker`, `docker_test`, `local`, `production`
and `test`, and `sg101/` itself has `apps.py`, `celery.py`, `urls.py` and
`views.py` — no WSGI module. `runserver` builds its own handler, so nothing has
needed one. What exists is **`sg101/apache/sg101.wsgi`**, a mod_wsgi script for
jaguar: it `site.addsitedir`s a **Python 2.7** site-packages path, appends
`/svr/django-sites/sg101/...` to `sys.path`, sets a `PYTHON_EGG_CACHE`, and
hardcodes `DJANGO_SETTINGS_MODULE = 'sg101.settings.production'`. Pointing
gunicorn at it would fail; pointing gunicorn at `sg101.wsgi` fails too, with
`ModuleNotFoundError`.

**That script also carries a feature nothing else does.** An `OFFLINE = False`
flag at the top switches the whole site to an `offline_handler` that serves
`sg101/templates/offline.html` with `503 Service Unavailable` (and `405` on
non-GET) — a maintenance mode toggled by editing the file and touching it, which
is how `fabfile.py:33` reloads the app. The template is still in the tree. When
the mod_wsgi script goes, **maintenance mode goes with it unless something
replaces it**, and the one day it is most likely to be wanted is cutover day.
WhiteNoise replaces it by serving static assets from inside the application, which
keeps the container self-contained. **Cloudflare fronts the origin**, so WhiteNoise
serves each asset once to the edge rather than to every visitor, and the usual
performance objection does not apply at this site's volume.

**WhiteNoise covers static files only.** `/media` — avatars, `downloads`, `potd`,
smilies, banners — stays on the VM's disk and is served by the proxy; user photos
are on S3. Conflating the two is the failure mode to avoid.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`
  (§3.2 target state — gunicorn and WhiteNoise appear in the diagram)

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/research/docker-strategy.md`
  (*Static files* — records that prod uses `ManifestStaticFilesStorage` today)

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. **Create `sg101/wsgi.py`** — the standard `get_wsgi_application()` module,
   taking `DJANGO_SETTINGS_MODULE` from the environment with a sensible default,
   never hardcoding production the way the mod_wsgi script does.
2. Add `gunicorn` to **`requirements.txt`** — task 01 deleted
   `requirements-docker.txt` after measuring it equal to this file plus the three
   dev pins, so `requirements.txt` is now what the `prod` target installs and
   `requirements_dev.txt` reaches the `dev` target through its `-r`. One file,
   one edit. Leave `main`'s `requirements.txt` alone: that is what live
   production on jaguar installs from. Make gunicorn the production image's
   entry point, serving `sg101.wsgi:application`.
3. Size the worker count from the VM's CPU count rather than hardcoding it, and
   record the reasoning in a comment.
4. Add `whitenoise` to `requirements.txt` and place its middleware
   immediately after `SecurityMiddleware` — **which this project does not have.**
   Found 2026-09-17 running `check --deploy` against the production module
   during task 01: `security.W001`, *"You do not have
   'django.middleware.security.SecurityMiddleware' in your MIDDLEWARE"*.
   `base.py:112` starts `MIDDLEWARE` with `CommonMiddleware`, and **no `SECURE_*`
   setting is defined anywhere in the package.** So this requirement as written
   cannot be followed, the same way requirement 1 named a `sg101.wsgi` that did
   not exist.

   **Decide the middleware before placing WhiteNoise after it.** Adding
   `SecurityMiddleware` is not a formality: it is what makes
   `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS`, `SECURE_CONTENT_TYPE_NOSNIFF`
   and `SECURE_REFERRER_POLICY` do anything, and HSTS in particular is
   difficult to walk back once a browser has cached it. It also interacts with
   the Cloudflare front, which already terminates TLS. Treat it as its own
   decision with its own values, and place WhiteNoise relative to whatever that
   decides — WhiteNoise's own requirement is only that it sit above the
   middleware that would otherwise serve static files, not that
   `SecurityMiddleware` exist.

   Note the toolbar sits at `MIDDLEWARE[0]` in dev and is asserted there by
   `core/tests/test_settings.py`, so a new first middleware changes that test.
5. Give `STATIC_ROOT` a real path outside `/tmp`, and confirm whether the
   existing `ManifestStaticFilesStorage` configuration survives Django 5.2's
   `STORAGES` setting. Task 01 leaves a placeholder value; the decision is this
   task's.
6. Run `collectstatic` as part of the image build or the container entry point,
   and state which and why.
7. **The fate of `sg101/apache/sg101.wsgi` and of maintenance mode — DECIDED
   2026-09-17.**

   **The script is deleted from this branch.** It is Python 2.7 site paths for a
   host being decommissioned, and it hardcodes a settings module. Jaguar keeps
   its own copy, which is on `main` under hg, so **deleting it here does not
   touch the running site** — and jaguar's copy is still needed, because its
   `OFFLINE` flag is what freezes writes during the cutover window. Recorded as
   `cutover-runbook.md` **C0**, before the final snapshot.

   **Maintenance mode is not rebuilt in `wsgi.py`.** The flag worked under
   mod_wsgi because it reloaded on mtime; gunicorn imports the module once per
   worker, so flipping a boolean means a restart either way. It also only
   answers while the application is up, which is not the case it is wanted for.

   **Two layers replace it, neither of them this task's:**

   - **Cloudflare, primary.** A maintenance Snippet (or the same template as a
     Worker on the free plan) returns a 503 page **without contacting the
     origin**, so it covers the VM being down, and it supports an IP allowlist
     so the site can be verified while others see the notice. **Watch the
     Workers free tier**: 100k requests/day against a measured ~90.8k/day, so
     bind the route only while maintenance is on rather than leaving it bound
     behind an internal flag.
   - **Apache in the compose stack, backstop — task 03's.** A rewrite conditioned
     on a file's existence gives a page that can be toggled over SSH with
     `touch`, needing no dashboard, and it works when gunicorn is stopped for a
     migration. `sg101/templates/offline.html` stays in the tree as its content.
8. Leave the development workflow on `runserver`.

### The static-assets decision this task shares with task 10

`plan.md` is explicit that **"is built CSS a committed artifact or a deploy-time
build step?"** is *"one decision about static assets, not two"* — it interacts
directly with WhiteNoise, `collectstatic` and the `ManifestStaticFilesStorage`
that `production.py:38` already names. Committing built CSS is what the project
has always done and it keeps deploys simple; building at deploy time removes the
artifact from review but puts Node in the production image.

**Decide it here, and record it here.** Task 10 rebuilds the toolchain and
inherits this decision — it does not re-make it. Sequencing note: task 10 can
run before or after this task, but the decision cannot be deferred past whichever
runs first.

## Dependencies
- Task 01 — the `prod` Dockerfile target and the consolidated settings package
- Task 10 — shares the committed-artifact-vs-deploy-build decision above
- Django 5.2's `STORAGES` setting, which supersedes `STATICFILES_STORAGE`
- `sg101/templates/offline.html`, if maintenance mode is kept

## Implementation Approach
1. Write `sg101/wsgi.py` first and prove gunicorn can serve it, before touching
   static files — an entry point that does not import is the failure that makes
   everything after it ambiguous.
2. Add both packages and wire the middleware, checking the existing static
   storage configuration against Django 5.2 rather than assuming it carries over.
3. Give `STATIC_ROOT` a real value and move it out of the base module if the test
   settings are what wanted `/tmp` (`base.py:95` is `/tmp/test_static_root`).
4. Replace the production `CMD` with gunicorn; leave the dev target alone.
5. Verify by requesting a static asset from a running production container and
   reading the response headers, not by inspecting configuration.

## Acceptance Criteria

1. **The production image does not run `runserver`**
   - Given the image built at the `prod` target
   - When it is started
   - Then gunicorn serves the application and `runserver` appears nowhere in the
     production path

2. **`collectstatic` has a real destination**
   - Given production settings
   - When `collectstatic` runs
   - Then assets land under a non-temporary `STATIC_ROOT` and the command reports
     a non-zero file count

3. **Static assets are served with cache headers**
   - Given a running production container
   - When a hashed static asset is requested
   - Then WhiteNoise serves it with a long-lived `Cache-Control` header

4. **A missing asset is a 404, not a 500**
   - Given a running production container
   - When a nonexistent static path is requested
   - Then the response is 404

5. **The WSGI entry point takes its settings from the environment**
   - Given `sg101/wsgi.py`
   - When it is imported with `DJANGO_SETTINGS_MODULE` set
   - Then that module is used, no settings module is hardcoded, and
     `sg101/apache/sg101.wsgi`'s Python 2.7 paths appear nowhere in the
     production path

6. **The static-assets decision is written down**
   - Given the planning record for this step
   - When it is read
   - Then it states whether built CSS is committed or built at deploy time, and
     task 10 is consistent with it

7. **The suite stays green**
   - Given the full test suite run the way CI runs it
     (`manage.py test --noinput --settings=sg101.settings.docker_test`)
   - When it is run
   - Then it passes, including coverage of the static configuration

## Metadata
- **Complexity**: Medium
- **Labels**: gunicorn, WhiteNoise, Static Files, Production Hardening
- **Required Skills**: WSGI servers, Django static files, Docker

## Amendment record — 2026-09-17

1. **Requirement 1 told gunicorn to serve `sg101.wsgi`, which does not exist.**
   The only WSGI file in the tree is jaguar's mod_wsgi script under
   `sg101/apache/`, on Python 2.7 paths. Creating the module is now requirement 1
   and has its own acceptance criterion.
2. **Maintenance mode was about to be deleted silently.** The `OFFLINE` flag and
   `offline.html` live only in that script; its replacement is now an explicit
   decision rather than a casualty.
3. **`requirements.txt` was named alone** for two new dependencies. The image
   and CI install `requirements-docker.txt`, so both files on this branch get the
   pin — and `main`'s copy, which is what jaguar installs from today, gets
   neither.
4. **The committed-CSS-vs-deploy-build decision is now referenced here**, where
   `plan.md` says it belongs — with task 10 inheriting it rather than re-deciding.
5. **`SecurityMiddleware` does not exist in this project** (2026-09-17), so
   requirement 4's anchor had to become a decision rather than a position. Found
   by running `check --deploy`, which is the second premise in this file that
   reading alone would not have caught.
