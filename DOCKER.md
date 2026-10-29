# Running SG101 locally with Docker

Run the SG101 site (Python 3.12 / Django 5.2 / PostgreSQL 16 / Redis) on
your Mac inside Docker, seeded with a copy of the production database. Docker gives us a
consistent little Linux environment that matches the target deploy platform —
handy for a stack this far from a modern Mac's defaults.

New to Docker? The only concepts you need here:

- **Image** — a blueprint (built from `Dockerfile`) with Python 3.12 + all the
  app's dependencies baked in.
- **Container** — a running instance of an image. Each service (`web`, `postgres`, …)
  is its own container.
- **Compose** — `docker-compose.yml` describes all the containers and how they
  talk to each other, so one command starts the whole thing.

---

## 0. Prerequisites (one time)

1. **Install Docker Desktop** and launch it once so the engine is running (the
   whale icon appears in the menu bar):
   ```
   brew install --cask docker
   ```
   Then open **Docker.app** and let it finish setup.
2. Verify it works:
   ```
   docker --version
   docker compose version
   ```

## 1. Provide the two local-only files (one time)

Neither is committed to source control.

1. **`.env`** — SECRET_KEY, DB credentials, and API keys, read from the
   environment (12-factor config). Copy the template; the example's defaults work
   as-is for local dev (a placeholder SECRET_KEY, `DB_*` values that match the
   `postgres` service, and blank/optional API keys):
   ```
   cp .env.example .env
   ```
   `.env` is git-ignored; Compose loads it into the app services via `env_file:`.

2. **A copy of the production database** — a PostgreSQL dump in `snapshots/`,
   e.g. one of production's nightly backups (section 4 below).

## 2. Build the image

Downloads Python 3.12 + installs the pinned dependencies. The first build takes a
while (several minutes); later builds are cached.
```
docker compose build
```

## 3. Start the stack

```
docker compose up
```
This starts five services: `postgres`, `redis`, `web`, `worker`, `beat`. The app
runs on PostgreSQL with nothing to configure. Leave this running in this
terminal (it streams logs). Open a
**second** terminal for the commands below. To run it in the background instead,
use `docker compose up -d`.

The site is now at **http://localhost:8000** — but the database is empty until
you load a snapshot.

**Create the schema** on an empty `postgres` service, if you are not loading a
snapshot (once, or again after `docker compose down -v`):
```
docker compose exec web python manage.py migrate
```

## 4. Load a copy of production

Production's nightly backup is a PostgreSQL dump (`pg_dump -Fc`) in the dumps
bucket (section 8, *Backups, and restoring from them*). Reading it needs an
administrative credential, because the backup's own cannot. Copy the one you
want into `snapshots/`, which is git-ignored and mounted into the `postgres`
container:
```
aws s3 cp "s3://$DUMPS_BUCKET/sg101-<time>.dump" snapshots/
```

Then restore it, rebuild what is derived from it, and check:
```
tools/pg_snapshot.sh restore sg101-<time>.dump
docker compose exec web python manage.py rebuild_redis --noinput
docker compose exec web python manage.py reindex_search
docker compose exec web python manage.py reconcile_search
```
Section 6 says why each step is there. A dump of production holds password
hashes and private messages: keep it in `snapshots/` and nowhere that syncs.
Then reload http://localhost:8000 and you should see real forum/news content.

## 5. Run the test suite

```
docker compose exec web python manage.py test --settings=sg101.settings.docker_test
```
No snapshot needed — Django builds a throwaway `test_sg101` database from the
migrations and drops it again. 887 tests, about 12 seconds.

**The suite runs on PostgreSQL, the same engine the site runs on.** It used to
run on sqlite, which was roughly two seconds faster; that is the whole of what
the change costs, and it buys a suite that can see engine-specific behavior. Two
things made it the obvious call: full-text search is Postgres-only, so a portable
suite could not cover the search implementation at all, and this project has
already had an app's migrations drift from the schema it runs against without a
test noticing. There is no sqlite path any more — one engine, one schema, from
your terminal through to CI, which runs this exact command.

If a previous run left a test database behind, Django asks before dropping it;
add `--noinput` to answer yes, or `--keepdb` to reuse it and save a second.

### Smoke-testing image uploads

```
docker compose exec web python /app/tools/image_smoke.py
```

Uploads real JPEGs and PNGs — including an RGBA one and a JPEG carrying EXIF
orientation — through the avatar, user-photo and photo-of-the-day views, checks
what came back out of storage, and deletes everything it made. Run it after a
Pillow bump or any change under `core/images/`.

The suite mocks PIL and storage in most places and runs against a throwaway
database, so it cannot tell you an upload works on *this* deployment. This can,
and that gap is not hypothetical: a resampling constant was once reverted with
its own mock assertions and 41 tests stayed green over an upload path that
raised on the first real image.

By default the user-photo checks are forced down the local-disk branch, so
nothing touches S3.

#### Against the real S3 bucket

```
docker compose exec web python /app/tools/image_smoke.py --s3
```

Adds a round trip through the real `sg101.user.photos` bucket: uploads through
the view, fetches the object back over plain https **with no credentials** —
which is what proves it is publicly readable — checks the metadata the upload
attached, deletes it through `user_photos.storage.delete_photos` so the local/S3
routing is exercised against a real S3 URL, and confirms it is gone.

**This needs live `AWS_ACCESS_KEY` / `AWS_SECRET_KEY` and it writes real objects
to the real bucket**, which is why it is opt-in. It is also the only thing in
the project that can tell you the S3 code works: every S3 test in the suite
mocks boto3, so none of them can catch a wrong argument, and none of them knows
whether the credentials still authenticate or whether the bucket still permits a
public-read write.

Objects it creates are named `_image_smoke_<hex>` so an interrupted run leaves
something findable. The cleanup removes them and verifies they are gone; if a
run is killed outright:

```
aws s3 ls s3://sg101.user.photos/ | grep _image_smoke_
aws s3 rm s3://sg101.user.photos/<key>
```

Run this on any host that is going to serve uploads — it is what turns "the
settings look right" into "a member can upload a photo here."

**It writes to whatever database the settings point at** — in dev, the restored
copy of production. It creates a scratch user, uploads as them, and removes it
all in a `finally`, checking afterwards that the user is gone. Take a snapshot
first anyway (section 6). Don't point it at production.

It forces the user-photo upload down its local-storage branch, since the S3
branch wants live credentials and a real bucket. Both run the same PIL code, so
the image handling is covered either way — the S3 code itself is not.

---

## 6. PostgreSQL snapshots, and getting data back

A PostgreSQL snapshot restores into a target that already has the right types,
and lets you pull back a single table as easily as the whole database.

```bash
tools/pg_snapshot.sh dump                 # snapshots/sg101-<timestamp>.dump
tools/pg_snapshot.sh dump pre-task-06     # ... with a label, for a checkpoint
tools/pg_snapshot.sh list
```

**Take one before anything that writes to the database** — a rung, a migration,
a restore, a script you have just written. Measured on the current snapshot:
**8 seconds and 128 MB**, which is cheap enough that there is no reason not to.

**The search index is dumped without its data.** It is two thirds of the
database (1.1 GB of 1.7 GB) and it is derived, so a snapshot carries the schema
and you rebuild the contents. A stale index would be worse than an empty one:
`reconcile_search` would report drift you have to think about, instead of a
rebuild you can just run.

### Restoring everything

```bash
tools/pg_snapshot.sh restore sg101-20260805-191413-pre-task-06.dump
docker compose exec web python manage.py rebuild_redis --noinput   # ~3 s
docker compose exec web python manage.py reindex_search     # ~1m35s
docker compose exec web python manage.py reconcile_search   # expect "clean"
```

**Redis is not part of the database, and a restore leaves it describing the old
one.** The forum feeds, the home page's recent topics, the post, topic and user
counts and the newest members are kept in Redis, keyed by post, topic and user
IDs, and the restored database reuses those IDs for different rows: the home
page then shows old content under links that lead to real posts. The Django
cache, which holds sessions and the public forum list, is stale the same way.
`rebuild_redis` clears the cache and rebuilds that state from the database, then
checks it, and fails naming each difference if they disagree; `--check` runs the
check alone and changes nothing. It leaves who's online, the upload rate limiter
and the Celery broker alone. Outside a restore, `make manage cmd="rebuild_redis
--check"` checks the development stack, and `make prod-manage
cmd="rebuild_redis --check"` checks production.

This replaces the database, so it asks you to type its name first. It stops
`web`/`worker`/`beat` before restoring — they hold connections, and those
connections block the drops — and starts them again afterwards. A full round
trip is about a minute, plus the index rebuild.

### Restoring part of it

Usually what you want is some rows back, not the database back. Restore into a
scratch database alongside the real one, then copy rows across:

```bash
tools/pg_snapshot.sh scratch <file> forums_forum forums_topic forums_post
```

Both databases are in the same cluster, so piping `\copy` between them moves
rows with every column type intact. The command prints the recipe. Two things to
watch, both of which have bitten:

- **Order matters when rows point at each other.** `forums_forum.last_post_id`
  and `forums_topic.last_post_id` reference posts, so load the posts first and
  fill those columns afterwards.
- **Reset the sequences** with `setval()` before anything inserts, or the next
  insert collides.

### Why this exists

On 2026-08-05 a scratch script deleted a forum, and with it 4,626 topics and
24,107 posts. `Forum.last_post` is a `OneToOneField` with `on_delete=CASCADE`
pointing the wrong way: **deleting the post a forum points at deletes the
forum**, and everything inside it. `tools/site_smoke.py` guards this in
`delete_topic()`; a second script written without that guard did not.

Recovery took an hour, through the MySQL database the site then ran on. With a
snapshot it would have been a
`scratch` restore and one `\copy`. Note that a snapshot only helps if it is
older than the damage — which is the argument for taking one at the start of a
session rather than when something looks wrong.

### Checking a restored database

Two tools check what a restore produced, beyond `reconcile_search`:

- **`tools/compare_schema.py`** — the database's schema against one the
  migrations build: columns, indexes, constraints, foreign keys (including
  their action and deferrability), defaults and sequence ownership.
  Production's database was converted from MySQL rather than built by the
  migrations, and that conversion's worst problems were schema differences no
  test could see. It needs a reference database, which is just an empty one
  with migrate run against it:
  ```
  docker compose exec -T postgres psql -U sg101 -d postgres \
      -c "DROP DATABASE IF EXISTS sg101_reference WITH (FORCE)" \
      -c "CREATE DATABASE sg101_reference"
  docker compose exec -T -e DB_NAME=sg101_reference web python manage.py migrate
  docker compose exec -T web python tools/compare_schema.py
  ```
- **`tools/site_smoke.py`** — the running site against the restored database:
  the read checklist, both password flows, the admin, and real writes (a
  topic, a private message, a photo), each checked to display and then
  removed again. It writes, so take a snapshot first.
  ```
  docker compose exec -T web python tools/site_smoke.py
  ```

## 7. A host virtualenv for your editor

**The container is still where code runs.** Nothing in this section changes how
the site, the test suite or CI execute — all three remain exactly as described
above. `.venv` exists for one reason: so an editor's language server can read the
code. Before it existed, pyright could not resolve a single third-party import,
so every `django`, `celery` and `PIL` line was flagged and real diagnostics were
unfindable in the noise.

### Recreating it

```
asdf install python 3.12.14          # the version comes from .tool-versions
python -m venv .venv                 # 3.12.14, because you are in this directory
.venv/bin/python -m pip install --upgrade pip

# Flatten both requirements files and swap in psycopg2-binary.
cat requirements.txt requirements_dev.txt \
  | grep -v '^-r ' \
  | sed 's/^psycopg2==/psycopg2-binary==/' > /tmp/host-reqs.txt
.venv/bin/pip install -r /tmp/host-reqs.txt
.venv/bin/pip install django-types
```

**`.tool-versions` is what makes the plain `python` above correct.** It is
committed, and it pins this directory to 3.12.14 for asdf (and mise). Without it
you would get the global interpreter -- currently 3.14, and a free-threaded build
at that -- and a venv built on it would type-check against a different standard
library than the one the code runs on.

**It can drift from the image, by design.** The Dockerfile floats its base tag
(`FROM python:3.12`), so a rebuild can land on a newer patch than the line pinned
here. That gap is harmless for editor tooling, but if you want to know:

```
docker compose run --rm --no-deps web python --version   # what the image has
python --version                                         # what .tool-versions pins
```

Bump the pin when they disagree and you care; nothing breaks if you don't. A
fresh clone that has not run `asdf install` yet will see `python` error in this
directory rather than silently fall back to the global one, which is the failure
mode you want.

### The pin that differs from the image, and why

**`psycopg2` is replaced by `psycopg2-binary`.** `pg_config` does not exist on
this host, and `psycopg2` builds from source rather than shipping a wheel.
Homebrew could supply it, but there is no need: `psycopg2-binary` is the same
`psycopg2` module and the same import surface, built with a bundled libpq, so
it installs from a wheel with no headers.

### What installed from a wheel, and what did not

Of the 43 installed packages, **exactly one needed a source build**:
`repoze.timeago`, which has no wheel on PyPI (upstream stopped in 2011) but is
pure Python and needs no headers. Everything else, `Pillow` and `lxml` included,
installed from a wheel. This is worth recording because an attempt on 2026-07-31
was abandoned on the belief that four pins would need source builds the host
could not do; the interpreter and dependency work since then removed all four.

### django-types, not django-stubs

Django generates `Model.objects` and every field attribute at runtime, so a
checker sees neither without help. Both stub packages were measured against this
codebase:

| | `django-stubs` 6.1.0 | `django-types` 0.24.0 |
|---|---|---|
| `Topic.objects` | `Manager[Topic]` | `BaseManager[Topic]` |
| `t.name` | **`Unknown`** | **`str`** |
| project-wide errors | 827 | 892 |

`django-stubs` is built for mypy and leaves its field classes generic
(`class CharField(Field[_ST, _GT])`), filling the type parameters from a **mypy
plugin** that pyright cannot run — so field types come out `Unknown` and hover
and completion give nothing. `django-types` declares them directly. Its coarser
`BaseManager` label is cosmetic: chaining, indexing, iteration and `count()` all
resolve correctly.

Neither can see the implicit `id` primary key or reverse accessors like
`topic.posts`; those are plugin-only, and are why `reportAttributeAccessIssue` is
a warning rather than an error in `pyrightconfig.json`.

### What it is not

It is **not** a way to run the code. There is no `secrets.json` handling, no
database, and no Redis on the host path. `manage.py` run from `.venv` will not
get far, and is not meant to. Use the `docker compose` commands above.

The `.:/app` bind mount does carry `.venv` into the running container, and
`.dockerignore` cannot prevent that — it only keeps it out of the image's
`COPY . /app` layer, which is verified and is what matters, since those are
macOS-architecture wheels. Inside the container it sits inert, because nothing
activates it and the container's Python is `/usr/local`.

## 8. Running the production stack

`docker-compose.prod.yml` is the stack the new host runs: the `prod` image under
gunicorn, behind Apache, with production settings. It runs on the Mac too, which
is how it was built and tested. **Always pass `-f docker-compose.prod.yml`** —
without it every command below acts on the development stack instead. The
examples use a shell function to save typing:

```bash
dcp() { docker compose -f docker-compose.prod.yml "$@"; }
```

The common ones are also `make` targets, all prefixed `prod-` (`make
prod-maint-on`, `make prod-logs svc=web`, `make prod-backup`). Run `make` on its
own to list them.

It is its own compose project (`sg101-prod`), with its own PostgreSQL and Redis
volumes, so it can run next to the development stack without touching it.

### One-time setup

| What | Where | Notes |
| --- | --- | --- |
| TLS certificate + key | `secrets/tls/origin.pem`, `secrets/tls/origin.key` | Cloudflare Origin CA on the host (runbook B5); self-signed locally, below |
| Google Calendar key | `secrets/gcal/gcal-service-account.json` | mounted read-only into `web` only; must be readable by uid 1000, the container's user (runbook B1) |
| Environment | `.env` | the same file the development stack reads; the production stack also requires `GUNICORN_WORKERS` and `CELERY_WORKER_CONCURRENCY` from it and refuses to start without them (`.env.example`) |
| Host state | `var/` | created by the command below; git-ignored |

```bash
# umask 022, so the directories are 755 on any host; Ubuntu's user umask gives
# 775. The nightly logrotate does not mind (Ubuntu's global `su root adm` turns
# its permission check off), but logrotate run on logrotate/sg101 alone skips
# every file in a group-writable directory. Not `mkdir -m 755`: that sets only
# the last directory of each path.
(umask 022 && mkdir -p var/log/apache var/log/django var/maintenance var/public/hosted var/public/photos)
# Locally only -- a throwaway certificate:
mkdir -p secrets/tls
openssl req -x509 -newkey rsa:2048 -nodes -days 30 -subj "/CN=surfguitar101.com" \
    -addext "subjectAltName=DNS:surfguitar101.com,DNS:www.surfguitar101.com" \
    -keyout secrets/tls/origin.key -out secrets/tls/origin.pem
```

To give a local stack data, copy the development database across. This only
reads from the development side:

```bash
docker compose exec -T postgres pg_dump -U sg101 -d sg101 -Fc \
        --exclude-table-data=search_searchdocument \
    | dcp exec -T postgres pg_restore -U sg101 -d sg101 --no-owner --no-privileges
```

### Start, stop, inspect

| Goal | Command |
| --- | --- |
| Build and start | `dcp up -d --build` |
| Deploy a pull with migrations | `make prod-deploy` (maintenance on, `migrate`, restart, off) |
| Status and health | `dcp ps` |
| Stop, keep data | `dcp down` |
| Follow a service's output | `dcp logs -f web` (or `proxy`, `worker`, `beat`) |
| Apache's logs | `var/log/apache/access.log`, `error.log` |
| Django's logs | `var/log/django/*.log` |
| Django shell | `dcp exec web python manage.py shell` |
| Deployment checks | `dcp exec web python manage.py check --deploy` |
| Smoke test | `tools/prod_smoke.sh` (stop the development stack first) |

Every service has a health check. `web` and `proxy` render the home page, so
they go `unhealthy` when the database or Redis is down, not only when their own
process is. Nothing restarts on `unhealthy`; `restart: unless-stopped` acts only
when a process exits.

### Redis: the ceiling and what eviction takes

One Redis serves three things, and they are not alike:

| db | Holds | Expires? | If it is lost |
| --- | --- | --- | --- |
| 0 | kept state — who's online, the forums' latest-post lists | no | gone; some of it rebuilds on the next write |
| 1 | the Celery broker | no | queued tasks never run |
| 2 | the Django cache | yes, 600 s | a database query |

The eviction policy is server-wide, so `allkeys-lru` would discard queued tasks
as readily as cache entries. `volatile-lru` evicts only keys carrying a TTL,
which is what makes one policy safe across all three.

```bash
dcp exec redis redis-cli config get maxmemory
dcp exec redis redis-cli config get maxmemory-policy
dcp exec redis redis-cli info stats | grep evicted_keys
```

`maxmemory` defaults to 256 MB and is overridden with `REDIS_MAXMEMORY` in
`.env`. It is a bound on a runaway, not a cache size: the working set measured
~3 MB on the old host, whose memcached never evicted once in 150 days against a
64 MB limit. **A non-zero `evicted_keys` is worth looking at rather than tuning
away** — at these volumes it means something is writing far more than the site
ever has.

Two things it does not do. It does not bound the process: `maxmemory` limits
Redis's own accounting, while fragmentation and a forked `BGSAVE` sit above it.
And it does not spare `user_photos:counts:*`, the upload rate limiter — the one
expiring key in db 0 that nothing can rebuild, so evicting it returns that
member's daily quota. Both are accepted deliberately; `core/tests/test_redis_ttls.py`
pins the inventory so a new expiring key has to be thought about.

### Reload the proxy

The Apache configuration is the `apache/` directory, mounted into the container.
Edit it, check it, then reload without dropping connections:

```bash
dcp exec proxy sh -c '. /etc/apache2/envvars && apache2 -t'
dcp exec proxy apache2ctl -k graceful
```

A change to `apache/Dockerfile` itself needs `dcp up -d --build proxy`.

### Maintenance mode

```bash
touch var/maintenance/on    # every request gets offline.html with a 503
rm var/maintenance/on       # back to normal
```

No reload needed. It works while `web` is stopped, which is when it is wanted:
Apache answers it without gunicorn. Cloudflare's own maintenance page is the
first choice; this is the one that still works with Cloudflare out of the
picture.

### Opening it in a browser

Production settings answer only to `surfguitar101.com`, so a browser has to
send that name to the local stack. A throwaway Chrome does it without changing
anything system-wide:

```bash
open -na "Google Chrome" --args --user-data-dir="$(mktemp -d)" \
    --host-resolver-rules="MAP surfguitar101.com 127.0.0.1"
```

Its fresh profile has no remembered HSTS for the real site, which is what lets
you click past the self-signed certificate.

### Backups, and restoring from them

A host timer (`backup/sg101-backup.timer`, nightly at 04:30) runs the `backup`
service once and it exits. It writes to two buckets:

| Bucket | Holds | Kept |
| --- | --- | --- |
| dumps | `sg101-<UTC time>.dump`, `pg_dump -Fc`, search index rows left out | 90 days |
| media | a copy of `media/`, new and changed files only, never deleted | forever, prior versions included |

Both are versioned. The job's credential can add objects and list them, and
**cannot read, delete or reconfigure anything** — so a compromised host can
neither destroy the backups nor download them. **Restoring therefore needs an
administrative credential**, passed with `-e`, which overrides the job's own in
`secrets/backup.env`:

```bash
admin() { dcp run --rm -T -e AWS_ACCESS_KEY_ID=... -e AWS_SECRET_ACCESS_KEY=... backup "$@"; }
admin aws s3 ls "s3://$DUMPS_BUCKET/"                # newest last
```

**Every command below streams through the host and writes no file on it.** Never
save a dump into `media/`, `static/` or `var/` — Apache serves those to the
internet, and a dump holds password hashes and private messages.

**Run a backup now**, and see what it did — it prints the key and size:

```bash
dcp run --rm backup
```

**Restore into a scratch database** to inspect it or copy rows back, leaving
the live one untouched. Row-copying is described in section 6.

```bash
dcp exec -T postgres sh -c 'createdb -U "$POSTGRES_USER" sg101_scratch'
admin aws s3 cp "s3://$DUMPS_BUCKET/sg101-<time>.dump" - |
    dcp exec -T postgres sh -c \
    'pg_restore -U "$POSTGRES_USER" -d sg101_scratch --no-owner --no-privileges'
```

**Replace the live database.** Destructive: everything since the dump is lost.

```bash
touch var/maintenance/on
dcp stop web worker beat                   # their connections block the drops
admin aws s3 cp "s3://$DUMPS_BUCKET/sg101-<time>.dump" - |
    dcp exec -T postgres sh -c \
    'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner --no-privileges'
dcp start web worker beat
dcp exec web python manage.py rebuild_redis --noinput   # section 6
dcp exec web python manage.py reindex_search     # the dump has no index rows
dcp exec web python manage.py reconcile_search   # should report no drift
rm var/maintenance/on
```

`pg_restore` prints notices about objects that did not exist yet; those are
expected. An `error:` line is not.

**Restore media.** Current versions, over what is on disk — the container's user
is given the directory's owner so the files come back owned as the site expects:

```bash
dcp run --rm -T --user "$(stat -c %u:%g media)" -v "$PWD/media:/restore" \
    -e AWS_ACCESS_KEY_ID=... -e AWS_SECRET_ACCESS_KEY=... \
    backup aws s3 sync "s3://$MEDIA_BUCKET/" /restore/
```

Empty directories do not come back — object storage has only files, and
production has ~125 of them, mostly `avatars/users/<name>` left by deleted
avatars. Nothing needs them: Django creates a directory when it saves into it.

A file that was overwritten has its earlier content as a prior version:
`admin aws s3api list-object-versions --bucket "$MEDIA_BUCKET" --prefix <path>`,
then `get-object --version-id`.

**The drill** exercises all of this against a local MinIO, including a restore
with every table's row count compared, and is what to run after changing
anything under `backup/`:

```bash
tools/backup_drill.sh        # needs this stack up
```

## Everyday commands

`make` lists shortcuts for most of these, for both stacks. This table and the
sections above are what those shortcuts run.

| Goal | Command |
| --- | --- |
| Build / rebuild the image | `docker compose build` |
| Start everything (foreground) | `docker compose up` |
| Start in background | `docker compose up -d` |
| Stop (keep the DB data) | `docker compose down` |
| Stop **and wipe the DB** | `docker compose down -v` |
| Follow web logs | `docker compose logs -f web` |
| A shell inside the web container | `docker compose exec web bash` |
| Django shell | `docker compose exec web python manage.py shell` |
| Run a management command | `docker compose exec web python manage.py <cmd>` |
| Run the tests | `docker compose exec web python manage.py test --settings=sg101.settings.docker_test` |
| PostgreSQL prompt | `docker compose exec postgres psql -U sg101 sg101` |
| Snapshot the database | `tools/pg_snapshot.sh dump [label]` |
| List snapshots | `tools/pg_snapshot.sh list` |
| Restore the whole database | `tools/pg_snapshot.sh restore <file>` |
| Restore a table to pick rows from | `tools/pg_snapshot.sh scratch <file> [table...]` |

## How the pieces fit

- **`Dockerfile`** — builds the Python 3.12 image in two targets: `prod`
  (system libs + `requirements.txt`) and `dev` (`FROM prod`, plus
  `requirements_dev.txt` — the test suite and the debug toolbar).
- **`docker-compose.yml`** — defines the five services and wires them
  together. web/worker/beat all build the `dev` target.
- **`sg101/settings/dev.py`** — dev settings; points the DB at the container
  services and enables the debug toolbar. Redis needs nothing here: `base.py`
  reads its host and port from the environment and defaults them to the `redis`
  service. Selected via `DJANGO_SETTINGS_MODULE` in compose, and the default for
  `manage.py`.
- **`sg101/settings/databases.py`** — maps `DB_ENGINE` to a backend, service
  name, and port, so the settings modules never hardcode an engine. PostgreSQL
  is the only one.
- **`docker-compose.prod.yml`** — the production stack (section 8): the `prod`
  target under gunicorn, Apache in front, only the proxy's ports published.
- **`apache/`** — the proxy: a small Dockerfile for the image, and the
  configuration it reads through a bind mount.
- **`sg101/settings/production.py`** — production settings, selected by the
  production stack.
- **`sg101/settings/docker_test.py`** — test settings (PostgreSQL, and the
  broker on a Redis database of its own so a suite run cannot touch what the
  development stack has queued), used by both local runs and CI.
- **`snapshots/`** — where your DB dumps live: copies of production's backups
  and the snapshots `tools/pg_snapshot.sh` writes (git-ignored).

## Troubleshooting

- **`docker: command not found`** — Docker Desktop isn't installed or running.
- **`web` can't reach the database** — the `postgres` container is still
  initializing on first start; `web` waits for its healthcheck, but a restore
  must wait too. Give it a few seconds and retry.
- **A dependency fails to compile during `build`** — expected occasionally with
  20-year-old pins; we resolve these faithful-first (bump the patch version only
  if a pin truly can't build). Note the failing package and we'll address it.
- **Pages taking ~5 seconds each** — this was a Docker DNS quirk, now fixed via
  `dns_opt: [single-request-reopen]` on the app services. Cause: resolving a
  service name (`postgres`/`redis`) makes glibc fire parallel IPv4+IPv6 DNS queries;
  Docker's embedded resolver answers the IPv4 one but not IPv6, so every lookup
  blocked the full 5s resolver timeout — and Django opens a fresh DB connection
  per request, so it hit on every page. `single-request-reopen` forces the two
  lookups to happen sequentially, eliminating the stall. (If you ever see it
  return, confirm the container's `/etc/resolv.conf` has that option.)
