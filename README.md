# SurfGuitar101 (sg101)

The Django application that powers [SurfGuitar101.com](https://www.surfguitar101.com/),
a community website for friends and fans of instrumental surf music.
It provides discussion forums, surf music news, a podcast, a daily
photo feature, a downloads library, a curated weblink directory, a
crowd-sourced surf band map, private messaging, polls, contests,
donations tracking, and an event calendar.

## Branches

- **`main`** — the active branch, and what production deploys. Everything
  below describes it. The modernization was done on a `modernize` branch and
  merged here once it was live.
- **Feature branches** — work happens on short-lived branches cut from `main`
  and merged back when that work is deployed.

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
make up
make manage cmd=migrate
```

The site is then on <http://localhost:8000/>. `make help` lists the everyday
commands for the dev stack and for production.

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
cd sg101 && npm install       # once, and after package.json changes
make css
```

`npm run watch:css`, in `sg101/`, recompiles on save while working on the Sass.

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
make test                     # the whole suite, or t="forums" for one app
```

The suite includes the browser tests, which drive headless Chromium through
Playwright; `make test-browser` runs only those.

There is a **second, separate run** — the deprecation gate, which promotes
deprecation warnings to errors. It is what has caught every Django removal a
version before it landed, so run it before proposing a change:

```
make deprecation-gate
```

The target runs the suite with `tools/deprecation_gate.sh`'s filter in
`PYTHONWARNINGS`. The script only *prints* that filter — running it by itself
is not the gate. `make -n deprecation-gate` shows the full command.

## Continuous integration

GitHub Actions runs the suite on every push to any branch and on every pull
request to `main` (`.github/workflows/ci.yml`). CI seeds `.env` from `.env.example` and builds the
same Compose image used locally, so the database in CI is identical to a
developer's rather than merely similar.

## Deployment

Production runs this repository's `main` branch: the Docker Compose stack in
`docker-compose.prod.yml`, on a Linode VM behind Cloudflare, live since
2026-10-08. Apache sits in front of gunicorn, alongside PostgreSQL, Redis and
the Celery worker and beat. The host's own configuration (fail2ban, logrotate,
the nightly backup timer, the origin firewall) is versioned here too, under
`apache/`, `backup/`, `fail2ban/`, `firewall/`, `logrotate/` and `msmtp/`.

A deploy is a pull on the server, then one `make` target:

```
git pull
make prod-up        # build and restart; runs no migrations
make prod-deploy    # instead, when the pull carries migrations
```

`prod-deploy` puts the site in maintenance mode while it migrates. Neither
target pulls the `python:3.12` base image, so when the base image itself has a
fix you need (its CA certificates, its pip), run `docker pull python:3.12`
first. `make help` lists the rest of the production targets.

## Documentation

- [`DOCKER.md`](DOCKER.md) — running the site locally, end to end.
- [`AGENTS.md`](AGENTS.md) — a short orientation for AI coding agents, including
  the non-obvious behaviours worth knowing before changing anything.
- [`.agents/summary/index.md`](.agents/summary/index.md) — generated
  architecture and per-app documentation; start at the index.
- [`.agents/planning/`](.agents/planning/) — the modernization project's design,
  research and status. `STATUS.md` there is the authoritative record of what has
  been done and why.
