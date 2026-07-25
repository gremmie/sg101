# Running SG101 locally with Docker

Run the SG101 site (Python 3.7 / Django 3.2 / MySQL or PostgreSQL / Redis) on
your Mac inside Docker, seeded with a real production database snapshot. Docker gives us a
consistent little Linux environment that matches the target deploy platform —
handy for a stack this far from a modern Mac's defaults.

New to Docker? The only concepts you need here:

- **Image** — a blueprint (built from `Dockerfile`) with Python 3.7 + all the
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
   `db` service, and blank/optional API keys):
   ```
   cp .env.example .env
   ```
   `.env` is git-ignored; Compose loads it into the app services via `env_file:`.

2. **A production DB snapshot** — put the MySQL dump in `snapshots/`, e.g.
   `snapshots/sg101.sql.gz`. (Loading it is step 4 below.)

## 2. Build the image

Downloads Python 3.7 + installs the pinned dependencies. The first build takes a
while (several minutes); later builds are cached.
```
docker compose build
```

## 3. Start the stack

```
docker compose up
```
This starts all six services: `db` (MySQL), `postgres`, `redis`, `web`, `worker`,
`beat`. Both databases run at once while the site is being moved from one to the
other; the app talks to whichever `DB_ENGINE` names (see section 6). Leave it
running in this terminal (it streams logs). Open a **second** terminal for the
commands below. To run it in the background instead, use `docker compose up -d`.

The site is now at **http://localhost:8000** — but it has no data until you load
the snapshot.

## 4. Load the production snapshot

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

Then reload http://localhost:8000 — you should see real forum/news content. Log
in with a known account from the snapshot.

## 5. Run the test suite

The tests use sqlite by default (fast, no snapshot needed):
```
docker compose exec web python manage.py test --settings=sg101.settings.docker_test
```
Green suite in-container = the harness works. This is the baseline everything
else builds on. To run the same suite against PostgreSQL instead, see section 6.

## 6. PostgreSQL

The site is moving from MySQL to PostgreSQL, so the stack runs both. One
variable decides which one the app uses:

```
DB_ENGINE=postgresql docker compose up      # or put DB_ENGINE=postgresql in .env
```
`mysql` is still the default. Host and port follow the engine automatically
(`db`:3306 or `postgres`:5432), so there is nothing else to set;
`sg101/settings/databases.py` holds the mapping.

**Create the schema** on the empty `postgres` service (once, or again after
`docker compose down -v`):
```
docker compose exec -e DB_ENGINE=postgresql web python manage.py migrate
```

**Run the suite against Postgres:**
```
docker compose exec web python manage.py test --settings=sg101.settings.docker_test_pg
```

---

## 7. Converting MySQL data to PostgreSQL

This is the procedure used at cutover. It is repeatable: every run drops and
recreates the target database, so it always starts from empty.

Load the dump into MySQL first (§4), then:

```
# 1. Convert. Reads .env for credentials; override the databases as needed.
MYSQL_DB=sg101 PG_DB=sg101 tools/pgloader/convert.sh

# 2. Verify the conversion itself, BEFORE migrating (see the note below).
docker compose exec -T -e MYSQL_DB=sg101 -e PG_DB=sg101 web \
    python tools/pgloader/verify.py

# 3. Bring the schema up to the current migration state.
docker compose exec -T -e DB_ENGINE=postgresql web \
    python tools/pgloader/post_convert.py
```

Step 1 prints a summary and writes it to `tools/pgloader/logs/`; rejected rows,
if there ever are any, land in `tools/pgloader/logs/rejects/`. **A non-zero
error count must be explained, never waved through.**

**Run `verify.py` before `post_convert.py`.** It compares every table's exact
row count against MySQL, and `migrate` legitimately adds rows to
`django_migrations` and `auth_permission` — run it after and those two are
reported as expected growth rather than failures, but the comparison is no
longer like-for-like.

`verify.py` checks three things the conversion can get wrong silently: exact
row counts per table, every text value in the eight cp1252 tables (md5 against
MySQL's own decoding), and that every sequence sits past `MAX(pk)` so the next
insert cannot collide.

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
- **`post_convert.py` does two things a plain `migrate` cannot.** It fakes the
  initial migrations of the 21 apps whose tables already exist, and it first
  records `oembed.0001_initial`, because `forums/0001_initial` has declared a
  dependency on oembed since 2015 and Django's consistency check otherwise
  refuses *every* migrate command. It then applies the prefix-matching indexes
  in `pattern_ops_indexes.sql`, which Django would have created had its
  initials not been faked.
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

## Everyday commands

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
| MySQL prompt | `docker compose exec db mysql -uroot -prootpw sg101` |
| PostgreSQL prompt | `docker compose exec postgres psql -U sg101 sg101` |
| Run a command against Postgres | `docker compose exec -e DB_ENGINE=postgresql web python manage.py <cmd>` |

## How the pieces fit

- **`Dockerfile`** — builds the Python 3.7 image (system libs + pip deps from
  `requirements-docker.txt`).
- **`docker-compose.yml`** — defines the six services and wires them together.
- **`sg101/settings/docker.py`** — dev settings; points the DB and Redis at the
  container services over the network (the legacy settings used unix sockets).
  Selected via `DJANGO_SETTINGS_MODULE` in compose.
- **`sg101/settings/databases.py`** — maps `DB_ENGINE` to a backend, service
  name, and port, so the settings modules never hardcode an engine.
- **`sg101/settings/docker_test.py`** — test settings (sqlite + Redis over TCP);
  **`docker_test_pg.py`** — the same suite against PostgreSQL.
- **`snapshots/`** — where your DB dumps live (git-ignored).

## Troubleshooting

- **`docker: command not found`** — Docker Desktop isn't installed or running.
- **`web` can't reach the database** — the `db` container is still initializing
  on first start; `web` waits for its healthcheck, but a snapshot load must wait
  too. Give it a few seconds and retry.
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
