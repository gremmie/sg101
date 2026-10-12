# Task: The browser test base class, and the upload modal test

## Description
Add `core.tests.browser.BrowserTestCase`, the base class every later browser
test builds on, and prove it with one real test: on `/news/submit/`, logged in,
clicking the post box's Upload button opens the upload modal. The test must be
seen to fail under two mutations, and the same run must be green in CI.

## Background
Task 01 puts Playwright and headless Chromium in the dev image. This task gives
them a harness.

Research topic 3 ran a probe `StaticLiveServerTestCase` under the unchanged
`docker_test` settings (PostgreSQL, Redis, `DEBUG = False`), and found one
catch. Playwright's sync API runs an asyncio event loop in the test's thread.
Without `DJANGO_ALLOW_ASYNC_UNSAFE`, the first ORM call after Playwright
starts raises `SynchronousOnlyOperation`. The design sets it **in the base
class only**, so Django's guard stays on for every other test.

The modal test guards a real, known fault. Foundation's init failing (for
example under jQuery 3 without the one-line patch, research topic 8) leaves
the page looking fine while every Reveal modal stays shut. Step 3 extends this
test to assert jQuery 3.7.1.

Facts about the page under test:
- `news.views.submit` (URL name `news-submit`) sets `V3_DESIGN`, so the page
  extends `v3/base.html`, and it redirects anonymous users to login.
- The Upload button is `a.editor-upload[data-open="upload-modal"]` in
  `sg101/templates/core/v3/post_box.html`. The modal is `#upload-modal`
  (`.reveal`, `data-reveal`) in `post_box_modals.html`.
- `v3/base.html` loads jQuery 2.2.4 **from `ajax.googleapis.com`**, then
  `what-input.min.js`, `foundation.min.js` and `sg101.js` from static. So until
  step 3 self-hosts jQuery, this test needs outbound network access to Google's
  CDN, locally and in CI. Say so in the test class's docstring. Don't work
  around it by stubbing jQuery: that would test a page production doesn't
  serve.
- `SESSION_ENGINE` is `cached_db`, so a session made with
  `Client.force_login` must be readable by the live server. The live server
  shares the test's database and Redis.

CI (`.github/workflows/ci.yml`) runs the whole suite under `coverage run
--source='.'` and the deprecation gate, so warnings are errors. A warning
raised by Playwright, the live server or a stray unclosed resource fails CI.
Close the page, context, browser and Playwright in `tearDownClass`, in that
order.

## Reference Documentation
**Required:**
- Design: .agents/planning/2026-10-10-v3-forums-and-js/design/detailed-design.md (§7.2)

**Additional References (if relevant to this task):**
- .agents/planning/2026-10-10-v3-forums-and-js/research/playwright.md (the async override, `login_as` via session cookie, tags)
- .agents/planning/2026-10-10-v3-forums-and-js/research/jquery3.md (why the modal is the canary for Foundation's init)
- .agents/planning/2026-10-10-v3-forums-and-js/implementation/plan.md (Step 1)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. Create `core/tests/browser.py` with `BrowserTestCase(StaticLiveServerTestCase)`:
   - decorated `@tag('browser')`. Subclasses inherit it, so
     `--exclude-tag browser` skips them and `--tag browser` selects them.
   - `setUpClass` sets `DJANGO_ALLOW_ASYNC_UNSAFE` before starting Playwright,
     and `tearDownClass` restores the environment to how it found it. The
     override must not leak into tests that run after.
   - one headless Chromium per class, a fresh browser context and page per test
   - `login(user)`: `Client.force_login(user)`, then put its session cookie
     into the test's browser context for the live server's host
   - a page-error collector: listen for `pageerror` on each page, and fail the
     test in teardown (or a `tearDown`/`addCleanup` check) if any fired, with
     the error messages in the failure
2. `core` imports nothing else in the repo (AGENTS.md). The base class must
   not import any other app. Tests that use it live in their own apps.
3. Add the first test in the news app's tests: log in a user (`submit` is only
   `@login_required`), open `reverse('news-submit')`, click the Upload button, and assert
   `#upload-modal` becomes visible. Use Playwright's auto-waiting assertions
   (`expect(...).to_be_visible()`), not sleeps.
4. Follow the surrounding test code's style. Comments describe the code, never
   this plan's step numbers.
5. Add a `test-browser` target to the Makefile's `##@ Development` section,
   right after `test`, and add it to `.PHONY`. It runs only the browser tests,
   in the same way `test` runs the suite:
   `$(DC) exec web python manage.py test $(TEST_SETTINGS) --tag browser $(t)`,
   with a `##` help line in the same style. `make test` stays the full suite,
   browser tests included, so that it matches CI. Don't add an
   `--exclude-tag browser` target: `make test t="--exclude-tag browser"`
   already does that.
6. No changes to `docker_test.py` or any other settings module are needed. If
   one turns out to be, stop and raise it with Brian first.

## Dependencies
- Task 01 (Playwright and Chromium in the dev image).
- Outbound access to `ajax.googleapis.com` while the test runs.

## Implementation Approach
1. Write the modal test first against a minimal base class. See it fail for
   the right reason, then build out the base class.
2. Add the page-error collector, and the cleanup in the right order.
3. Mutation-check (see the criteria). Make each mutation, run, see the
   specific failure, revert, and confirm with `git diff` that the tree is clean.
4. Add the `test-browser` Makefile target.
5. Run `make test-browser`, `make test t="--exclude-tag browser"`,
   `make test` (the full suite), and `make deprecation-gate` as its own run.
6. On Brian's go-ahead to commit and push, watch CI and record the job's
   duration against a recent run on `main`.

## Acceptance Criteria

1. **The upload modal opens**
   - Given a logged-in user on `/news/submit/` in headless Chromium
   - When the post box's Upload button is clicked
   - Then `#upload-modal` is visible, and the test passes

2. **Mutation: Foundation removed**
   - Given the `foundation.min.js` script tag removed from `v3/base.html`
   - When the modal test runs
   - Then it fails because the modal never becomes visible; restore the tag afterwards

3. **Mutation: an uncaught page error**
   - Given an inline `<script>` that throws, added to the page
   - When the modal test runs
   - Then the page-error collector fails the test and names the thrown error, even though the modal opens; restore afterwards

4. **The async override doesn't leak**
   - Given the full suite run with browser tests included
   - When a test outside `BrowserTestCase` runs after a browser test class
   - Then `DJANGO_ALLOW_ASYNC_UNSAFE` is in the state it was before the class started

5. **Tags select and exclude**
   - Given the suite
   - When run with `make test-browser`, then `make test t="--exclude-tag browser"`, then `make test`
   - Then the first runs only the modal test, the second runs everything else and not it, and the third runs both, its count being the sum of the other two

6. **`make help` lists the target**
   - Given the Makefile change
   - When `make help` runs
   - Then `test-browser` appears in the Development section with its help line

7. **The suite, the gate and CI**
   - Given the change
   - When the full suite runs, then the deprecation gate as its own run, then CI on push
   - Then all three are green with no new warnings, and CI's job duration before and after is reported

## Metadata
- **Complexity**: Medium
- **Labels**: Playwright, browser tests, test infrastructure, Foundation, post box, Makefile
- **Required Skills**: Django `StaticLiveServerTestCase`, Playwright for Python (sync API), Django sessions and test client, mutation testing
