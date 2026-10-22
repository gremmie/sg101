# Dependencies

**Generated 2026-10-21.** `requirements.txt`, `requirements_dev.txt` and
`sg101/package.json` are authoritative; this is orientation. Every Python pin
is exact, transitive ones included where they matter, and most carry a comment
saying why.

## Python — runtime

| Package | Role |
|---|---|
| Django 5.2 | LTS |
| gunicorn | the application server in production |
| whitenoise | serves the collected static files from the application process |
| psycopg2 | PostgreSQL driver |
| celery, kombu, billiard, amqp, vine | background and scheduled work |
| redis | cache, broker, presence, forum state |
| django-environ | 12-factor config |
| boto3 | S3 (user photos) |
| requests, certifi | outbound HTTP; certifi pinned so a withdrawn CA stops being trusted when the pin moves |
| google-api-python-client, google-auth | the calendar's service account |
| Markdown, bleach, lxml, docutils, ftfy | rendering and cleaning member content |
| Pillow | images |
| tzdata | zoneinfo's backward names: most profiles store `US/Pacific`-style zones the base image lacks |

Runtime is **Python 3.12** (`Dockerfile`).

## Python — dev image only

`playwright` (with headless Chromium installed in the dev image),
`django-debug-toolbar`, `coverage`, `testfixtures`.

## Front end

- **Foundation 6.3.1's Sass** and Motion UI, compiled by `sass` + PostCSS in
  `sg101/` (`npm run build:css`). Node is a developer dependency only; the
  application image has none.
- **jQuery 3.7.1 and jQuery UI 1.13.3, self-hosted** in
  `sg101/static/js/vendor/`, with Foundation 6.2.0's JavaScript patched by one
  line for jQuery 3.
- **The post box is plain ES modules** with no build step and no jQuery.
- The old `base.html` design still carries Blueprint and markItUp for the
  pages not yet moved (see `components.md`).

## Deliberately absent

- **No Haystack, Xapian, or third-party search package.** Search is native
  PostgreSQL FTS. `tools/xapian_installer.sh` is a leftover and installs
  nothing this project uses.
- **No `django-anymail`.** Email is SMTP through environment configuration.
- **No django-tagging.** News tags are a PostgreSQL array.
- **No linter or formatter config**, apart from `pyrightconfig.json` for
  editor type checking.
- **No `secrets.json`.**

## Services, not packages

PostgreSQL 16, Redis 8, Amazon S3, Postmark, Cloudflare (DNS, CDN, WAF, block
list, Email Routing, Turnstile), Linode (the VM and its Cloud Firewall),
Google Calendar, PayPal, healthchecks.io.

## Version discipline

The **deprecation gate** — the suite run with deprecation warnings promoted to
errors — is the mechanism that has caught every Django removal a version before
it landed, and CI runs the suite under it. See `workflows.md`.

**Base-image updates do not arrive on their own.** `make prod-up` reuses the
cached `python:3.12` base, so its CA store and bundled pip stay as they were
until `docker pull python:3.12` before a build.
