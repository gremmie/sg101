# Task: Serve the Application with gunicorn and WhiteNoise

## Description
Replace Django's development server with gunicorn in the production image, and
give static files a real home through WhiteNoise and a `STATIC_ROOT` that is not
a temporary directory.

## Background
The production image currently ends in
`CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]`. `runserver` is
Django's development server — single-threaded, auto-reloading, and documented as
unsuitable for production use. Neither `gunicorn` nor `whitenoise` appears
anywhere in the repository today: not in `requirements.txt`,
`requirements-docker.txt`, the `Dockerfile`, or any settings module.

**`sg101/settings/base.py:95` sets `STATIC_ROOT = '/tmp/test_static_root'`** — a
test value living in the base module, so `collectstatic` has no real destination.

On jaguar, Apache serves static files from a `static_serve` directory via the
config in `sg101/apache/`. That configuration does not travel with the code.
WhiteNoise replaces it by serving static assets from inside the application, which
keeps the container self-contained. **Cloudflare fronts the origin**, so WhiteNoise
serves each asset once to the edge rather than to every visitor, and the usual
performance objection does not apply at this site's volume.

**WhiteNoise covers static files only.** `/media` — avatars, `downloads`, `potd`,
smilies, banners — stays on the VM's disk and is served by the proxy; user photos
are on S3. Conflating the two is the failure mode to avoid.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`
  (§3.2 target state — gunicorn and WhiteNoise appear in the diagram)

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/research/docker-strategy.md`
  (*Static files* — records that prod uses `ManifestStaticFilesStorage` today)

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Add `gunicorn` to `requirements.txt` and make it the production image's entry
   point, serving `sg101.wsgi`.
2. Size the worker count from the VM's CPU count rather than hardcoding it, and
   record the reasoning in a comment.
3. Add `whitenoise` and place its middleware immediately after
   `SecurityMiddleware`, which is where it must sit.
4. Give `STATIC_ROOT` a real path outside `/tmp`, and confirm whether the
   existing `ManifestStaticFilesStorage` configuration survives Django 5.2's
   `STORAGES` setting.
5. Run `collectstatic` as part of the image build or the container entry point,
   and state which and why.
6. Leave the development workflow on `runserver`.

## Dependencies
- Task 01 — the `prod` Dockerfile target and production settings module
- Django 5.2's `STORAGES` setting, which supersedes `STATICFILES_STORAGE`

## Implementation Approach
1. Add both packages and wire the middleware, checking the existing static
   storage configuration against Django 5.2 rather than assuming it carries over.
2. Give `STATIC_ROOT` a real value and move it out of the base module if the test
   settings are what wanted `/tmp`.
3. Replace the production `CMD` with gunicorn; leave the dev target alone.
4. Verify by requesting a static asset from a running production container and
   reading the response headers, not by inspecting configuration.

## Acceptance Criteria

1. **The production image does not run `runserver`**
   - Given the image built at the `prod` target
   - When it is started
   - Then gunicorn serves the application and `runserver` appears nowhere in the
     production path

2. **`collectstatic` has a real destination**
   - Given production settings
   - When `collectstatic` runs
   - Then assets land under a non-temporary `STATIC_ROOT` and the command reports
     a non-zero file count

3. **Static assets are served with cache headers**
   - Given a running production container
   - When a hashed static asset is requested
   - Then WhiteNoise serves it with a long-lived `Cache-Control` header

4. **A missing asset is a 404, not a 500**
   - Given a running production container
   - When a nonexistent static path is requested
   - Then the response is 404

5. **The suite stays green**
   - Given the full test suite
   - When it is run
   - Then it passes, including coverage of the static configuration

## Metadata
- **Complexity**: Medium
- **Labels**: gunicorn, WhiteNoise, Static Files, Production Hardening
- **Required Skills**: WSGI servers, Django static files, Docker
