# Implementation plan: the V3 forums, the post box, and the site's JavaScript

Design: `../design/detailed-design.md`. Requirements: `../idea-honing.md`
(Q1–Q13). Research: `../research/`.

## Checklist

- [x] Step 1: Playwright in the dev image, and the first browser test
- [x] Step 2: The post box as ES modules, without jQuery — **ships**
- [x] Step 3: jQuery 3.7.1 and jQuery UI 1.13.3, self-hosted — **ships**
- [ ] Step 4: Smileys in the post box (#9) — **ships**
- [ ] Step 5: Upload error messages, then multiple image uploads (#16) — **ships**
- [ ] Step 6: Port the `v3-dev` reading pages, and the screenshot review
- [ ] Step 7: The complete post card, and the topic page's JavaScript
- [ ] Step 8: Posting forms, the video button, and the confirmation pages — **ships: forums release 1**
- [ ] Step 9: The list pages — **ships: forums release 2**
- [ ] Step 10: The moderator pages — **ships: forums release 3**
- [ ] Step 11: Remove the shoutbox — **ships**
- [ ] Step 12: Retire `base.html`, its assets, and `V3_DESIGN` — **ships**

## How the steps work

**Branches (Q11).** Each shipping group is one branch cut from `main`, merged
when Brian deploys it. `main` always matches what leopard should run.

| Branch (placeholder name) | Steps | Ships as |
|---|---|---|
| `post-box-vanilla` | 1, 2 | post box rewrite |
| `jquery3` | 3 | jQuery 3 |
| `smileys` | 4 | #9 |
| `multi-upload` | 5 | #16 |
| `forums-v3-release-1` | 6, 7, 8 | forums release 1 |
| `forums-v3-release-2` | 9 | forums release 2 |
| `forums-v3-release-3` | 10 | forums release 3 |
| `retire-shoutbox` | 11 | shoutbox removal |
| `retire-base-html` | 12 | `base.html` retirement |

**Every step:**

- **Tests come first or alongside.** Each browser test is mutation-checked:
  break what it guards once, see it fail, restore.
- **The suite passes,** and so does the deprecation gate as its own run
  (AGENTS.md).
- **A Sass change is committed with its rebuilt `main.min.css`.**
- **Code comments describe the code,** never this plan's step numbers.
- **Brian reviews before each commit.** Each step goes through
  `/agent-sops:code-task-generator` and `/agent-sops:code-assist`.

---

## Step 1: Playwright in the dev image, and the first browser test

**Objective.** Browser tests run in the suite and in CI, proved by one test
against the post box as it is today.

**Guidance.**

- **Dockerfile `dev` target only:** add `playwright` to
  `requirements_dev.txt`, and run `playwright install --with-deps --only-shell
  chromium` as root before the `USER` switch. The `prod` target must not change.
- **`core/tests/browser.py`:** the `BrowserTestCase` base class (design §7.2):
  - a browser per class
  - `DJANGO_ALLOW_ASYNC_UNSAFE` set for these tests only
  - `login(user)`
  - fails on any uncaught page error
  - tagged `browser`
- **First test:** on `/news/submit/`, logged in, clicking Upload opens the
  upload modal.
- **CI:** check the job still finishes within reason, and record the image
  build time and size before and after.

**Tests.**

- The modal test passes.
- **Mutation:** remove `foundation.min.js` from `v3/base.html` and the test
  fails; restore.
- **Mutation:** throw from an inline script on the page and the page-error
  collector fails the test; restore.
- `docker compose build` of the `prod` target is byte-for-byte unaffected:
  same `requirements.txt`, no Playwright.

**Integration.** This is test infrastructure every later step uses. No
shipped behaviour changes.

**Demo.** `manage.py test --tag browser` opens a real headless Chromium against
the live test server and passes. The same run is green in CI.

---

## Step 2: The post box as ES modules, without jQuery

**Objective.** Every post box behaves exactly as today, but runs on plain ES
modules with no jQuery and no jQuery Form, and module imports are cache-busted
in production.

**Guidance.**

- **`core.storage.ManifestStaticFilesStorage`** with
  `support_js_module_import_aggregation = True`, used in `production.py`
  (design §3.3).
- **`sg101/static/js/v3/core/http.js`** (design §4.1).
- **`post_box/editor.js`, `post_box/post_box.js`, `post_box/preview.js`,
  `post_box/hot_link.js`, `post_box/uploads.js`**, with uploads still one file
  at a time.
- **The 12 templates** that load `js/v3/post_box.js` and `jquery.form.min.js`
  switch to `<script type="module">` for the entry module, and drop jQuery
  Form wherever only the post box needed it.
- **Hot-link and upload insert at the cursor** instead of appending (design
  §4.2).
- **Delete the old `post_box.js`.**

**Tests.**

- **The storage test.** Post-process a temporary static tree and assert the
  hashed entry module imports hashed specifiers. **Mutation:** set the flag
  `False` and see it fail.
- **Browser:**
  - preview renders Markdown
  - hot-link inserts at the cursor. Fetching an outside URL in a test isn't
    allowed, so serve a small image from the live server and allow its host
    in the test settings.
  - a single upload inserts at the cursor, with local upload and a temp
    `MEDIA_ROOT`
  - the bold and link buttons work
  - on `bio/edit_profile` (two post boxes), the right textarea receives the
    insertion
- **Unit tests** of `editor.js`'s pure functions are covered through the
  browser tests. No Node test runner (Q2).

**Integration.** Builds on step 1's base class. Steps 4, 5 and 8 extend these
modules.

**Demo.** On news submit, profile edit, message compose and a comment form, the
toolbar, preview, hot-link and upload all work. The network panel shows no
jQuery Form, and a production-style `collectstatic` shows hashed imports.
**Merge and deploy steps 1–2.**

---

## Step 3: jQuery 3.7.1 and jQuery UI 1.13.3, self-hosted

**Objective.** Every V3 page runs on a self-hosted jQuery 3.7.1. Foundation,
the datepickers and the autocompletes behave exactly as on 2.2.4.

**Guidance (design §4.3).**

- **Vendor into `sg101/static/js/vendor/`**, with a README giving the version,
  source URL and SHA-256 of each file:
  - `jquery-3.7.1.min.js`
  - jQuery UI 1.13.3 (JS, and the `redmond` theme CSS and images)
- **`v3/base.html` loads jQuery from `{% static %}`.** The `script_tags`
  `jquery-ui` entries point at the local copies. The old design's
  `jquery` 1.11 entry is untouched, since it goes in step 12.
- **The one-line Foundation patch**, recorded in the README.
- **Reveal's `aria-hidden` (Brian, 2026-10-14).** Opening any Reveal modal,
  Foundation sets `aria-hidden="true"` on `<body>`, and the overlay it creates
  (`_makeOverlay`) carries `aria-hidden="true"` while holding the modal it
  focuses. Chrome refuses both and logs an error and a warning, on every post
  box modal (step 2 task 03's walk). **Required:** with a modal open, neither
  `<body>` nor any ancestor of the focused modal has `aria-hidden="true"`, and
  `aria-hidden` is put back as it was on close. **Not yet decided:** how. A
  second patch to the vendored file, recorded in the README with the first,
  is the likely shape. Measure first, before choosing:
  - whether Foundation 6.9.0 changed this upstream (its fix shows the intent,
    though there's no upgrade, Q12/Q13)
  - what Firefox and Safari do with `aria-hidden` on `<body>`, where Chrome
    refuses it
  - whether the overlay needs to be hidden from assistive technology at all,
    or `inert` on the page behind does that job
- **`comments.js`:** `.size()` → `.length`.

**Tests.**

- **Browser:** extend step 1's modal test to assert the page runs jQuery
  3.7.1. **Mutation:** revert the Foundation patch, and the modal test fails.
- **Browser:** the datepicker on `bio/edit_profile` and the autocomplete on
  `bio/member_search` appear directly under their inputs. **Mutation:** load
  jQuery UI 1.11.0, and the autocomplete test fails, since its menu sits at
  (0, 0).
- **Browser:** with a post box modal open, `<body>` and the modal's ancestors
  have no `aria-hidden="true"`, and Chrome logs no console error. **Mutation:**
  put back each of Reveal's two `aria-hidden` settings in turn, and the test
  fails each time.
- **Manual (design §7.3), at phone and desktop widths:**
  - the navigation drilldown and dropdown
  - the Orbit banner
  - the home page Cycle slideshow
  - posting a comment on a download, a poll and a photo of the day

**Integration.** Independent of step 2's modules, which use no jQuery. It
replaces the library the rest of the V3 site runs on.

**Demo.** Any V3 page reports `jQuery.fn.jquery === "3.7.1"` with no console
errors. No request leaves for `ajax.googleapis.com` from a V3 page. Datepicker
and autocomplete look as before. **Merge and deploy.**

---

## Step 4: Smileys in the post box (#9)

**Objective.** A smiley button in every post box opens a modal with every
smiley. Clicking one inserts its code at the cursor.

**Guidance (design §4.2).**

- **`{% smiley_picker %}`** inclusion tag (main set, then extra; lazy images)
  in `post_box_modals.html`.
- **The smiley toolbar button**, visible on small screens.
- **`post_box/smileys.js`**, using `editor.insertAtCursor` with whitespace
  padding. The modal stays open with a Done button.

**Tests.**

- **Tag test:** main before extra, codes HTML-escaped in `data-code`.
- **Render test:** text with an inserted code renders the smiley image through
  `core/markup.py`. That proves the padding meets `get_smiley_regexes`.
- **Browser:**
  - place the cursor mid-word, insert a smiley, and assert the exact
    resulting text, including the spaces
  - insert two in a row, and both are correctly spaced
  - **Mutation:** drop the padding and the test fails.

**Integration.** Extends step 2's entry module and `editor.js`.

**Demo.** On news submit, insert three smileys at different points, preview,
and all three render as images. **Merge and deploy; close #9.**

---

## Step 5: Upload error messages, then multiple image uploads (#16)

**Objective.** A rejected upload says why. A member can pick up to 10 images,
remove any, and upload them one request at a time, each inserted as it
finishes.

**Guidance.**

- **Server first:** `upload_ajax_v3` returns every message in `error_msg`.
  The exception path returns a generic message and logs the exception
  (design §4.2, R10).
- **Then `post_box/uploads.js`:**
  - `multiple` file input and file list with thumbnails (object URLs,
    revoked)
  - remove buttons
  - the cap of 10, with a message when exceeded
  - a sequential queue
  - per-file ✓/✗ with the reason
  - a summary line
  - Upload disabled while running
- The `#32` resize bug is not part of this step.

**Tests.**

- **View tests** for every error path: not an image, over the rate limit,
  uploads disabled, an exception in save, not logged in, not AJAX. Each
  asserts `error_msg` carries the message. **Mutation:** restore `msg` and
  the form-error test fails.
- **Browser:**
  - 3 files, one not an image: 2 image codes inserted in order, 1 ✗ showing
    the server's reason
  - choosing 12 keeps 10 and says so
  - removing a file before upload means it isn't sent

**Integration.** Extends step 2's `uploads.js` and `http.js`.

**Demo.** On a forum-free V3 page with a post box, choose 4 photos and a text
file. Remove one photo. Upload: 3 image codes land at the cursor, and the text
file shows "Upload a valid image…". **Merge and deploy; close #16.**

---

## Step 6: Port the `v3-dev` reading pages, and the screenshot review

**Objective.** The forums index, a forum's topic list and the topic page
render on `v3/base.html` from `v3-dev`'s templates, and Brian reviews the look
before anything is built on it (Q6).

**Guidance.**

- **Bring over from `v3-dev`:** `index.html`, `forum_index.html`,
  `topic.html`, `display_post_v3.html`, `new_post_form.html`, the forum
  fragments, and the four shared fragments (design §4.4). Also the Sass in
  `_sg101.scss`/`_sg101_settings.scss`, then rebuild the CSS.
- **Update for Django 5.2:** `{% load static %}`, and `is_authenticated`
  without the call.
- **Add `V3_DESIGN: True`** to the three views. `quick_reply_ajax` renders
  `display_post_v3.html`.
- **Card colours by CSS `:nth-child`**, not `{% cycle %}`.
- **Quick reply, flag and delete aren't expected to work on this branch until
  step 7.** Today's `forums.js` targets the old table markup. This branch
  isn't deployed before step 8, so nothing is lost, and porting `v3-dev`'s
  jQuery variant only to delete it a step later isn't worth it.
- **Screenshots:** the three pages at 360 px and desktop widths, as anonymous,
  member and moderator, on dev data. Include **the post box toolbar at 360 px
  with 7 buttons** (smiley plus a stand-in video button), to settle R11's fit
  question.

**Tests.**

- **Render tests:** each page extends `v3/base.html` for each role.
  `/forums/topic/<id>/` returns 200 with the posts.
- **Browser:** the topic page loads with no page errors.

**Integration.** Uses the post box from steps 2–5. **Not deployed:** this
branch continues through step 8.

**Demo and gate.** Screenshots go to Brian. **Brian's decisions on the look,
and on the toolbar's fit at 360 px, are recorded before step 7 starts.** Any
change they ask for is made in this step.

---

## Step 7: The complete post card, and the topic page's JavaScript

**Objective.** The V3 topic page has every capability of today's (R14), run by
a jQuery-free `forums/static/js/topic.js`.

**Guidance.**

- **`display_post_v3.html` gains:**
  - the post anchor (`id="post-N"`, plus the `pN` name for old links)
  - quote-reply, edit, flag and delete
  - the stranger and spammer tools
  - attachments, the signature and "Last edited"
  - PM and email links
  - the stranger highlight, and the IP link to `post_ip`

  Tools are buttons with `data-post-id`.
- **`topic.js`:**
  - quick reply (append, clear, keep the text on failure)
  - flag and delete (keep `confirm()`; a callout instead of `alert()`)
  - the delete-topic confirm
- **Drop `forums.js` from the topic page.** It's still used by the old-design
  posting forms until step 8.

**Tests.**

- **Render test:** each R14 element is present for the right roles, and absent
  for the others. For example, delete and IP only for moderators; stranger
  tools only on a stranger's post and not one's own.
- **Browser:**
  - quick reply appends a post with the next card colour and clears the box.
    **Mutation:** break the append, and the test fails.
  - `post/<id>/` lands on the post's anchor
  - flag shows the server's reply in a callout

**Integration.** Builds on step 6's templates and step 2's `http.js` and post
box.

**Demo.** On dev data, read a topic, follow a permalink, quick-reply, flag a
post, and as a moderator delete one. All of it happens without a page reload or
an `alert()`.

---

## Step 8: Posting forms, the video button, and the confirmation pages — forums release 1

**Objective.** Release 1 is complete. New topic, reply and edit run on V3 with
the video button, and the three confirmation pages are V3. **Then it ships.**

**Guidance.**

- **`{% post_box form.body video=True %}`** and `post_box/video.js`; the video
  modal posts to `/oembed/fetch/` (design §4.2).
- **`{% post_attachments form %}`** renders existing attachments into the
  posting forms (edit, and a form re-shown after errors), in `video.js`'s
  markup.
- **Convert to V3, with `V3_DESIGN`:** `new_topic`, `new_post` (with
  `?quote=`), `edit_post`, `new_topic_thanks`, `favorite_status`,
  `subscription_status`.
- **`forums/static/js/nav.js`** replaces the inline `jump_box.js` and
  `forum_query.js`.
- **Delete `forums.js`** and the `fetch_attachments` and `fetch_saved` views
  and URLs once nothing calls them.
- **If step 6's review moved a button** to fit 360 px, apply it here.

**Tests.**

- **Template tags:** `post_box` with `video=True` renders the button and
  modal, and without it renders neither. `post_attachments` renders one entry
  per saved attachment, in order.
- **Views:**
  - the converted views render on `v3/base.html`
  - an edit of a post with attachments shows them without any AJAX endpoint
  - the removed URLs 404
- **Browser:**
  - **adding a video posts its `attachment` id with a reply.** Use an
    `Oembed` row that already exists, so `fetch_media` answers from the
    database and makes no outside request.
  - removing it before posting means it isn't sent
- **Manual (design §7.3):** walk release 1 as anonymous, member and moderator.
  Check subscription mail after a reply with a real worker on the dev stack:
  deferred work, which `CELERY_TASK_ALWAYS_EAGER` hides.

**Integration.** Completes the forum pages built in steps 6–7. Nothing in
release 1 still loads `base.html`.

**Demo.** Start a topic with a video, reply with a quote, edit the reply to
add a second video, then favorite and subscribe from the topic page. Every page
in that path is V3. **Merge and deploy forums release 1; Brian announces it if
he wishes.**

---

## Step 9: The list pages — forums release 2

**Objective.** The unread, unanswered and active topic lists, a member's posts,
and favorites and subscriptions management are V3.

**Guidance.**

- **Convert `topic_list.html`, `post_list.html` and `manage_topics.html`**,
  with `V3_DESIGN` on their views (`unread_topics`, `unanswered_topics`,
  `active_topics`, `my_posts`, `posts_for_user`, `manage_favorites`,
  `manage_subscriptions`).
- **Pagination:** use `core/v3/pagination.html`, as the reading pages do.
- **`manage_topics`'s checkboxes** reuse the master-checkbox behaviour,
  through step 10's `mod.js` or a shared module if it lands first.

**Tests.**

- **Render tests** for each of the 7 URLs on `v3/base.html`.
- **The manage pages' removal POSTs** still remove what's checked.
- **Browser:** the master checkbox checks all.

**Integration.** Reuses release 1's fragments and pagination.

**Demo.** As a member with favorites and subscriptions, walk all 7 URLs and
remove a favorite. **Merge and deploy forums release 2.**

---

## Step 10: The moderator pages — forums release 3

**Objective.** The seven moderator pages are V3. With that, the forums no
longer use `base.html`.

**Guidance.**

- **Convert** `mod_forum`, `mod_split_topic`, `move_topic`, `post_ip`,
  `stranger`, `spammer` and `spammer_nailed`, with `V3_DESIGN` on their views.
- **`forums/static/js/mod.js`** replaces `forums_mod.js`.
- **Afterwards, grep** that no forum template extends `base.html`.

**Tests.**

- **Render tests** per page, as a moderator, and 403 or a redirect as a
  member, as today.
- **The bulk actions** (stick, lock, delete, move) still act on the checked
  topics. Split and move still work.
- **Browser:** the master checkbox on `mod_forum`.

**Integration.** Completes the forums. After this, only the shoutbox and the
flatpages template (if #33 hasn't landed) extend `base.html`.

**Demo.** As a moderator, bulk-lock two topics, split a topic, move one, and
mark a stranger as legitimate. Every page is V3. **Merge and deploy forums
release 3; close #17.**

---

## Step 11: Remove the shoutbox

**Objective.** The shoutbox's data is archived and its tables dropped, and the
app is gone.

**Guidance (design §4.5, items 1–3).**

1. **Commit `archive/shoutbox/`,** a `dumpdata shoutbox` export taken from
   production. **Brian runs the export on leopard.**
2. **On leopard, before deploying the removal:** `make prod-manage
   cmd="migrate shoutbox zero"`. **Brian runs it.**
3. **Remove** `shoutbox/`, the `/shout/` URLs, its templates and static
   files, and the setting entry. Also remove `ShoutFlag` from
   `custom_admin_tags.py` and the admin dashboard, and the shout deletion in
   `antispam/utils.py` with its test.

**Tests.**

- `/shout/` 404s.
- The admin dashboard renders without a shouts line.
- `deactivate_spammer` still deactivates and still deletes what it should.
- `makemigrations --check` is clean.

**Integration.** `base.html` still includes the shoutbox tag, so remove that
include in this step too. `base.html` itself goes in step 12.

**Demo.** `/shout/` is gone. The archive file holds every shout, and its count
matches production's before the drop. **Merge and deploy, in the order above.**

---

## Step 12: Retire `base.html`, its assets, and `V3_DESIGN`

**Objective.** One base template, one jQuery, and none of the old design's
assets.

**Guidance (design §4.5, items 4–6).**

- **Delete `base.html` and what only it used:**
  - `navbar.html`
  - Blueprint and `css/base.css`
  - markItUp
  - the `script_tags` entries for jQuery 1.11 and markItUp
  - the `/smiley/farm/` views and `smiley_farm` tag
  - the old forum templates no longer rendered (`display_post.html` and
    others)
  - the three unrendered `ygroup/*.html`
  - `flatpages/default.html` if #33 hasn't landed
- **Grep before deleting each asset:** for every file, show that nothing
  references it.
- **Update the navigation tests** for one base template.
- **`V3_DESIGN`, as its own commit:**
  - the eight tags render their `v3/` templates unconditionally
  - delete the eight old variant templates
  - remove the flag from the 21 files that set it
  - update the two tests that pass it

**Tests.**

- **The suite and the deprecation gate pass.**
- **Every URL resolves to a page that renders:** a test that walks the URL
  conf's named routes taking no arguments and checks each renders, with no
  `TemplateDoesNotExist`.
- **Browser:** step 3's tests still pass.
- **A static check:** nothing under `sg101/templates` extends `base.html`,
  and `rg 'V3_DESIGN'` finds nothing.

**Integration.** Finishes R2 and the part of #18 this project covers.

**Demo.** `git grep base.html` finds no template that extends it. No page
loads Blueprint, jQuery 1.11 or markItUp. The home page, a forum topic, news
and a profile render as before. **Merge and deploy; close #18 or narrow it
to what remains:** jQuery itself (tied to Foundation), and replacing jQuery
UI's datepicker and autocomplete.
