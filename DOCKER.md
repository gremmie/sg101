# Running SG101 locally with Docker

Run the SG101 site (Python 3.12 / Django 5.2 / PostgreSQL 16 / Redis) on
your Mac inside Docker, seeded with a real production database snapshot. Docker gives us a
consistent little Linux environment that matches the target deploy platform —
handy for a stack this far from a modern Mac's defaults.

New to Docker? The only concepts you need here:

- **Image** — a blueprint (built from `Dockerfile`) with Python 3.12 + all the
  app's dependencies baked in.
- **Container** — a running instance of an image. Each service (`web`, `db`, …)
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

2. **A production DB snapshot** — put the MySQL dump in `snapshots/`, e.g.
   `snapshots/sg101.sql.gz`. Production still runs MySQL, so a snapshot is a
   MySQL dump and getting it into the site's PostgreSQL database means converting
   it (sections 4 and 7 below).

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
runs on PostgreSQL with nothing to configure. MySQL (`db`) is **not** among them
— it sits behind an opt-in profile now that only the snapshot conversion needs
it (see section 6). Leave this running in this terminal (it streams logs). Open a
**second** terminal for the commands below. To run it in the background instead,
use `docker compose up -d`.

The site is now at **http://localhost:8000** — but the database is empty until
you load a snapshot.

**Create the schema** on an empty `postgres` service, if you are not loading a
snapshot (once, or again after `docker compose down -v`):
```
docker compose exec web python manage.py migrate
```

## 4. Load the production snapshot

The snapshot is a **MySQL** dump and the site's database is PostgreSQL, so this
is two steps: load the dump into the `db` service, then convert it (section 7).
`db` only runs when you ask for it:
```
docker compose --profile mysql up -d db
```

MySQL data persists in a Docker volume (`db_data`), so you only do this once
(again after `docker compose down -v`). The snapshot is mounted read-only inside
the `db` container at `/snapshots`.

Decompress on the Mac and pipe into the container's `mysql` (the MySQL image has
neither `bzip2` nor `gzip` for this). For a **bzip2** dump (what we have):
```
bunzip2 -c snapshots/sg10120260712.sql.bz2 | docker compose exec -T db mysql -uroot -prootpw sg101
```
For a **gzip** dump: `gunzip -c snapshots/xxx.sql.gz | docker compose exec -T db mysql -uroot -prootpw sg101`
For a plain **.sql**: `docker compose exec -T db mysql -uroot -prootpw sg101 < snapshots/xxx.sql`

The ~460k-post dump takes a minute or two. It loads cleanly because the `db`
service runs with 5.5-style `sql_mode=` (empty) — MySQL 5.7's default strict mode
would otherwise reject the old `0000-00-00` dates in the dump.

Now **convert it to PostgreSQL** — section 7. Then reload
http://localhost:8000 and you should see real forum/news content; log in with a
known account from the snapshot.

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

**It writes to whatever database the settings point at** — in dev, the converted
production snapshot. It creates a scratch user, uploads as them, and removes it
all in a `finally`, checking afterwards that the user is gone. Take a snapshot
first anyway (section 8). Don't point it at production.

It forces the user-photo upload down its local-storage branch, since the S3
branch wants live credentials and a real bucket. Both run the same PIL code, so
the image handling is covered either way — the S3 code itself is not.

## 6. MySQL, and switching engines

PostgreSQL is the default and needs no configuration. MySQL is still in the
Compose file for one reason — a production snapshot is a MySQL dump, so the
conversion needs somewhere to read from — and it stays until the real cutover,
which converts a fresh snapshot the same way. It does not start on its own:

```
docker compose --profile mysql up          # the whole stack, MySQL included
docker compose --profile mysql up -d db    # just MySQL, alongside a running stack
```

To point the **app** back at MySQL, name the engine and start its service:
```
DB_ENGINE=mysql docker compose --profile mysql up
```
Host and port follow the engine automatically (`db`:3306 or `postgres`:5432), so
`DB_ENGINE` is the only knob; `sg101/settings/databases.py` holds the mapping,
and `DB_HOST`/`DB_PORT` override it for a database outside Compose.

**A profile is a filter on both ends: `docker compose down` will not stop `db`
either.** A plain `down -v` removes `postgres_data` and leaves `db_data` and a
running MySQL container behind — which then holds the network open. To take the
whole thing down, name the profile:
```
docker compose --profile mysql down -v
```

---

## 7. Converting MySQL data to PostgreSQL

This is the procedure used at cutover. It is repeatable: every run drops and
recreates the target database, so it always starts from empty.

Both databases have to be running, so bring the stack up with the `mysql`
profile and load the dump into MySQL first (§4):

```
docker compose --profile mysql up -d
```

Then:

```
# 1. Convert. Reads .env for credentials; override the databases as needed.
MYSQL_DB=sg101 PG_DB=sg101 tools/pgloader/convert.sh

# 2. Verify the conversion itself, BEFORE migrating (see the note below).
docker compose exec -T -e MYSQL_DB=sg101 -e PG_DB=sg101 web \
    python tools/pgloader/verify.py

# 3. Bring the schema up to the current migration state.
docker compose exec -T web python tools/pgloader/post_convert.py

# 4. Compare the data itself, column by column, and check referential
#    integrity. Runs after post_convert.py, unlike step 2.
docker compose exec -T -e MYSQL_DB=sg101 -e PG_DB=sg101 web \
    python tools/pgloader/verify_data.py

# 4b. Compare the schema against one the migrations build. Needs a reference
#     database, which is just an empty one with migrate run against it.
docker compose exec -T postgres psql -U sg101 -d postgres \
    -c "DROP DATABASE IF EXISTS sg101_reference WITH (FORCE)" \
    -c "CREATE DATABASE sg101_reference"
docker compose exec -T -e DB_NAME=sg101_reference web python manage.py migrate
docker compose exec -T web python tools/pgloader/compare_schema.py

# 5. Second opinion on the same rows, through Django's serializer.
MYSQL_DB=sg101 PG_DB=sg101 tools/pgloader/crosscheck_dumpdata.sh

# 6. Smoke the running site, reads and writes. Needs the stack up against the
#    converted database, which is what `docker compose up -d` now gives you.
docker compose exec -T web python tools/pgloader/smoke.py
```

**Keep steps 4 and 5 ahead of step 6.** Using the site changes the site:
sessions get written and topic view counters go up. `smoke.py` removes the
content it creates, but it cannot un-read a page, so a comparison against the
untouched MySQL source has to happen before anything browses.

Step 1 prints a summary and writes it to `tools/pgloader/logs/`; rejected rows,
if there ever are any, land in `tools/pgloader/logs/rejects/`. **A non-zero
error count must be explained, never waved through.**

**Run `verify.py` before `post_convert.py`.** It compares every table's exact
row count against MySQL, and `migrate` legitimately adds rows to
`django_migrations` and `auth_permission` — run it after and those two are
reported as expected growth rather than failures, but the comparison is no
longer like-for-like.

What each check covers:

- **`verify.py`** — three things the conversion can get wrong silently: exact
  row counts per table, every text value in the eight cp1252 tables (md5
  against MySQL's own decoding), and that every sequence sits past `MAX(pk)`
  so the next insert cannot collide.
- **`verify_data.py`** — every column of every table, by checksum, on both
  engines: 543 columns and 5.7 million values, with datetimes compared as the
  application sees them, `NULL` held distinct from `''`, and booleans,
  decimals and `inet` rendered to a common form. Also checks that every
  foreign key holds, is enforced, and is built the way Django builds it. Four
  differences are expected and are listed with the number of rows each may
  affect; anything beyond that count fails.
- **`compare_schema.py`** — the converted schema against one the migrations
  build, across columns, indexes, constraints, foreign keys (including their
  action and deferrability), defaults and sequence ownership. This is the
  check that catches pgloader converting MySQL faithfully but not the way
  Django would have built it, which is where this conversion's worst problems
  have been. Index and constraint *names* are deliberately not compared:
  pgloader's are `idx_393735_username` where Django's are
  `forums_topic_last_post_id_ed000e17_fk`, Django resolves them by
  introspection, and comparing them would bury the differences that matter.
- **`crosscheck_dumpdata.sh`** — twelve models dumped from both engines
  through Django's own serializer and diffed, which comes at the rows from
  outside SQL entirely.
- **`smoke.py`** — the running site: the read checklist, both password flows,
  the admin, and real writes (a topic, a private message, a photo), each
  checked to display and then removed again.

### Things worth knowing

- **The source database is only read.** MySQL is untouched, so the app can be
  pointed back at it at any time.
- **`tools/pgloader/sg101.load` carries the type mappings**, each commented
  with why it exists. The ones that matter: MySQL's `latin1` is really
  **cp1252** (declaring `latin1` mangles smart quotes and trademark signs);
  `int(11)` must be forced to 32-bit `integer` or every primary key arrives as
  `bigint`; the IP columns become `inet`; and `bio_userprofile.country` must
  become `varchar`, because PostgreSQL pads `char(2)` and an unset country
  comes back as two spaces instead of empty — which is truthy, and crashes
  every profile page for the 12,854 members who have not set one.
- **`post_convert.py` does several things a plain `migrate` cannot.** It fakes
  the initial migrations of the 21 apps whose tables already exist, and it
  first records `oembed.0001_initial`, because `forums/0001_initial` has
  declared a dependency on oembed since 2015 and Django's consistency check
  otherwise refuses *every* migrate command. It then applies the
  prefix-matching indexes in `pattern_ops_indexes.sql`, which Django would
  have created had its initials not been faked. Last it repairs three things
  pgloader leaves in a state Django would not: the foreign keys (below), the
  `CHECK` constraints behind `PositiveIntegerField` — MySQL says UNSIGNED,
  which has no equivalent to carry across, so nothing stopped a negative
  value — and two leftover column defaults, which Django never sets because
  it applies field defaults in Python. Each is derived from Django's own
  field definitions rather than listed, and each is idempotent.
- **Naive datetimes are read as `TIME_ZONE`, not UTC.** MySQL `datetime`
  carries no offset and, with `USE_TZ` off, Django wrote local wall-clock time
  into it. Django maps `DateTimeField` to `timestamptz` on PostgreSQL, so
  every value has to be placed on the timeline as it lands, using the session
  timezone — and at the server default of UTC the whole database ends up 5–6
  hours early once Django reads it back in `America/Chicago`. `convert.sh`
  sets the timezone on the target database before loading, reading it from
  Django so the two cannot drift. That the stored values really are local time
  is not an assumption: the 02:00 hour is empty on every DST spring-forward
  day across twenty years of posts, which is the gap only local time has.
- **Foreign keys are rebuilt as `NO ACTION ... DEFERRABLE INITIALLY
  DEFERRED`.** That is how Django's schema editor makes them, and its ORM
  depends on it — cascades happen in Python, and the deletion collector
  removes rows in whatever order suits it, leaving the database to confirm
  consistency once, at commit. pgloader carries InnoDB's semantics across
  instead and writes every constraint `ON UPDATE RESTRICT ON DELETE RESTRICT`,
  which is checked immediately and *cannot* be deferred. Left that way,
  ordinary operations fail against a converted database while working against
  a migrated one: deleting a forum topic is enough, because the topic's own
  `last_post` points at a post being removed in the same transaction.
- **pgloader publishes an amd64 image only**, so it runs under emulation on
  Apple Silicon. The conversion still takes well under a minute.
- **Collation changes.** The converted database is `en_US.utf8`, where MySQL
  used `latin1_swedish_ci`/`utf8_general_ci`. Text sorting differs — most
  visibly `ORDER BY username` — and comparisons are now case-**sensitive**;
  see `research/collation-audit.md` for the lookups that were adjusted.
- **Postgres has no per-table encoding.** The eight cp1252 tables are
  transcoded on the way in and land in a single UTF-8 database. Since nothing
  in MySQL was `utf8mb4`, 4-byte characters (emoji) become storable for the
  first time.

---

## 8. PostgreSQL snapshots, and getting data back

The MySQL service is a fallback of a sort — it holds the original production
dump, and forum data has been recovered from it. But recovering that way means a
full pgloader conversion, or a hand-written cross-engine copy that has to get
column types, booleans and the naive-datetime-into-`timestamptz` seam right. A
PostgreSQL snapshot restores into a target that already has the right types.

```bash
tools/pg_snapshot.sh dump                 # snapshots/sg101-<timestamp>.dump
tools/pg_snapshot.sh dump pre-task-06     # ... with a label, for a checkpoint
tools/pg_snapshot.sh list
```

**Take one before anything that writes to the database** — a rung, a migration,
a conversion, a script you have just written. Measured on the current snapshot:
**8 seconds and 128 MB**, which is cheap enough that there is no reason not to.

**The search index is dumped without its data.** It is two thirds of the
database (1.1 GB of 1.7 GB) and it is derived, so a snapshot carries the schema
and you rebuild the contents. A stale index would be worse than an empty one:
`reconcile_search` would report drift you have to think about, instead of a
rebuild you can just run.

### Restoring everything

```bash
tools/pg_snapshot.sh restore sg101-20260805-191413-pre-task-06.dump
docker compose exec web python manage.py reindex_search     # ~1m35s
docker compose exec web python manage.py reconcile_search   # expect "clean"
```

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
forum**, and everything inside it. `tools/pgloader/smoke.py` guards this in
`delete_topic()`; a second script written without that guard did not.

Recovery took an hour through MySQL. With a snapshot it would have been a
`scratch` restore and one `\copy`. Note that a snapshot only helps if it is
older than the damage — which is the argument for taking one at the start of a
session rather than when something looks wrong.

## 9. A host virtualenv for your editor

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

# Flatten both requirements files, drop mysqlclient, swap in psycopg2-binary.
cat requirements.txt requirements_dev.txt \
  | grep -v '^-r ' | grep -v '^mysqlclient' \
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

### The two pins that differ from the image, and why

Neither `mysql_config` nor `pg_config` exists on this host, and both packages
build from source rather than shipping wheels. Homebrew could supply both, but
neither is worth installing:

- **`mysqlclient` is omitted.** Only `tools/pgloader/{verify,verify_data}.py`
  import `MySQLdb`, both of them migration tooling — nothing in the application
  touches it. The cost is two
  `reportMissingModuleSource` *warnings*, not errors, because pyright ships
  typeshed stubs for `MySQLdb` and still gives full type information for it.
- **`psycopg2` is replaced by `psycopg2-binary`.** Same `psycopg2` module and the
  same import surface, built with a bundled libpq, so it installs from a wheel
  with no headers. This one matters because the site does run on PostgreSQL, so
  the import has to resolve.

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

## 10. Running the production stack

`docker-compose.prod.yml` is the stack the new host runs: the `prod` image under
gunicorn, behind Apache, with production settings. It runs on the Mac too, which
is how it was built and tested. **Always pass `-f docker-compose.prod.yml`** —
without it every command below acts on the development stack instead. The
examples use a shell function to save typing:

```bash
dcp() { docker compose -f docker-compose.prod.yml "$@"; }
```

It is its own compose project (`sg101-prod`), with its own PostgreSQL and Redis
volumes, so it can run next to the development stack without touching it.

### One-time setup

| What | Where | Notes |
| --- | --- | --- |
| TLS certificate + key | `secrets/tls/origin.pem`, `secrets/tls/origin.key` | Cloudflare Origin CA on the host (runbook B5); self-signed locally, below |
| Environment | `.env` | the same file the development stack reads |
| Host state | `var/` | created by the command below; git-ignored |

```bash
mkdir -p var/log/apache var/log/django var/maintenance var/public/hosted var/public/photos
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

## Everyday commands

| Goal | Command |
| --- | --- |
| Build / rebuild the image | `docker compose build` |
| Start everything (foreground) | `docker compose up` |
| Start in background | `docker compose up -d` |
| Start MySQL too (conversion) | `docker compose --profile mysql up -d` |
| Stop (keep the DB data) | `docker compose down` |
| Stop **and wipe the DB** | `docker compose down -v` |
| Stop / wipe **including MySQL** | `docker compose --profile mysql down [-v]` |
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
| MySQL prompt (needs the profile) | `docker compose exec db mysql -uroot -prootpw sg101` |

## How the pieces fit

- **`Dockerfile`** — builds the Python 3.12 image in two targets: `prod`
  (system libs + `requirements.txt`) and `dev` (`FROM prod`, plus
  `requirements_dev.txt` — the test suite and the debug toolbar).
- **`docker-compose.yml`** — defines the services and wires them together: five
  by default, plus `db` (MySQL) behind the `mysql` profile. web/worker/beat all
  build the `dev` target.
- **`sg101/settings/dev.py`** — dev settings; points the DB at the container
  services and enables the debug toolbar. Redis needs nothing here: `base.py`
  reads its host and port from the environment and defaults them to the `redis`
  service. Selected via `DJANGO_SETTINGS_MODULE` in compose, and the default for
  `manage.py`.
- **`sg101/settings/databases.py`** — maps `DB_ENGINE` to a backend, service
  name, and port, so the settings modules never hardcode an engine.
- **`docker-compose.prod.yml`** — the production stack (section 10): the `prod`
  target under gunicorn, Apache in front, no MySQL, only the proxy's ports
  published.
- **`apache/`** — the proxy: a small Dockerfile for the image, and the
  configuration it reads through a bind mount.
- **`sg101/settings/production.py`** — production settings, selected by the
  production stack.
- **`sg101/settings/docker_test.py`** — test settings (PostgreSQL, and the
  broker on a Redis database of its own so a suite run cannot touch what the
  development stack has queued), used by both local runs and CI.
- **`snapshots/`** — where your DB dumps live, both the MySQL production dumps
  and the PostgreSQL snapshots `tools/pg_snapshot.sh` writes (git-ignored).

## Troubleshooting

- **`docker: command not found`** — Docker Desktop isn't installed or running.
- **`web` can't reach the database** — the `postgres` container is still
  initializing on first start; `web` waits for its healthcheck, but a snapshot
  load must wait too. Give it a few seconds and retry.
- **`no such service: db`** — MySQL is behind a profile now; add
  `--profile mysql` to the command (see section 6).
- **A dependency fails to compile during `build`** — expected occasionally with
  20-year-old pins; we resolve these faithful-first (bump the patch version only
  if a pin truly can't build). Note the failing package and we'll address it.
- **Pages taking ~5 seconds each** — this was a Docker DNS quirk, now fixed via
  `dns_opt: [single-request-reopen]` on the app services. Cause: resolving a
  service name (`db`/`redis`) makes glibc fire parallel IPv4+IPv6 DNS queries;
  Docker's embedded resolver answers the IPv4 one but not IPv6, so every lookup
  blocked the full 5s resolver timeout — and Django opens a fresh DB connection
  per request, so it hit on every page. `single-request-reopen` forces the two
  lookups to happen sequentially, eliminating the stall. (If you ever see it
  return, confirm the container's `/etc/resolv.conf` has that option.)
- **Apple Silicon note** — `db` runs the amd64 MySQL 5.7 image under emulation
  (`platform: linux/amd64`; MySQL 5.7 has no arm64 build). Everything else,
  Postgres included, runs native arm64. Emulation adds some DB overhead but is
  not a major factor for typical pages, and it goes away with MySQL itself.
