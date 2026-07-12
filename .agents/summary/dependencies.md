# Dependencies

Pinned in `requirements.txt` (production + dev) and `requirements_dev.txt`
(adds dev-only tooling on top via `-r requirements.txt`).

## Framework & data layer

- **Django 1.8.15** — web framework (old-style `MIDDLEWARE_CLASSES`,
  pre-`AppConfig.ready()` idioms in older apps)
- **MySQL-python** — MySQL DB driver
- **django-picklefield** — pickled-object model fields
- **django-tagging** — tagging support (`FORCE_LOWERCASE_TAGS`,
  `MAX_TAG_LENGTH` in settings)

## Search

- **django-haystack 2.4.1** — search abstraction layer
- **xapian-haystack** (installed from a pinned commit of
  `github.com/notanumber/xapian-haystack`, not PyPI) — Xapian backend for
  Haystack
- **queued-search 2.1.0** + `-e hg+ssh://.../queues` (private Mercurial
  dependency, "queues-dev") — the batching queue in front of Xapian
  indexing described in [workflows.md](workflows.md)

## Async / background jobs

- **celery 3.1.86**, **kombu**, **amqp**, **billiard**, **anyjson** —
  task queue stack
- **redis**, **python-memcached** — Redis client (broker + Who's-Online
  + wiki cookie set) and memcached client (production cache backend)

## External service SDKs

- **boto 2.13.0** — Amazon S3 client (`core/s3.py`, `user_photos`)
- **google-api-python-client**, **oauth2client**, **httplib2**,
  **uritemplate**, **pyasn1**, **pyasn1-modules**, **rsa** — Google
  Calendar OAuth2 integration (`gcalendar`)
- **requests** — general HTTP client

## Content processing

- **Markdown 2.5.1** — renders user-authored profile/signature/post text
  to HTML (`core/markup.py`)
- **bleach 1.4**, **html5lib 1.0b3**, **lxml 3.4.2**, **docutils 0.10** —
  HTML sanitizing/parsing pipeline for user-submitted content
- **ftfy 2.0.1** — fixes mangled Unicode/mojibake in imported text (used
  heavily by the `legacy`/`ygroup` phpBB and Yahoo Group import tooling)
- **Pillow 2.7.0** — image processing (avatars, user photos, POTD)

## Misc

- **django-elsewhere** (installed from a pinned GitHub commit, app name
  `elsewhere`) — backs the "elsewhere" section of a user's profile
  (`bio`'s `edit_elsewhere` view/template): social network profiles,
  instant messenger handles, and personal websites a member lists on
  their profile page (`SocialNetworkForm`, `InstantMessengerForm`,
  `WebsiteForm`, `WebsiteProfile` models)
- **python-dateutil 1.5**, **pytz** — date/time handling
- **repoze.timeago** — human-readable relative timestamps ("3 hours ago")
- **simplejson**, **six** — JSON/Py2-3 compat shims

## Dev-only (`requirements_dev.txt`)

- **Fabric 1.4.1** — deployment automation (`fabfile.py`)
- **django-debug-toolbar 1.4** — auto-enabled in `settings/local.py`
  when `DEBUG=True` and the package is importable
- **mock**, **testfixtures** — test helpers
- **pycrypto**, **ssh** — dependencies of Fabric's SSH transport
- **sqlparse** — SQL formatting (debug toolbar dependency)

## Pinned VCS dependencies (not on PyPI)

Three packages are installed via `-e` (editable) VCS URLs at specific
commits rather than version numbers — treat these as vendored/forked code
whose source lives outside this repo:

```
git+https://github.com/gremmie/django-elsewhere.git@1203bd3...
git+https://github.com/notanumber/xapian-haystack.git@a3a3a4e...
hg+ssh://brian@bobcat//svr/dvcs/hg/repos/public/queues@862e884...
```

Upgrading these requires access to the referenced repos/hosts, not just
a PyPI version bump.
