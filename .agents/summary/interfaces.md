# Interfaces and Integration Points

**Generated 2026-10-21.**

## URL structure

`sg101/urls.py` mounts each app's own `urls.py` under a prefix. **Prefixes do not
always match app names** — `bio` → `/profile/`, `weblinks` → `/links/`,
`gcalendar` → `/calendar/`. Grep `sg101/urls.py` rather than guessing.

Apache answers some paths without Django: `/media/`, `/photos/`, `/hosted/`,
`/favicon.ico`, `/robots.txt`, and `/offline.html`, which is every response
while maintenance mode is on (`make prod-maint-on`).

## External services

| Service | Used by | Notes |
|---|---|---|
| PostgreSQL 16 | everything | also the search engine |
| Redis | `core/services.py`, Celery, `whos_online`, `forums`, cache | db 0 site state, db 1 broker, db 2 cache |
| Amazon S3 | `user_photos`, `core/s3.py`; the backups | boto3; the backup buckets are separate and write-only to the job |
| Postmark | `core/functions.send_mail` → `core/tasks.py`; host mail via `msmtp/` | SMTP, configured from the environment only |
| Cloudflare | DNS, TLS, CDN, Email Routing, the block list, request buffering | the block list is written by fail2ban's action and `tools/cloudflare_block_list.py` |
| Cloudflare Turnstile | `antispam/turnstile.py` | on the contact form and registration |
| Linode Cloud Firewall | `tools/origin_firewall.py` | admits only Cloudflare's ranges to the origin |
| Google Calendar | `gcalendar` | a service account; the key is mounted into `web` |
| PayPal IPN | `donations` | legacy API |
| healthchecks.io | `backup.sh`, logrotate's heartbeat | alarms on a failed or missing nightly run |

## Mail

Almost all site mail goes through `core.functions.send_mail` → a Celery task.
Every message carries an `EmailCategory`, logged one line per send to
`email.log` — never the body. No-reply mail is sent from a fixed address, not
one derived from `Site.domain`.

**One path bypasses the wrapper, deliberately**: Django's `AdminEmailHandler`
(error reports, on in production only). The stock password-reset view would
be a second; it is replaced by `SitePasswordResetForm` (`accounts/urls.py`)
precisely so that it does not send inline and outside the wrapper. **Host mail is a separate path**: cron and root
mail on leopard goes through `msmtp` to Postmark, not through Django.

`core.mail_backends.AllowlistEmailBackend` delivers only to listed addresses.
It is for a copy of the site holding real member data, such as a beta or a
rehearsal, and is not production's backend.

## Logging

Built by `sg101/settings/logging_config.py` for each target. Every timestamp
is UTC. Dedicated files with their own handlers:

| Logger | File | Notes |
|---|---|---|
| `auth` | `auth.log` | `propagate: False`. **One record per line**, line breaks escaped, because fail2ban reads it a line at a time. Registration and login failures with IPs. |
| `turnstile` | `turnstile.log` | every verification, and submissions that carry no token |
| `search` | `search.log` | `propagate: False` — keeps query volume out of `sg101.log` |
| `email` | `email.log` | **`propagate: True`** — deliberately lands in both files |
| root | `sg101.log` | everything else; also the container's output |

**In production the handlers never rotate**; they are `WatchedFileHandler`s,
because a dozen processes share each file. Rotation is the host's, in
`logrotate/sg101`, and the files are on leopard under `/svr/sg101/var/log/`:

| File | Rotation | What that holds in practice |
|---|---|---|
| `sg101.log` | 2 MB × 12, checked daily | **about ten months**: production writes roughly 85 KB a day. It was 100 KB × 10, about three weeks, until 2026-10-22 |
| `auth.log` | 2 MB × 12 | years at the current rate |
| `email.log`, `search.log`, `turnstile.log` | 2 MB × 5 | years at the current rate; none has rotated yet |
| Apache `access.log`, `error.log` | weekly × 26 | six months |

**A question about anything only `sg101.log` records** — a traceback, a
`User deactivated for spam:` line — **reaches back only to 2026-09-27**, the
oldest line when the rotation was raised. From there the history grows until
the larger files hold about ten months. For spam history read the database
(`UserProfile.status`), not the log.
`WORKER TIMEOUT` lines are gunicorn's, in `web`'s container output, and go when
the container is replaced by a deploy.

The dev target writes the same files under `sg101/logs/`, rotating in process,
at DEBUG.

## HTTP clients

`requests` is the only HTTP client. **Pass a timeout.** `antispam/turnstile.py`
takes `TURNSTILE_TIMEOUT` and is the pattern to copy.
