# SurfGuitar101 (sg101)

The Django application that powers [SurfGuitar101.com](https://www.surfguitar101.com/),
a community website for friends and fans of instrumental surf music.
It provides discussion forums, surf music news, a podcast, a daily
photo feature, a downloads library, a curated weblink directory, a
crowd-sourced surf band map, private messaging, polls, contests,
donations tracking, and an event calendar.

## Branches

- **`modernize`** — the active branch. Everything below describes it.
- **`main`** — preserved legacy history from before the modernization, kept
  for reference. It has no CI and does not run on a modern stack.

## Tech stack

- Python 3.12 / **Django 5.2 LTS**
- PostgreSQL 16
- Redis (cache, Celery broker, Who's-Online tracking)
- Celery (scheduled and background jobs)
- **Native PostgreSQL full-text search** — no Haystack, no Xapian
- Amazon S3 (user photo storage), Postmark (transactional email),
  Cloudflare (DNS/CDN/WAF, inbound email routing), Google Calendar,
  PayPal (donations)

See [`.agents/summary/dependencies.md`](.agents/summary/dependencies.md)
for the full dependency list and [`.agents/summary/architecture.md`](.agents/summary/architecture.md)
for how the pieces fit together.

## Setup

Development runs in Docker. **[`DOCKER.md`](DOCKER.md) is the full guide** —
prerequisites, loading a production snapshot, switching database engines,
snapshots, and troubleshooting. The short version:

```
cp .env.example .env          # committed template; its defaults work as-is
docker compose build web
docker compose up -d
docker compose exec web python manage.py migrate
```

The site is then on <http://localhost:8000/>.

Configuration is 12-factor: every setting is read from the environment via
`django-environ`. `.env` is git-ignored and loaded into the app services by
Compose; `.env.example` is committed and carries working local defaults,
including Cloudflare's public Turnstile test keys. There is **no
`secrets.json`** — that was retired during the modernization.

## Building the stylesheet

The v3 stylesheet is written in Sass under `sg101/scss/` and compiled to
`sg101/static/css/v3/main.min.css`, **which is committed**. The build needs
Node (developed against v26); the application image does not contain Node and
deploys do not build CSS.

```
cd sg101
npm install
npm run build:css
```

`npm run watch:css` recompiles on save while working on the Sass.

**Edit the Sass, never `main.min.css`.** The built file is an artifact: anything
written into it by hand is silently discarded by the next build. Committing it
keeps deploys to one step and keeps CSS changes reviewable in the diff, at the
cost of having to remember to rebuild — so **a change to `sg101/scss/` and the
rebuilt `main.min.css` belong in the same commit.**

Foundation and Motion UI come from npm and are pinned in `package.json`;
browser targets live in its `browserslist` key, which is what decides the
vendor prefixes `autoprefixer` emits.

## Running tests

```
docker compose exec web python manage.py test --settings=sg101.settings.docker_test
```

There is a **second, separate run** — the deprecation gate, which promotes
deprecation warnings to errors. It is what has caught every Django removal a
version before it landed, so run it before proposing a change:

```
docker compose run --rm -e PYTHONWARNINGS="$(tools/deprecation_gate.sh)" web \
    python manage.py test --noinput --settings=sg101.settings.docker_test
```

`tools/deprecation_gate.sh` only *prints* the warning filter — running the
script by itself is not the gate.

## Continuous integration

GitHub Actions runs the suite on every push and pull request to `modernize`
(`.github/workflows/ci.yml`). CI seeds `.env` from `.env.example` and builds the
same Compose image used locally, so the database in CI is identical to a
developer's rather than merely similar.

## Deployment

**There is no current automated deployment.** `fabfile.py` remains from the
pre-modernization setup and is stale — its `update` task still runs
`hg pull --update`, from before the move to git. Deploying to a new host is the
last step of the modernization and has not happened yet.

## Documentation

- [`DOCKER.md`](DOCKER.md) — running the site locally, end to end.
- [`AGENTS.md`](AGENTS.md) — a short orientation for AI coding agents, including
  the non-obvious behaviours worth knowing before changing anything.
- [`.agents/summary/index.md`](.agents/summary/index.md) — generated
  architecture and per-app documentation; start at the index.
- [`.agents/planning/`](.agents/planning/) — the modernization project's design,
  research and status. `STATUS.md` there is the authoritative record of what has
  been done and why.
