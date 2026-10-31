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
