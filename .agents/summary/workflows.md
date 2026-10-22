# Workflows

**Generated 2026-10-21.** `make help` lists every everyday command for both
stacks; this file covers what the target names do not say.

## Local development

The dev stack is `docker-compose.yml`: `postgres` (16), `redis`, `web`
(`runserver`, `sg101.settings.dev`, the debug toolbar), `worker`, `beat`, and
`db` (mysql:5.7), which is **profile-gated behind `--profile mysql`** and exists
only for converting and verifying a jaguar snapshot.

```
docker compose up -d          # or: make up
```

`.env` is git-ignored and loaded via Compose's `env_file:`. Seed it from the
committed `.env.example`, which carries working defaults — including
Cloudflare's public Turnstile test keys, so a fresh checkout has working forms
with no account anywhere.

`make snapshot` / `make snapshots` take and list dev database snapshots in
`snapshots/`, through `tools/pg_snapshot.sh`.

## Testing — two runs, not one

```
docker compose exec web python manage.py test --settings=sg101.settings.docker_test
```

**The deprecation gate is a separate run**, and it is what has caught every
Django removal on this project a version before it landed:

```
docker compose run --rm -e PYTHONWARNINGS="$(tools/deprecation_gate.sh)" web \
    python manage.py test --noinput --settings=sg101.settings.docker_test
```

`tools/deprecation_gate.sh` **only prints the filter**. Running the script and
seeing exit 0 is not the gate passing — the gate is the suite run with that
filter applied. `make deprecation-gate` runs it properly.

**`PYTHONWARNINGS` rather than `-W`, deliberately:** `-W` does not reach
subprocesses, and `core/tests/test_settings.py` runs assertions through a
subprocess helper that would otherwise sit outside the gate.

**Browser tests** drive headless Chromium through Playwright, which the dev
image carries. They subclass `core/tests/browser.py`'s base class and are
tagged `browser`: `make test-browser` runs only them, and the ordinary suite
includes them. They exist for faults a unit test cannot see — JavaScript, and
work deferred to Celery.

## Writing tests — two things that will bite

**Logging is disabled wholesale in the test settings.** `assertLogs` sees nothing
until you re-enable it, and the failure presents as a missing log line that is
not missing:

```python
old_disable = logging.getLogger().manager.disable
logging.disable(logging.NOTSET)
self.addCleanup(logging.disable, old_disable)
```

`contact/tests/test_views.py` and `antispam/tests/test_turnstile.py` both do
this.

**`CELERY_TASK_ALWAYS_EAGER` hides worker faults by construction.** A broken
deferred task passes the suite and fails in a browser. Browser-test anything
touching deferred work.

## CI

`.github/workflows/ci.yml` runs on **every branch push** and on PRs to `main`.
In order: the committed stylesheet must rebuild to itself; `.env` is seeded
from `.env.example`; the same image a developer runs is built; missing
migrations fail the run; the suite runs **under the deprecation gate**, with
coverage; and the production image must run unprivileged at its fixed UID.

## The v3 stylesheet

`sg101/scss/` compiles to `sg101/static/css/v3/main.min.css` with `make css`
(`npm run build:css` in `sg101/`, Sass + PostCSS). **The output is committed**:
the application image has no Node and deploys build no CSS. Change the Sass,
rebuild, commit both. CI's first step catches a stylesheet that does not match
its Sass.

## Deploying

Production is a git checkout at `/svr/sg101` on leopard, on `main`.

```
git pull
make prod-up        # build, then start; runs no migrations
make prod-deploy    # instead, when the pull carries migrations
```

`prod-deploy` builds while the old containers still serve, turns maintenance
mode on (Apache answers `offline.html` with a 503), migrates from the new
image, starts the new containers, waits for `web`'s health check, and turns
maintenance off. Neither target pulls the base image; run
`docker pull python:3.12` first when a base-image change (CA certificates, a
bundled pip) is wanted.

`fabfile.py` is **stale** — it runs `hg pull --update` — and is not the deploy
path. `.agents/planning/2026-07-04-modernizing-sg101/cutover-runbook.md` § D9
is the deploy procedure of record.

gunicorn's worker count is `GUNICORN_WORKERS` and Celery's is
`CELERY_WORKER_CONCURRENCY`, both **required** in production's `.env`; the
compose file refuses to start without them.

## Backups and restores

A host timer runs the `backup` service nightly at 04:30 UTC: `pg_dump -Fc` to
the dumps bucket (90-day expiry) and `aws s3 sync` of `media/` to the media
bucket (never deleted, prior versions kept). Both buckets are versioned. **The
job's credential can only list and add**, so a compromised host can neither
destroy nor read the backups; a restore needs an administrative credential.
`make prod-backup` runs one now, and `make prod-backup-drill` rehearses backup
and restore against a local MinIO. `DOCKER.md` has the restore procedure.
**After any database restore, run `manage.py rebuild_redis`.**

## Operating the edge

- `make blocklist-show` / `blocklist-add` / `blocklist-remove` /
  `blocklist-clear` — the Cloudflare block list that fail2ban writes.
- `make firewall-plan` / `firewall-check` / `firewall-apply` — the origin
  firewall against `apache/cloudflare-ranges.txt`.
- `make cloudflare-ranges-check` — the ranges file against Cloudflare's lists.
- `make prod-proxy-reload` — test Apache's config, then reload gracefully.

## Where the project record lives

`.agents/planning/` holds each planning project; `2026-07-04-modernizing-sg101/STATUS.md`
is authoritative for the modernization, including the reasoning behind
decisions that look odd. `.agents/tasks/` holds the task files. **Search these
before concluding something is undocumented** — a great deal of apparent
mystery in this codebase is recorded there with the measurement attached.
