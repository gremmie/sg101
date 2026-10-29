# Components

**Generated 2026-10-21.** Grouped by role rather than listed alphabetically, so
an agent can find the right app without reading all of them.

## The kernel — `core`

Importable by anything. Its library modules import no app; `markup.py`,
`tasks.py` and the template tags do (see `architecture.md`).

| Module | Responsibility |
|---|---|
| `functions.py` | `send_mail` wrapper (nearly all site mail funnels here), `get_ip`, `email_admins` |
| `tasks.py` | the Celery task that sends mail; `cleanup` and `max_users` on beat |
| `email_categories.py` | `EmailCategory` StrEnum + subject redaction rules for `email.log` |
| `mail_backends.py` | `AllowlistEmailBackend`: sends only to listed addresses, for a copy of the site holding real member data |
| `markup.py`, `html.py`, `mdexts/` | Markdown rendering, HTML cleaning, the site's Markdown extensions |
| `middleware.py` | `RealClientIP` (production only), `InactiveUserMiddleware`, `WhosOnline` |
| `storage.py` | the manifest storage that also hashes JavaScript module imports |
| `services.py` | Redis connection helper |
| `s3.py` | S3 wrapper (user photos) |
| `download.py` | fetching remote files, used by the hot-link image path |
| `whos_online.py` | Redis-backed presence |
| `paginator.py` | shared pagination |
| `templatetags/script_tags.py` | `{% script_tags "jquery" %}` and friends: the site-served script bundles |
| `management/commands/` | `make_fixed_page` (Markdown fixed pages), `max_users` |
| `tests/browser.py` | the Playwright browser-test base class |

**Mail has one documented exception.** Django's `AdminEmailHandler` sends error
reports *outside* the wrapper, so crash mail is neither categorised nor counted
in `email.log`. `core/email_categories.py` says so in its docstring.

## Search — `search`

`documents.py` (the index model), `indexer.py` (writes), `query.py` (reads,
including spelling variants of a few band names), `receivers.py` (signals),
`tasks.py` (Celery), `reconcile.py` (weekly drift sweep),
`forms.py`/`views.py`/`urls.py` (the `/search/` UI).

## Anti-abuse — `antispam`

- `models.py` — `SpamPhrase`
- `utils.py` — phrase matching, `spam_check`, `suspend_user`, `deactivate_spammer`.
  **Heavy imports**; see `architecture.md`.
- `decorators.py` — `log_auth_failures`, wrapping auth views so failed POSTs
  reach `auth.log`, which `fail2ban` reads. Narrow imports.
- `turnstile.py` — Cloudflare Turnstile verification, on the contact form and
  on registration. Logs to `turnstile.log`, including submissions that carry no
  token at all. Narrow imports.

## Identity — `accounts`, `bio`

`accounts` owns registration, activation, login and password flows. **Registration
is one page**: details, Turnstile, a honeypot field named `question`, and the
agreement boxes, then an emailed activation link. Login matches the username
without regard to case. `bio` owns `UserProfile`, attached to `auth.User` by
`OneToOneField(related_name='profile')` — there is **no custom
`AUTH_USER_MODEL`**.

## Community content

`forums` (the largest), `news`, `downloads`, `weblinks`, `podcast`, `potd`
(photo of the day), `bandmap`, `ygroup` (imported Yahoo group archive), `polls`,
`contests`, `shoutbox`, `messages` (private messaging), `comments`,
`elsewhere` (a member's off-site profile links; a vendored fork, seeded with
the networks members use), `smiley`, `bulletins`, `countdown`, `banners`,
`oembed`, `donations`, `contact`, `user_photos`.

- **`forums` keeps derived state in Redis** (counts, latest posts).
  `manage.py rebuild_redis` rebuilds it from the database, for after a restore.
- **`news` tags are a PostgreSQL array on the story**, not a tagging app.
  `rename_tag` and `merge_tags` are its management commands.
- **`messages` collides with `django.contrib.messages`.** Resolved in
  `sg101/apps.py` by `DjangoMessagesConfig`, which relabels the built-in app to
  `django_messages`. Do not rename this app or its `AppConfig` without
  understanding why it exists.

## Integrations

`gcalendar` (Google Calendar through a service account; approved member events
are pushed to the site's calendar), `donations` (PayPal IPN), `user_photos`
(S3, plus the hot-link path that fetches a remote image).

## Two page designs, side by side

Most templates extend **`v3/base.html`** (Foundation 6, jQuery 3.7.1, the
`main.min.css` built from `sg101/scss/`). **The forums, the shoutbox, `ygroup`
and the flatpage template still extend the old `base.html`** (Blueprint, the
old scripts). Views put `V3_DESIGN` in the context for v3 pages, and a few
`core` template tags choose their partial by it. A template-only change can
therefore land in either design; check which base the page extends. The V3
forums project retires `base.html` once the forums move.

## The post box — the shared editor

`sg101/static/js/v3/post_box/` is the editor on the v3 posting forms: ES
modules for the editor, preview, smiley picker, hot-link and upload modals.
Templates load `post_box.js` with `type="module"`; `js/v3/core/http.js` is its
fetch helper. It is on the `bio`, `comments/v3`, `contests`, `downloads`,
`gcalendar`, `messages`, `news`, `polls` and `potd` templates. **The forums are
not on it yet**: `forums/new_post.html` and `edit_post.html` still load
markItUp and `js/forums.js` through `{% script_tags %}`. Moving them is the V3
forums project's later work (`.agents/planning/2026-10-10-v3-forums-and-js/`).

## Host and proxy configuration — not apps

Versioned with the code, installed on leopard by the cutover runbook.

| Directory | What it is |
|---|---|
| `apache/` | the `proxy` image (Debian's apache2) and its config, bind-mounted so a change is a graceful reload: vhost, `mod_remoteip`, maintenance mode, `cloudflare-ranges.txt` |
| `backup/` | the `backup` image, `backup.sh`, the systemd timer (04:30 UTC), bucket provisioning and the write-only IAM policy |
| `fail2ban/` | jails `sg101-auth` and `sg101-reg` reading `auth.log`, and an action that bans at Cloudflare's block list |
| `firewall/` | settings for `tools/origin_firewall.py`, which keeps Linode's Cloud Firewall to Cloudflare's ranges |
| `logrotate/` | rotation for the Django and Apache logs, and a heartbeat on the nightly run |
| `msmtp/` | send-only host mail (cron, root) relayed through Postmark |
