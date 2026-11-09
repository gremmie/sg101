# Project Status — the V3 forums, the post box, and the site's JavaScript

**Last updated:** 2026-11-09
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
  box modules set neither `aria-hidden` nor focus. **Brian put the fix in
  step 3** (`implementation/plan.md`, step 3 guidance), which already patches
  `foundation.min.js`.
- **Network, spot-checked on compose by a headless probe** at 375 and 1280
  px, logged in through a session made directly (so `last_login` was left
  alone) and deleted afterwards: all eight modules 200, no request for
  `jquery.form.min.js` or the old `v3/post_box.js`, no page errors. The only
  non-2xx is a 404 for a sidebar POTD thumbnail missing from dev's `media/`.

**Step 2 is complete. Steps 1 and 2 are deployed** (2026-10-14). `main`
merged into `post-box-vanilla` (`3244bed3`), CI green there, and `main`
fast-forwarded to it, CI green again. Brian deployed with `git pull` and
`make prod-up` (no migrations), and the live post box works.

**Separate change, its own commit:** `sg101/settings/dev.py` reads
`USER_PHOTOS_LOCAL_UPLOAD` from the environment (default `False`;
production pins it `False`), and `.env.example` documents it. Before that it
was a constant, and `.env` couldn't turn it on.

## Step 3 task 01 — jQuery 3.7.1 and jQuery UI 1.13.3, served from the site — DONE 2026-10-15 (`bea6525f`)

Task file: `.agents/tasks/2026-10-10-v3-forums-and-js/step03/task-01-self-hosted-jquery-3.code-task.md`.
Branch `jquery-3`, on `8f282a3c` (the step's task files); committed `bea6525f`.

**What changed.**

- **`sg101/static/js/vendor/`** (new): `jquery-3.7.1.min.js`, and
  `jquery-ui-1.13.3/` holding `jquery-ui.min.js`, the `redmond` theme's
  `jquery-ui.min.css` and the 13 images it names, all from code.jquery.com.
  The two `.js` files' SRI hashes both appear on releases.jquery.com
  (`sha256-/JqT3SQf…` and `sha256-sw0iNNXm…`). `README.md` lists each file's
  version, source and SHA-256 (16 rows, rechecked against the files), and the
  Foundation edit.
- **`v3/base.html`** loads jQuery from `{% static %}`. **`settings/base.py`**:
  both `jquery-ui` entries name the local files. The old design's `jquery`
  1.11.1 entry is unchanged.
- **`foundation.min.js`**: `(window).load(function` → `(window).on("load",function`,
  the one occurrence. **`comments.js`**: `.size()` → `.length`.
- The two browser-test docstrings that said the tests need Google's CDN are
  shortened to their first line.

**The vendored Foundation JavaScript is 6.2.0, not 6.3.1.** The design, the
research, the plan and both task files said 6.3.1. The file reports
`Foundation.version` `"6.2.0"`, was last changed 2016-03-03 ("Update to
Foundation 6.2", `4b6639d5`), and its SHA-256 (`a34cbbdb…53813`) equals
`foundation-sites@6.2.0`'s `dist/foundation.min.js` from jsDelivr. 6.2.1–6.2.4
don't match. Only the Sass is 6.3.1 (`sg101/package.json`). Research topic 8's
fixes still hold, since its probe ran against this file. Corrected in design
§4.3 and task 02's Background (whose 6.9.0 comparison needs the right base),
and recorded in the vendor README. **Then everywhere else, on Brian's call**
(2026-10-15): edited in place in the design (overview, R3, R7, both diagrams,
Appendix A and D), `summary.md`, `research/research-plan.md` and task 01's file.
The records (`rough-idea.md`, `idea-honing.md`, research topics 7 and 8) keep
their text with a dated correction beside it. Research topic 7's CSS comparison
is unaffected, because it compares Sass.

**Tests.** All browser tests, using `BrowserTestCase`, which also fails a test
on any uncaught page error.

| Test | Today's tree (2.2.4, UI 1.11.0) | After | Mutation, and what it showed |
|---|---|---|---|
| `news` `SubmitJQueryTestCase.test_page_runs_jquery_3_7_1` | **fails**, `'2.2.4' != '3.7.1'` | passes | (the red run) |
| `news` `SubmitJQueryTestCase.test_page_requests_nothing_from_googles_cdn` | **fails**, lists Google's 2.2.4 URL | passes | (the red run) |
| `news` `SubmitPostBoxTestCase.test_upload_button_opens_the_upload_modal` (step 1's) | passes | passes | Foundation patch reverted: modal not visible, and an uncaught page error |
| `bio` `EditProfileDatepickerTestCase` (new) | passes | passes | 1.11.0 still passes (research predicted it). A `beforeShow` that moves the widget to (0, 0): fails, top −743 against the field's 379 |
| `bio` `MemberSearchAutocompleteTestCase` (new) | passes | passes | `jquery-ui` JS back to Google's 1.11.0: fails, menu top 0 against 519.5, and `r.getClientRects is not a function`, research's fault exactly |
| `polls` `PollCommentTestCase` (new file) | — | passes | `.size()` put back: fails, no `1.`, and `$(...).size is not a function` |

Each mutated file was restored from a copy and `cmp` showed it byte-identical.
The placement tests assert the widget's top within 5 px of the field's bottom,
and left edges within 5 px.

**The comment test is on a poll, not a news story** as the task file said.
News stories take comments only at `version == 0`; current stories are
`NEWS_VERSION = 2` and discuss in a forum topic, so a new story renders no
comment form. `comments.js` also runs on downloads, POTD and contests. A
browser test replaced the task's manual comment on dev, so nothing was written
to the dev database.

**Old-design forum pages, on dev.** A headless probe logged in through a
session made directly and deleted afterwards (checked), and loaded `topic`,
`new_topic`, `new_post` and `edit_post`. Each ran jQuery 1.11.1 with jQuery UI
1.13.3, and **no page error** on any. The only non-2xx responses were dev
`media/` files (two avatars, one POTD thumbnail). The probe's first run named
Django's `ModelBackend` in the session, not the site's
`accounts.backends.CaseInsensitiveModelBackend`, so the three posting pages
redirected to login and weren't checked. Fixed and re-run; the figures above
are from that run.

**Production-style `collectstatic`**, under `sg101.settings.production` with
`STATIC_ROOT` overridden to a temporary directory in a throwaway container:
succeeds. All three vendored files and `foundation.min.js` get hashed names,
and all 13 image `url()`s in the hashed theme CSS are rewritten to hashed names
that exist.

**Suite and gate**, as separate runs: 1457 tests OK each. The two `celery`
`ERROR` log lines in both are tests that make SMTP refuse on purpose.

**Brian's manual check on dev (2026-10-15): looks good.** Two things it
turned up, neither from this change:

- **The home page slideshow is empty on dev.** `{% slideshow_images %}` reads
  `MEDIA_ROOT/slideshow/`, which dev's `media/` lacks (git-ignored; production's
  copy is only on leopard). Five numbered placeholders were generated into dev's
  `media/slideshow/`. Dev's cache is `LocMemCache`, per process, so clearing the
  `home_slideshow` fragment from `manage.py shell` does nothing; restarting
  `web` empties it.
- **Orbit (the phone-width banner) shows nothing if the page loads at desktop
  width and the window is then narrowed. Not a regression.** Measured headless,
  each way on jQuery 3.7.1 and with the request swapped for Google's 2.2.4:
  loaded at 375 px, both show the logo, advance to the second slide within
  6 s, and raise no error. Loaded at 1280 px and narrowed to 375, both leave
  `.orbit-container` at `height: 0px` and the slides at `max-height: 0px`,
  still rotating. The banner is `hide-for-medium`, so Orbit initialises hidden,
  measures 0, and doesn't re-measure. A phone loads at phone width, so visitors
  don't meet it. To check Orbit by hand, narrow the window *then* reload.
  Not fixed; it's Foundation 6.2.0's behaviour.
  **Correction (2026-11-04):** "visitors don't meet it" overlooks a phone
  turned from landscape (usually 640 px or wider, medium) to portrait. That is
  inferred, not seen. The fix is plan step 13.

**Not done here:** the manual walk of the menus, Orbit and Cycle (task 03),
and Reveal's `aria-hidden` (task 02).

## Step 3 task 02 — Reveal stops hiding the open modal from assistive technology — DONE 2026-10-16 (`1fdb2e58`)

Task file: `.agents/tasks/2026-10-10-v3-forums-and-js/step03/task-02-reveal-aria-hidden.code-task.md`.
Branch `jquery-3`, on `f8939e80`; committed `1fdb2e58`.

**The three measurements.**

1. **Foundation 6.3.0 already removed both settings, and 6.9.0 has neither.**
   `js/foundation.reveal.js` from jsDelivr for 6.2.0, 6.3.0, 6.3.1 and
   6.4–6.9: from 6.3.0 on, `_makeOverlay` creates the overlay with no
   `aria-hidden`, `open` doesn't touch `<body>`'s, and `close` leaves `<body>`
   alone. No version adds `aria-modal` or `inert`. 6.3.0's only addition was a
   shared focus trap (`Keyboard.trapFocus`). Our 6.2.0 already keeps Tab inside
   an open modal with its own `tab_forward`/`tab_backward`.
2. **What browsers do with `aria-hidden` on `<body>`.** The ARIA editor's
   draft (`w3c.github.io/aria/#aria-hidden`, read 2026-10-15): authors MUST NOT
   use it on `html` or `body`, and user agents MUST NOT expose the hidden state
   there. `aria-hidden="false"` is now a synonym of unset. Chrome refuses it,
   which is the error we saw. Firefox fixed it in Bugzilla 1880578 (Firefox
   139), and WebKit in bug 269523 (2024). **The Firefox and WebKit rows come from
   their bug trackers, not a measurement:** the installed Playwright has no
   `page.accessibility`, and only Chrome's tree is reachable, over CDP. So the
   setting does nothing on current browsers. On older ones it hides the whole
   page, the open modal included.
3. **The overlay doesn't need hiding.** It's an empty `div` holding only the
   modal, so hiding it can only hide the modal. Chrome refuses that too,
   because focus is inside. `inert` would be new behaviour, not a replacement.

**Measured in Chrome before the change** (dev, news submit, upload modal,
probe logged in through a session made and deleted for it): on open, `<body>`
is `aria-hidden="true"` and the modal's ancestors with `aria-hidden="true"`
are the overlay and `<body>`. Chrome's accessibility tree (CDP
`Accessibility.getFullAXTree`) shows both refused: the dialog not ignored,
and 1,255 of 1,332 nodes exposed, the page behind included. Both console
messages appear. After close, `<body>` is left with `aria-hidden="false"`.

**Brian chose option A** (2026-10-15): do what Foundation 6.3.0 did, no
`aria-modal` (B) and no `inert` (C), as the smallest hand edit that matches
upstream and meets the requirement.

**What changed.**

- **`foundation.min.js`**, three edits, each checked to occur once: the
  overlay's `.attr({tabindex:-1,"aria-hidden":!0})` → `.attr({tabindex:-1})`;
  `open`'s `<body>` `.attr("aria-hidden",…)` removed; `close`'s
  `t("body").attr({"aria-hidden":!1,tabindex:""})` → `.attr({tabindex:""})`.
  `tabindex` is left as 6.2.0 has it.
- **Vendor README** records them next to task 01's patch.
- **Two browser tests** in `news` `SubmitPostBoxTestCase`:
  `test_an_open_modal_is_not_hidden_from_assistive_technology` (no ancestor of
  the open upload modal has `aria-hidden="true"`), and
  `test_closing_a_modal_leaves_body_as_it_was` (`<body>`'s `aria-hidden` after
  close equals before). The second closes with the modal's close button.
  Escape pressed straight after opening arrives before Reveal binds its key
  handler (in a `setTimeout`), so the modal stays open.

**Tests, red then green, and the mutations.** Before the change: the first
failed with `['DIV', 'BODY']`, the second with `'false' != None`. After it,
both pass. Each of Reveal's settings put back alone, restored from a copy and
`cmp`-checked after each:

| Put back | Fails |
|---|---|
| `<body>` `aria-hidden` on open | both: `['BODY']`, and `'true' != None` (nothing resets it on close any more) |
| the overlay's `aria-hidden` | the first: `['DIV']` |
| `<body>` `aria-hidden="false"` on close | the second: `'false' != None` |

**A console assertion was written and removed, because it couldn't fail.** The
first test also asserted that no console message mentions `aria-hidden`. With
the two assertions swapped and the `<body>` setting put back, it passed. The
DOM assertion caught the mutation. Measured on the unpatched file: with the
modal open 2.5 s, Chrome logs **nothing**; both messages appear only once
something requests the accessibility tree (the probe's CDP call; in a person's
browser, DevTools or assistive technology). A headless test never does, so the
test checks the attributes, and a comment says why. **The message check is
the probe's instead.** After the change, with the tree requested, no console
message at all, `<body>` has no `aria-hidden` before, during or after, no
ancestor of the open modal is hidden, and the dialog is exposed.

**Suite and gate**, as separate runs, before the follow-up below: 1459 tests OK each (18 browser tests).

**Found, not fixed: the upload dialog's accessible name is `""`**, a
Font Awesome glyph. Reveal sets `aria-labelledby` to its opening link, whose
only content is the icon. The other modals weren't checked. Not in this
task's scope.

**Then a third `aria-hidden`, found by Brian on dev (2026-10-16): closing a
modal with the mouse.** Chrome's console: `Blocked aria-hidden on an element
because its descendant retained focus`, focus on `<button.button>`, ancestor
`div.small.reveal#preview-modal`. `close` ends by marking the modal itself
`aria-hidden="true"`. 6.2.0 moves focus back to the opening link only for
Escape and Enter. A mouse click leaves it on the button inside. Measured
with the probe (preview modal, accessibility tree requested), identical on
task 01's committed file and on task 02's change, so **it predates this task**:

| Closed by | Focus after | Chrome |
|---|---|---|
| mouse click on "Close" | lost to `<body>` | the warning |
| Enter on "Close" | the Preview link | nothing |
| Escape | the Preview link | nothing |

Upstream, 6.4.0 added `this.$anchor.focus()` at the end of `close`, and 6.5.0
made it `this.$activeAnchor`, recorded in `open` as the focused opening link,
else all of them. **Brian chose the 6.5.0 port** (option 1 of three; the
others were 6.4.0's version, which on profile edit's two shared-modal post
boxes ends on the wrong one, and leaving it). Two more edits to
`foundation.min.js`: `open` records `$activeAnchor` first; `close` ends with
`this.$activeAnchor.focus()`. With an overlay, `close`'s hide finishes after
it returns, so focus moves before `aria-hidden` is set. README records both.

**Test:** `bio` `EditProfilePostBoxTestCase.test_closing_a_modal_by_mouse_returns_focus_to_the_link_that_opened_it`:
open the preview from the **first** post box, close it with a mouse click on
"Close", and that box's Preview link is focused. Red before (`Locator
expected to be focused`), green after. **The first box, not the second as
first written:** `$anchor` holds both links in page order, and focusing each
in turn ends on the second. So the second box's link would pass with 6.4.0's
version too. Mutations, each restored and `cmp`-checked: the `focus()` call
removed, fails; `this.$anchor.focus()` (6.4.0), fails.

**Probe after the change:** all three close paths leave focus on the Preview
link with no message, and each of the four post box modals (hot-link, upload,
preview, help) closed with its × returns focus to its own link with no message.

Suite and gate after: 1460 OK each (19 browser tests).

**Left for task 03:** every post box modal opened and closed by hand with the
console open. The fix is in Reveal itself, so it reaches every modal.

## Step 3 task 03 — the jQuery 3 walk, two more Foundation fixes, the menu icon a button — DONE 2026-10-17

Task file: `.agents/tasks/2026-10-10-v3-forums-and-js/step03/task-03-jquery-3-walk-and-ship.code-task.md`.
Branch `jquery-3`, on `89239ee7`.

**The walk, by a headless probe** on the dev stack at 375 × 812 and 1280 ×
900, each width loaded at that width. It logged in as a fixed user (pk 2)
through a session made directly and deleted afterwards (`last_login`
unchanged, checked), and hid the dev debug toolbar, whose `#djDebugRoot`
sits over the phone menu and takes its clicks. A snapshot was taken first
(`sg101-20261017-144908-before-jquery3-walk.dump`). The comments it posted
were deleted at the end, and a count afterwards found none.

| Checked | Result |
|---|---|
| `jQuery.fn.jquery`, and requests to `googleapis.com` | `3.7.1`, none, at both widths |
| Cycle, home page | advances (placeholder 4 → 5), both widths |
| Orbit, loaded at 375 | 94.7 px high, rotates on its own, next button works |
| Dropdowns, 1280 | Forums opens on hover and closes on leave; Site → Polls navigates |
| Drilldown, 375 | the icon opens the menu; Surf Music, Back, then Site → Polls navigate. **A page error on the icon tap**, below |
| Comment on a download (985) and on the POTD | posted and numbered, both widths. Dev has no open poll; `PollCommentTestCase` covers polls |
| Post box modals: hot-link, upload, preview, help, closed with ×; preview also with its Close button and Escape; news submit, and both boxes of profile edit | with Chrome's accessibility tree requested (CDP), no ancestor of an open modal `aria-hidden`, `<body>`'s `aria-hidden` unchanged after close, no console message. **Escape on profile edit's first box returned focus to the second box's link**, below |

The only console errors were 404s for files dev's `media/` lacks (the probe
reported every other 4xx response separately, and there were none). The
probe's `#medium-menu` visibility check read false at both widths because
that box is 0 px high (its children float); the links in it are visible.

**1. The phone menu icon raised `Syntax error, unrecognized expression: #` on
every tap, on jQuery 3 only.** Swapping in Google's 2.2.4 removed it. The
icon was `<span class="menu-icon dark" data-toggle>`, the markup 6.2.0's docs
show, and 6.2.0's `[data-toggle]` click handler built `"#" + ""`. jQuery 2's
quick-ID regex takes `#` as an empty ID (`#([\w-]*)`), jQuery 3's needs a
character (`#([\w-]+)`), so it goes to the selector engine, which throws. The
menu still opened, because ResponsiveToggle binds the icon itself. Foundation
6.3.0 added the guard. The file's eleven other `"#"+…` selectors are in
plugins no template uses (accordion, tabs, slider, sticky, Abide's
`equalto`, `data-toggle-focus`, tab bar).

**2. Task 02's focus port was incomplete.** 6.2.0's three keyboard handlers
(Escape on the window, Escape on the modal, Enter on a `[data-close]` button,
from a `setTimeout(…, 1)`) each focus `$anchor` after `close` has focused
`$activeAnchor`, so on profile edit focus ends on the last box's link. A
focus trail measured it on the unpatched file: Enter, box 1 then box 2 15 ms
later; Escape, box 1 then box 2 in the same millisecond. 6.4.0 had removed
all three when it put the focus call into `close`; task 02 ported only that
half. News submit, with one box, never showed it.

**Brian chose (2026-10-17): both upstream ports, and the template change as
well**, then also the icon as a `<button>`, which it should have been: a
`<span>` takes no keyboard focus, so a keyboard user at phone width couldn't
open the menu at all.

**What changed.**

- **`foundation.min.js`**, four edits, each checked for its occurrence count
  (1, 2, 1): the `[data-toggle]` guard; the `$anchor.focus()` dropped from
  both Escape handlers; the Enter-on-close `setTimeout` branch → `||`. 6.4.0
  deleted the modal's whole keydown handler, which 6.3.0's
  `Keyboard.trapFocus` had replaced; 6.2.0 has no `trapFocus`, and that
  handler holds its Tab trap, so only the focus moves went. Vendor README
  records them.
- **`v3/base.html`**: `<button class="menu-icon dark" type="button"
  data-toggle="medium-menu" aria-label="Menu">`. The value is what
  Foundation 6.9.0's docs ask for, and 6.9.0's ResponsiveToggle accepts it
  or empty. With it, the triggers handler finds `#medium-menu`, which has no
  `toggle.zf.trigger` handler, and does nothing. **Unchanged look, measured:**
  the same box (20 × 16 at 8, 271), the same computed padding, border,
  background and display (Foundation's global `button` reset is in the built
  CSS), and the menu bar's screenshots are byte-identical. No Sass changed.

**Tests**, red before and green after:

| Test | Before |
|---|---|
| `core` `PhoneMenuTestCase.test_tapping_the_menu_icon_opens_the_menu` (new file) | fails: the `#` page error |
| `…test_an_empty_data_toggle_raises_no_error` (clicks an injected bare `data-toggle`) | added once the template named the menu, so the guard has its own test |
| `…test_the_menu_icon_opens_the_menu_from_the_keyboard` | fails: the span isn't focusable |
| `bio` `EditProfilePostBoxTestCase.test_closing_a_modal_with_escape_…` | fails: focus on box 2 |
| `…test_escape_with_focus_outside_the_modal_…` | (written for the mutation below) |
| `…test_closing_a_modal_with_enter_…` | **passed at first, and couldn't fail**: `to_be_focused` checked before 6.2.0's 1 ms timer moved focus. Now waits for a timer queued after it; fails |

Mutations, each alone, restored from a copy and `cmp`-checked:

| Put back | Fails |
|---|---|
| no `[data-toggle]` guard | the empty `data-toggle` test (`#` page error) |
| `$anchor.focus()` in the modal's Escape handler | the Escape test |
| `$anchor.focus()` in the window's Escape handler | **nothing at first**: with focus inside, the modal's handler closes first, and `close` unbinds the window's before the key bubbles to it. The focus-outside test, added for it, fails |
| the Enter `setTimeout` | the Enter test |
| the icon a `<span>` | the keyboard test |
| bare `data-toggle` in the template | **nothing, and by design**: with the guard, bare and named behave the same |

**The probe again after the change:** every row passes but the 404s and the
0-height box above, and Escape on profile edit's first box returns focus to
its own link.

**Suite and gate**, as separate runs: 1466 tests OK each. `make test-browser`:
25 OK.

**Brian's hand check on dev (2026-10-17): works** — at phone width, Tab to
the menu icon and Enter opens the menu; on profile edit, Escape on the first
box's preview returns focus to its own link.

**Step 3 is complete and deployed** (2026-10-17). `main` merged into
`jquery-3` (`609896c6`), CI green there, and `main` fast-forwarded to it, CI
green again. Brian deployed with `git pull` and `make prod-up` (no
migrations), and the live menu and post box modals work.

- **Console errors on Brian's first live load, gone after a hard refresh.**
  The text wasn't kept. Measured afterwards: the HTML is `cf-cache-status:
  DYNAMIC` with no `Cache-Control`, `Last-Modified` or `ETag`, every script
  and stylesheet it names is content-hashed and 200, and the live
  `foundation.min.f1df7c78409f.js` is the committed file (its hash, and it
  holds the `[data-toggle]` guard). So a fresh load can't pair new HTML with
  old assets. Most likely a page held from before the deploy (an open tab, or
  the back/forward cache). Not reproduced.

## Step 4 task 01 — the smiley picker modal and its toolbar button — DONE 2026-10-17

Task file: `.agents/tasks/2026-10-10-v3-forums-and-js/step04/task-01-smiley-picker-modal.code-task.md`.
Branch `smileys`, on `cea6761d` (the step's task files).

**Brian's decisions (2026-10-17):** render the picker into the page rather
than fetch it on open (the task file's Background holds the measurements);
**the icon is ☺** (U+263A with U+FE0E, candidate B of three screenshotted at
375 px: the site's `smile.gif`, ☺, Foundation's `fi-like`); and test the two
shared templates directly, plus one page in a browser, rather than every page
that includes the modals.

**What changed.**

- **`{% smiley_picker %}`** in `smiley/templatetags/smiley_tags.py`, beside
  `smiley_farm`: `get_smilies()` then `get_smilies(extra=True)`, into
  `smiley/smiley_picker.html`. Each smiley is `<button type="button"
  data-code>` around `<img loading="lazy" alt="code" title="title code">`,
  the code escaped by autoescaping.
- **`#smiley-modal`** in `post_box_modals.html` (which now loads
  `smiley_tags`), built like the help modal: `small reveal modal-scrollable`,
  ×, and a **Done** button. Done has no `aria-label`, so its name is its text.
- **The toolbar button**, before hot-link: `<a class="editor-smiley"
  data-open="smiley-modal" aria-label="Smileys">` around `<span
  class="size-21">☺︎</span>`. Shown on small screens. No Sass changed.

**Tests**, all red first (the tag didn't exist; no button; no modal):

| Test | Asserts |
|---|---|
| `smiley` `SmileyPickerTestCase` (new file; the app had no tests) | the exact button order is the main set then the extras; one button per smiley; every image lazy with alt text; a code `:"<&:`, created for the test since no real code holds those characters, renders `data-code=":&quot;&lt;&amp;:"` |
| `core` `PostBoxTestCase.test_toolbar_has_a_smiley_button_shown_on_small_screens` | opens `smiley-modal`, named "Smileys", no `hide-for-small-only` |
| `core` `PostBoxModalsTestCase` (new) | the include holds `#smiley-modal` with the picker and a Done button that closes |
| `news` `SubmitSmileyPickerTestCase` (browser) | the button opens the modal with every smiley; Done closes it |

The smiley tests clear the cache in `setUp`: `get_smilies` caches for an hour
and the test `LocMemCache` outlives a test. The first core test class was
written under the name of an existing `PostBoxTestCase` further down the same
file, which shadowed it, so its tests never ran; caught by the run count, and
merged into the existing class.

**The order test first classified codes as main or extra, and failed on real
data: `:lol:` is two rows**, main "LOL" (pk 13) and extra "Laughing" (pk 30),
in the fixture and on dev. It now compares the whole sequence. Below for what
the duplicate does.

Mutations, each alone, restored from a copy and `cmp`-checked; all ten caught:

| Mutation | Fails |
|---|---|
| extras first | order |
| extras dropped | order, one-button, lazy, browser |
| `{{ s.code\|safe }}` | escaping |
| no `loading="lazy"` | lazy |
| no `alt` | lazy |
| button `hide-for-small-only` | toolbar |
| button without `data-open` | toolbar, browser |
| button without `aria-label` | toolbar |
| no `{% smiley_picker %}` in the modal | modal include, browser |
| Done relabelled | modal include, browser |

**On dev, by a headless probe** (session made and deleted, toolbar hidden as
in step 3 task 03): at 375 and 1280, **0 smiley image requests before the
modal opens and 85 after**, no page errors. The toolbar's six buttons fit at
375. At phone width Reveal shows a `small` modal full-screen. A few blank
cells in the screenshots aren't missing files (none is, checked against
`MEDIA_ROOT`); probably animated GIFs on a blank frame, not confirmed.

**The duplicate `:lol:`, fixed in the data by Brian (2026-10-17).**
`get_smiley_regexes` builds one regex per row and the first match wins, so
`:lol:` rendered as "Laughing" (`icon_lol.gif`), measured through
`site_markup` on dev, and the main set's "LOL" image was never shown. Brian
changed Laughing's code to `:laugh:` in the admin on dev and production.
Posts saved before keep the HTML they were rendered with. The `smilies.json`
fixture is changed to match.

**Then: nothing cleared the smiley caches on an admin edit**, so production
kept the old regexes in Redis for up to an hour. Brian asked for it here.
`smiley/models.py` lists the manager's five keys in `CACHE_KEYS`
(`smiley_map`, `smileys`, `smileys_extra`, `smiley_regexes_rel`,
`smiley_regexes_abs`; nothing else holds smiley data past one call, since
`SiteMarkup` and `SmilifyHtml` are built per use), and `post_save` and
`post_delete` receivers delete them. The admin's bulk delete still sends
`post_delete` per row. `smiley` `SmileyCacheTestCase` (new): one test per
cached view, each caching it, editing a smiley and seeing the edit, plus a
delete. All six red first; **the delete test passed at first and couldn't
fail**: `delete()` sets `pk` to `None`, so it checked `None` was absent. It
keeps the pk first now. Mutations: each key dropped from the list, each
receiver removed; all seven caught.

**Brian's review of the look (2026-10-17):** a "More smileys" heading before
the extras (of a rule or a heading, mocked up at both widths), space above
Done, and padding round each smiley. The tag now passes `main` and `extra`
separately. Sass in `_sg101.scss`: `.smiley-picker` (1 rem below, buttons
0.25 rem × 0.5 rem padding and `cursor: pointer`, since Foundation's button
reset leaves the arrow) and `.smiley-picker-heading`. **Then hover and pressed
states**, Brian's request: Foundation's global reset strips a bare `<button>`
of every visual cue, so a click showed nothing. `:hover` is `$light-gray`
(#e6e6e6), `:active` `$medium-gray` (#cacaca); screenshotted at rest, hovered,
pressed and keyboard-focused (Chrome's focus ring, `outline: auto`; Foundation
removes the outline only after mouse input). **A rebuild of the
unchanged Sass reproduced the committed `main.min.css` byte for byte first;**
after each change the built file differs from the committed one only by the new `.smiley-picker` rules.
Test: `test_the_extras_are_headed_more_smileys`, red first; mutations
(heading removed, heading above the main set) both caught. The later
screenshots show images in the cells that were blank before, so those were
animated GIFs on a blank frame.

**Suite and gate**, as separate runs: 1480 tests OK each.

## Step 4 task 02 — clicking a smiley inserts it; the picker non-modal and draggable — DONE 2026-10-18

Task file: `.agents/tasks/2026-10-10-v3-forums-and-js/step04/task-02-smileys-module.code-task.md`.
Branch `smileys`, on `3d737781`.

**What changed.**

- **`editor.js`**: `insertAtCursor(…, { padded })`, beside `ownLine`. A space
  goes before the code unless it starts the text or follows whitespace, and
  after unless it ends the text or whitespace follows; the caret ends after
  the trailing space, so the next smiley lands after it.
- **`post_box/smileys.js`** (new): a click on a `[data-code]` button inserts
  that code, padded, into the active post box. Focus stays on the picker.
  Dragging by the title (`.smiley-modal-title`) uses pointer events to set the
  modal's `top` and `left`, only at Foundation's medium breakpoint and up
  (`matchMedia('(min-width: 40em)')`, checked as each drag starts). The title
  can't leave the window vertically, and at least 100 px of it stays on screen
  across; its edges are measured as the drag starts, since it sits inside the
  modal's padding (the first version clamped the modal and left 68 px of the
  title, which the test caught).
- **`post_box.js`**: wires `initSmileys`, and focusing a textarea makes it the
  active box. Every modal sees that; only the overlay-less picker can be open
  while it happens.
- **`post_box_modals.html`**: `data-overlay="false"
  data-close-on-click="false"` on `#smiley-modal`, and the title's class. No
  change to `foundation.min.js` (measured before the task, recorded in its
  file).
- **Sass**: `.smiley-modal-title` at medium and up: `cursor: move`,
  `touch-action: none`, `user-select: none` (a drag doesn't select the title's
  text). The rebuilt CSS differs from the committed one by that rule only.

**Tests**, red first except the render test:

| Test | Asserts |
|---|---|
| `core` `SmileyPaddingTestCase` (new) | the strings the browser tests expect render one image per code through `site_markup`, including `ab :-) :-) cd`; `ab:-)cd` stays text. It checks the renderer against the picker's output, so it passed before the picker existed |
| `news` `SubmitSmileyPickerTestCase` (6 cases, 7 new tests) | mid-word, end, start, between spaces and empty text, exact results; two different smileys and the same one twice, each spaced once; the picker stays open after a click; no overlay, and a click in the post focuses it with the picker open; dragging the title moves the modal by the drag at 1280; dragged far up-left and far down-right, the title stays on screen; at 375 a drag moves nothing |
| `bio` `EditProfilePostBoxTestCase.test_smileys_go_into_the_box_last_clicked_into` | picker opened from the first box, caret placed in the second, a smiley goes into the second only |

Mutations, each alone, restored from a copy and `cmp`-checked:

| Mutation | Fails |
|---|---|
| picker inserts unpadded | padding cases, two in a row, the profile edit test |
| no space before | the same |
| no space after | padding cases, two in a row |
| drag handler not installed | drag |
| drag on phones too | the phone test |
| drag unclamped | off-screen |
| focus not tracked | the profile edit test |
| overlay back | post usable, drag (the overlay takes the pointer) |
| `data-close-on-click` removed | post usable |
| the picker closes after a smiley | stays open, padding cases, two in a row |
| the renderer's lookbehind removed | **nothing at first**: two *different* codes are each matched by their own regex, so the lookbehind only matters for the same code twice, whose first match takes the shared space. `ab :-) :-) cd` added to the render test (and a same-code browser test beside it); then it fails |

**Accepted, not fixed:** Reveal keeps Tab inside an open modal, so a
keyboard user can't Tab from the picker into the post; Escape closes it and
returns focus to the button. A window resize re-centres a dragged picker
(recorded in the task file).

**Then a title bar, Brian's review (2026-10-18).** He asked for something on
the title that says it drags. Mocked up at 1280: a grey band with a grip, the
site's primary blue, a dotted texture; then blue with a grip in 70% white or
light blue (#8fc3e6). **His choice: blue, grip in 70% white.** The title is
now the modal's first child (`div.smiley-modal-title`, out of the Foundation
row) spanning the modal's padding, `$primary-color` behind white text at
`$lead-font-size`, with the × inside it in white. It is `position: sticky`:
the picker scrolls when taller than its 80% `max-height`, which would have
carried the drag handle and the × out of reach. The grip
(`span.smiley-modal-grip`, two columns of three CSS-drawn dots, not a glyph)
shows only at medium and up, where dragging works.

The × on the handle needed one code change, test first: the drag handler
captured the pointer on any press, so the click never reached the ×
(`test_the_close_button_in_the_title_bar_closes_the_picker` failed: "expected
to be hidden"). Presses that start on a button are now left alone.

New tests: the × closes the picker; the grip is visible at 1280 and hidden at
375 (added to the drag and phone tests); the title stays at the modal's top
after the picker scrolls. That one first failed for a reason of its own: the
test server serves no media, so the picker held no image heights and never
overflowed at 600 px; it runs at 300 px. Mutations, built CSS or module
edited, restored and `cmp`-checked: not sticky, fails the scroll test; button
presses start drags, fails the × test; grip hidden everywhere, fails the drag
test. On dev with images loaded: screenshots at 1280 × 900, 375 × 812, and
1280 × 500 scrolled 200 px with the bar still on top; no page errors.

**Suite and gate**, as separate runs: 1493 tests OK each.

## Step 4 task 03 — the smiley walk, the download page's doubled modals — DONE 2026-10-19

Task file: `.agents/tasks/2026-10-10-v3-forums-and-js/step04/task-03-smileys-walk-and-ship.code-task.md`.
Branch `smileys`, on `0c95789e`.

**The walk, by a headless probe** on the dev stack at 375 × 812 and 1280 ×
900, logged in as pk 2 through a session made directly and deleted after
(`last_login` unchanged, checked), with the dev debug toolbar hidden, as in
step 3 task 03. A snapshot was taken first
(`sg101-20261019-190742-before-smileys-walk.dump`). Nothing was posted; the
message it viewed was already read. Eight pages, every one that includes the
post box modals: news submit, profile edit (both boxes), message compose,
message view, a download's comment form (985), calendar add, downloads add.

| Checked | Result |
|---|---|
| **The demo**, news submit at 1280: smileys at the start, after "up", at the end, then preview | `:argh: Surf is up :-( and the reverb is wet :no:`; the preview holds three smiley images |
| Toolbar on one row | 6 buttons at 375, the last ending at x 323; 13 at 1280 |
| Smiley image requests | 0 before the picker opens, 85 after, every page, both widths |
| Done reachable, and closes | every page and box, both widths; at 375 the picker is full-screen and scrolls (941 px of content in 812) |
| A smiley goes into the box it was opened from | every page; profile edit's two boxes each separately |
| At 1280: drag the picker aside, click into line two of the post, insert | the post takes focus with the picker open, and the smiley lands in line two |
| Page errors, console errors | none but 404s for files dev's `media/` lacks (a POTD thumbnail, an avatar) |

**Lazy loading outside Chromium, by Brian (2026-10-19):** in Firefox and
Safari, no smiley image is requested until the picker opens.

**Against the old forums' "More Smileys" window** (`core/comment_dialogs.html`,
a jQuery UI dialog, opened on a new-post page): that holds only the extra set
in a narrow box; the picker holds both sets. Both drag and stay open while
smileys go in.

**Seen, and left as task 02 designed it:** the drag keeps 100 px of the title
bar on screen, so a picker dragged far down or right can put Done, or the ×,
outside the window. Dragging the bar back brings them in. The probe met it at
first by dragging 500 px.

**The download page held every post box modal twice**, the picker among them:
`download_detail.html` included `post_box_modals.html` beside a comment form
that includes it too (both since 2016), so each modal id appeared twice. The
picker still worked there (the probe inserted at both widths); the others went
unchecked. **Brian chose to fix it here (2026-10-19):** the page's own include
is gone, which leaves the modals to signed-in members, as on the other four
pages with a comment form. `downloads` `DownloadBrowseTests.test_details_has_one_of_each_post_box_modal`
failed first, 2 of each of the five modals, and passes after. The probe again
on that page: one picker, every check passes at both widths.

**Suite and gate**, as separate runs: 1494 tests OK each. `make test-browser`: 37 OK.

**Step 4 is complete and deployed** (2026-10-19). Committed `17974260`
(the fix) and `03ec9cca` (this record); `main` merged into `smileys`
(`0fdcd154`), CI green there, and `main` fast-forwarded to it, CI green
again. Brian deployed with `git pull` and `make prod-up` (no migrations, no
CSS rebuild). Measured on leopard afterwards: the checkout on `0fdcd154`,
`web` and `worker` restarted and healthy, and the running image holds
`smileys.js`, the picker in `post_box_modals.html`, and no modals include in
`download_detail.html`. **Brian's spot check on the live site:** smileys
insert, and the preview shows them as images. #9 closed, naming `0fdcd154`;
branch `smileys` deleted.

## Step 5 task 01 — the over-quota test, three quota-counter leaks, and HEIC measured — DONE 2026-10-29

Task file: `.agents/tasks/2026-10-10-v3-forums-and-js/step05/task-01-upload-error-paths-and-heic.code-task.md`.
Branch `multi-upload`, with `main` merged in.

**The over-quota test.** `UploadAjaxV3Tests.test_over_quota_says_why`
(`user_photos/tests/test_upload_views.py`) posts a real JPEG through the
real `UploadForm` and the real rate limit in the test redis, with
`USER_PHOTOS_RATE_LIMIT=(0, 60)`, and expects a 400 whose payload is
exactly `{'url': '', 'error_msg': "You've exceeded your upload quota.
Please try again later."}`. It passed on first run, since step 2 already
fixed the view, so it was mutation-verified: `upload_ajax_v3` changed to
skip `__all__` when flattening `form.errors` fails this test alone
(`error_msg` `''`); `test_a_file_that_is_not_an_image_says_why` stays
green, so it does not cover this path. The view was restored byte-identical
(SHA-1 checked). A first attempt at the mutation did not apply (the same
two lines are in the hot-link view, line 249) and no result was taken from
that run.

**The quota counter leaked, and now does not.** `UploadForm.clean()` runs
the rate limit even when the file is invalid, so the not-an-image test was
already incrementing `user_photos:counts:uploader` in the test redis (db 14)
for a day: one run of the class left it at 1, TTL 86400. The class's
`setUp` now deletes that key and deletes it again on cleanup, as
`core/tests/test_redis_ttls.py` does; after a run, none is left.

**Two more leaks, older, fixed the same way.** After a full suite run db
14 held `user_photos:counts:pjmoto` at 6 (`SubmitUploadTestCase`,
`news/tests/test_browser.py`, which uploads for real) and
`user_photos:counts:test_user` at 1 (`HotlinkImageTestCase`,
`user_photos/tests/test_views.py`), each for a day. The `pjmoto` one
mattered to task 03: its browser tests will upload up to ten files a run
under a limit of 50 a day, so reruns would have failed as if the upload
were broken. Brian asked for both fixed, place and time his choice of
mine; each class's `setUp` now deletes its user's key and deletes it again
on cleanup. Both classes increment the counter after `setUp`, so an empty
db 14 after running them shows the cleanup at work: it was empty.

**HEIC, at the server.** Sample: an 800 × 600 JPEG from
`core/tests/images/imagemakers.py`, converted with `sips -s format heic`
on macOS 26.7 (176,534 bytes, `ftyp` brand `heic`, HEVC Main Still). Not a
photo from a phone: no depth map, no image sequence. Posted to
`upload_ajax_v3` in the dev `web` container through `RequestFactory`, as
an unsaved user (no session, no `last_login`), with
`USER_PHOTOS_LOCAL_UPLOAD=True` forced; the probe's quota key was deleted
after.

| Sent as | Status | `error_msg` |
|---|---|---|
| `IMG_0001.HEIC`, `image/heic` | 400 | Upload a valid image. The file you uploaded was either not an image or a corrupted image. |
| `IMG_0001.HEIC`, `application/octet-stream` | 400 | the same |
| control: the source JPEG, same form | valid | — |

Pillow 12.3.0, `pillow_heif` not installed. Nothing names HEIC, so a member
is told their photo is not an image or is corrupted.

**HEIC, in the browser, by Brian (2026-10-29)** on macOS, a local page with
two file inputs, picking the same sample:

| | A: no `accept` (the post box today) | B: `accept="image/jpeg,image/png,image/gif,image/webp"` |
|---|---|---|
| Chrome | `sample.heic`, `image/heic`, 176,534 bytes | the file cannot be selected |
| Safari | `sample.heic`, `image/heic`, 176,534 bytes | selectable; arrives as `samplesyj4tn.jpg`, `image/jpeg`, 219,587 bytes |

So with `accept` listing JPEG and not HEIC, **Safari on macOS converts the
HEIC to JPEG itself**; Chrome greys it out and says nothing. Unmeasured:
iOS (task 04's phone check), Firefox, and whether dropping a file on the
input in Chrome gets past `accept`. An explicit list also stops other
formats Pillow reads today (BMP, TIFF) from being picked.

**Options, for Brian:**

1. **Leave as is.** A HEIC is rejected as "not an image or corrupted".
2. **A clearer server message.** Recognise a HEIC (its `ftyp` brand, or the
   extension) and say so: e.g. "HEIC photos aren't supported yet. Please
   choose a JPEG, PNG or GIF." Covers every browser and route, converts
   nothing.
3. **`accept` on the upload input.** Safari converts; Chrome refuses the
   file without a reason; the server still rejects anything that gets past
   it. Combines with 2.
4. **Accept HEIC on the server:** `pillow-heif`, a new dependency, **and**
   conversion to JPEG, since `core/images/upload.py` keeps the original
   format and extension and only Safari shows a HEIC.

**Brian's choice (2026-10-29): options 2 and 3, in task 02.** The
explicit `accept` list goes on the input that task 02 already rewrites
(adding `multiple`), and the server message with it. Task 02's file now
carries both, with the detection rule (`ftyp` major brand `heic`, `heix`,
`hevc` or `hevx`, or `heic` among the compatible brands; not `mif1` alone,
which AVIF shares) and its tests. The message's wording is for Brian to
approve there. Option 4 is not scheduled.

**Suite and gate**, as separate runs, with every change above: 1513 tests
OK each. After the suite, db 14 holds no `user_photos:*` key.

Committed: not yet; left unstaged for review.

## Step 5 task 02 — the upload modal's file list, its `accept` list, and the HEIC message — DONE 2026-10-30

Task file: `.agents/tasks/2026-10-10-v3-forums-and-js/step05/task-02-multi-file-list.code-task.md`.
Branch `multi-upload`.

**Wording, Brian's (2026-10-30):** the HEIC message "HEIC photos aren't
supported. Please choose a JPEG, PNG or GIF."; the modal's text "Choose one
or more images from your computer or device. Each image is resized when
uploaded, and its image code is placed in your post." (which also loses the
old "placed your post"); after trying it on dev, Brian changed its first
sentence to "You can upload up to 10 images from your computer or
device." The cap message ("You can upload up to 10 images
at a time; 2 were left out.", "1 was" for one) and the placeholder ("No
preview" on a light-gray square) as proposed.

**The HEIC message.** `user_photos/forms.py` gains `is_heic(f)`, which
reads the file's first `ftyp` box, and `UploadImageField`, an `ImageField`
whose `to_python` swaps Django's `invalid_image` error for the HEIC
message when the header says HEIC. HEIC means a major brand `heic`, `heix`,
`hevc` or `hevx`, or `heic` among the compatible brands; not `mif1` alone,
which AVIF shares. It runs only after Pillow has failed, so a valid upload
pays nothing. `UploadForm` uses it, so the old `upload_ajax` gets the
message too. View tests, written first, in `UploadAjaxV3Tests`: an `ftyp`
header (the test file's `ftyp()` builder; no encoder needed) with major
brand `heic`, with `heix`, with `mif1` but `heic` compatible, each named;
an `avif` / `mif1` / `miaf` file keeps "Upload a valid image." The first
three failed with today's message before the change. Also checked against
task 01's real `sips` HEIC, both as an in-memory upload and as a
`TemporaryUploadedFile` on disk: the HEIC message each time; the source
JPEG still valid.

| Mutation in `forms.py` | Failed |
|---|---|
| `mif1` counted as HEIC | `test_another_ftyp_file_is_not_called_heic` |
| major brand only, compatible brands not read | `test_heic_among_the_compatible_brands_is_named` |
| `heic` the only brand | `test_a_heic_variant_brand_is_named` |
| the swap never happens | the three HEIC tests |
| `UploadForm` back on `forms.ImageField` | the three HEIC tests |

Restored byte-identical (SHA-1 checked).

**The list.** `post_box_modals.html`: the input takes
`multiple accept="image/jpeg,image/png,image/gif,image/webp"`, with
`<ul id="photo-upload-list">` below it. `uploads.js` no longer uses
`image_form.js` (hot-link still does, unchanged): each `change` adds the
chosen files to an array of `{file, url, item}` up to 10 and clears the
input; each entry is a thumbnail from `URL.createObjectURL`, the name, and
a remove button labelled "Remove <name>". A thumbnail whose `<img>` fails to
load becomes the placeholder and stays. Remove revokes its URL; the reset
`initUploads` returns, called as the modal opens, revokes them all. **Until
task 03, Upload sends the first file in the list**, as a `FormData` of the
form with `image_file` set to it, and clears the list on success; both
older upload browser tests pass unchanged.

The remove buttons first carried Foundation's `close-button` class. That
positions absolutely in the modal's corner, so they stacked on one another
(a click timed out) and made the modal's own × locator ambiguous. They
have their own `upload-remove` style.

Browser tests, written first, `news.tests.test_browser.SubmitUploadListTestCase`:
the input's `accept` and `multiple`; 2 then 3 chosen gives 5, and the input
is empty after; a thumbnail is a loaded `blob:` image; 12 chosen keeps the
first 10 and says 2 were left out; 9 listed then 2 chosen keeps 10 and says
1; removing the second of 3 leaves the other two and revokes exactly that
thumbnail's URL; a text file shows the placeholder, no `<img>`, and stays;
closing and reopening the modal empties the list and revokes every URL
made. Object URLs are recorded by wrapping `URL.createObjectURL` and
`revokeObjectURL` in an init script. Before the change: 5 errors, the
input refusing several files, and 3 failures.

| Mutation in `uploads.js` | Failed |
|---|---|
| no cap | both cap tests |
| the cap ignores what is listed | `test_the_cap_counts_what_is_already_listed` |
| input not cleared | `test_choices_add_up` |
| remove does not revoke | `test_remove_takes_out_that_file_and_releases_its_thumbnail` |
| reset does not revoke | `test_reopening_the_modal_empties_the_list_and_releases_every_thumbnail` |
| no placeholder | `test_a_file_that_cannot_be_drawn_shows_a_placeholder` |

Restored byte-identical (SHA-1 checked).

**Remove closed the whole modal, found by Brian on dev (2026-10-30).** The
remove handler takes the entry, and its button, out of the page during the
click. Reveal's overlay handler then sees a target that is neither the
modal nor inside it, and closes the modal. The remove test had passed
regardless: it read the list's names, and Playwright reads them from a
hidden modal too. It now asserts the modal is still visible, and failed
first. **Fixed, Brian's choice (option A over a `stopPropagation` in
`uploads.js`), by backporting Foundation 6.3.1's guard** (checked in
`node_modules/foundation-sites/js/foundation.reveal.js`, 6.3.1) into the
vendored 6.2.0 `foundation.min.js`: both of Reveal's click-to-close
handlers, the overlay's and the overlay-less body's, gain
`||!t.contains(document,i.target)`, so a click whose target has left the
page is not a click outside. Each edit was matched exactly once in its
handler. Reverting the overlay guard alone fails the remove test again;
restored byte-identical. **The body handler's guard has no test:** Reveal
uses it only for a modal with `data-overlay="false"` that closes on click,
and the site has none (the smiley picker, the only overlay-less one, has
`data-close-on-click="false"`). It is upstream's code unchanged.

**A file already listed was listed again, found by Brian on dev
(2026-10-30).** The server would not have stored it twice (`UploadForm.save()`
returns the member's existing photo for an identical file), but the post
would have had its code twice and the upload counted twice against the
quota. **Brian's choice: skip it and say so.** A page never sees a file's
path, so a file is the same if its name, size and `lastModified` match;
two different files with one name are both kept. A skipped file does not
count toward the 10. The message names them ("b.png is already in the
list."; "a.png, b.png and c.png are already in the list.") and is joined
with the cap message when both apply. The duplicate tests choose real files
from disk, since a file handed to Playwright as bytes is not certain to
keep its `lastModified` from one choice to the next. Five tests, written
first: four failed with the duplicate listed; the fifth (a removed file can
be chosen again) passed before and guards against remembering too much.
A sixth, two different `IMG_0001.png`s both listed, was added because
without it a name-only key passed everything.

| Mutation in `uploads.js` | Failed |
|---|---|
| no duplicate check | the four duplicate tests |
| skipped files count against the cap | `does_not_count_against_the_cap`, `a_skipped_file_and_the_cap_are_both_reported` |
| the key is the name alone | `test_different_files_with_one_name_are_both_listed` |
| a removed file stays remembered | `test_a_file_removed_can_be_chosen_again` |
| only the first message shown | `test_a_skipped_file_and_the_cap_are_both_reported` |

Restored byte-identical (SHA-1 checked).

**Sass** in `sg101/scss/_sg101.scss` (`.upload-list`, `.upload-thumb`,
`.upload-placeholder`, `.upload-name`, `.upload-remove`): 64 px thumbnails,
`object-fit: cover`, names that wrap anywhere. Rebuilt; `main.min.css`
changed with it. Sass prints 17 deprecation warnings with and without the
change.

**Looked at on the dev stack** at 375 × 812 and 1280 × 900, through a
session made directly and deleted after (`last_login` unchanged), with the
debug toolbar hidden: three PNGs (one portrait, one with a 60-character
name) and a text file. No horizontal scroll at either width, no page
errors; the portrait crops square, the long name wraps beside its
thumbnail, the text file shows the placeholder.

**The native input's "No file chosen".** Cleared after each choice, the
input reads "No file chosen" beside a full list. Brian chose (2026-10-30)
to hide it behind a styled "Choose images" button in task 03, whose file
now asks for it.

**Suite and gate**, as separate runs: 1525 tests OK each. `--tag browser`:
45 OK. After the suite, db 14 holds no `user_photos:*` key. All three
again after the Reveal backport: 1525, 1525, 45, OK each; and after the
duplicate handling: 1531, 1531, 51, OK each, db 14 again empty.

Committed: not yet; left unstaged for review.

## The hot-link and upload modals' buttons: Cancel left, the action right — 2026-10-30

Brian's call, after task 02: in both modals Cancel now comes first and the
primary action (Hot-Link, Upload) last, on the right of the `text-right`
row. Only these two modals have a pair; preview, help and the smiley picker
have one button each. `SubmitPostBoxTestCase.test_cancel_comes_before_the_primary_action`
reads each row's labels; it failed on both modals in the old order.

Enter in a field submits through the form's first *submit* button. Cancel
is `type="button"`, so Enter still hot-links. No test pressed Enter before;
`test_enter_in_the_address_hot_links` does, and fails if the hot-link
modal's Cancel is made `type="submit"` (Enter then closes the modal);
restored byte-identical.

**A void run, my mistake.** I started the full runs in the background and
then ran single tests in the foreground while they went on. Both use the
test database `test_sg101`, so each destroyed or shared the other's: the
background run ended 13 browser errors and 357 gate errors, and a
foreground run of the Enter test read "Please login to use this service".
All of it was discarded; the checks above and the runs below were made with
nothing else running.

Suite and gate, as separate runs with nothing else running: 1533 tests OK
each; `--tag browser`: 53 OK; db 14 empty after.

**The two bio pages, at Brian's request (2026-10-30).** `bio/edit_profile.html`
(Save) and `bio/avatar.html` (Update Avatar) put the action first; Cancel
now comes first on both. Their rows are left-aligned, like
`messages/report_message.html`, which already had Cancel first, so the
order is swapped and the alignment left as it is. Cancel there is a link,
so it takes no part in submitting the form. `bio` `ProfileTest.test_cancel_comes_before_the_primary_action`
compares the two positions in each page; it failed on both before the swap.
Suite and gate, separate runs: 1534 tests OK each; `--tag browser`: 53 OK.

## Step 5 task 03 — the upload queue, and "Choose images" — DONE 2026-11-01 (`21e69dc1`)

Task file: `.agents/tasks/2026-10-10-v3-forums-and-js/step05/task-03-sequential-upload-queue.code-task.md`.
Branch `multi-upload`.

**The queue.** `uploads.js` sends the list to `upload_ajax_v3` one request at
a time, in order. A success inserts the code and marks the entry ✓; a failure
marks it ✗ with the server's reason and the queue goes on. While it runs,
Upload is disabled and reads "Uploading 2 of 3…"; "Choose images" and the input
are disabled, and so is remove on entries sent or in flight. A waiting entry
can still be removed: it is not sent, and the total shrinks. The batch ends
with "2 of 3 added", in the success style only if all were added. Uploaded
entries leave the list and release their object URLs; failed ones stay, and
Upload sends them again.

**Decisions the task file left open.**

- **Closing the modal during a batch stops what has not been sent (Brian,
  2026-11-01; over carrying on, or refusing to close).** The file in flight
  finishes and its code goes in, since the server may already have it. The
  loop checks the form's `offsetParent` between files, so it needs no jQuery
  listener and covers Cancel, ×, Esc and a click outside alike; only Cancel
  was tested. Opening the modal is the reset, and it does nothing to a running
  batch except stop it: the file in flight and the rest stay listed, and the
  rest can be uploaded when it lands.
- **The summary replaces "Success! The image code was added to your post."**
  One file reads "1 of 1 added". Two older upload tests changed to match.
- **A 200 that is not the expected JSON** shows "Something went wrong with this
  image. Please try again.", not the parser's message.
- **The codes go into the textarea the batch began from**, not the active one:
  opening the modal from another post box changes the active one while the file
  in flight has yet to land.
- **"Choose images" is a `<button type="button">` that calls `input.click()`**,
  not a `<label>`: focus, Enter, Space and `disabled` are then the browser's.
  The input has `show-for-sr` and `tabindex="-1"`, so there is one tab stop.

**Clicking elsewhere mid-batch, measured.** The modal's overlay means the post
can be reached only by closing the modal, which stops the batch, so at most one
code can arrive after that. On the dev stack, with uploads intercepted: 2 files,
the modal closed with the first in flight, then a selection made in the post
and the first answered. 1 request was made, and the code **replaced the selected
text**: `keep SELECTED keep` became `keep \n![image](…)\n keep`. Left as it is;
that is what `insertAtCursor` does for every caller, and it now needs a selection
made within one upload's time. A caret moved there is simply followed
(`test_a_code_in_flight_goes_where_the_caret_has_moved_to`).

**Tests, written first.** `news.tests.test_browser.SubmitUploadQueueTestCase`
(20) and one in `bio.tests.test_browser.EditProfilePostBoxTestCase`, for the two
post boxes. `LocalUploadTestCase` is split out of `SubmitUploadTestCase` to
share its temporary `MEDIA_ROOT` and quota cleanup. Order is checked by opening
the stored file each code points at and reading its color, not by counting
codes. One at a time is checked by holding each upload in `page.route`. Before
the change, 20 of the 22 tests then run failed; the two that passed (the empty-list
message; a code following a moved caret) are covered by the mutations below.

| Mutation | Failed |
|---|---|
| sends not awaited (parallel) | 13 tests, among them `one_request_at_a_time` |
| stop at the first failure | `a_failure_says_why`, `no_response_marks_that_file` |
| list order reversed | 7, among them `codes_land_in_list_order` |
| removed from the page but not from the array | `a_file_removed_before_upload`, `a_waiting_file_removed`, `a_failed_file_removed` |
| no check for removal in the loop | `a_waiting_file_removed` |
| closing does not stop | `closing_during_a_batch` |
| reopening does not stop; reset wipes a running batch | `reopening_during_a_batch`, each |
| active textarea read at insert | `a_code_in_flight_goes_into_the_box` |
| caret reset before inserting | `a_code_in_flight_goes_where_the_caret`, `codes_land_in_list_order` |
| uploaded entries stay listed | 7 |
| remove left enabled in flight | `one_request_at_a_time` |
| remove left disabled after failing | `a_failed_file_removed`, `a_failure_says_why` |
| "Choose images" left enabled; input left enabled | `one_request_at_a_time`, each |
| total ignores removals; remove does not refresh it | `a_waiting_file_removed`, each |
| ✗ not cleared on retry | `the_mark_of_a_failed_file_clears` |
| parser's message shown | `an_answer_that_cannot_be_read` |
| summary always success; never success | `a_failure_says_why`; `codes_land_in_list_order` |
| empty-list check gone | `upload_with_an_empty_list` |
| the button does nothing | the three button tests, "No file dialog opened." |
| removal does not revoke | `files_leaving_the_list`, `remove_takes_out_that_file` |
| input not hidden; `display: none` | `the_native_input_is_hidden`, each |
| input a tab stop | `the_input_is_not_a_second_tab_stop` |

27 in all. Restored byte-identical each time (compared with a saved copy).
The battery's two extra keyboard-test errors are not counted as results. Their
output was not kept; the race below is the likely cause, seen in the suite run's
identical test and traceback.

**A flaky test, and its cause measured.** The keyboard test timed out waiting
for the file dialog in 2 of the battery's 27 runs, once under a mutation that
could not touch it, then again in a full suite run. It did not recur in 20 runs
without load. In a throwaway loop of open, focus, Enter, with 8 busy processes
in the container, **31 of 120 presses got no `filechooser` event**. At each
miss the button had the focus, the key was not prevented and the button's click
fired, so the page was right: two guesses (Reveal moving the focus; Reveal's
`preventDefault` while it has no focusable elements) were wrong. With the
listener added before the page loaded, under the same load: **0 of 120**.
`page.on('filechooser')` turns on interception without waiting for it, so
`expect_file_chooser` just before a fast key press can lose. The class now
listens from `setUp`; six runs of the three button tests under load passed.

**Looked at on the dev stack** at 375 × 812 and 1280 × 900, through a session
made directly and deleted after (`last_login` unchanged), the debug toolbar
hidden, uploads intercepted so nothing reached S3: no horizontal scroll, no page
errors, the disabled controls and the ✗ with its long reason as intended.
**Not tried:** the task's throttled upload by hand on a real upload; held routes
stood in for it. Task 04's walk and Brian's phone check come next.

**Sass:** `.upload-detail`, `.upload-result`, a disabled `.upload-remove`.
Rebuilt; `main.min.css` changed with it.

**Two additions, after Brian tried it on dev (2026-11-01).** Both his, from what
he saw with a throttled connection.

- **Five minutes for an upload.** `core/http.js`'s 30 s covers sending the
  file, so at 400 kbps anything over about 1.5 MB failed with "The server took
  too long to answer", and a retry failed the same way. Research topic 1 had
  closed the member's upload time as covered by Cloudflare's buffering, which is
  true of gunicorn and not of a timer in the browser. A 6.5 MB photo needs about
  1.7 Mbps to beat 30 s, and about 175 kbps to beat five minutes. `uploads.js`
  passes `timeoutMs`; preview and hot-link keep 30 s. **This has been live for
  single uploads since step 2.** A connection that truly hangs now takes five
  minutes to show its ✗; closing the modal stops the rest, not that file.
- **"Uploading…" with a spinner on the row being sent.** The button's label
  moves only between files, so a slow file looked like nothing happening. The
  spinner is CSS (`.upload-sending::before`), not `static/icons/ajax_busy.gif`:
  JS cannot use `{% static %}` and production's names are hashed, it takes the
  theme's color and the text's size, and step 12 retires the old pages' assets.
  It does not spin under `prefers-reduced-motion`; **that rule has no test.**

Without throttling the progress is barely visible on dev: recorded frame by
frame, 3 files of 55 KB took 0.23 s and 2 of 5.4 MB took 0.29 s, stored locally
with no S3. At 50 KB/s and 400 ms latency, 2 of 216 KB took 9.6 s, about 4.8 s
per label.

Tests, written first: `test_a_slow_upload_has_five_minutes` (Playwright's fake
clock, still sending at 299 s, failed by 301 s),
`test_the_row_being_sent_says_so_with_a_spinner`,
`test_a_failed_row_loses_its_spinner`, which guards and passed before the change.

| Mutation | Failed |
|---|---|
| the default 30 s; 4 minutes; 50 minutes | `a_slow_upload_has_five_minutes`, each |
| the row not marked as sending | `a_slow_upload`, `the_mark_of_a_failed_file_clears`, `the_row_being_sent` |
| sending class left on after success | `the_row_being_sent` |
| sending class left on after failure | `a_failed_row_loses_its_spinner` |
| no animation in the built CSS | `the_row_being_sent` |

Restored byte-identical.

**Suite and gate**, as separate runs with nothing else running: 1558 tests OK
each; `--tag browser`: 77 OK. After them db 14 holds no `user_photos:*` key.

## The debug toolbar hidden by default in dev — 2026-11-01

Brian's request: it sits over the page and he no longer uses it. `dev.py` reads
`DEBUG_TOOLBAR` (default off) into `SHOW_DEBUG_TOOLBAR`, and only
`SHOW_TOOLBAR_CALLBACK` looks at it; the app, middleware and `__debug__/` URLs
stay as they were. The callback used to return `DEBUG`, which `base.py` sets
to `True` outright, so that check decided nothing in dev and is gone.
`tools/site_smoke.py`'s check now passes when the toolbar's presence matches
the setting. To turn it on: `DEBUG_TOOLBAR=True` in `.env`, then
`docker compose up -d web`.

Three tests in `core.tests.test_settings.DebugToolbarWiringTests`. Default on
fails `hidden_unless_asked_for`; returning `DEBUG` fails it and
`debug_toolbar_false_hides_it`; never shown fails `debug_toolbar_shows_it`.
Restored byte-identical.

Measured through the real route, reading `http://localhost:8000/`: no `djDebug`
by default; with the line added to `.env` and `up -d web`, present; with `.env`
restored (byte-identical) and `up -d web`, gone. The smoke check, run alone,
passed at each. The rest of `site_smoke.py` was not run.

## Step 5 task 04 — the upload walk, the phone check, and shipping — DONE 2026-11-01

Task file: `.agents/tasks/2026-10-10-v3-forums-and-js/step05/task-04-upload-walk-and-ship.code-task.md`.
Branch `multi-upload`, on `7cf1dda5`. 
**The walk, by a headless probe** on the dev stack (2026-11-01), logged in as
pk 2 through a session made directly and deleted after (`last_login`
unchanged, checked), the toolbar off. Snapshot first:
`sg101-20261101-183222-before-uploads-walk.dump`.

**The demo, with real uploads to local storage,** on news submit at 1280: 4 PNGs
and `notes.txt` chosen, the second PNG removed, Upload. 3 codes landed in order
on their own lines between `first` and `second`; the summary read "3 of 4
added"; `notes.txt` stayed listed with "✗ Upload a valid image…". No page errors.

**A real slow upload, past the old limit:** a 2.43 MB JPEG through Chromium's
throttling at 50 KB/s with 400 ms latency took 49.2 s and was added. Under the
30 s limit it would have failed. This did not go through Cloudflare; that is
for the live spot check.

**Closing during a batch**, 2 files with the first held: by ×, by Esc and by a
click outside, the modal closed and 1 request was made each way. Task 03 had
tested only Cancel, and the probe below closes with it too.

**Every page with a post box, at 375 × 812 and 1280 × 900:** news submit,
profile edit (both boxes), message compose, message view (a message already
read), a download's comment form (985), calendar add, downloads add. On each, 10
files with long names and uploads answered by the probe, the second with a 400:

| Checked | Result |
|---|---|
| Horizontal scroll of the page; modal wider than itself | none, everywhere |
| Upload scrolled to, inside the window, and clicked | everywhere |
| Summary and what stayed | "9 of 10 added", 1 entry listed, everywhere |
| Codes in the box it was opened from | 9, everywhere; profile edit's boxes each separately |
| Cancel reached and closes | everywhere |
| Page errors, console errors, failed requests other than `/media/` | none |

**A comment form on a poll was not walked:** poll 20 had no post box in the page
(no other poll tried). The download's comment form is the same template.

**The phone check moves to the live site, Brian's choice (2026-11-01).** His phone
could not reach the dev stack, on the home Wi-Fi or with the Mac on the phone's
hotspot; the cause was not found. Every check of that port was made from the Mac
itself, so no other device has been seen to reach it. The task file allows either
place, and thumbnails are made on the phone, so the measurement holds. Step 5
ships before that result; a poor one would make the canvas downscale a follow-up.

**Thumbnails, no answer yet.** In headless Chromium on the Mac, 10 synthetic
12 MP JPEGs of 5.9 MB each decode in 219 ms (`img.decode()`). That says nothing
about a phone. An earlier figure from this probe, 0.05 s, measured only
`img.complete`, which holds once the header is read, and was thrown away.

**The probe's own faults, none in the product.** It first crashed after the real
uploads and before its cleanup, which left 4 photos, 8 files and 5 counts on the
quota in dev. They were removed by hand: 184 photos for pk 2 as before, the quota
from 29 to 24 with its expiry kept. Its first page results also read a previous
batch's summary from the hidden callout, the trap noted at the top of
`news/tests/test_browser.py`, and reported box 2 of profile edit as not inserting;
waiting for the callout to be visible cleared it. The final page run made 0
photos and 0 files and left the quota as it was.

**Suite and gate, one last time on the branch**, as separate runs with nothing
else running: 1561 tests OK each; `--tag browser`: 77 OK. The merge is a
fast-forward: `main` has nothing the branch lacks. No migrations, and nothing
changed in the requirements, the Dockerfile or the Compose files.

**Safari on macOS, by Brian (2026-11-01):** on the dev stack, from a list of checks
(a mixed batch, Choose images by mouse and keyboard, remove, closing mid-batch,
Responsive Design Mode at an iPhone size, a HEIC file from Finder): "safari looks
good". Which of them he ran was not itemized.

**Step 5 is complete and deployed** (2026-11-01). `main` was fast-forwarded to
`multi-upload` at `c49208f4`, CI green on both. Brian deployed. The live stylesheet, read over public HTTP, holds the spinner's `upload-spin`. The checkout and
containers on leopard were not read from here: an SSH read was refused by this
session's permissions, so the deployed revision is Brian's report.

**Brian's live checks (2026-11-01):** "spot check and phone check look good". The
spot check was two images in one batch through Cloudflare. The phone check was 10
library photos on a Pixel 8 in Chrome: **all the thumbnails showed in about a
second**, by his estimate. **The canvas downscale is not needed:** no problem was
seen, and the task adds it only if the result calls for it. A Pixel 8 is a recent
phone, so this says little about an older one, and iOS was not tried.

Found along the way, not part of this step: new S3 photos have no image content
type, #40.

## #40: new S3 photos stored without an image content type — new uploads fixed 2026-11-01

Found by Brian after step 5's merge: a new PNG opened directly in Chrome downloaded
instead of showing. Not this plan's work; it is here because that is where it
turned up. The issue holds the cause and the headers measured.

`S3Bucket._put` now sets `ContentType` from the key. It uses
`mimetypes.MimeTypes(filenames=())` with `strict=False`, Python's own tables and
not the system's. Measured in the `web` container: WebP comes back from a strict
lookup only because `/etc/mime.types` supplies it, and from the built-in tables
only non-strictly. A key of no known type sends no `ContentType`, as before.

`core.tests.test_s3.S3BucketContentTypeTestCase`, written first: each format, the
key and not the temporary file's name deciding, and one test through a real boto3
client with botocore's `Stubber`, so botocore checks the argument, which the file's
mock-based tests cannot.

| Mutation in `core/s3.py` | Failed |
|---|---|
| never set | the format, file object, named file and Stubber tests |
| a strict lookup | `each_image_format` (WebP), the Stubber test |
| `Content_Type` | the same four as never set |
| set even when unknown | `a_key_of_no_known_type`, and four existing upload tests |
| guessed from the bucket's name | the same four as never set |

Restored byte-identical.

Suite and gate, as separate runs: 1566 tests OK each.

**The objects already stored, measured (2026-11-02), not changed.** Part 2 of #40
writes to the production bucket and waits on Brian. Every object was listed and read
with `HEAD`, through the production credentials in dev's `.env`, at Brian's request:
43,655 objects, 21,828 photos and 21,827 thumbnails (told apart by key length, 22 or
32 characters against 23 or 33, which is inferred, and every key was one or the
other).

| | Mislabelled | Of how many |
|---|---|---|
| Thumbnails | 21,827 (`application/octet-stream` before 2026, `binary/octet-stream` in 2026) | all of them, since 2013 |
| Photos, 2026 | 72 `binary/octet-stream`, from the rewrite | all of 2026's still stored |
| Photos, before 2026 | 90 `application/octet-stream`: 68 `.webp`, and the 22 below | 21,756 |

Of the 162 photos, 140 get a type from the key. 22 do not: 11 with no extension, 7
`.jfif`, 4 `.jpg fog`. Across photos and thumbnails together 21,945 can be typed from the key and 44 cannot. 29 `.bmp` photos are
`image/x-ms-bmp`, not `image/bmp`, which is not a fault a browser minds. A thumbnail
is shown in an `<img>`, where the label does not matter, and is rarely opened alone.

An upload made after the fix does not appear above because Brian deleted his two test
photos first, which also made a first reading look wrong: they answered 403 and 404
because they were gone. A first run left botocore's debug log in the session's
scratch file, holding the access key ID, not the secret; it was deleted.

**The repair tool (2026-11-02), applied; see below.** `tools/fix_s3_content_types.py`
handles the 140 photos, Brian's choice; thumbnails and the 22 are left alone. A dry
run by default; `--apply` copies each object onto itself, and `--limit` takes a few
first. The copy sets the ACL and metadata again, carries the other headers, and is
conditional on the ETag read. A photo that is not public is left alone. After each
copy it reads the object back, with credentials and over plain https, and the first
one not as expected stops the run. `core.s3.content_type_for` is new, so the tool and
`_put` share one answer.

**Its dry run against the bucket:** 43,655 objects, 21,828 photos, 140 to repair, all
140 public, 22 with no type from the key. 68 `application/octet-stream` to
`image/webp`; of `binary/octet-stream`, 55 to `image/jpeg`, 16 to `image/png`, 1 to
`image/webp`. So every 2026 photo has a usable key, and before 2026 only `.webp` does.

`core.tests.test_fix_s3_content_types`, 12 tests, written with the tool and not
first, so all of it mutation-checked: 18 mutations, among them the ACL, the metadata
and the directive dropped, a dry run that writes, thumbnails selected, private photos
published, the read-back skipped. 17 failed at once. The other, the public status
unchecked, survived, because the "made private" case also served a wrong type; that
case now keeps the type and the mutation fails it. The copy's arguments go through a
real boto3 client with `Stubber`. The tests meet no real copy; `--limit` was for that.

Suite and gate, as separate runs: 1578 tests OK each.

**Applied by Brian (2026-11-02), 140 photos.** First `--apply --limit 3`, one of each
change. Read separately over plain https, each answered 200 with its new type, its
`date` and `user` metadata, and bytes that are a valid image; its Last-Modified had
moved, as expected. Brian opened the WebP in the browser and it displayed. Then
`--apply` for the other 137, which reported no failure: 67 to `image/webp`, 54 to
`image/jpeg`, 15 to `image/png`, 1 more to `image/webp`. The dry run afterwards: **0 to
repair**, the same 22 left alone. 10 of the 137 chosen at random answered 200 with the
right type. Whether each still shows in its post was not checked one by one; the URLs
and the public read are unchanged. 21,827 thumbnails and 22 photos stay mislabelled, by
decision.

**Seen by Brian:** both test photos, opened from the site after the fix, displayed
in the browser.

**Measured live (2026-11-02), new uploads now right:** two images Brian uploaded
through the site after deploying, stored a second apart, read back from S3 with
`HEAD`: a JPEG `image/jpeg`, a PNG `image/png`. Both open as intact images, resized
to 660 wide. Before the fix, the newest JPEGs measured `binary/octet-stream`.

## Step 6 task 01 — the forums index and a forum's topic list on V3 — DONE 2026-11-04

Task file: `.agents/tasks/2026-10-10-v3-forums-and-js/step06/task-01-forum-index-pages.code-task.md`.
Branch `v3-forums-release-1`, on `c1639add`. Not deployed: this branch ships
with steps 7 and 8.

**`v3-dev`'s hashes in `research/v3-dev-forums.md` predate the history
rewrite.** `d8ec4821` is `77e719a2` now; the merge base `24f83e72` is unchanged.

**What each side changed since the merge base, measured file by file.** Of the 14
templates, `main` changed 6, all by the `staticfiles` line, plus one more change:
`3155590f` dropped the member map link from `accounts/user_stats_tag.html` when it
pruned the `membermap` app. `v3-dev`'s copy still links `membermap-index`, which
would have made `/forums/` a `NoReverseMatch`; the port keeps `main`'s sentence.
`v3-dev` had also commented out the index's two `{% cache %}` blocks; **they are
restored (Brian, 2026-11-04)**, so production does the work it does today.

**The fragment split, grepped again:** as the task file has it. `jump_box` is also
on `topic.html`, which is old until task 02, so that page has the input-group
markup without Foundation's styles for now; its Go button was walked and works.

**The four V3 variants** are `v3-dev`'s markup in `sg101/templates/forums/v3/`;
the originals are byte-identical to `main` (`git diff --exit-code main`, with
`forum_query.js`, `jump_box.js`, `pagination.html`, `topic_list.html` and
`topic.html`). `last_post_info`, `topic_icons` and `forum_navigation` are now
`simple_tag(takes_context=True)`, through one helper choosing on `V3_DESIGN`:
an `inclusion_tag` fixes its template at registration. Each renders the same
values as before, in a context of their own.

**The Sass:** the blue, surf green and shell pink families, `.shiny`, `.green3`,
`.inline-forms`. **`.post-odd` left out (Brian, 2026-11-04):** no `v3-dev`
template uses it, and task 02 alternates with `:nth-child`. The cards are task
02's. Rebuilt; split on `}`, `main.min.css` differs from `HEAD` by exactly those
three rules.

**Tests, written first:** `V3PagesTestCase` in `forums/tests/test_views.py`, 7
tests. Against the old templates, the three for the new behaviour failed (V3 per
role, pagination, the V3 fragments); the other four passed, as they pin what must
not change (the moderator's link, the index's stats blocks, the old pages and
their fragments). Its `setUp` clears the cache: the index's cached blocks render
no template on a hit. Three `core` tag tests asserted the old markup of
`max_users` and `whos_online` (the `<div id>` wrappers, one-line sentences); they
now compare with whitespace collapsed, and `max_users` with no stats renders
nothing, as the V3 fragment has no wrapper.

**Mutations, 11, all caught, each file restored and its hash checked:** each view
without `V3_DESIGN`; `page_nav` back in the context; the old pagination include;
the tag helper always V3, and never; the index's old `forum_query`; the member map
link back; `whos_online` gone; the moderate link for everyone; `topic.html` on
`v3/base.html`. The `V3_DESIGN` mutations first surfaced as `KeyError`s; the
assertion now reads `.get()` and fails as an assertion (rechecked).

**Suite and gate**, separate runs: 1587 tests OK each.

**The walk, by a headless probe** in the web container on the dev stack, at 375 ×
900 and 1280 × 900, anonymous and as a dev superuser through a session made
directly and deleted after (it opened one topic, which marks it read for that
account): the index, `gear`'s topic list (the forum with the most topics), the
unanswered list and a topic. 90 checks: both Go boxes navigate on both designs,
breadcrumbs, both paginations, the icon font, the arrows, the moderate link, the
old pages' PNGs and `forum-nav` headings. No page errors, and no failed requests
other than `/media/` (dev has no copies). 6 failed:

- **4, the old design at 375**: the unanswered list and the topic are 950 px wide,
  as today.
- **2, a finding: `gear`'s topic list is 394 px wide at 375**, 19 over. Long
  usernames in Last Post have no break point: the widest cell's minimum is 188 px
  ("SurfbobGremmiepants610"), beside a 150 px topic name ("Prophet/Echobrain?").
  `surf-music`'s fits (355 px), and so did the index. This is `v3-dev`'s layout
  meeting today's data, not the port. Fixed below.

**The phone fix (Brian, 2026-11-04): `overflow-wrap: anywhere`.** Both tables
carry `forum-table`; below medium (`small only`) its cells take `anywhere` and
the last column a width of 10 rem. `anywhere` alone fixed the overflow but let
the table squeeze Last Post to 91 px, splitting "johnnyanguish" and wrapping the
date over three lines; with the width, the date holds one line, ordinary names
stay whole and only the 22-character name breaks. Unscoped, it also split names
in the Author column at 1280, where nothing overflowed, so it stops at medium.
After it: the probe's 90 checks fail only the 4 old-design ones, and `gear` and
the index have no horizontal scroll at 320, 360, 375, 414 or 639. The suite and
the gate were rerun after it: 1587 OK each.

**Open, for task 03 (Brian, 2026-11-04): the forum tables overflow at tablet
widths.** From 640 to 1024 the sidebar sits beside the content, which leaves the
table 480 px at 640 and 768 px at 1024, and `v3-dev` shows all five columns from
medium up. `gear`'s table is 774 px wide there. Measured horizontal scroll, with
the phone fix in place (it does not reach these widths):

| Width | `gear` | the index |
|---|---|---|
| 640 | 309 px | 71 px |
| 768 | 213 px | 0 |
| 1023 / 1024 | 22 / 21 px | 0 |
| 1280 | 0 | 0 |

`/news/` and `/profile/members/` have none at 640 or 1024. **One remedy was
measured, by CSS injected into the page, no file changed:** the extra columns
(Replies, Author, Views; the index's Topics, Posts) shown from large rather than
medium, and the phone rule up to large. Overflow 0 at 640, 768 and 1023 on both
pages. At 1024 `gear` stays 21 over, two long names side by side in Author and
Last Post (208 px each); a 10 rem Author column was proposed for that and not
measured. It hides the counts and the author from tablets, a change to `v3-dev`'s
design, which is why it waits for the screenshot review.
**Decided in task 03 (Brian, 2026-11-04): a step of its own, plan step 14,**
with the post box toolbar's tablet overflow found there.

## Step 6 task 02 — the topic page and the post card on V3 — DONE 2026-11-04

Task file: `.agents/tasks/2026-10-10-v3-forums-and-js/step06/task-02-topic-page.code-task.md`.
Branch `v3-forums-release-1`, on `40002da6`. Not deployed.

**The templates.** `topic.html` changed on `main` since the merge base only by
its `staticfiles` line; `display_post_v3.html` and `new_post_form.html` exist
only on `v3-dev`. Everything they call exists on `main`. Ported from `v3-dev`
with `{% load static %}`, the two `{% cycle %}` lines gone, one card class
(`sg101-card`, `sg101-card-divider`), and the scripts cut to the post box
module (only when the reply form is on the page, as on news submit) and the
inline `jump_box.js`. Dropped: jQuery UI (only message compose's autocomplete
uses it), `jquery.form`, `forums.js` and the 2017 `post_box.js`. The modals are
included once, by `new_post_form.html`.

**The task file was off on one point:** `display_post.html`'s only other user
is `edit_post.html`, not the list and moderator pages. It stays either way.

**Found, not done here: today's page links an oversized image to its full
size.** `main`'s `topic.html` shrinks any post image over 660 px after
`imagesLoaded` and wraps it in a link to the original; `v3-dev` dropped the
script, and Foundation's `img { max-width: 100% }` only shrinks. Added to R14
and step 7 (Brian, 2026-11-04), then **taken out again the same day (Brian):
the link would show nothing more.** Measured on the dev copy of production's
data: of 32,946 posts with images, all but about 200 images are on the site's
own photo storage (S3 or `/media/user_photos`); since 2024, 3,477 of 3,478.
Uploads and hot-links alike are resized to fit 660 × 720, and a `Photo` keeps
only that image and a thumbnail, so there is no larger original to link to.
The browser fits each to its card. The exceptions, about 200 images
hot-linked straight from Dropbox, Google and others, mostly older, are not
resized, and the card shows them shrunk.

**Replies are lost on this branch until step 7.** `forums.js` is what turns
the reply form's submit into quick reply; the form itself posts to `.`, which
`topic_index` ignores. Expected by the plan; it matters only when trying a reply
on dev.

**The cards.** Each post is a row with an author card (from medium up) and a
body card. `#forum-topic-post-container > .row:nth-child(even)` colours both
cards and their dividers blue at 50%; the rest are surf green at 50%. The
minifier writes `(even)` as `(2n)`. `main.min.css`, split on `}`, gains exactly
those rules.

**Tests, written first.** Six render tests in `V3PagesTestCase` and a browser
test, `forums/tests/test_browser.py`. Against the old page the five for new
behaviour failed, the browser test by timing out on a V3 post box that wasn't
there; the other two (no post box for anonymous visitors, the edit page's old
card) passed, as they pin what must not change, and were seen to fail under
their mutations below. **The browser
test types and clicks Bold** rather than only collecting page errors: a module
that fails to load logs a console error and raises no page error. Task 01's
unconverted-pages test now takes the edit page in place of the topic.

**Mutations, 13, each file restored and its hash checked.** Caught: the topic
view without `V3_DESIGN` or with `page_nav`; `topic.html` on `base.html`; a
`{% cycle %}` back; a numbered card class; the `nth-child` rule broken; the
modals included twice; the module loaded for anonymous visitors; a module
import broken (by the browser test); quick reply on the old card; the edit page
on the V3 card; `forums.js` back (by the render test). **Two misses, one
fixed:**

- **The CSS check first missed its own mutation.** It looked for
  `…nth-child(2n) .sg101-card`, which also begins the divider's selector, so
  breaking the card's left it passing. It now requires the selector to end at
  the card; that and a second mutation (the card selector removed, the
  divider's kept) are caught.
- **The browser test does not see `forums.js` back.** On V3 markup it finds
  nothing to bind and raises nothing. The render test catches it; the task
  allowed the browser test either this or the broken import.

**An existing test now fails by design: `bio`'s
`UnverifiedAddressIsNotDisplayedTestCase.test_forum_post`.** It asserts the
verified address's `mailto` on a forum post, and the V3 card has no email link
until step 7 (R14). Its guarantee, no unverified address, still holds. **Marked
`@expectedFailure` (Brian, 2026-11-04)**, so step 7's link turns it into an
unexpected success, which fails the suite. Checked: with a `mailto` added to
the card for one run, `FAILED (unexpected successes=1)`; restored by hash.

**Suite and gate**, separate runs: 1594 tests, OK with 1 expected failure, each.

**The walk, by a headless probe** on the dev stack, logged in as a dev
superuser through a session made directly and deleted after (each topic opened
is marked read for that account): the last page of topic 41535 (5 posts on it)
and of 41524 (6), at 375 × 900 and 1280 × 900. 22 checks, all passing: the body
cards alternate green, blue from the first; a row appended to the container
takes the next colour; one post box, and Bold works; no page errors, no failed
requests other than `/media/`, no horizontal scroll. Two cards were looked at by
eye at each width.

## Step 6 task 03 — the screenshot review, the phone toolbar — DONE 2026-11-04

Task file: `.agents/tasks/2026-10-10-v3-forums-and-js/step06/task-03-screenshot-review.code-task.md`.
Branch `v3-forums-release-1`, on `5ba90760`.

**The shots.** A headless probe on the dev stack (data to 2026-10-07; snapshot
`before-forums-review` taken first), the debug toolbar off. Subjects by id:
forum 7 (`gear`, 8684 topics), topic 41216 (72 posts, 4 pages, unlocked; its
last page, which has the reply box), member `Klas` (no groups, able to reply),
moderator `CaptainSpringfield` (Forum Moderators). Sessions made directly and
deleted after; opening a topic marks it read for that account. 18 page shots,
the three pages at 360 and 1280 for anonymous, member and moderator, plus the
member's at 640 and 1024 for task 01's open question, all in the session
scratchpad: they show members' posts, avatars and, to the moderator, posters'
IP addresses. Nothing reached the repository; the stand-in video button was
injected by the probe, not written to a template.

**The phone toolbar, measured: seven buttons do not fit.** Foundation's menu
doesn't wrap, and a fieldset never shrinks below its contents, so a toolbar
too wide widens the page. On the topic's reply box, at 360:

| | Toolbar | Fieldset / its room | Page scroll |
|---|---|---|---|
| Today, 6 buttons | 313 px | 355 / 340 | 5 px |
| 7, with a stand-in | 366 px | 408 / 340 | 58 px |
| 7, side padding 0.5 rem | fits | 340 / 340 | 0 |

So **today's six already overran the forum reply box at 360.** `flex-wrap` did
nothing: this build's menu lays its items out as table cells.

**Found in the shots:**

- **A long link in a post is cut off.** The card hides what overflows it, so
  the page doesn't scroll and the end of the URL simply isn't there. A first
  test with a hyphenated URL passed before the fix; a browser breaks lines at
  hyphens. The test now uses a run with no break point.
- **The post box toolbar overflows at tablet widths on every page with one**:
  all 13 buttons, 661 px, from medium up. News submit scrolls 211 px at 640 and
  115 at 768; the forum reply box 238 and 142; none at 1024 or wider.
- **The phone header overflows with a long username.** For
  `CaptainSpringfield` at 360 the profile link wraps and Logout ends at 421
  px, on every V3 page; for `Klas` it fits at 360, not at 320 (324). First
  read as moderator-only; it is the name's length. Registration allows 30
  characters of `\w`, so a name never breaks.
- **Expected gaps, not faults:** the post tools, signatures, PM and email
  links and attachments (step 7); the empty Video Attachments box (step 8);
  missing avatars and photo of the day (dev has no media).

**Decisions (Brian, 2026-11-04), each the recommendation:**

- **The toolbar:** side padding 0.5 rem below medium. **Done.**
- **Long words in posts:** `overflow-wrap: anywhere` on the card's sections.
  **Done.**
- **Tablet widths:** the tables and the toolbar together, as **plan step 14**.
- **The header:** **plan step 15**, independent of the rest.
- **The look:** approved with one change, the header's ragged right edge,
  below. No other changes (Brian, 2026-11-04).

**The two fixes**, in `_sg101.scss`, rebuilt; `main.min.css` gains exactly
those two rules. Browser tests in `forums/tests/test_browser.py`, at 360: the
reply box leaves no horizontal scroll (failed first, 5 px), and a post's
unbroken 180-character link stays inside its card (failed first, 1142 px).
Each rule removed from the built CSS fails its test; restored by hash. On the
dev topic afterwards, with and without the stand-in: no horizontal scroll at
360 or 375, and no post cut off. At 320 Logout still overruns by 4 px, which
is step 15.
All 80 browser tests pass with the padding, which every post box takes. Suite
and gate, separate runs: 1596 tests, OK with 1 expected failure, each.

**The header's right edge (Brian, from a screenshot at about 1190 px):** the
menu bar ran past the forum's right edge and the banner stopped short of it.
Measured at 1280, where the page's row is 40-1240 and the content's edges are
55 and 1225: the banner ended at 1205 (the 750 px image left-aligned in a 770
px column), the menu bar spanned 40-1240 (its wrapper was `small-12` without
`columns`, so it had no gutters), and the top bar spanned the window (Search
ending at 1272; at 1920, 1912 against content at 1545). Three changes in
`v3/base.html`, all kept (Brian, 2026-11-04):

1. The menu bar's wrapper takes `columns`.
2. The banner's column takes `text-right`, so the slack sits between logo and
   banner: the gap goes from 41 to 61 px at 1280.
3. The top bar's contents sit in a `row` and `columns`, and
   `#base-header > .top-bar` loses its side padding, so the row's gutters set
   its edges; its background still spans the window.

After: Search, banner, menu bar and content end on the same pixel at 768,
1190, 1280 and 1920 (753, 1175, 1225, 1545), and the logo and menu bar start
together. At 360 the menu bar is inset 10 px to the content's gutter where it
had run edge to edge; nothing scrolls sideways at any width measured.
`main.min.css` gains the one rule. **Test:** `HeaderAlignmentTestCase` in
`core/tests/test_browser.py` compares the three right edges with the content's
at 1190, 1280 and 1920, each block separately. It failed before the change;
each of four mutations was caught by its own block only: the menu bar without
`columns`, the banner not right-aligned, the top bar's contents outside the
row, and the padding rule removed, which shows only at 1190, where the row
fills the window. Restored by hash. Suite and gate, separate runs, browser
tests included: 1597 tests OK with 1 expected failure each.

**Step 6 is complete** (2026-11-04): the forums index, a forum's topic list
and the topic page are on V3, reviewed, and ticked in the plan. Not deployed:
the branch carries steps 7 and 8 before forums release 1 ships. Carried
forward: plan step 7 (R14, and removing bio's `@expectedFailure`; the
full-size image link was taken back out, under task 02 above), step 8 (the reply form's help link), steps 14 and
15 (tablet widths, the phone header), and step 13 (the phone banner).

## Step 7 task 01 — the complete post card — DONE 2026-11-06

`display_post_v3.html` has every R14 item, item for item against
`display_post.html`, which is unchanged (`edit_post.html` uses it). Flag and
delete are `<button type="button">`s with `data-post-id`; they do nothing
until task 02's `topic.js`. The post's row is `id="post-N"`, and an empty
`<span id="pN">` inside it takes the `#pN` that `goto_post` and old links end
in. **Permalinks had been landing at the top of the page on this branch since
step 6**, as the V3 card had neither anchor.

**Decisions (Brian, 2026-11-06), each the recommendation:**

- **Flag: signed-in viewers only.** Today's card shows it to everyone and
  `flag_post` refuses an anonymous visitor.
- **Edit: an inline condition in the card**, the author or a moderator.
  `post_edit_button` stays for the old card. A `forums/v3/` variant chosen on
  `V3_DESIGN` would have given quick-replied posts the old PNG:
  `quick_reply_ajax`'s context has no `V3_DESIGN`.
- **PM and email: in a tools row under the post, at every width.** The author
  card is `show-for-medium`, so links only there would be gone on phones.

**Provisional icons, for task 03's review:** quote `fi-comment-quotes`, edit
`fi-pencil`, flag `fi-flag`, delete `fi-trash`, PM `fi-comment`, email
`fi-mail`, acquaintance `fi-check`, spammer `fi-skull`. Each has a `title`
and a `show-for-sr` label.

**The stranger highlight** is the old colour, `#fff6bf`, on the post's header
bar. The rule is `#forum-topic-post-container > .row
.sg101-card-divider.stranger`: as specific as the even-row rule and after it.
One notch less specific loses on blue rows only (a mutation, below).
`main.min.css` gained that rule and the tools row's, below; it lost none.

**Tests.** `PostCardTestCase` in `forums/tests/test_views.py`, 17 tests, and two more below: each
item for the viewers who may see it and absent for the others. The viewers are
anonymous, a member, the author and a moderator, on an active member's post
and on a stranger's. New profiles default to stranger with the email hidden,
so the tests set both. Also covered: a moderator's quick reply returns edit,
delete, flag and the IP link. Five browser tests in `forums/tests/test_browser.py` (three are below):
a permalink to post 40 of 40 lands on page 2 with the post in the viewport,
and a stranger's header differs from an ordinary one on both card colours and
matches itself across them. bio's `test_forum_post` lost its
`@expectedFailure` and passes.

Before the card: 27 failures and 1 error. The error was the colour test not
finding `#post-N`, so its colour assertion was proved by mutation instead.
**Eleven mutations, each caught by its own test, each file restored by hash:**
delete, the IP link, edit or flag shown too widely; stranger tools on the
moderator's own post or on a member's; email despite `hide_email`; no `pN`
(both the render test and the permalink test, run separately); no `stranger`
class; the CSS rule removed (headers equal, surf green); the rule one notch
less specific (headers equal, blue).

**On dev, as a moderator, at 360 and 1280:** a stranger's post, one with
attachments, and one edited with a signature all render every item, with no
page error and no sideways scroll.

**The name, the signature and "Last edited" (Brian, 2026-11-06):**

- **The author's name is bold**, in the author card and in the phone's
  header: wrapped in `<strong>` in the card, as `profile_link` is used
  site-wide.
- **The signature follows a short, light rule** in place of the "&mdash;",
  which had sat on a line of its own as the signature is its own paragraph.
  The rule is a third of the post's width, on the left, at 15% black; a
  full-width rule was tried and Brian chose the short one.
- **The signature steps back:** 0.875 rem and `#555`, about 6:1 against the
  lighter card colour, with its paragraphs 0.5 rem apart.
- **"Last edited" moved above the rule**, under the post it describes, in the
  signature's size and grey (`.forum-post-edited`). Under the signature it had
  read as the signature's last line. The header bar, beside "Posted on", was
  the other place considered; it would wrap for a moderator and add a fourth
  line on a phone.

- **The author card's details follow suit** (Brian, 2026-11-06): its
  section's `quiet` (which made it `smaller`, about 13.3 px, and left it
  near-black) became `.forum-post-author-details`, in the same rule as the
  signature and the edit note. The name above stays bold and full size.
- **"Last edited" is in the viewer's time zone.** It used Django's `date`
  filter, and nothing activates a member's zone, so it rendered in
  `TIME_ZONE` (Chicago), 24-hour with seconds, for everyone, while "Posted
  on" above it used `forum_date` and the member's zone and 12/24-hour
  preference. Today's card does the same. Now `forum_date` for both. **Test:**
  a member in `Australia/Sydney` on 12-hour time, a post made at 02:00 UTC on
  2026-01-15 and edited at 03:00: it reads "Jan 15 2026 02:00 PM". Before the
  fix the same page read "Posted on Jan 15 2026 01:00 PM" and "Last edited:
  Jan 14, 2026 21:00:00". The test's first version set only the edit time,
  earlier than the post's creation, so the card showed no edit note and the
  test failed for that reason; caught by printing the rendered note, and the
  creation time added.

**`quiet` means two things.** Blueprint's `.quiet` is `color: #666`, which
is why "Last edited" is grey on today's pages. V3's, in `_sg101.scss` since
the first V3 commit (`2c46c1fe`, 2016), is `font-size: smaller` with no
colour, so on V3 it is smaller and not greyer. The card's other `quiet`
items ("Posted on", the author card, the IP) are the same. Greying V3's
`quiet` would change every V3 page that uses it (the topic page, photo of the
day, the store, the Yahoo group archive), so "Last edited" took its own class
instead. Open: whether V3's `quiet` should be grey.

**Tests:** in `PostCardTestCase`, the name's link is wrapped in `<strong>`
twice; the signature section opens with the `<hr />`; "Last edited" comes
before it. In the browser, at 1280, the signature, the edit note and the author's
details are each smaller than the post's text and a different colour, and the rule is under
half the section's width. Written after the change, so eight mutations, each
caught and restored by hash: the author card's name not bold (1 of 2); no
rule; the edit note back under the signature; the edit note unstyled (16 px,
the post's size); the author details out of the shared rule (16 px); the
signature full size; the signature not grey
(`rgb(10, 10, 10)`, the post's colour); the rule full width (618 px against
325).

**Seen on dev, for step 8: an attached video is wider than the card on a
phone**, and the card hides the overflow. At 360 an embed's title ends
mid-word. The embed's `<iframe>` has a fixed width. Brian chose step 8 for
the fix, which is about video attachments.

**The tools row sat above empty card** wherever the author card was the
taller: the post card stretches to match (`height: 100%`) and the spare height
fell below its tools. **Brian chose (2026-11-06) to put the spare height above
the tools.** `.sg101-card` is a column flexbox, its `.card-section`s grow, and
the tools row doesn't. On phones the author card stays hidden:
`.show-for-medium` is `display: none !important`, which beats the `flex`.
`main.min.css` gains three rules and `.sg101-card{height:100%}` becomes one
with `display:flex;flex-direction:column`. **Test:**
`test_the_tools_sit_on_the_bottom_of_a_short_post`, at 1280, a one-line post
beside an author card with a location and a flag. It failed first with 118 px
under the tools; removing the `flex-grow` or the `display: flex` from the
built CSS each brings back the same 118 px, restored by hash. On the three dev
posts afterwards, the gap is 1 px (the border) at 360 and 1280, and the author
card hidden at 360 and shown at 1280.

**The tools row's layout (Brian, 2026-11-06):** right-aligned, more padding,
and the stranger tools on a line of their own. The row is a wrapping flexbox
with `space-between`: Top stays on the left, and the icons, now in a
`.forum-post-tool-icons` group, go right. Each icon is 1.25 rem with 0.25 rem
by 0.5 rem padding, which is also a bigger target to tap. The stranger tools
take `flex-basis: 100%` and `text-align: right`. **Test:**
`test_the_tools_sit_right_with_the_stranger_tools_below`, as a moderator on a
stranger's post at 1280: both lines end at the section's right edge, and the
stranger tools start below the icons. A first version also checked the delete
button sat past halfway; that passed before the change, so it was replaced.
Removing `justify-content` from the built CSS leaves the icons 425 px short of
the edge; removing the stranger rule leaves those tools 276 px short, beside
the icons. Both restored by hash. Re-shot on dev at 360 and 1280: as intended,
no sideways scroll, the tools still on the card's bottom edge.

**Found, not fixed (#41): `flag_icon` 500s on a country code it doesn't know.**
`bio_tags.flag_icon` sets `name` only when the code is in `FLAG_DATA`, so any
other code raises `UnboundLocalError` and the page fails. The keys are
lowercase; the test first used `'US'` and got a 500. No dev profile has a
code outside the data (counted 2026-11-06), so it is dormant.

Suite and gate, separate runs, browser tests included: 1622 tests, OK, each.

## Step 7 task 02 — `topic.js`: quick reply, flag and delete — DONE 2026-11-06

`sg101/static/js/v3/forums/topic.js`, an ES module with no jQuery, loaded
on every V3 topic page (flag and delete are on every page; the reply box only
on the last). Every request goes through `core/http.js`; nothing calls
`alert()`.

- **Quick reply** takes the reply form's `submit`, so Enter works as well as
  the button. It sends `new FormData(form)` (body, `topic_id`, any
  `attachment` inputs) to `/forums/quick-reply/`, appends the returned card to
  `#forum-topic-post-container`, and clears the box. On failure the text
  stays and the message shows in a red callout above the button. The button
  is disabled and relabelled while it posts.
- **Flag and delete** keep today's `confirm()` wording. The server's reply,
  either way, shows in a callout at the end of that post's body. They are
  handled by one listener on the container, so a quick-replied post's tools
  work at once. **A fix, not parity:** `forums.js` bound them once at load,
  so a quick-replied post's tools did nothing until a reload.
- **Delete topic** keeps its `confirm()`; cancelling stops the submit.
  Without the script (this branch since step 6) the button deleted at once.

**Decisions (Brian, 2026-11-06), each the recommendation:**

- **The module lives at `js/v3/forums/topic.js`**, not `forums/static/js/`
  as the plan and design §4.4 say. From there it imports `../core/http.js`
  as the post box modules do, and `test_the_site_modules_import_only_hashed_files`
  covers it unchanged (it collects only `sg101/static/js/v3`). Step 8's and
  later modules follow it.
- **A deleted post fades (1.5 s, Web Animations) and is then removed**, so
  later posts re-alternate their colours. Today's page only hid it.

**A bug found on dev, after the tests passed:** the flag's callout went into
the author card. `post.querySelector('.medium-9 .card-section')` matches
against the whole document, and the page's own content column is a
`.medium-9`, so the post's first `.card-section`, the author card's,
matched. At 360 that card is hidden and the reply was never seen; from medium
up it would have shown in the author column. The browser test had checked
the callout's text anywhere in the post, which passes for hidden text. The
selector is now `:scope > .medium-9 .card-section`, and the test checks the
callout is visible inside the post's own card, at 1280 and in a new test at
360. Both failed before the fix.

**Tests.** `TopicScriptTestCase` in `forums/tests/test_browser.py`, 8 tests.
Each records every dialog, so an `alert()` fails it. Quick reply appends a
post in the next colour, clears the box, and a `window` marker survives (no
reload). A refused reply (the topic locked after the page loads, 403) keeps
its text and shows the message. Flag shows the reply in the post's card, at
1280 and 360; a cancelled flag sends nothing. A moderator's delete removes the
post from the page and the database. Flag works on a quick-replied post. A
cancelled topic delete leaves the topic. Plus a render test: `topic.js` loads
once on page 1 of 2, anonymous and signed in. All failed before the module.

**Eight mutations, each caught by its test and restored by hash:** the append
removed (2 posts, not 3); the box cleared on failure; the tools bound per
button at load (the quick-replied post's flag shows nothing); the script tag
removed (the render test, and flag); the delete-topic confirm not wired (no
dialog); `alert()` for the flag's reply; the selector without `:scope` (the
360 test); the `http.js` import without its semicolon (the real-tree test
names `js/v3/forums/topic.<hash>.js` importing the unhashed file).

**On dev**, as a moderator at 360 and 1280, with the flag and quick-reply
requests answered in the browser (`page.route`), so the database was
unchanged (posts, flags and topics counted before and after): the flag's
reply shows at the end of the post, green, and a refused reply keeps its text
under a red callout. No page errors.

`forums.js` stays: the old-design new topic, reply and edit forms load it
until step 8.

Suite and gate, separate runs, browser tests included: 1631 tests, OK, each.

## Step 7 task 03 — the walk, the icons, own-post tools — DONE 2026-11-09

Task file: `.agents/tasks/2026-10-10-v3-forums-and-js/step07/task-03-walk.code-task.md`.
Branch `v3-forums-release-1`, on `532766a1`.

**The walk, by a headless probe** on the dev stack (data to 2026-10-07), the
debug toolbar off, mail to the console backend (`.env` sets no
`EMAIL_BACKEND`), so a flag sent nothing. Snapshot first:
`sg101-20261109-123029-before-step7-walk.dump`. Subjects by id: topic 41216's
last page (page 4), post 483917 for the permalink (30th of 72, so page 2),
post 485644 (topic 41534, email shown), post 485470 (a stranger's, topic
41505), member `Klas` (pk 7), moderator `CaptainSpringfield` (pk 12).
Sessions made directly through `AUTHENTICATION_BACKENDS[0]` and deleted after;
`last_login` unchanged, checked. At 360 and 1280, each role in its own
context, recording dialogs, page errors and main-frame navigations:

| Role | Checked | 360 | 1280 |
|---|---|---|---|
| anonymous | reads page 4; no flag button | ✓ | ✓ |
| member | permalink lands on page 2 with the post at the top | ✓ | ✓ (see below) |
| member | quick reply appends, next card colour, box cleared, no reload | ✓ | ✓ |
| member | flag: the reply in the post's own card, no reload | ✓ | ✓ |
| moderator | delete removes the member's reply in place, no reload | ✓ | ✓ |
| moderator | delete topic asks; cancel stays on the page | ✓ | ✓ |
| all | dialogs `confirm` only, no `alert()`; no page errors | ✓ | ✓ |

Two checks failed first, neither in the card. **At 1280 the permalink check
failed** on the post's top at −0.x px: it lands, and the probe's `top >= 0`
was too strict. **At 360 the moderator's page scrolls sideways** by 63 px:
the header's Logout ends at 423 for the long username, which is plan step 15.
The member's page at 360 has none.

**What the walk left in the dev database: nothing.** Its two replies were
deleted by the walk itself, and their flags with them (cascade). Topic and
forum counts and `last_post` matched the before-state. Put back by hand: the
view counts of the three topics opened, two `TopicLastVisit` rows, and the
`end_date` of three `ForumLastVisit` rows. Two were recorded before the walk.
The third, the moderator's for forum 6, opened by the stranger's post, was
not, and took its value from the snapshot. A state record taken
after cleanup was identical to the one before. **Redis had drifted before the
walk:** `rebuild_redis --check` found 11 problems, with the public post count 5
high and the topic count 2 high, where the walk added 2 posts and no topics.
Rebuilt; it matches.

**Decisions (Brian, 2026-11-09), each the recommendation:**

- **Quote is `fi-quote`**, the bare “ ” mark. `fi-comment-quotes` and PM's
  `fi-comment` were both speech bubbles, side by side in the tools row.
- **The other six icons stay:** edit `fi-pencil`, flag `fi-flag`, delete
  `fi-trash`, email `fi-mail`, acquaintance `fi-check`, spammer `fi-skull`.
- **Flag, PM and email are hidden on your own post.** The old card shows all
  three, and the walk flagged the member's own reply. A quick reply is
  always the poster's own, so it now has none of them.
- **The phone layout and the anonymous flag** were settled in task 01 (under
  task 01 above) and looked right in the shots: the moderator's six icons fit
  at 360.

**Tests.** In `PostCardTestCase`, flag, PM and email are now absent for the
post's author as well as for anonymous visitors. The quick-reply test checks
the moderator's own reply has none of the three. All four failed before the
template change, each only on the author. **Browser:** `TopicScriptTestCase`'s
posts are now another member's (`author`), as the member flagged their own.
`test_flag_works_on_a_quick_reply` became
`test_tools_work_on_a_quick_reply`, a moderator deleting their own quick
reply, since nobody else's quick reply is on the page. **bio's
`test_forum_post`** now views the topic as another member, as the post's
author no longer sees a `mailto` on it. Its point is the address shown to
other people.

**Three mutations, each caught and restored by hash:** flag shown on your own
post (the flag test and the quick-reply test); PM and email shown on it (the
PM, email and quick-reply tests); the tools bound to each post at load
instead of the container (`test_tools_work_on_a_quick_reply`, which fails on the
post still being there, after the reply was appended).

**Re-shot** at 360 and 1280: Klas's own post shows quote and edit only; on
others' posts the member gets quote, flag, PM, email and the moderator all
six. No page errors; the moderator's 63 px at 360 is the header again.
Screenshots stay in the session scratchpad.

**Still open, carried forward:** whether V3's `.quiet` should be grey (task
01, above); #41 (`flag_icon`); the header at 360 (plan step 15).

Suite and gate, separate runs, browser tests included: 1631 tests, OK, each.

**Step 7 is complete** (2026-11-09): the V3 topic page has every capability
of today's, run by `topic.js`, walked on dev and ticked in the plan. Not
deployed: forums release 1 ships at the end of step 8.
