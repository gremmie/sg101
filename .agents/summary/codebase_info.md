# Codebase Information

**Generated 2026-08-27.** Supersedes the 2026-07-12 generation, which described
the pre-modernization codebase and had become wrong in every major particular.

## What this is

The Django application behind [SurfGuitar101.com](https://www.surfguitar101.com/),
a community site for instrumental surf music: forums, news, a podcast, photo of
the day, downloads, weblinks, a band map, private messaging, polls, contests,
donations, and an event calendar.

## Stack

| | |
|---|---|
| Language | Python 3.12 (`Dockerfile`) |
| Framework | Django 5.2 LTS |
| Database | PostgreSQL 16 |
| Cache / broker | Redis |
| Async | Celery 5.6 (worker + beat) |
| Search | **PostgreSQL native full-text search** — no Haystack, no Xapian, no third-party search package |
| Object storage | Amazon S3 via boto3 (user photos) |
| Config | `django-environ`; every setting reads from the environment |
| VCS | **git** (`main` = preserved legacy history, `modernize` = active) |
| CI | GitHub Actions, `modernize` branch only |

## Repository layout

Every top-level directory is a Django app, on the standard
`models.py` / `views.py` / `urls.py` / `admin.py` / `forms.py` layout. The Django
*project* package is `sg101/`, not to be confused with the repo root.

- `sg101/settings/` — `base.py` holds everything shared; `local.py`,
  `docker.py`, `docker_test.py`, `production.py`, `test.py` import and override
  it. `databases.py` is a shared helper.
- `core/` — the shared kernel every other app may depend on, and which depends
  on nothing in the repo. Middleware, Redis helper (`services.py`), S3 wrapper
  (`s3.py`), Markdown/HTML rendering (`markup.py`, `html.py`), pagination, mail
  (`functions.py`, `tasks.py`, `email_categories.py`), Who's Online.
- `search/` — the PostgreSQL FTS subsystem built in Step 12: `documents.py`,
  `indexer.py`, `query.py`, `receivers.py`, `reconcile.py`, `tasks.py`.
- `tools/` — standalone scripts run directly, not via `manage.py`.
- `.agents/planning/` — the modernization project's design, research and
  `STATUS.md`. `STATUS.md` is the authoritative record of what has been done and
  why.
- `.agents/tasks/` — per-step code task files driving the work.

## Apps by size (model count)

`elsewhere` 13 · `forums` 9 · `downloads` 8 · `weblinks` 7 · `accounts` 6 ·
`potd` 5 · `messages` 5 · `tagging` 4 · `news` 4 · `bio` 4 · `polls` 3 ·
`comments` 3 — plus a long tail of two- and one-model apps.

`wiki` and `antispam` are behavioural apps; `wiki` has no models at all.

## Modernization status

The repo is mid-project. `.agents/planning/2026-07-04-modernizing-sg101/STATUS.md`
is authoritative; the short version is that Steps 1-16 are complete (Docker, git,
12-factor config, dead-code prune, Python 3, Django 5.2, PostgreSQL, native
search, S3, transactional email) and Step 17 (CAPTCHA) is in progress.

**A consequence worth knowing:** some subsystems are transitional. The contact
form runs on Turnstile; registration still runs its own question-and-honeypot
flow and gets the widget in a later task. Check `STATUS.md` before assuming
what is live.
