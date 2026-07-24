# Task: Stand Up PostgreSQL and Run the Suite Against It

## Description
Add PostgreSQL to the Docker Compose stack, add the `psycopg2` driver, and
parameterize the database settings so the application can run on Postgres. Prove
it by creating the schema on an empty Postgres database and running the full test
suite against it. No production data is involved in this task — that is task 03.

This is the first of six tasks in Step 11 (MySQL → PostgreSQL). It deliberately
stops short of touching real data so that engine-level problems surface in
isolation, before the conversion adds its own variables.

## Background
SG101 has run on MySQL since 2009 and currently uses `django.db.backends.mysql`
with `mysqlclient==1.4.6` on Django 3.2.25 / Python 3.7. The Compose `db` service
is `mysql:5.7` (running under emulation on Apple Silicon, with a permissive
`sql_mode=` so the legacy 5.5 dump's `0000-00-00` dates load).

Two facts make the engine swap tractable:
- **Zero raw SQL in application code** — no `.raw(`, `.extra(`, `RawSQL`, or
  `connection.cursor()` outside migrations. The ORM is used throughout.
- **Tests already run on sqlite3**, so the app is already exercised against a
  second engine.

**Driver constraint — the plan is out of date here.** `implementation/plan.md`
says "Add `psycopg` 3". That is wrong for this rung: Django 3.2's PostgreSQL
backend imports `psycopg2` and fails with `Error loading psycopg2 module` if it
is absent. Support for psycopg 3 was added in **Django 4.2**. This task MUST use
`psycopg2`, and moving to psycopg 3 becomes a candidate at Step 13.

**Python 3.7 constraint.** `psycopg2` 2.9.10 requires Python ≥ 3.8. The last line
supporting Python 3.7 is **2.9.9** — verify at install time and pin accordingly.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/research/database-migration.md`
  (portability signals, tooling, watch-items)
- `.agents/planning/2026-07-04-modernizing-sg101/research/docker-strategy.md`
  (the container is the future production artifact — dev/prod parity matters)

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Add a `postgres` service to `docker-compose.yml` with a named volume, a
   healthcheck, and a host port mapping, mirroring how the existing `db` service
   is set up. Choose a Postgres major version and record the rationale — Django
   3.2 supports 9.6+, but the project will climb to Django 5.2, so prefer a
   version that stays supported across the remaining rungs.
2. Keep the MySQL `db` service in place and working for the duration of Step 11.
   Both engines must be runnable side by side; task 03 needs to read from MySQL
   and write to Postgres, and the documented fallback (R17) is to stay on MySQL.
3. Add `psycopg2` to `requirements.txt` and `requirements-docker.txt`, pinned to
   the newest release that supports Python 3.7. Follow the existing convention of
   commenting *why* a pin is capped.
4. Parameterize `DATABASES` so the engine, host, and port come from environment
   variables, consistent with the Step 3 12-factor configuration. Update
   `.env.example`. Do not hardcode Postgres into `base.py`.
5. Create the schema on an empty Postgres database. Note that **21 of 26 apps
   have no migrations**, so this requires `migrate --run-syncdb` for the
   unmigrated apps in addition to `migrate` for the five migrated ones
   (comments, countdown, downloads, forums, news) plus Django's own and
   `tagging`. Confirm every expected table is created.
6. Run the full test suite against Postgres and get it green.
7. **Measurement checkpoint (feeds task 06):** record the suite's wall-clock
   runtime on Postgres and compare it against the current sqlite baseline of
   ~5 seconds for 567 tests. Write the numbers into the task's completion notes.
   Do not decide the test-database policy here — task 06 owns that decision, and
   it needs this data.

## Dependencies
- Docker Compose stack from Step 1 (`web`, `worker`, `beat`, `db`, `redis`)
- 12-factor env-var configuration from Step 3 (`django-environ`, `.env`)
- Django 3.2.25 / Python 3.7 from Step 10

## Implementation Approach
1. Add the `postgres` service to Compose and confirm it boots healthy on its own.
2. Add the pinned `psycopg2` requirement and rebuild the image; confirm the
   driver imports inside the container.
3. Introduce env-driven `DATABASES` settings and a Postgres-targeted settings
   module (or env values) alongside the existing MySQL ones.
4. Create the schema on an empty database; inspect the resulting table list and
   compare it to the MySQL table list for obvious omissions.
5. Run the suite, fix whatever engine-specific failures appear, and record the
   runtime.

## Acceptance Criteria

1. **Postgres Service Boots**
   - Given a clean checkout and `docker compose up`
   - When the stack starts
   - Then the `postgres` service reaches a healthy state and both it and the
     MySQL `db` service are running simultaneously

2. **Driver Available and Pinned**
   - Given the rebuilt image
   - When `import psycopg2` runs inside the container
   - Then it succeeds, and the pinned version is the newest release supporting
     Python 3.7, with the cap explained in a requirements comment

3. **Schema Creates on an Empty Database**
   - Given an empty Postgres database
   - When the schema is created (migrations plus `--run-syncdb` for the 21
     unmigrated apps)
   - Then it completes without error and every table the MySQL schema has is
     present, with any discrepancy explicitly listed and explained

4. **Full Suite Green on Postgres**
   - Given the application configured against Postgres
   - When the full test suite runs
   - Then all 567 tests pass (5 skipped), matching the sqlite baseline, with any
     test that had to change documented as an engine-behavior difference rather
     than silently adjusted

5. **MySQL Path Still Works**
   - Given the same checkout
   - When the application is pointed back at the MySQL `db` service
   - Then the site serves and the suite still passes, preserving the R17 fallback

6. **Runtime Measured for Task 06**
   - Given the suite has run on both engines
   - When the task is completed
   - Then the Postgres wall-clock runtime and the sqlite baseline are both
     recorded in the completion notes, with no test-database policy decided yet

## Metadata
- **Complexity**: Medium
- **Labels**: Database, PostgreSQL, Docker, Configuration, Step 11
- **Required Skills**: Django database configuration, Docker Compose, PostgreSQL
  administration, Python packaging constraints
