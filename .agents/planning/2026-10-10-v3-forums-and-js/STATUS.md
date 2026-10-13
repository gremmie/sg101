# Project Status — the V3 forums, the post box, and the site's JavaScript

**Last updated:** 2026-10-12
**Methodology:** Prompt-Driven Development (`/agent-sops:pdd`), then
`/agent-sops:code-assist` per task

The record of what each task did and measured. The plan and its checklist are
in `implementation/plan.md`; the decisions behind it are in `idea-honing.md`;
the artifacts are listed in `summary.md`.

**Two rules, carried over from the modernization project's `STATUS.md`, where
both were earned:**

1. **One claim, one home.** A decision lives in exactly one place and everything
   else points at it.
2. **A section is about one task, and it gets closed.** When work is committed,
   its heading names the commit.

## Step 1 task 01 — Playwright in the dev image — DONE 2026-10-12

Task file: `.agents/tasks/2026-10-10-v3-forums-and-js/step01/task-01-playwright-in-the-dev-image.code-task.md`.
Branch `post-box-vanilla`, cut from `main` at `2fbb8696`.

**What changed.** `playwright==1.63.0` in `requirements_dev.txt`, and in the
Dockerfile's `dev` target only, after its `pip install`:
`ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright` and `RUN playwright install
--with-deps --only-shell chromium`. **Brian chose the fixed path** over
Playwright's default (`/root/.cache/ms-playwright`), so the browser is found
whichever user the container runs as. The `dev` comment's "the three tools it
adds" became "the tools it adds". That line is in the comment block just above
`FROM prod AS dev`, the only line there that moved, and it is a comment.

**Costs, measured on the Mac (Docker Desktop, aarch64)** with `docker build
--no-cache --target <t> -t sg101-<t>:<before|after> .`, timed by wall clock;
size from `docker image ls` (on disk) and `docker image inspect --format
'{{.Size}}'` (content):

| image | before | after |
|---|---|---|
| `dev`, on disk | 2.21 GB | **3.35 GB** |
| `dev`, content | 522,914,685 B | **843,004,078 B** |
| `dev`, no-cache build | 31 s | **56 s** |
| `prod`, on disk | 2.21 GB | 2.21 GB |
| `prod`, content | 521,905,077 B | 521,904,846 B |
| `prod`, no-cache build | 31 s | 30 s |

`/ms-playwright` holds 269 MB (`chromium_headless_shell-1243`, `ffmpeg-1011`),
as research topic 3 measured in a container. One build each, so the times
carry a few seconds of noise. **Only aarch64 has been built**; CI's
`ubuntu-latest` is x86-64 and is the first build there.

**The prod image is unchanged in what it installs.** The two `prod` images
have identical `docker history` layer sizes and an identical `pip freeze`
(md5 `883fe398…`), `requirements.txt` is identical to `main`, and `python -c
"import playwright"` raises `ModuleNotFoundError`. **The 231-byte content
difference is the source copy:** `COPY . /app` carries the edited `Dockerfile`
and `requirements_dev.txt` (9,262 → 10,065 bytes together).

**Chromium launches.** A throwaway script (`sync_playwright()`, headless
launch, a `data:` URL with an inline script, a `pageerror` listener), not
committed:

- in `sg101-dev:after`: title set by the script, no page errors, Chromium
  `153.0.8010.12`;
- **under the bind mount**, after `docker compose build web` and `up -d
  --force-recreate web worker beat`: through `docker compose exec web` as
  root, with `/app` on Docker Desktop's `fakeowner` mount, and again as
  `-u sg101`;
- **mutation:** the same Dockerfile with the `playwright install` line removed
  (piped to `docker build -f -`, so the tree was not touched) fails it with
  `BrowserType.launch: Executable doesn't exist at
  /ms-playwright/chromium_headless_shell-1243/…`.

**Suite and gate:** 1,435 tests OK before (`docker compose exec web`), 1,435
OK after, and 1,435 OK under the deprecation gate as its own run. The only
`WARNING` lines are the suite's existing `email` log output, present before the
change too.

## Step 1 task 02 — the browser test base class and the upload modal test — DONE 2026-10-12

Task file: `.agents/tasks/2026-10-10-v3-forums-and-js/step01/task-02-browser-test-base-and-upload-modal-test.code-task.md`.
Branch `post-box-vanilla`, on `2de1ffc0`.

**What was added.** `core/tests/browser.py`: `BrowserTestCase(StaticLiveServerTestCase)`,
tagged `browser`. It sets `DJANGO_ALLOW_ASYNC_UNSAFE` in `setUpClass` and puts
back whatever was there before; it holds one Chromium per class and a fresh
context and page per test. `login(user)` copies a `Client.force_login` session
cookie (`sg101_sessionid`) into the context. A `pageerror` listener fails the
test in a cleanup, naming each error. The class-level teardown is done with
`addClassCleanup`, so a failure partway through `setUpClass` still closes what
was opened. `news/tests/test_browser.py`: logged in on `news-submit`, clicking
`a.editor-upload` makes `#upload-modal` visible. `make test-browser` runs only
the tag. No settings module changed.

**Written test first.** Against a stub base class whose `login` did nothing,
the test failed with `Page.click: Timeout 30000ms exceeded`, waiting for the
Upload button: the anonymous request had redirected to the login page. With
the base class it passed in 0.78 s.

**Mutations, each run and reverted (`git checkout` on the template; the base
class restored from a copy and confirmed identical with `cmp`):**

| mutation | result |
|---|---|
| `foundation.min.js` tag removed from `v3/base.html` | **2 failures**: `Locator expected to be visible`, and the collector's `$(...).foundation is not a function` (thrown by `sg101.js`) |
| an inline `<script>throw new Error(…)</script>` after `sg101.js` | **1 failure**, the collector's, naming the error; the modal opened |
| the `addClassCleanup(cls._restore_async_unsafe)` line removed | the env check below reads `after 'true'` |

**The override does not leak.** A throwaway script ran the class through
Django's test runner inside the `web` container, reading the variable before
and after: unset → unset (`None`), and preset to `'preset'` → `'preset'`.

**Counts (`make`, in the dev stack):** `make test-browser` 1 test; `make test
t="--exclude-tag browser"` 1,435; `make test` **1,436**; `make
deprecation-gate` 1,436 OK. Its one non-`email` warning line, `Empty
recipient_list in send_mail`, appeared in task 01's gate run too. `make help`
lists `test-browser` under Development.

**Not yet measured: CI.** The test needs `ajax.googleapis.com` until jQuery is
self-hosted; CI's duration before and after is read on the push.

## Step 2 task 01 — hashed module imports in production's static storage — DONE 2026-10-12

Task file: `.agents/tasks/2026-10-10-v3-forums-and-js/step02/task-01-hashed-module-imports.code-task.md`.
Branch `post-box-vanilla`, on `8110f467`.

**What changed.** `core/storage.py`: `ManifestStaticFilesStorage`, Django's
class with `support_js_module_import_aggregation = True`. It's a class
attribute that `HashedFilesMixin.__init__` reads, not a constructor argument,
so `STORAGES` `OPTIONS` can't set it; a subclass is the only way.
`production.py` names it. `core/tests/test_settings.py`'s
`test_static_files_are_served_from_a_manifest` now expects it.
`core/tests/test_storage.py` is new: 4 tests, run through `collectstatic`
itself with only the given tree collected into a temporary `STATIC_ROOT`.

**Found while exploring: Django rewrites an `import … from` or `export … from`
only when a semicolon ends it** (Django 5.2.17, `HashedFilesMixin`'s patterns
end `\s*;`). Measured through `collectstatic`:

| entry module | result |
|---|---|
| `import … from './c.js';`, `'../b.js';`, `export … from '../a.js';` | all three hashed, each naming a file that exists |
| `import { b } from '../b.js'` (no `;`), then other code | **left as `'../b.js'`; collectstatic succeeds.** Silent in production |
| the same, then `export { a } from '../a.js';` | the export's rewrite runs on across the line: `collectstatic` raises `ValueError: The file 'm/a.7fe5b7cbaa60.js' could not be found`, so the image build fails |

A first probe that called `post_process` directly showed the third row
writing `../a.7fe5b7cbaa60.7fe5b7cbaa60.js` silently. That was the probe
discarding the exceptions `post_process` yields, not what `collectstatic`
does. **Brian chose a standing real-tree test** over a semicolon lint or the
synthetic test alone: `test_the_site_modules_import_only_hashed_files`
collects `sg101/static/js/v3/` under the new storage. It fails if any relative
`from`/`import` specifier in a hashed module is unhashed or names a file that
wasn't written. Its specifier pattern is written independently of Django's,
so it finds the statements Django skips. **It has no imports to check until
step 2 task 02**; until then it asserts only that `js/v3/sg101.js` was
collected.

**Tests first.** With `STORAGE` pointed at Django's own class: the hashing
test failed (all three specifiers unhashed), the semicolon test found no
`missing` reason (nothing was rewritten to double-hash), and the production
test failed on the class name. The real-tree test passed (no imports yet).

**Mutations, each restored and confirmed identical with `cmp`:**

| mutation | result |
|---|---|
| `support_js_module_import_aggregation = False` | 2 failures: hashing test (unhashed list), and `ValueError not raised` in the build-fails test |
| `sg101/static/js/v3/zz_planted.js` with `import './sg101.js'` and no `;` | real-tree test fails: `('js/v3/zz_planted.408810aaea62.js', './sg101.js', 'unhashed')`; file deleted |
| the helper's `unhashed` branch removed | the missing-semicolon test fails (`[] != [… 'unhashed']`) |

**Production's own `collectstatic`:** `docker build --target prod` (the
Dockerfile runs it under `sg101.settings.production`) succeeded: `1120 static
files copied to '/app/static_root', 1120 post-processed`, and
`staticfiles.json` holds 1,120 entries. The image was removed afterwards.

**Suite and gate:** 1,440 OK each (1,436 + 4), the gate as its own run, no new
warnings.

**For task 02:** every `import`/`export … from` in the new modules must end in
a semicolon. The real-tree test will fail on any that doesn't.
