# AGENTS.md

Guidance for AI coding agents working in this repository. Deeper detail lives in
[`.agents/summary/index.md`](.agents/summary/index.md) — a snapshot generated
2026-08-27, describing production as it ran then. Where it and this file
disagree, this file is newer.

## What this is

The Django application behind **SurfGuitar101.com**, a community site for
instrumental surf music fans: forums, news, podcast, photo of the day, downloads,
weblinks, a band map, private messaging, polls, contests, donations, an event
calendar.

**Python 3.12 / Django 5.2 LTS / PostgreSQL 16 / Redis / Celery. Git.**

The repo is **mid-modernization, and none of it is deployed yet.** Production
still runs the old code (Python 2.7, Django 1.8, MySQL, Apache + `mod_wsgi`) on
the old host, jaguar, until the Step 21 cutover. So what this repo does and what
the live site does can differ. Which steps are done, and why, is in
`.agents/planning/2026-07-04-modernizing-sg101/STATUS.md`, which is
authoritative; this file does not track it.

## Layout

Every top-level directory is a Django app on the standard layout. The Django
*project* package is `sg101/`, not the repo root.

- `sg101/settings/` — `base.py` holds everything shared; `dev.py`,
  `production.py`, `test.py`, `docker_test.py` override it. One module per
  deployment: `dev.py` is the Compose stack, `production.py` the VM.
- `core/` — the shared kernel: mail wrapper, Markdown rendering, Redis and S3
  helpers, middleware, pagination. **It imports nothing else in the repo.** Keep
  it that way.
- `search/` — native PostgreSQL full-text search.
- `antispam/` — spam phrases, auth-failure logging, Turnstile verification.
- `tools/` — standalone scripts, run directly rather than via `manage.py`.
- `.agents/planning/` and `.agents/tasks/` — the modernization record.

`sg101/urls.py` mounts each app under a prefix, and **prefixes do not always
match app names** (`bio` → `/profile/`, `weblinks` → `/links/`, `gcalendar` →
`/calendar/`). Grep it rather than guessing.

## Running things

```
docker compose up -d
docker compose exec web python manage.py test --settings=sg101.settings.docker_test
```

**The deprecation gate is a second, separate run**, and it is what has caught
every Django removal a version before it landed:

```
docker compose run --rm -e PYTHONWARNINGS="$(tools/deprecation_gate.sh)" web \
    python manage.py test --noinput --settings=sg101.settings.docker_test
```

`tools/deprecation_gate.sh` only *prints* the filter. Running it and seeing exit
0 is **not** the gate passing.

## Non-obvious things

- **Config is 12-factor and there is no `secrets.json`.** Everything reads the
  environment via `django-environ`. `.env` is git-ignored; `.env.example` is
  committed with working defaults and is what CI seeds from.
- **Logging is disabled wholesale in the test settings**, so `assertLogs` sees
  nothing until you re-enable it — and the failure looks like a missing log line
  that is not missing. Copy the enable-and-restore dance in
  `contact/tests/test_views.py` or `antispam/tests/test_turnstile.py`.
- **`CELERY_TASK_ALWAYS_EAGER` hides worker faults by construction.** A broken
  deferred task passes the suite and fails in a browser. Browser-test anything
  touching deferred work.
- **`REMOTE_ADDR` is only correct because Apache rewrites it** from
  `CF-Connecting-IP` via `mod_remoteip`, believing it only from the ranges in
  `apache/cloudflare-ranges.txt`. Gunicorn is a separate process, so it takes a
  second hop: the vhost passes the answer as `X-Real-IP`, and
  `core.middleware.RealClientIP` puts it back into `REMOTE_ADDR`. Use
  `core.functions.get_ip`, and never prefer `X-Forwarded-For` — any client can
  forge it.
- **Log retention differs per file and limits what you can ask.** `sg101.log`
  rotates at 100 KB x 10 (~5 months); `auth.log` at 2 MB x 5 (19+ months).
- **The `messages` app collides with `django.contrib.messages`.** Resolved in
  `sg101/apps.py` (`DjangoMessagesConfig`), which relabels the built-in app to
  `django_messages`. Don't rename this app or its `AppConfig` without
  understanding why.
- **Moderation uses split models, not a boolean.** `downloads`, `weblinks` and
  `news` each have a `*Base` subclassed into `Pending*` and the live model.
  Extend that; don't add `is_approved`.
- **Rendered HTML is cached in sibling fields** (`Post.body`/`html`) and rendered
  at save time. Changing rendering needs a data migration, not just a template
  change.
- **The v3 stylesheet is a committed build artifact.** `sg101/scss/` compiles to
  `sg101/static/css/v3/main.min.css` via `npm run build:css` in `sg101/`. Editing
  the built file works until the next rebuild discards it — change the Sass and
  commit both. The application image has no Node and deploys do not build CSS, so
  a forgotten rebuild ships stale styling with no error anywhere.

- **The `wiki` app is gone.** It minted a cookie for an external MoinMoin wiki to
  validate against Redis. The wiki itself still runs on the old host until the
  cutover, when it becomes a redirect; its content is archived under
  `archive/wiki/`.
- **`antispam/utils.py` imports `bio`, `comments`, `forums` and `user_photos`.**
  For something with callers in several apps, follow the narrow shape of
  `antispam/decorators.py` or `antispam/turnstile.py` instead.
- **`fabfile.py` is stale** — it runs `hg pull --update`, from before the move to
  git. It is not the deploy path; deployment is Step 21 and hasn't happened.
- **`tools/xapian_installer.sh` is a leftover** of the search stack removed in
  Step 4. Nothing uses it.
- **Search `.agents/` before concluding something is undocumented.** A great deal
  of apparent mystery here is recorded with the measurement attached.

## Custom Instructions

<!-- This section is maintained by developers and agents during day-to-day work.
     It is NOT auto-generated by codebase-summary and MUST be preserved during refreshes.
     Add project-specific conventions, gotchas, and workflow requirements here. -->
