# Research topic 3: Playwright in Docker and CI

Researched 2026-10-10. Question (from Q9): what does Playwright for Python
add to the test image and to CI, and how does it run against Django's live
server under `docker_test` settings?

**It works, with one setting Django needs.** Measured in throwaway
containers (`docker compose run --rm -u root web`) from the dev image:
Debian 13.6, aarch64 on the Mac, Python 3.12, Django 5.2.17. The image itself
wasn't changed.

## Install cost

| | Measured |
|---|---|
| `pip install playwright` | 1.63.0; 3 s; 136 MB in site-packages |
| `playwright install --with-deps chromium` (full Chromium and the headless shell) | 17 s; 662 MB of browsers; 88 MB of Debian packages fetched |
| `playwright install --with-deps --only-shell chromium` | **269 MB** (headless shell and ffmpeg only) |

The dev image is 2.21 GB today. With `--only-shell` it would grow by roughly
400 MB plus the system libraries. **Only the `dev` target needs it:** the `prod`
target and leopard's image are untouched. `--with-deps` runs `apt-get`, so in
the Dockerfile it runs before the `USER` switch.

CI builds the same image (`docker compose build web`), so it pays the same
~20 s per build, plus the download, unless Docker layer caching is added.
GitHub's `ubuntu-latest` runner is x86-64. Playwright ships Chromium for both
architectures. Only the Mac's aarch64 was tried.

## Running against Django's live server

The probe was a `StaticLiveServerTestCase` that starts Playwright's sync API
in `setUpClass`, opens a headless Chromium, and loads pages from
`self.live_server_url`. It ran under the unchanged `docker_test` settings
(PostgreSQL, Redis, `DEBUG = False`):

- `/forums/` loaded in 0.43 s with its real title and **no JavaScript page
  errors**. That's an old-design page with jQuery, Cycle and the shoutbox.
- `/news/submit/` redirected to `/accounts/login/?next=…` as expected for an
  anonymous user.
- Whole test: 1.3 s, plus about 1 s of browser start per class.

**The catch: `DJANGO_ALLOW_ASYNC_UNSAFE`.** Playwright's sync API runs an
asyncio event loop in the test's thread. Without the override, the first ORM
call after Playwright starts raises `SynchronousOnlyOperation: You cannot call
this from an async context`. Reproduced: a `User.objects.create_user()`
after `sync_playwright().start()` failed this way. With
`DJANGO_ALLOW_ASYNC_UNSAFE=true` in the environment, the same test passed.
Two fixes, both common:

- **Set it only for the browser tests:** `os.environ.setdefault(...)` in their
  shared base class, before Playwright starts.
- Or set it in `docker_test.py` for the whole suite.

The first keeps Django's safety check active for every other test.

## For the design

- **A shared base class** (`core/tests/browser.py` or similar) starts one
  browser per class, sets the async override, and offers `login_as(user)`
  (copy the session cookie from `Client.force_login` into the browser
  context) and a page-error collector that fails the test.
- **Tag the browser tests** (`@tag('browser')`) so a quick local run can
  `--exclude-tag browser`. CI runs everything.
- **Uploads:** the multi-upload test (Q9) must not reach S3. The test settings
  don't set `USER_PHOTOS_LOCAL_UPLOAD` or `MEDIA_ROOT`. Existing tests switch
  storage per test: `patch` on the settings in
  `core/tests/images/test_upload.py`, and `override_settings` with a temp
  `MEDIA_ROOT` in `user_photos/tests/test_storage.py`. Follow the latter:
  `override_settings(USER_PHOTOS_LOCAL_UPLOAD=True, MEDIA_ROOT=<temp dir>)` on
  the browser test class.
- **Celery is eager in tests**, so a browser test catches DOM faults, not
  worker faults. AGENTS.md's warning about deferred work still applies.
