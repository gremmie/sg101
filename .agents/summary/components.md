# Components

**Generated 2026-08-27.** Grouped by role rather than listed alphabetically, so
an agent can find the right app without reading all of them.

## The kernel — `core`

Importable by anything, imports nothing from the repo.

| Module | Responsibility |
|---|---|
| `functions.py` | `send_mail` wrapper (nearly all site mail funnels here), `get_ip`, `email_admins` |
| `tasks.py` | the Celery task that actually sends mail |
| `email_categories.py` | `EmailCategory` StrEnum + subject redaction rules for `email.log` |
| `markup.py`, `html.py` | Markdown rendering and HTML cleaning |
| `services.py` | Redis connection helper |
| `s3.py` | S3 wrapper (user photos) |
| `middleware.py` | site-wide middleware |
| `whos_online.py` | Redis-backed presence |
| `paginator.py` | shared pagination |

**Mail has one documented exception.** Django's `AdminEmailHandler` sends error
reports *outside* this wrapper, so crash mail is neither categorised nor counted
in `email.log`. `core/email_categories.py` says so in its docstring.

## Search — `search`

`documents.py` (the index model), `indexer.py` (writes), `query.py` (reads),
`receivers.py` (signals), `tasks.py` (Celery), `reconcile.py` (weekly drift
sweep), `forms.py`/`views.py`/`urls.py` (the `/search/` UI).

## Anti-abuse — `antispam`

- `models.py` — `SpamPhrase`
- `utils.py` — phrase matching, `spam_check`, `suspend_user`, `deactivate_spammer`.
  **Heavy imports**; see architecture.md.
- `decorators.py` — `log_auth_failures`, wrapping auth views so failed POSTs
  reach the auth log that `fail2ban` watches. Narrow imports.
- `turnstile.py` — Cloudflare Turnstile verification (Step 17). Narrow imports.

## Identity — `accounts`, `bio`

`accounts` owns registration, activation and password flows. `bio` owns
`UserProfile`, attached to `auth.User` by `OneToOneField(related_name='profile')`
— there is **no custom `AUTH_USER_MODEL`**.

Registration is multi-stage: a details form, a session-held code echoed across
two pages, then an emailed activation link. Step 17 task 04 collapses this;
check `STATUS.md` for current state.

## Community content

`forums` (9 models — the largest), `news`, `downloads`, `weblinks`, `podcast`,
`potd` (photo of the day), `bandmap`, `ygroup` (imported Yahoo group archive),
`polls`, `contests`, `shoutbox`, `messages` (private messaging), `comments`,
`elsewhere` (13 models — off-site profile links), `tagging`, `smiley`,
`bulletins`, `countdown`, `banners`, `oembed`, `donations`, `contact`,
`user_photos`, `snapshots`.

**`messages` collides with `django.contrib.messages`.** Resolved in
`sg101/apps.py` by `DjangoMessagesConfig`, which relabels the built-in app to
`django_messages` (wired at `sg101/settings/base.py:158`). Do not rename this app
or its `AppConfig` without understanding why it exists.

## Integrations

`gcalendar` (Google Calendar — carries a Step 8 stub awaiting Step 18),
`donations` (PayPal IPN), `user_photos` (S3), `wiki`.

**`wiki` has no models.** It exists to mint a signed cookie
(`wiki/middleware.py`) that a separate external MoinMoin application validates
against a Redis set. Wiki content is not in this repo. Step 19 retires it.
