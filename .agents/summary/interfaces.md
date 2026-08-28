# Interfaces and Integration Points

**Generated 2026-08-27.**

## URL structure

`sg101/urls.py` mounts each app's own `urls.py` under a prefix. **Prefixes do not
always match app names** — `bio` → `/profile/`, `weblinks` → `/links/`,
`gcalendar` → `/calendar/`. Grep `sg101/urls.py` rather than guessing.

## External services

| Service | Used by | Notes |
|---|---|---|
| PostgreSQL 16 | everything | also the search engine |
| Redis | `core/services.py`, Celery, `whos_online`, `wiki` | cache + broker + presence |
| Amazon S3 | `user_photos`, `core/s3.py` | boto3 |
| Postmark | `core/functions.send_mail` → `core/tasks.py` | SMTP, via env config only |
| Cloudflare Turnstile | `antispam/turnstile.py` | Step 17, not yet wired to forms |
| Google reCAPTCHA | `contact/forms.py` | **being replaced**; see `STATUS.md` |
| Google Calendar | `gcalendar` | carries a Step 8 stub |
| PayPal IPN | `donations` | legacy API |
| MoinMoin wiki | `wiki/middleware.py` | external app, signed-cookie handshake via Redis |

## Mail

Almost all site mail goes through `core.functions.send_mail` → a Celery task,
which is why swapping providers was close to settings-only. Every message
carries an `EmailCategory`, logged one line per send to `email.log` — never the
body.

**Two paths bypass the wrapper**, and both are documented rather than accidental:
Django's `AdminEmailHandler` (error reports), and historically the stock
password-reset view — the latter now uses `SitePasswordResetForm`
(`accounts/urls.py`) specifically to stop it sending inline and outside the
wrapper.

## Logging

Configured in each settings module. Dedicated files with their own handlers:

| Logger | File | Notes |
|---|---|---|
| `auth` | `auth.log` | `propagate: False`. Watched by `fail2ban`. Registration and login failures with IPs. |
| `search` | `search.log` | `propagate: False` — keeps query volume out of `sg101.log` |
| `email` | `email.log` | **`propagate: True`** — deliberately lands in both files |
| root | `sg101.log` | everything else |

**Retention differs sharply and decides what questions can be asked.**
`sg101.log` rotates at 100 KB x 10 (~5 months in practice); `auth.log` at
2 MB x 5 (over 19 months). A question about registration history is answerable;
one about contact-form history five months back is not.

## HTTP clients

`requests` is the only HTTP client. **Pass a timeout.** `antispam/turnstile.py`
takes `TURNSTILE_TIMEOUT` and is the pattern to copy;
`contact/forms.py` predates it and passes none, which is a known defect awaiting
Step 17 task 02.
