# Task: The post box as ES modules, proven on the news submission page

## Description
Rewrite the post box's JavaScript as plain ES modules with no jQuery and no
jQuery Form: `core/http.js`, plus `post_box/editor.js`, `post_box/post_box.js`,
`post_box/preview.js`, `post_box/hot_link.js` and `post_box/uploads.js`.
Switch **one** page, `news/submit_news.html`, to load the new entry module, and
prove it there with browser tests. Behaviour stays as today except for one
change: hot-link and upload insert their image code **at the cursor** instead
of appending it. The other ten pages keep the old `post_box.js` until task 03.

## Background
Today `sg101/static/js/v3/post_box.js` (221 lines) is one jQuery file. It has
global helpers (`editorWrapSelection`, `editorPrependLines`, `editorLink`), a
`$(document).ready` that wires each `.v3-editor`, and jQuery Form `ajaxForm`
handlers for `#hot-link-form` and `#photo-upload-form`. Preview, hot-link and
upload listen for Foundation's `open.zf.reveal` / `closed.zf.reveal` jQuery
events. A module-level `$postBox` records which textarea opened a modal,
because one page's modals are shared by every post box on it (profile edit has
two).

The design (§3.2, §4.1, §4.2) sets the shape:
- **The jQuery boundary.** Modules never import or call jQuery. Foundation
  still opens and closes reveals through `data-open` / `data-close`. A module
  reacts to the `click` on its own toolbar button, not to Foundation's jQuery
  events. To close a reveal from code, it clicks that reveal's `[data-close]`
  button.
- **`core/http.js`:** `postForm(url, formData, {timeoutMs = 30000})`,
  `getJSON(url, params, {timeoutMs})`, and `RequestError` (whose `message` is
  for the member). It adds `X-CSRFToken` from the `csrftoken` cookie and
  `X-Requested-With: XMLHttpRequest`, and uses an `AbortController` timeout.
  On a non-2xx response the message comes from, in order: the JSON body's
  `error_msg`; a plain-text body under 200 characters; the status text; then
  "Something went wrong (status N)". An HTML error page never reaches the
  member as markup.
- **`editor.js`:** `wrapSelection`, `prependLines`, `insertLink`, and
  `insertAtCursor(textarea, text, {ownLine})`. That inserts at the saved
  selection, puts the caret after it, and with `ownLine` adds newlines so the
  text sits on its own line. The saved selection must survive the modal
  taking focus.
- **`post_box.js` (entry):** finds every post box, wires its buttons, and keeps
  the **active post box** (the textarea whose modal button was clicked last).
- **`preview.js`:** POSTs the active textarea's text as `data` to
  `/comments/markdown/v3/` when the preview button is clicked, and shows the
  HTML in `#editor-preview-panel`.
- **`hot_link.js`, `uploads.js`:** today's forms and status callouts, sent with
  `postForm`. Uploads stay **one file at a time**; multi-upload is step 5.
  Today's upload error path does `$.parseJSON(xhr.responseText)`, which throws
  on a non-JSON body. `http.js` replaces that.

Facts measured for this task:
- **`csrftoken` is readable from JavaScript.** No settings module sets
  `CSRF_COOKIE_HTTPONLY`, and `sg101.js` already reads the cookie. Check it
  again if that changes.
- **`core.functions.is_ajax` checks `X-Requested-With`.** Both
  `upload_ajax_v3` and `hotlink_image` return 405 without it, so `http.js` must
  send it.
- **Hot-link needs no fetch for an allowed host.** `HotLinkImageForm.save`
  returns an `https` URL whose host is in `USER_IMAGES_SOURCES`
  (`surfguitar101.com`, the two S3 hosts, `lh3.googleusercontent.com`)
  unchanged, without downloading it. `clean()` still calls `rate_limit_user`.
  So the browser test can hot-link `https://surfguitar101.com/…` with no
  network fetch and **no settings change**. That replaces the plan's
  suggestion to serve an image from the live server and allow its host in
  test settings. Confirm in `user_photos/forms.py` before relying on it.
- **Uploads:** `USER_PHOTOS_ENABLED` is `True` in base settings, and
  `USER_PHOTOS_LOCAL_UPLOAD` is `False`. The upload test uses
  `override_settings(USER_PHOTOS_LOCAL_UPLOAD=True, MEDIA_ROOT=<temp dir>)` and
  never reaches S3 (design §7.2).
- **`submit_news.html`** renders `{% post_box add_form.short_markup %}`,
  includes `core/v3/post_box_modals.html`, and in `{% block custom_js %}`
  loads `js/jquery.form.min.js` then `js/v3/post_box.js`. Both are replaced on
  this page by one `<script type="module">` for the entry module.
- The modals' HTML (`post_box_modals.html`) and the toolbar
  (`core/v3/post_box.html`) are shared with ten other pages still on the old
  script. Change them only where both old and new scripts still work.
  Otherwise add the hooks the modules need without removing what the old
  script uses. Task 03 removes the leftovers.
- **Coverage may under-count browser tests.** CI's report showed
  `core/tests/browser.py` at 72% and `news/tests/test_browser.py` at 85%,
  although the test runs and passes. A likely cause, not confirmed: coverage
  isn't following Playwright's greenlets without its `concurrency` setting.
  Find out which lines are reported missing and why, and raise any settings
  change with Brian before making it.

## Reference Documentation
**Required:**
- Design: .agents/planning/2026-10-10-v3-forums-and-js/design/detailed-design.md (§3.2, §4.1, §4.2, §6, §7.2)

**Additional References (if relevant to this task):**
- .agents/planning/2026-10-10-v3-forums-and-js/research/upload-error-message.md (the `msg` / `error_msg` mismatch; the server fix itself is step 5)
- .agents/planning/2026-10-10-v3-forums-and-js/research/playwright.md (uploads under `override_settings`)
- .agents/planning/2026-10-10-v3-forums-and-js/STATUS.md (step 1: `BrowserTestCase`)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. Create, under `sg101/static/js/v3/`: `core/http.js`, `post_box/editor.js`,
   `post_box/post_box.js`, `post_box/preview.js`, `post_box/hot_link.js` and
   `post_box/uploads.js`. Use relative import specifiers only (task 01's
   storage rewrites them). Don't use jQuery, jQuery Form, dynamic `import()`
   or a build step.
2. Keep today's behaviour for every toolbar button: bold `**`, italic `_`,
   strike `---`, link (prompt, `[Link](url)` or `[selection](url)`), quote
   `> `, tablature four spaces, bullet `* `, numbered `1. `. Also keep
   preview, hot-link, upload, and the status callouts' texts.
3. Hot-link and upload insert `![image](url)` with
   `insertAtCursor(…, {ownLine: true})`, not by appending.
4. Errors reach the member as one sentence in the modal's status callout,
   through `RequestError.message`. No `alert()` is added. Preview's existing
   `alert()` becomes a message in the preview panel.
5. Switch `news/submit_news.html` to the entry module, and drop jQuery Form
   from that page. The other ten pages are unchanged.
6. Browser tests (with step 1's `BrowserTestCase`, in the news app or a
   `core` browser test module that imports no other app) on news submit:
   - preview renders Markdown (for example `**bold**` shows a `<strong>`)
   - bold wraps the selection; link inserts with a URL given to the prompt
     (Playwright's `page.on('dialog')`)
   - hot-link of an allowed-host `https` URL inserts the code at the cursor,
     not at the end, in text with a caret set in the middle
   - a single upload of a small generated image inserts at the cursor, under
     local upload and a temp `MEDIA_ROOT`
   - an upload of a non-image shows a readable reason in the callout and
     inserts nothing
7. Comments describe the code, never this plan's step numbers.

## Dependencies
- Task 01 (hashed module imports), for production.
- Step 1's `BrowserTestCase` and `make test-browser`.
- `ajax.googleapis.com` reachable during browser tests until jQuery is
  self-hosted in step 3.

## Implementation Approach
1. Write the browser tests first, against the page as it is today. Those
   whose behaviour exists today (preview, bold, link, single upload) should
   pass on the old script. That proves the tests before the rewrite. The
   at-cursor tests should fail, because today's code appends.
2. Write `http.js` and `editor.js`, then the entry and the feature modules.
   Switch `submit_news.html`.
3. Make the tests pass on the new modules. Mutation-check at least:
   `insertAtCursor` appending instead, `X-Requested-With` not sent, and the
   error message taken from the status text instead of `error_msg`.
4. Check in a browser at phone and desktop widths that nothing else on the
   page moved. Watch the console and network panels: no jQuery Form, and no
   errors.
5. Run `make test-browser`, the full suite, and the deprecation gate as its own
   run.

## Acceptance Criteria

1. **Every toolbar button behaves as before**
   - Given news submit on the new modules
   - When each text button is used on a selection, and link with a prompt answer
   - Then the textarea holds what the old script produced

2. **Preview**
   - Given text with Markdown in the post box
   - When the preview button is clicked
   - Then the preview panel shows the rendered HTML, and a failure shows a readable message in the panel instead of an `alert()`

3. **Hot-link and upload insert at the cursor**
   - Given text with the caret in the middle
   - When an allowed-host URL is hot-linked, or a small image uploaded under local upload
   - Then `![image](url)` appears on its own line at the caret, not at the end

4. **A failed request reads as a sentence**
   - Given an upload of a non-image
   - When Upload is clicked
   - Then the callout shows the server's reason, nothing is inserted, and the Upload button is enabled again

5. **No jQuery in the modules**
   - Given the new files
   - When searched for `$(`, `jQuery` and `ajaxForm`
   - Then none appear, and the page loads no `jquery.form.min.js`

6. **Mutations are caught**
   - Given each mutation in the approach, made one at a time
   - When the browser tests run
   - Then a test fails for each; all restored, tree clean

7. **Suite, gate and CI**
   - Given the change
   - When the suite runs, then the gate as its own run, then CI on push
   - Then all are green, and the coverage question above is answered in the task's notes

## Metadata
- **Complexity**: High
- **Labels**: JavaScript, ES modules, post box, fetch, Playwright, browser tests, uploads
- **Required Skills**: Vanilla JavaScript (ES modules, fetch, AbortController, textarea selection), Foundation Reveal, Django CSRF, Playwright for Python
