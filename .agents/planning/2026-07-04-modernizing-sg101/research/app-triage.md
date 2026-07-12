# Research: App Usage Triage (keep / prune / port)

**Status:** Static triage complete; a few items confirmed with the user
(2026-07-04). Data sources: `sg101/urls.py` (URL routing), `INSTALLED_APPS`,
per-app `templatetags/`, template references, management commands, models.

## Legend
- **KEEP** — core, actively used, port forward.
- **PRUNE** — remove as part of lift-**and-prune**.
- **REVIVE** — currently broken/stale but wanted; modernize.
- **VERIFY** — needs a data/usage check (ideally against a DB snapshot) before final call.

## Triage table

| App | Routed at | Role | Verdict |
|-----|-----------|------|---------|
| accounts | `/accounts/` | Auth, registration, login | **KEEP** (critical) |
| bio | `/profile/` | User profiles (+search index) | **KEEP** |
| forums | `/forums/` | Core forums (+search, feeds, tasks) | **KEEP** (critical) |
| news | `/news/` | News stories (+search, feed) | **KEEP** |
| downloads | `/downloads/` | File downloads (+search) | **KEEP** |
| weblinks | `/links/` | Link directory (+search) | **KEEP** |
| podcast | `/podcast/` | Podcast (+search) | **KEEP** |
| potd | `/potd/` | Photo of the day (+Celery pick) | **KEEP** |
| polls | `/polls/` | Polls | **KEEP** |
| messages | `/messages/` | Private messages (+purge task) | **KEEP** |
| comments | `/comments/` | Commenting system | **KEEP** |
| donations | `/donations/` | PayPal IPN donations | **KEEP** (modernize: `urllib2`→requests; verify PayPal IPN still supported) |
| contests | `/contests/` | Contests | **KEEP** (VERIFY still run) |
| contact | `/contact/` | Contact form | **KEEP** |
| core | `/core/` | Shared utilities, middleware, S3, tasks | **KEEP** (foundational) |
| bandmap | `/bandmap/` | Band map (mgmt cmd, templates) | **KEEP** |
| membermap | `/member_map/` | Member map | **KEEP** (VERIFY; no tests) |
| user_photos | `/user_photos/` | S3 photo uploads | **KEEP** (S3/boto→boto3) |
| shoutbox | `/shout/` | Shoutbox | **KEEP** |
| smiley | `/smiley/` | Emoticons (templatetag) | **KEEP** (used via `smiley_tags`) |
| antispam | `/antispam/` | Spam defense (+reCAPTCHA support) | **KEEP** |
| gcalendar | `/calendar/` | Google Calendar events | **REVIVE** (port `apiclient`/`httplib2`/`oauth2client` → modern `google-api-python-client` v2 + `google-auth`) |
| oembed | `/oembed/` | oEmbed media embedding | **KEEP** (VERIFY usage; likely used by forum/markup) |
| ygroup | `/ygroup/` | Read-only Yahoo Group archive (+search) | **KEEP** (archive of historical content; `__unicode__`, `django.core.urlresolvers` to fix) |
| countdown | *(templatetag)* | Countdown widget in `base.html` | **KEEP** (used via `countdown_tags`) |
| banners | *(templatetag)* | Banner ads/rotation | **KEEP** (used via `banner_tags`; VERIFY still used) |
| bulletins | *(templatetag)* | Site bulletins/announcements | **KEEP** (used via `bulletin_tags`) |
| **irc** | `/irc/` | IRC integration | **PRUNE** (user: not used) |
| **legacy** | *(none)* | One-off phpBB→Django import scripts (`import_old_*`, `translate_old_posts`, `phpbb.py`, `html2md.py`) | **PRUNE** (user confirmed; keep a git tag for reference) |
| **wiki** | *(middleware)* | SSO cookie bridge to external **MoinMoin** wiki (+cookie-expiry task) | **RETIRE (candidate)** — user open to retiring the MoinMoin wiki; if retired, prune the `wiki` app, `WikiMiddleware`, and `wiki.tasks.expire_cookies`. Archive wiki content first. |
| custom_search / queued_search / queues | *(search)* | Async Xapian index updating | **PRUNE** if moving to Postgres FTS (see `search-stack.md`) |
| elsewhere | — | django-elsewhere (social links) | **KEEP** (use user's GitHub fork; port to Py3) |
| tagging | — | django-tagging | **KEEP/REPLACE** (django-tagging is stale; evaluate maintained fork/alternative in `upgrade-path.md`) |

## Confirmed user decisions (2026-07-04)
- **`irc`** → prune.
- **`legacy`** → prune (one-time importers; tag in git history, then remove).
- **MoinMoin wiki** → "live but could retire it" → treat `wiki` app as a
  **retire candidate**: plan to archive wiki content and prune the app + bridge,
  unless the user decides to keep it. (If kept, the external MoinMoin — legacy
  Py2 — becomes its own hosting/modernization concern to track separately.)
- **Search** → live in prod; plan to replace Xapian with Postgres FTS (prunes
  custom_search/queued_search/queues). See `search-stack.md`.

## Still to VERIFY (ideally against a production DB snapshot)
- `contests`, `banners`, `membermap`, `oembed` — confirm still actively used
  (row counts / recent activity) before final keep/prune.
- Whether anything imports from `legacy` beyond its own commands (grep clean so
  far) before deletion.
