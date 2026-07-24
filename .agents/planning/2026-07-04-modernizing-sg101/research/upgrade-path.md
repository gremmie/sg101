# Research: Django/Python Upgrade Path & Dependency Modernization

**Status:** Complete (with web-verified version facts, July 2026).

## The LTS ladder + Python compatibility

Each Django version supports a Python range; the ladder must keep Django and
Python in a compatible window at every rung. Key boundary: **Django 2.0 drops
Python 2** — so the interpreter switch happens *on Django 1.11* (the last version
supporting both).

| Rung | Django | Python support | Notes |
|------|--------|----------------|-------|
| start | 1.9.13 | 2.7 | current |
| 1 | **1.11 LTS** | 2.7, 3.4–3.6 | Make code Py2/Py3-compatible here; **flip interpreter to Py3** while staying on 1.11 |
| 2 | **2.2 LTS** | 3.5–3.9 | Py3-only from here |
| 3 | **3.2 LTS** | 3.6–3.10 | |
| 4 | 4.2 LTS | 3.8–3.12 | **4.2 reached EOL April 2026** → now a *pass-through*, not a safe resting point |
| 5 | **5.2 LTS** ⭐ | 3.10–3.14 | **Target.** Supported until **April 2028**. Land on Python 3.12 (safe, widely supported) |

Sources: [Django releases/endoflife](https://endoflife.date/django),
[Django 5.2 release notes](https://docs.djangoproject.com/en/6.0/releases/5.2/),
[Django release process](https://docs.djangoproject.com/en/dev/internals/release-process/).

**Implication:** 4.2 being EOL means the "acceptable pause point" is really 3.2
(still community-relevant) or just push to 5.2. Land on **5.2 LTS + Python 3.12**.

## Py2→Py3 code surface (from static scan; see codebase-and-coverage.md)

Concentrated & mostly mechanical: ~25 `print` statements, ~35 `except X, e:`,
8 octal literals (`0644`→`0o644`), 8 `iteritems/iterkeys/itervalues`, 1 `xrange`,
**37 `__unicode__`** methods, `urllib2` (donations IPN), `boto` (core/s3.py),
`django.core.urlresolvers` (ygroup). Use `python-modernize`/`futurize` for the
bulk; hand-fix urllib2→requests, boto→boto3, `__unicode__`→`__str__`.

## Django API breakage already spotted (concentrated at 1.11→2.x)

- `MIDDLEWARE_CLASSES` → `MIDDLEWARE` (1.10).
- `SessionAuthenticationMiddleware` removed (2.0).
- `url()` everywhere → `re_path`/`path` (removed 4.0).
- Function-based auth views + `uidb36` in `urls.py` → class-based, `uidb64`
  (1.11/2.1). **Real work at rung 2.**
- `django.core.urlresolvers` → `django.urls` (removed 2.0).
- `render_to_response`, `MIDDLEWARE` tuple/list, on_delete required for FKs (2.0),
  `settings.MIDDLEWARE`, template `TEMPLATE_*` settings — audit per rung.
- Per-rung discipline (Q10): run with `-W error::DeprecationWarning` and clear all
  warnings before each jump.

## Dependency modernization map

Current stack (`requirements.txt`, `requirements_dev.txt`) → modern target:

| Current | Target | Notes / effort |
|---------|--------|----------------|
| Django 1.9.13 | 5.2 LTS | the ladder |
| celery 3.1.23 (+kombu/billiard/amqp/anyjson) | Celery 5.x | **Big jump.** New settings namespace (`CELERY_`/lowercase), new task protocol (4.0), `BROKER_URL`→`broker_url`. Redis broker stays. |
| redis 2.10.5 | redis-py 5.x | |
| boto 2.13 | **boto3** (or `django-storages`) | rewrite `core/s3.py` (~30 lines). Works with S3 *or* Linode/DO S3-compatible object storage |
| Pillow 2.7 | Pillow 11.x | API mostly stable; watch `Image.ANTIALIAS`→`Resampling` |
| mysqlclient 1.4.6 | **drop** (→ **`psycopg2`** for Postgres; psycopg 3 needs Django 4.2, so Step 13 at the earliest) or keep if staying MySQL | tied to DB decision |
| python-dateutil 1.5 | 2.9 | very old→current |
| pytz 2015.2 | `zoneinfo` (Django 4+ default) | drop pytz eventually |
| Markdown 2.5.1 | Markdown 3.x | extension API changed |
| bleach 1.4 | `nh3` (bleach is deprecated/archived) | evaluate; sanitization is security-critical |
| django-tagging 0.4.3 | `django-taggit` | tagging is stale; taggit is maintained — a small data migration |
| django-picklefield 0.3.1 | current, or **remove pickle** → JSONField | pickle fields are a security smell; prefer JSON |
| django-haystack 2.4.1 + xapian-haystack + queued-search + `queues` | **drop** (Postgres FTS) or haystack 3.x | see search-stack.md (decision pending snapshot) |
| google-api-python-client 1.3.1 + oauth2client + httplib2 | google-api-python-client v2 + `google-auth` | gcalendar revival (Q2); contained to `calendar.py`+`oauth.py` |
| six 1.8, simplejson, repoze.timeago | remove (stdlib) after Py3 | |
| requests 2.7, html5lib, lxml, ftfy, docutils, uritemplate | current | routine bumps |
| django-elsewhere (`elsewhere`) | user's GitHub fork, port to Py3 | vendor/pin |
| Fabric 1.4.1 (dev) | drop (Docker deploy) or Fabric 3 | deployment replaced by container pipeline |
| pycrypto 2.5 (dev) | **drop** (unused in app code; CVEs) | confirm nothing imports `Crypto` |
| mock 1.0.1 (dev) | stdlib `unittest.mock` | |
| django-debug-toolbar 1.4 (dev) | current | |

## Recommended rung workflow (per Django step)
1. Bump Django to next rung in the Docker env.
2. Fix breakage until the app boots and the suite passes.
3. Bump/replace dependencies required by that rung (not all at once).
4. Clear all deprecation warnings (CI: warnings-as-errors).
5. Run the manual smoke checklist.
6. Commit; tag the rung. Site is shippable at this point.

## Private/vendored deps to home before CI
- `elsewhere` (django-elsewhere) → user's fork.
- `queues` (private `bobcat` hg) → vendor, or moot if Postgres FTS drops it.
- `xapian-haystack` pin → moot if Postgres FTS.
