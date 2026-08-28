# Dependencies

**Generated 2026-08-27.** Versions from `requirements.txt`; treat that file as
authoritative and this as orientation.

## Core

| Package | Version | Role |
|---|---|---|
| Django | 5.2.17 | LTS |
| psycopg2 | 2.9.12 | PostgreSQL driver |
| celery | 5.6.3 | background and scheduled work |
| redis | 6.4.0 | cache, broker, presence |
| django-environ | 0.14.0 | 12-factor config |
| boto3 | 1.43.72 | S3 (user photos) |
| requests | 2.34.2 | outbound HTTP |
| Pillow | 12.3.0 | image handling |

Runtime is **Python 3.12** (`Dockerfile`).

## Deliberately absent

- **No Haystack, Xapian, or third-party search package.** Search is native
  PostgreSQL FTS. `tools/xapian_installer.sh` is a leftover of the removed stack
  and installs nothing this project uses.
- **No `django-anymail`.** Email is SMTP through environment configuration; the
  provider swap needed no package.
- **No linter or formatter config** in the repo.
- **No `secrets.json`.** Retired in Step 3.

## Services, not packages

PostgreSQL 16, Redis, Amazon S3, Postmark, Cloudflare (DNS/CDN/WAF, Email
Routing, Turnstile), Google Calendar, PayPal, and an external MoinMoin wiki.

## Version discipline

The **deprecation gate** — the suite run with deprecation warnings promoted to
errors — is the mechanism that has caught every Django removal a version before
it landed. It is not optional tooling; it is how the upgrade ladder was climbed
safely. See `workflows.md`.
