# Components

Each entry below is a top-level Django app (a directory at the repo root).
Grouped by role.

## Platform / shared kernel

- **`core`** — Shared infrastructure used across the site: custom
  middleware (`InactiveUserMiddleware`, `WhosOnline`), Redis connection
  helper (`services.py`), S3 wrapper (`s3.py`), Markdown rendering
  (`markup.py`), HTML sanitizing (`html.py`), custom paginator, download
  helper (`download.py`), the `FixedView` generic view for static pages
  (about/colophon/privacy/tos), and site-wide Celery tasks
  (`cleanup`, `send_mail`, `max_users`).
- **`accounts`** — User registration/login flows, `PendingUser` (email
  confirmation before account activation), illegal username/email
  blocklists.
- **`antispam`** — reCAPTCHA decorator, a `SpamPhrase` blocklist model,
  and signal receivers that log auth events to the `auth` logger for
  fail2ban to consume.
- **`custom_search`** — Glue between Haystack/Xapian and the rest of the
  site: a custom `QueuedSignalProcessor` (`receivers.py`) that decides
  which model saves/deletes get enqueued for re-indexing, plus search
  form/view customizations.
- **`banners`** — Ad campaign/banner rotation (`Campaign`, `Banner`).
- **`countdown`** — Displays a countdown to an upcoming `Event`.
- **`contact`** — Simple contact form (no models).
- **`donations`** — PayPal IPN-based donation tracking (`Donation`
  model), monthly goal display.
- **`irc`** — Renders info about the site's IRC channel (no models).

## Community / content apps

- **`forums`** — The largest app: `Category` → `Forum` → `Topic` → `Post`
  hierarchy, per-category/forum group-based permissions
  (`permissions.py`), attachments, unread-post tracking
  (`ForumLastVisit`/`TopicLastVisit`), RSS feeds, moderation
  (`FlaggedPost`).
- **`bio`** — User profile (`UserProfile`), badge system (`Badge`,
  `BadgeOwnership`, `badges.py`), profile flags/reporting, and the
  "elsewhere" section (social network/IM/website links, backed by the
  third-party `elsewhere` app — see [dependencies.md](dependencies.md)).
- **`bulletins`** — Site-wide announcement banners (`Bulletin`).
- **`comments`** — Generic threaded/flat commenting (`Comment`,
  `CommentFlag`) attachable to other models.
- **`shoutbox`** — Ephemeral live chat-like shout stream (`Shout`,
  `ShoutFlag`).
- **`messages`** — Private user-to-user messaging (`Message`, `Options`,
  `Flag`); relabeled at the Django app-registry level to avoid clashing
  with `django.contrib.messages` (see `sg101/apps.py`).
- **`polls`** — Site polls (`Poll`, `Choice`).
- **`contests`** — Community contests (`Contest`).
- **`wiki`** — No models; middleware/signal glue that issues a signed
  cookie so a separate external MoinMoin wiki instance can authenticate
  site users.
- **`ygroup`** — Read-only archive of posts imported from the site's
  former Yahoo Group (`Thread`, `Post`); see `tools/load_ygroup.py` and
  `tools/translate_yahoo_group.py` for the one-time import scripts.
- **`legacy`** — Data and helpers (`phpbb.py`, `html2md.py`) related to
  migrating content from a prior phpBB-based forum.

## Media / surf-specific apps

- **`news`** — Site news stories, split into `PendingStory`/`Story`
  (`StoryBase`), categories, RSS feed.
- **`podcast`** — Podcast `Channel`/`Item`, searchable via Haystack.
- **`potd`** — "Photo of the Day": `Photo` pool, `Current` (today's
  pick), `Sequence` (ordering), with a Celery task (`pick_potd`) that
  rotates the photo daily.
- **`downloads`** — File download library with categories, moderation
  (`PendingDownload`/`Download` via `DownloadBase`), allowed file
  extensions, and vote/rating tracking (`VoteRecord`).
- **`weblinks`** — Curated external link directory, same
  pending/public split pattern as `downloads` and `news`
  (`LinkBase` → `Link`/`PendingLink`), plus `FlaggedLink` moderation.
- **`bandmap`** — Crowd-sourced map of surf bands (`BandEntry`).
- **`membermap`** — Map of member locations (`MapEntry`).
- **`user_photos`** — Member photo uploads (`Photo`), stored on S3
  (`s3.py`), with rate limiting (`USER_PHOTOS_RATE_LIMIT`).
- **`gcalendar`** — Google Calendar-backed event listing (`Event`,
  `PendingEventManager`), synced via Google OAuth2 (`oauth.py`,
  `calendar.py`).
- **`oembed`** — oEmbed provider/response caching (`Provider`, `Oembed`)
  so embedded media (YouTube, etc.) in posts doesn't re-fetch metadata
  every render.
- **`smiley`** — Custom emoticon/smiley set used in post rendering.

## Project package

- **`sg101/`** — Not an "app" in the content sense; holds
  `settings/` (see [architecture.md](architecture.md)), the root
  `urls.py` that wires every app's `urls.py` together, `celery.py`
  (Celery app bootstrap), and top-level `views.py` (`HomePageView`,
  `StoreView`).

## Non-Django tooling

- **`tools/`** — Standalone scripts (not a Django app): data-migration
  and maintenance scripts (`load_ygroup.py`, `translate_yahoo_group.py`,
  `filter_posts.py`, `flag_data.py`, `post_sub.py`,
  `sg101mp3comptool.py`, `tz.py`). Run directly with the project's
  Python environment, not via `manage.py`.
