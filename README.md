# SurfGuitar101 (sg101)

The Django application that powers [SurfGuitar101.com](https://www.surfguitar101.com/),
a community website for friends and fans of instrumental surf music.
It provides discussion forums, surf music news, a podcast, a daily
photo feature, a downloads library, a curated weblink directory, a
crowd-sourced surf band map, private messaging, polls, contests,
donations tracking, and an event calendar.

## Tech stack

- Python 2 / **Django 1.8**
- MySQL (production/dev), SQLite (test settings)
- Redis (Celery broker, Who's-Online tracking, search-queue backend,
  external wiki auth)
- Celery (scheduled/background jobs)
- Xapian via django-haystack (full-text search)
- Amazon S3 (user photo storage), Google Calendar API, PayPal (donations)

See [`.agents/summary/dependencies.md`](.agents/summary/dependencies.md)
for the full dependency list and [`.agents/summary/architecture.md`](.agents/summary/architecture.md)
for how the pieces fit together.

## Setup

1. Install dependencies:
   ```
   pip install -r requirements_dev.txt
   ```
2. Create `sg101/settings/secrets.json` (not checked into version
   control). It must supply, at minimum:
   ```json
   {
     "SECRET_KEY": "...",
     "DB_NAME": "...",
     "DB_USER": "...",
     "DB_PASSWORD": "...",
     "GCAL_CLIENT_ID": "...",
     "GCAL_CLIENT_SECRET": "...",
     "GCAL_CREDENTIALS_PATH": "...",
     "AWS_ACCESS_KEY": "...",
     "AWS_SECRET_KEY": "...",
     "RECAPTCHA_SITE_KEY": "...",
     "RECAPTCHA_SECRET_KEY": "..."
   }
   ```
   Ask a project maintainer for real values — there is no bundled
   example file.
3. Have MySQL and Redis running locally (or point settings at existing
   instances). `sg101/settings/local.py` expects MySQL via a local Unix
   socket by default.
4. Run migrations and start the dev server:
   ```
   python manage.py migrate
   python manage.py runserver
   ```
   `manage.py` defaults to `DJANGO_SETTINGS_MODULE=sg101.settings.local`.

## Running tests

```
python manage.py test --settings=sg101.settings.test
```

The test settings use SQLite and run Celery tasks eagerly, so no Redis
or MySQL is required to run the test suite.

## Deployment

There is no CI pipeline. Deployment is manual via Fabric
(`fabfile.py`), which runs over SSH against the production host:

```
fab update           # hg pull --update on the server
fab collectstatic    # collect static assets for production
fab touch            # touch the WSGI file to trigger a reload
```

## Documentation

Deeper architectural and per-app documentation is generated into
[`.agents/summary/`](.agents/summary/index.md) — start at `index.md` for
a guided index, or read the root [`AGENTS.md`](AGENTS.md) for a shorter
navigation-oriented summary aimed at AI coding agents.
