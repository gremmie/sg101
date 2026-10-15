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

## Step 2 task 02 — the post box as ES modules, on news submit — DONE 2026-10-12

Task file: `.agents/tasks/2026-10-10-v3-forums-and-js/step02/task-02-post-box-modules.code-task.md`.
Branch `post-box-vanilla`, on `eb49bdf9`.

**What changed.**

- **Modules**, under `sg101/static/js/v3/`, no jQuery, every import ending in
  `;`:
  - `core/http.js`: `postForm` and `RequestError`. The design's `getJSON` is
    left until something calls it.
  - `post_box/editor.js`, `post_box.js` (entry), `preview.js`, `hot_link.js`
    and `uploads.js`.
  - Two small ones the design didn't name: `status.js` (show or hide a modal's
    callout) and `image_form.js` (the post-and-insert flow hot-link and upload
    share; `uploads.js` leaves it when multi-upload arrives).
- **`news/submit_news.html`** loads the entry module in place of
  `jquery.form.min.js` and `post_box.js`.
- **The shared templates are unchanged.** The modules hook onto the old ids
  and classes (`.v3-editor`, `#hot-link-form`, `#photo-status`…), so task 03
  has no leftover hooks to remove there.
- **Hot-link and upload insert at the caret**, on their own line.
- **One behaviour the design didn't name, Claude's call:** a textarea the
  member never focused reports its caret at 0 (a form re-shown with its
  text), so an image goes **at the end** there, as before (`trackCaret` in
  `editor.js`).
- **Preview's `alert()` is gone**; a failure shows in the panel.

**Brian decided 2026-10-12:**

1. **R10's server fix moved here from step 5.** `upload_ajax_v3` now puts
   every message in `error_msg`, as plain messages (not `as_text()` bullets),
   and its `form.save()` exception path logs and returns a generic sentence
   instead of `str(ex)`, mirroring `hotlink_image`. Without it `http.js` could
   only say "Bad Request". The old script reads `error_msg` too, so the other
   ten pages get the reasons now.
2. **CI's coverage runs with `--concurrency=greenlet,thread`** (`ci.yml`, with
   a comment).

**The coverage question, answered.** Measured locally (`coverage run
--source=core/tests,news/tests`, news browser tests):

- **Without the flag:** `core/tests/browser.py` 72%, missing 40–42 and 54–61,
  everything after the first Playwright call; `news/tests/test_browser.py`
  85%.
- **With `greenlet,thread`:** 95% and 100%. The two lines still missing (49,
  the preset-variable branch; 65, `self.fail`) genuinely don't run.
- **`thread` must stay listed:** with `greenlet` alone, `comments/views.py`
  under the browser tests read 29% against 37%, because the live server's
  thread went untraced.
- **CI's exact command** (coverage, `--concurrency=greenlet,thread`, under the
  gate) ran locally: 1,450 OK.

**Tests.** `news/tests/test_browser.py` now has 9 tests in two classes:

- `SubmitPostBoxTestCase`: the modal, bold, link (prompt answered), preview,
  preview's failure (session cookie cleared: the view's "only available to
  logged-in users" shows in the panel), hot-link at the caret, and hot-link
  into a never-focused box.
- `SubmitUploadTestCase`: local upload under a temporary `MEDIA_ROOT`; an
  upload at the caret, and a non-image whose reason shows.
- `user_photos/tests/test_upload_views.py` gained the disabled and non-image
  messages, and the 500 now asserts a generic message and a logged traceback.

**Written first, against the old script:** 5 of the 7 tests then written
passed, and both at-caret tests failed as they should (the image appended
after `second`). Two faults in my own tests surfaced on the way, both fixed:

- **The status callouts start out hidden, already holding "Success! …"**, so
  `to_contain_text('Success')` passed with nothing inserted. Every status
  assertion now also requires `to_be_visible()`.
- **The upload test's temporary `MEDIA_ROOT` lacked `user_photos/`**, so local
  upload raised `FileNotFoundError` (a 500). The class now creates it, as
  `user_photos/tests/test_storage.py` and `core/tests/images/test_real_images.py`
  do.

The three new view tests failed first on the old view, each for the reason
research topic 6 recorded.

**Mutations, each restored and confirmed identical with `cmp`:**

| mutation | caught by |
|---|---|
| `insertAtCursor` always appends | both at-caret tests |
| `X-Requested-With` not sent | 4 tests (hot-link and upload get 405) |
| `http.js` ignores `error_msg` | the non-image test (shows "Bad Request") |
| preview's failure sent to `alert()` | the preview-failure test |
| `upload_ajax_v3`'s form error back under `msg` | the view test and the browser test |
| never-focused check removed | **survived at first** (see below); then the never-focused test |

**The surviving mutation was a test that didn't reproduce the fault.** The
first version set the textarea's value from script, and Chromium then puts
the caret at the end, so "use the selection" and "append" agreed. Rewritten to
re-show the form from the server (submitted without a title through
`form.submit()`, which skips the browser's `required` check), where the caret
really is 0. A first version waited with `wait_for_load_state()`, which
returned on the old page's finished load. The Hot-link click then landed on
the page being navigated away from, so the new page had no active post box;
the mutation run showed the error "Cannot read properties of null". It now
waits inside `expect_navigation()`. **Passed 5 of 5 plain; failed 3 of 3
mutated, with the image at the top**, which is the fault itself.

**A look at the page** (a throwaway browser test, not committed; screenshots
in the session scratchpad): at 360 px and 1280 px, news submit loads the six
modules and **no `jquery.form.min.js`**, the console is empty, the desktop
layout is unchanged, and the preview modal opens at phone width.

**Suite and gate:** 1,450 OK each (1,440 + 2 view tests + 8 browser tests), as
separate runs.

**Two fixes to the shared modals from Brian's review** (`core/v3/post_box_modals.html`,
so every post box page gets them):

- **The hot-link field's placeholder is `https://`**, not `http://`.
- **The help's nested-list example now nests.** Python-Markdown nests a list
  item only when it is indented **4 spaces**. The example used 3, so it
  rendered as one flat list, on jaguar too. Measured with `site_markup`: 3
  spaces flat, 4 nested; 2-space bullets flat, 4-space nested. The example
  now uses 4 spaces and says "if you indent 4 spaces", and rendered from the
  template it nests. **Left alone, deliberately:** making 2- and 3-space
  nesting work would take a third-party extension, and since `Post.html` is
  rendered at save it would also need a data migration. Also left alone: the
  example's bulleted and numbered lists, pasted together, merge into one
  `<ul>`, because Python-Markdown doesn't start a new list on a change of type
  without `sane_lists`.

## Step 2 task 03 — every post box on the modules, the old script deleted — DONE 2026-10-14 (`0d7024fa`)

Task file: `.agents/tasks/2026-10-10-v3-forums-and-js/step02/task-03-post-box-rollout.code-task.md`.
Branch `post-box-vanilla`, on `03c770cd`; committed `0d7024fa`, after
`758b2747` (the separate dev settings change below).

**Re-measured first, and the lists match the task file:** `grep -rl
'js/v3/post_box.js' . --include='*.html'` named 10 templates (the task's 11
less news submit), and `jquery.form` named 14 (those 10 plus the four forum
templates).

**What changed.**

- **The ten pages** (`bio/edit_profile`, `contests/contest_detail`,
  `downloads/add`, `downloads/download_detail`, `gcalendar/event`,
  `messages/compose`, `messages/view_message`, `news/story`,
  `polls/poll_detail`, `potd/view`): the `jquery.form.min.js` and
  `js/v3/post_box.js` tags became the one entry `<script type="module">`, at
  the same place and indentation. Nothing else on them moved.
- **`sg101/static/js/v3/post_box.js` is deleted.** `static/js/jquery.form.min.js`
  stays (it's in the top-level `static/`, not `sg101/static/`).
- **The shared templates had no hooks used only by the old script**, as task
  02 recorded. **Brian chose to remove two pieces of dead markup**: the
  commented-out `tabs-panel` line in `core/v3/post_box.html`, and the empty
  `#photo-upload-progress` div in `core/v3/post_box_modals.html`.

**`#photo-upload-progress` isn't unreferenced, as I first claimed.** Brian
found it in `static/js/markitup/sets/markdown/set.js:129`, my search having
covered `sg101/static` only. markItUp uses the div as its switch: if it's
there, markItUp calls `ajaxForm` on `#photo-upload-form` and inserts into
`#id_body`. The removal still stands. markItUp is loaded (the `markitup`
bundle in `base.py`) only by the four forum templates, and by
`comments/markdown_preview.html` for its CSS. None of them includes the v3
modals; their upload form is `user_photos/image_forms.html`, which keeps its
div. On a v3 page the div could only have woken markItUp's handler.

**For step 8: the forum pages' jQuery Form isn't dead.** The task file's
"only `post_box.js` calls jQuery Form" was measured over `sg101/static/js`.
Across both static trees, the one non-minified caller left is markItUp's
`set.js` (`ajaxForm`), on the forum pages.

**Test.** `bio/tests/test_browser.py`, `EditProfilePostBoxTestCase`: with
both boxes holding `first\nsecond` and the caret after `first` in one box, a
hot-link from that box's button puts the image there, on its own line at the
caret, and leaves the other box unchanged. One test for the signature (the
second box) and one for `profile_text`. Hot-link only: the active post box is
chosen in the entry module before either form posts, and upload at the caret
is already covered on news submit.

- **Against the old script:** both failed at the at-caret assertion, with the
  image in the right box but appended (`first\nsecond\n![image](…)`).
- **After the switch:** both pass.
- **Mutation:** the entry module set `active` to the page's first
  `.v3-editor textarea` instead of the clicked one. The signature test failed
  (signature unchanged, the image in `profile_text`) and the `profile_text`
  test passed, which is right, since it can't tell the two apart. Restored,
  byte-identical (`shasum`, and an empty `git diff`).

**Production hashes the imports.** `collectstatic` under
`sg101.settings.production` with `SECRET_KEY=build-time-only`, as the
Dockerfile runs it, but with `STATIC_ROOT` overridden to a temporary directory
in the web container (production's `STATIC_ROOT` is inside the bind-mounted
tree). 1,127 manifest entries. Every import in the eight hashed modules names
a hashed file that exists, e.g. `post_box.0fd555f9fd06.js` imports
`./editor.909edb7e6c35.js`, `./hot_link.455fe229c2b3.js`,
`./preview.f39fddda5085.js` and `./uploads.c4e8cbd18d9b.js`, and
`image_form.js` and `preview.js` import `../core/http.f3b4cba2538b.js`. No
`js/v3/post_box.*.js` was collected.

**Suite and gate:** 1,452 OK each (1,450 + the 2 new tests), as separate
runs. `core/tests/test_static.py` passes, so no template names a missing
static file. `make test-browser`: 11 OK.

**A news story can't show the comment form any more** (Brian, during the
walk). `news/story.html` renders it, and loads the post box, only for
`story.version == 0` with `can_comment_on` (comments allowed, under 30 days
old); later stories comment in a forum topic. The dev database's newest
version-0 story is from 2015-11-27 (989 in all), so the branch is
unreachable. The switch there is kept, so no page names the deleted script.
**The walk uses POTD's comment form instead**, the same
`{% render_comment_form_v3 %}`.

**The manual walk (Brian, 2026-10-14)**, on the dev stack with
`USER_PHOTOS_LOCAL_UPLOAD=True`: news submit, profile edit (both boxes),
message compose and POTD's comment form, at phone and desktop widths. Toolbar,
preview, hot-link and upload work on each, and the console shows nothing new.

- **Two console messages on every modal are Foundation's, and pre-existing.**
  Chrome refuses Reveal's `aria-hidden="true"` on `<body>` as a modal opens
  (an error), and on `.reveal-overlay`, which holds the modal Reveal then
  focuses (a warning). Both are in the vendored `foundation.min.js`
  (`_makeOverlay`, and `open`'s `t("body")…attr("aria-hidden", …)`); the post
  box modules set neither `aria-hidden` nor focus. Left for the step that
  patches `foundation.min.js`.
- **Network, spot-checked on compose by a headless probe** at 375 and 1280
  px, logged in through a session made directly (so `last_login` was left
  alone) and deleted afterwards: all eight modules 200, no request for
  `jquery.form.min.js` or the old `v3/post_box.js`, no page errors. The only
  non-2xx is a 404 for a sidebar POTD thumbnail missing from dev's `media/`.

**Step 2 is complete.** Steps 1 and 2 merge to `main` and deploy together.

**Separate change, its own commit:** `sg101/settings/dev.py` reads
`USER_PHOTOS_LOCAL_UPLOAD` from the environment (default `False`;
production pins it `False`), and `.env.example` documents it. Before that it
was a constant, and `.env` couldn't turn it on.
